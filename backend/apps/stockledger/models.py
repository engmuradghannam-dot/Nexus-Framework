"""Stock movements + inventory valuation (FIFO / LIFO / Moving Average)."""
from django.db import models


class StockMovement(models.Model):
    TYPES = [("in", "Receipt"), ("out", "Issue")]

    item_code = models.CharField(max_length=50, db_index=True)
    item_name = models.CharField(max_length=200, blank=True)
    warehouse = models.CharField(max_length=100, blank=True)
    movement_type = models.CharField(max_length=3, choices=TYPES)
    quantity = models.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date = models.DateField(db_index=True)
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "stock_movements"
        ordering = ["item_code", "date", "id"]

    def __str__(self):
        return f"{self.item_code} {self.movement_type} {self.quantity}"


def valuate(movements):
    """Return closing qty and value under FIFO, LIFO and Moving Average.

    movements: iterable of dicts/objects with movement_type, quantity, unit_cost,
    already ordered chronologically.
    """
    def q(m, k):
        v = getattr(m, k, None) if not isinstance(m, dict) else m.get(k)
        return float(v or 0)

    def typ(m):
        return getattr(m, "movement_type", None) if not isinstance(m, dict) else m.get("movement_type")

    fifo, lifo = [], []          # lists of [qty, cost]
    ma_qty = ma_val = 0.0        # moving average running qty/value

    for m in movements:
        qty, cost, t = q(m, "quantity"), q(m, "unit_cost"), typ(m)
        if t == "in":
            fifo.append([qty, cost]); lifo.append([qty, cost])
            ma_val += qty * cost; ma_qty += qty
        else:  # issue
            # FIFO: consume from front
            need = qty
            while need > 1e-9 and fifo:
                take = min(need, fifo[0][0]); fifo[0][0] -= take; need -= take
                if fifo[0][0] <= 1e-9: fifo.pop(0)
            # LIFO: consume from back
            need = qty
            while need > 1e-9 and lifo:
                take = min(need, lifo[-1][0]); lifo[-1][0] -= take; need -= take
                if lifo[-1][0] <= 1e-9: lifo.pop()
            # Moving average: issue at current avg
            avg = (ma_val / ma_qty) if ma_qty > 1e-9 else 0
            ma_qty -= qty; ma_val -= qty * avg
            if ma_qty < 0: ma_qty = 0.0; ma_val = 0.0

    fifo_qty = sum(l[0] for l in fifo)
    fifo_val = sum(l[0] * l[1] for l in fifo)
    lifo_val = sum(l[0] * l[1] for l in lifo)
    ma_avg = (ma_val / ma_qty) if ma_qty > 1e-9 else 0
    return {
        "closing_qty": round(fifo_qty, 2),
        "fifo_value": round(fifo_val, 2),
        "lifo_value": round(lifo_val, 2),
        "moving_avg_value": round(ma_qty * ma_avg, 2),
        "moving_avg_cost": round(ma_avg, 2),
    }
