from rest_framework import serializers
from .models import Webhook, WebhookDelivery, FileUpload, APIRequestLog, BatchOperation

class WebhookSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    delivery_count = serializers.IntegerField(source='deliveries.count', read_only=True)
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = '__all__'
        read_only_fields = ['secret', 'success_count', 'fail_count', 'last_triggered']

    def get_success_rate(self, obj):
        total = obj.success_count + obj.fail_count
        return round(obj.success_count / total * 100, 2) if total else 0

class WebhookDeliverySerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source='webhook.name', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = '__all__'

class FileUploadSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_size_human = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = '__all__'
        read_only_fields = ['file_size', 'url', 'thumbnail_url']

    def get_file_size_human(self, obj):
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

class APIRequestLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = APIRequestLog
        fields = '__all__'

class BatchOperationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = BatchOperation
        fields = '__all__'

    def get_progress(self, obj):
        if obj.total_count == 0:
            return 0
        return round((obj.success_count + obj.fail_count) / obj.total_count * 100, 2)
