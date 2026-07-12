"""Bank accounts, statement transactions, and reconciliation."""
from decimal import Decimal

from django.db import models


class BankAccount(models.Model):
    name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200, blank=True)
    iban = models.CharField(max_length=40, blank=True)
    currency = models.CharField(max_length=10, default="SAR")
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "bank_accounts"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def balances(self):
        txns = self.transactions.all()
        book = Decimal(self.opening_balance or 0)
        recon = Decimal(self.opening_balance or 0)
        unreconciled = 0
        for t in txns:
            delta = t.amount if t.direction == "in" else -t.amount
            book += delta
            if t.reconciled:
                recon += delta
            else:
                unreconciled += 1
        return {
            "book_balance": float(book),
            "reconciled_balance": float(recon),
            "difference": float(book - recon),
            "unreconciled_count": unreconciled,
        }


class BankTransaction(models.Model):
    DIRECTION = [("in", "Deposit"), ("out", "Withdrawal")]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    direction = models.CharField(max_length=3, choices=DIRECTION)
    reference = models.CharField(max_length=120, blank=True)
    reconciled = models.BooleanField(default=False)

    class Meta:
        db_table = "bank_transactions"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.description} {self.amount}"
