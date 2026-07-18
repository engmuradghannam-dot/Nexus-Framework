"""Evaluating custom formula and lookup fields — safely.

A formula field is an Excel-like expression referencing other fields:
    "{qty} * {unit_price} * 1.15"
A lookup field pulls a value from another module's row, like VLOOKUP.

The formula evaluator NEVER uses eval(). It parses the expression with Python's
ast module and walks the tree, permitting only numeric literals and the four
arithmetic operators plus parentheses. Anything else — a function call, an
attribute access, a name that isn't a resolved reference — is rejected. This is
the difference between "a calculator" and "arbitrary code execution", and it is
not negotiable for user-supplied input.
"""
import ast
import operator
import re
from decimal import Decimal, InvalidOperation

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_REF = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class FormulaError(ValueError):
    """Raised when a formula is malformed or references something unknown."""


def referenced_keys(formula):
    """The set of {field_key} references a formula depends on."""
    return set(_REF.findall(formula or ""))


def _to_number(value):
    if value is None or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise FormulaError(f"Value '{value}' is not a number.")


def evaluate_formula(formula, context):
    """Evaluate `formula`, substituting {key} from `context` (key -> value).

    Returns a Decimal. Raises FormulaError on anything unsafe or malformed —
    never executes arbitrary code, never returns a wrong number silently.
    """
    if not formula or not formula.strip():
        raise FormulaError("Formula is empty.")

    missing = referenced_keys(formula) - set(context)
    if missing:
        raise FormulaError(f"Formula references unknown field(s): {', '.join(sorted(missing))}.")

    # Replace {key} with the numeric value, parenthesised so a negative value
    # can't change the parse (e.g. a - -3).
    def sub(match):
        return f"({_to_number(context[match.group(1)])})"

    expr = _REF.sub(sub, formula)

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise FormulaError("Formula is not a valid arithmetic expression.")

    return _eval_node(tree.body)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise FormulaError("Only numbers are allowed in a formula.")
        return Decimal(str(node.value))
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise FormulaError("Only + - * / are allowed.")
        left, right = _eval_node(node.left), _eval_node(node.right)
        if op is operator.truediv and right == 0:
            raise FormulaError("Division by zero.")
        return op(left, right)
    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARY.get(type(node.op))
        if op is None:
            raise FormulaError("Unsupported unary operator.")
        return op(_eval_node(node.operand))
    # Anything else — Name, Call, Attribute, Subscript, comparison, ... — is
    # exactly what we refuse to run.
    raise FormulaError("Formula contains something that isn't simple arithmetic.")


def resolve_lookup(field, local_values):
    """Resolve a lookup field to a value from another module's row.

    `local_values` is this record's field_key -> value map. We read the local
    match value, find the source row whose match field equals it, and return the
    requested field. Returns None when there's no match — a lookup that finds
    nothing is blank, not an error and not a zero.
    """
    from django.apps import apps as django_apps

    from .models import CustomFieldValue

    match_value = local_values.get(field.lookup_match_local)
    if match_value in (None, ""):
        return None
    if not (field.lookup_module and field.lookup_match_source and field.lookup_return):
        return None

    # The source match/return fields may be real model fields on the source
    # module, or themselves custom fields. Try the model first, then custom
    # field values.
    model = _module_model(field.lookup_module)
    if model is not None:
        row = _find_model_row(model, field.lookup_match_source, match_value)
        if row is not None:
            if hasattr(row, field.lookup_return):
                return getattr(row, field.lookup_return)
            # return field is a custom field on the source row
            cfv = CustomFieldValue.objects.filter(
                field__module=field.lookup_module,
                field__field_key=field.lookup_return,
                record_id=str(row.pk),
            ).first()
            return cfv.value if cfv else None
    return None


# Maps a module name to the model whose rows it stores. Extend as modules gain
# custom-field support; an unmapped module simply can't be a lookup source yet.
_MODULE_MODELS = {
    "inventory": ("inventory", "Item"),
    "selling": ("selling", "Customer"),
    "buying": ("buying", "Supplier"),
    "invoicing": ("invoicing", "Invoice"),
    "hr": ("hr", "Employee"),
    "accounts": ("accounts", "Account"),
}


def _module_model(module):
    from django.apps import apps as django_apps

    ref = _MODULE_MODELS.get(module)
    if not ref:
        return None
    try:
        return django_apps.get_model(ref[0], ref[1])
    except LookupError:
        return None


def _find_model_row(model, match_field, match_value):
    if not hasattr(model, match_field) and match_field not in {
        f.name for f in model._meta.get_fields()
    }:
        return None
    try:
        return model.objects.filter(**{match_field: match_value}).first()
    except Exception:
        return None
