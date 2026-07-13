"""Execute a report definition and return (columns, rows)."""
from decimal import Decimal


def _num(v):
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal(0)


def _match(row, f):
    field, op, val = f.get("field"), f.get("op", "eq"), f.get("value")
    cell = row.get(field)
    if op == "eq":
        return str(cell) == str(val)
    if op == "ne":
        return str(cell) != str(val)
    if op == "contains":
        return str(val).lower() in str(cell or "").lower()
    if op in (">", "<", ">=", "<="):
        try:
            a, b = _num(cell), _num(val)
        except Exception:
            return False
        return {">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b}[op]
    return True


def _rows_for_source(source, tenant, user):
    from apps.invoicing.models import Invoice
    from apps.records.models import ModuleRecord

    def scope(qs, field="tenant"):
        if getattr(user, "is_superuser", False):
            return qs
        t = getattr(user, "tenant", None)
        return qs.filter(**{field: t}) if t is not None else qs

    if source == "invoices":
        out = []
        for i in scope(Invoice.objects.all()):
            out.append({"invoice_number": i.invoice_number, "type": i.invoice_type,
                        "party": i.party_name, "date": str(i.invoice_date),
                        "subtotal": float(i.subtotal), "tax": float(i.tax_amount),
                        "total": float(i.total), "status": i.status})
        return out
    return [{"id": r.id, **(r.data or {})} for r in scope(ModuleRecord.objects.filter(module=source))]


def run_report(defn, user):
    rows = _rows_for_source(defn.source, getattr(user, "tenant", None), user)
    for f in (defn.filters or []):
        rows = [r for r in rows if _match(r, f)]

    if defn.group_by:
        groups = {}
        for r in rows:
            groups.setdefault(str(r.get(defn.group_by, "—")), []).append(r)
        agg = defn.aggregate or "count"
        out = []
        for key, grp in groups.items():
            entry = {defn.group_by: key}
            if agg.startswith("sum:"):
                fld = agg.split(":", 1)[1]
                entry[f"sum_{fld}"] = float(sum(_num(x.get(fld)) for x in grp))
            entry["count"] = len(grp)
            out.append(entry)
        cols = [defn.group_by] + ([f"sum_{agg.split(':',1)[1]}"] if agg.startswith("sum:") else []) + ["count"]
        return cols, sorted(out, key=lambda x: x["count"], reverse=True)

    cols = defn.columns or (list(rows[0].keys()) if rows else [])
    return cols, [{c: r.get(c) for c in cols} for r in rows]
