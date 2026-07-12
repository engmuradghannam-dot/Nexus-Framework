from rest_framework import serializers

from .models import BankAccount, BankTransaction


class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = "__all__"


class BankAccountSerializer(serializers.ModelSerializer):
    balances = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ["id", "name", "bank_name", "iban", "currency", "opening_balance", "balances"]

    def get_balances(self, obj):
        return obj.balances()
