"""Seed a complete, coherent ERP demo: company -> stock -> orders -> invoices.

The existing seed_demo covers Industry/PMO only. This one populates the trading
and manufacturing spine — including the policy tables that HR, Sales and
Procurement own — so every rule implemented against ERP_Complete_System.xlsx
has real data behind it.

Idempotent: keyed on natural keys, safe to re-run. Pass --flush-demo to rebuild
the demo company from scratch.

The configured rates below are ILLUSTRATIVE DEMO VALUES, not advice. Leave
entitlements, end-of-service bands, commission rates, tier thresholds and
penalty terms are all deliberately configurable precisely because they are the
business's to decide — these are here so the screens have something in them.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

COMPANY_CODE = "DEMO-KSA"


class Command(BaseCommand):
    help = "Seed a full ERP demo: stock, orders, receipts, invoices, policies."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush-demo", action="store_true",
            help="Delete the demo company and everything under it, then rebuild.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.core.models import CompanyProfile

        if options["flush-demo".replace("-", "_")]:
            deleted, _ = CompanyProfile.objects.filter(code=COMPANY_CODE).delete()
            self.stdout.write(self.style.WARNING(f"Flushed demo ({deleted} rows)."))

        company = self._company()
        branches = self._branches(company)
        self._accounts(company)
        self._policies(company)
        items = self._items(company)
        self._stock(company, branches, items)
        self._procurement(company, branches, items)
        self._sales(company, branches, items)
        self._manufacturing(company, branches, items)

        self.stdout.write(self.style.SUCCESS(
            f"\nDemo ready for {company.name} ({COMPANY_CODE})."
        ))

    # ---------- foundation ----------

    def _company(self):
        from apps.core.models import CompanyProfile

        company, created = CompanyProfile.objects.get_or_create(
            code=COMPANY_CODE,
            defaults={"name": "شركة نكسس التجارية / Nexus Trading Co", "currency": "SAR"},
        )
        self._say("Company", company.name, created)
        return company

    def _branches(self, company):
        from apps.core.models import Branch, BinLocation, Warehouse

        specs = [
            ("Riyadh HQ", "RUH", "Head Office", "24.7136", "46.6753", 5000),
            ("Jeddah Branch", "JED", "Branch", "21.4858", "39.1925", 3000),
            ("Dammam Branch", "DMM", "Branch", "26.4207", "50.0888", 2000),
        ]
        branches = {}
        for name, code, kind, lat, lng, capacity in specs:
            branch, created = Branch.objects.get_or_create(
                company=company, code=code,
                defaults={
                    "name": name, "address": name, "branch_type": kind,
                    "latitude": Decimal(lat), "longitude": Decimal(lng),
                    "license_number": f"CR-{code}-1010",
                    "license_expiry": date.today() + timedelta(days=400),
                },
            )
            # BRN-RULE-001 already created the warehouse via signal.
            wh = Warehouse.objects.filter(branch=branch).first()
            if wh and not wh.capacity:
                wh.capacity = capacity
                wh.save(update_fields=["capacity"])
            if wh:
                for n, zone in enumerate(["A", "B"], start=1):
                    BinLocation.objects.get_or_create(
                        warehouse=wh, code=f"{zone}-01",
                        defaults={"zone": zone, "aisle": "1", "rack": str(n),
                                  "capacity": capacity // 4, "pick_sequence": n},
                    )
            branches[code] = branch
            self._say("Branch", f"{name} (+warehouse, 2 bins)", created)
        return branches

    def _accounts(self, company):
        from apps.accounts.models import Account, CostCenter

        chart = [
            ("1000", "Cash", "Asset"), ("1200", "Bank", "Asset"),
            ("1300", "Accounts Receivable", "Asset"), ("1400", "Inventory", "Asset"),
            ("2100", "Accounts Payable", "Liability"), ("2200", "VAT Payable", "Liability"),
            ("4000", "Sales Revenue", "Income"),
            ("5000", "Cost of Goods Sold", "Expense"), ("5200", "Salaries Expense", "Expense"),
        ]
        for number, name, kind in chart:
            _, created = Account.objects.get_or_create(
                company=company, account_number=number,
                defaults={"account_name": name, "account_type": kind},
            )
            self._say("Account", f"{number} {name}", created)
        for name in ["Operations", "Sales", "Administration"]:
            CostCenter.objects.get_or_create(company=company, name=name)

    # ---------- the numbers the business owns ----------

    def _policies(self, company):
        """ILLUSTRATIVE values only — every one of these is configurable
        because it is the business's call, not the code's."""
        from apps.buying.models import LatePenaltyTerm, SupplierScorecardCriterion
        from apps.crm.models import LeadScoringRule
        from apps.hr.models import (
            EndOfServiceBand, EndOfServicePolicy, HRPolicy, LeaveEntitlement,
        )
        from apps.selling.models import CommissionRule, CustomerTier

        HRPolicy.objects.get_or_create(company=company)

        for emp_type, tenure, days in [("", 0, 21), ("", 5, 30), ("Contract", 0, 15)]:
            LeaveEntitlement.objects.get_or_create(
                company=company, employment_type=emp_type, min_tenure_years=tenure,
                defaults={"days_per_year": Decimal(days)},
            )

        eosb, _ = EndOfServicePolicy.objects.get_or_create(
            company=company,
            defaults={"notes": "DEMO VALUES — HR and legal must confirm the bands."},
        )
        for lo, hi, months, resign in [(0, 5, "0.5", "0.333"), (5, None, "1", "0.667")]:
            EndOfServiceBand.objects.get_or_create(
                policy=eosb, from_years=lo, to_years=hi,
                defaults={"months_per_year": Decimal(months),
                          "resignation_fraction": Decimal(resign)},
            )

        tiers = {}
        for name, threshold, discount in [
            ("Bronze", "50000", "0"), ("Silver", "250000", "2.5"), ("Gold", "1000000", "5"),
        ]:
            tier, _ = CustomerTier.objects.get_or_create(
                company=company, name=name,
                defaults={"min_annual_revenue": Decimal(threshold),
                          "discount_percent": Decimal(discount)},
            )
            tiers[name] = tier

        CommissionRule.objects.get_or_create(
            company=company, name="Standard",
            defaults={"rate_percent": Decimal("2")},
        )
        CommissionRule.objects.get_or_create(
            company=company, name="Gold accounts", tier=tiers["Gold"],
            defaults={"rate_percent": Decimal("3.5")},
        )

        for name, weight in [("Quality", 40), ("On-time delivery", 35), ("Price", 25)]:
            SupplierScorecardCriterion.objects.get_or_create(
                company=company, name=name, defaults={"weight": Decimal(weight)},
            )
        LatePenaltyTerm.objects.get_or_create(
            company=company, supplier=None,
            defaults={"percent_per_day": Decimal("0.5"), "grace_days": 3,
                      "max_percent": Decimal("10")},
        )

        for name, field, match, value, pts in [
            ("Has email", "email", "not_empty", "", 25),
            ("Has phone", "phone", "not_empty", "", 20),
            ("Referral", "source", "equals", "Referral", 40),
            ("Named organization", "organization", "not_empty", "", 15),
        ]:
            LeadScoringRule.objects.get_or_create(
                company=company, name=name,
                defaults={"field_name": field, "match_type": match,
                          "match_value": value, "points": pts},
            )
        self.stdout.write("  Policies: HR, leave, EOSB, tiers, commission, "
                          "scorecard, penalties, lead scoring (DEMO VALUES)")

    # ---------- master data ----------

    def _items(self, company):
        from apps.inventory.models import Item, ItemGroup

        group, _ = ItemGroup.objects.get_or_create(company=company, name="Hardware")
        specs = [
            ("STL-100", "Steel Sheet 1mm", 45, 200, 500, "FIFO"),
            ("BLT-200", "Bolt M8", 2, 1000, 5000, "Moving Average"),
            ("PNT-300", "Industrial Paint 5L", 120, 50, 200, "FIFO"),
            ("CAB-400", "Cabinet Assembly", 850, 10, 40, "Moving Average"),
        ]
        items = {}
        for code, name, rate, reorder_level, reorder_qty, valuation in specs:
            item, created = Item.objects.get_or_create(
                company=company, item_code=code,
                defaults={
                    "item_name": name, "item_group": group,
                    "standard_rate": Decimal(rate), "reorder_level": reorder_level,
                    "reorder_qty": reorder_qty, "valuation_method": valuation,
                },
            )
            items[code] = item
            self._say("Item", f"{code} {name}", created)
        return items

    def _stock(self, company, branches, items):
        from apps.core.models import BinLocation, Warehouse
        from apps.inventory.models import StockEntry

        wh = Warehouse.objects.filter(branch=branches["RUH"]).first()
        bin_a = BinLocation.objects.filter(warehouse=wh, code="A-01").first()
        for code, qty, rate in [
            ("STL-100", 400, 42), ("BLT-200", 3000, 1.8), ("PNT-300", 120, 110),
        ]:
            if StockEntry.objects.filter(
                item=items[code], warehouse=wh, reference="Demo opening stock"
            ).exists():
                continue
            StockEntry.objects.create(
                company=company, branch=branches["RUH"], warehouse=wh,
                bin_location=bin_a, item=items[code], entry_type="Receipt",
                quantity=Decimal(qty), rate=Decimal(str(rate)),
                reference="Demo opening stock",
            )
        self.stdout.write(f"  Stock: opening balances in {wh.name}")

    # ---------- procurement chain ----------

    def _procurement(self, company, branches, items):
        from apps.buying.models import (
            GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem, Supplier,
        )
        from apps.core.models import Warehouse

        wh = Warehouse.objects.filter(branch=branches["RUH"]).first()
        suppliers = {}
        for name, email, rating in [
            ("مصنع الحديد السعودي / Saudi Steel Works", "sales@saudisteel.demo", 4),
            ("Gulf Fasteners Co", "info@gulffast.demo", 5),
        ]:
            sup, created = Supplier.objects.get_or_create(
                company=company, name=name,
                defaults={"email": email, "rating": rating,
                          "contract_start": date.today() - timedelta(days=300),
                          "contract_end": date.today() + timedelta(days=45),
                          "payment_terms": "Net 30"},
            )
            suppliers[name] = sup
            self._say("Supplier", name, created)

        # Set preferred suppliers so PRC-RULE-001 has something to route to.
        items["STL-100"].supplier = suppliers["مصنع الحديد السعودي / Saudi Steel Works"]
        items["STL-100"].save(update_fields=["supplier"])
        items["BLT-200"].supplier = suppliers["Gulf Fasteners Co"]
        items["BLT-200"].save(update_fields=["supplier"])

        po, created = PurchaseOrder.objects.get_or_create(
            company=company, po_number="PO-DEMO-0001",
            defaults={
                "supplier": suppliers["مصنع الحديد السعودي / Saudi Steel Works"],
                "branch": branches["RUH"], "warehouse": wh,
                "transaction_date": date.today() - timedelta(days=20),
                # Deliberately 10 days late so PRC-RULE-003's penalty is
                # visible past the 3-day grace, rather than demoing as zero.
                "required_by": date.today() - timedelta(days=10),
                "status": "Draft",
            },
        )
        if created:
            PurchaseOrderItem.objects.create(
                purchase_order=po, item=items["STL-100"], qty=200, rate=44
            )
            po.recalculate_totals()
            po.refresh_from_db()
            grn = GoodsReceipt.objects.create(
                company=company, purchase_order=po, grn_number="GRN-DEMO-0001",
                receipt_date=date.today() - timedelta(days=1), warehouse=wh,
            )
            GoodsReceiptItem.objects.create(
                goods_receipt=grn, po_item=po.items.first(),
                qty_received=200, qty_rejected=5, rejection_reason="Surface damage",
            )
            # The PO must be Submitted for a receipt to post against it.
            PurchaseOrder.objects.filter(pk=po.pk).update(status="Submitted")
            po.refresh_from_db()
            grn.submit()
            self.stdout.write("  Procurement: PO-DEMO-0001 + GRN (195 accepted, 5 rejected)")

    # ---------- sales chain ----------

    def _sales(self, company, branches, items):
        from apps.core.models import Warehouse
        from apps.crm.models import Lead
        from apps.invoicing.models import Invoice
        from apps.selling.models import Customer, SalesOrder, SalesOrderItem, SalesTaxCharge

        wh = Warehouse.objects.filter(branch=branches["RUH"]).first()
        customers = {}
        for name, email, limit in [
            ("مؤسسة البناء الحديث / Modern Build Est", "po@modernbuild.demo", "500000"),
            ("Al-Faisal Contracting", "accounts@alfaisal.demo", "150000"),
        ]:
            cust, created = Customer.objects.get_or_create(
                company=company, name=name,
                defaults={"email": email, "credit_limit": Decimal(limit),
                          "payment_terms": "Net 30", "marketing_consent": False},
            )
            customers[name] = cust
            self._say("Customer", name, created)

        for lead_name, org, source, email in [
            ("Khalid Al-Otaibi", "Otaibi Group", "Referral", "k@otaibi.demo"),
            ("Sara Nasser", "Nasser Interiors", "Website", "s@nasser.demo"),
            ("Walk-in enquiry", "", "Walk-in", ""),
        ]:
            lead, created = Lead.objects.get_or_create(
                company=company, lead_name=lead_name,
                defaults={"organization": org, "source": source, "email": email},
            )
            lead.recalculate_score()  # CRM-RULE-001

        so, created = SalesOrder.objects.get_or_create(
            company=company, so_number="SO-DEMO-0001",
            defaults={
                "customer": customers["مؤسسة البناء الحديث / Modern Build Est"],
                "branch": branches["RUH"], "warehouse": wh,
                "transaction_date": date.today() - timedelta(days=5),
                "status": "Draft",
            },
        )
        if created:
            SalesOrderItem.objects.create(
                sales_order=so, item=items["STL-100"], qty=50, rate=65
            )
            SalesOrderItem.objects.create(
                sales_order=so, item=items["PNT-300"], qty=10, rate=150
            )
            so.recalculate_totals()
            so.refresh_from_db()
            SalesTaxCharge.objects.create(
                sales_order=so, tax_rate=Decimal("15"),
                tax_amount=(so.total_amount * Decimal("0.15")).quantize(Decimal("0.01")),
            )
            so.recalculate_totals()
            so.refresh_from_db()
            SalesOrder.objects.filter(pk=so.pk).update(status="Submitted")
            so.refresh_from_db()
            so.reserve_stock()  # SAL-RULE-002 / SAL-RULE-004
            Invoice.create_from_sales_order(
                so, invoice_number="INV-DEMO-0001", invoice_date=date.today(),
                due_date=date.today() + timedelta(days=30),
            )
            self.stdout.write("  Sales: SO-DEMO-0001 (reserved) + INV-DEMO-0001 from it")

        # Trading history. Without it every customer qualifies for no tier and
        # SAL-RULE-005 demos as a blank column — technically correct, useless
        # to look at.
        history = [
            ("مؤسسة البناء الحديث / Modern Build Est", [90000, 120000, 75000]),
            ("Al-Faisal Contracting", [22000, 18000]),
        ]
        for name, amounts in history:
            for n, amount in enumerate(amounts, start=1):
                number = f"SO-HIST-{name[:3]}-{n}"
                if SalesOrder.objects.filter(so_number=number).exists():
                    continue
                past = SalesOrder.objects.create(
                    company=company, customer=customers[name], so_number=number,
                    branch=branches["RUH"], warehouse=wh,
                    transaction_date=date.today() - timedelta(days=30 * n + 10),
                    status="Delivered",
                )
                SalesOrderItem.objects.create(
                    sales_order=past, item=items["CAB-400"],
                    qty=1, rate=Decimal(amount),
                )
                past.recalculate_totals()

        for cust in customers.values():
            cust.recalculate_tier()  # SAL-RULE-005
            self.stdout.write(
                f"  Tier: {cust.name} → {cust.tier.name if cust.tier else 'none yet'}"
            )

    # ---------- manufacturing ----------

    def _manufacturing(self, company, branches, items):
        from apps.core.models import Warehouse
        from apps.manufacturing.models import BOM, BOMItem, WorkOrder, Workstation

        wh = Warehouse.objects.filter(branch=branches["RUH"]).first()
        station, _ = Workstation.objects.get_or_create(
            company=company, code="PRESS-01",
            defaults={"name": "Hydraulic Press", "branch": branches["RUH"],
                      "hour_rate": Decimal("120"),
                      "maintenance_interval_days": 90,
                      "last_maintenance_date": date.today() - timedelta(days=20)},
        )
        bom, created = BOM.objects.get_or_create(
            company=company, item=items["CAB-400"], bom_name="Cabinet Assembly v1",
            defaults={"quantity": 10, "operating_cost": Decimal("400"),
                      "labor_cost": Decimal("600")},
        )
        if created:
            BOMItem.objects.create(bom=bom, item=items["STL-100"], qty=25, rate=44)
            BOMItem.objects.create(bom=bom, item=items["BLT-200"], qty=120, rate=Decimal("1.8"))
            BOMItem.objects.create(bom=bom, item=items["PNT-300"], qty=4, rate=110)
            self.stdout.write("  Manufacturing: BOM makes 10 cabinets per batch")

        WorkOrder.objects.get_or_create(
            company=company, wo_number="WO-DEMO-0001",
            defaults={
                "branch": branches["RUH"], "warehouse": wh, "bom": bom,
                "order_date": date.today(), "item_to_manufacture": items["CAB-400"],
                "qty_to_produce": 20, "status": "Draft", "workstation_ref": station,
            },
        )
        self.stdout.write(
            "  Manufacturing: WO-DEMO-0001 left in Draft — releasing it needs an "
            "approved BOM (MFG-CTRL-001), which is a demo of the control, not a gap."
        )

    # ---------- output ----------

    def _say(self, kind, name, created):
        verb = "created" if created else "exists"
        self.stdout.write(f"  {kind}: {name} — {verb}")
