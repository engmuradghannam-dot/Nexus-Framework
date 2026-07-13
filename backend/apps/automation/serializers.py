from rest_framework import serializers

from .models import ScheduledJob, Webhook, WebhookDelivery


class ScheduledJobSerializer(serializers.ModelSerializer):
    next_run = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ScheduledJob
        fields = "__all__"
        read_only_fields = ["tenant", "last_run", "run_count"]


class WebhookSerializer(serializers.ModelSerializer):
    delivery_count = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = ["tenant"]

    def get_delivery_count(self, obj):
        return obj.deliveries.count()


class WebhookDeliverySerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source="webhook.name", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = "__all__"
        read_only_fields = ["tenant"]
