from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.apps import apps
from django.db import transaction
import requests
import json
import time
import uuid
from .models import Webhook, WebhookDelivery, FileUpload, APIRequestLog, BatchOperation
from .search import AdvancedSearchViewSet, AggregationAPIViewSet
from .tenancy import TenantViewSet, TenantUserViewSet
from .serializers import (
    WebhookSerializer, WebhookDeliverySerializer, FileUploadSerializer,
    APIRequestLogSerializer, BatchOperationSerializer
)

# ============ WEBHOOKS ============
class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        webhook = self.get_object()
        payload = {
            "event": "test",
            "timestamp": timezone.now().isoformat(),
            "data": {"message": "Webhook test"}
        }

        try:
            start = time.time()
            response = requests.post(
                webhook.url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-Webhook-Secret': webhook.secret,
                    'X-Webhook-Event': 'test',
                    **webhook.headers
                },
                timeout=webhook.timeout
            )
            duration = int((time.time() - start) * 1000)

            WebhookDelivery.objects.create(
                webhook=webhook,
                event='test',
                payload=payload,
                status='success' if response.status_code < 400 else 'failed',
                response_status=response.status_code,
                response_body=response.text[:1000],
                duration_ms=duration,
                completed_at=timezone.now()
            )

            return Response({
                "status": "success" if response.status_code < 400 else "failed",
                "status_code": response.status_code,
                "duration_ms": duration
            })
        except Exception as e:
            WebhookDelivery.objects.create(
                webhook=webhook,
                event='test',
                payload=payload,
                status='failed',
                response_body=str(e)[:1000],
                completed_at=timezone.now()
            )
            return Response({"status": "failed", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()
        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        event = request.data.get('event')
        payload = request.data.get('payload', {})

        webhooks = Webhook.objects.filter(is_active=True)
        triggered = []

        for webhook in webhooks:
            if '*' in webhook.events or event in webhook.events:
                try:
                    start = time.time()
                    response = requests.post(
                        webhook.url,
                        json={"event": event, "timestamp": timezone.now().isoformat(), "data": payload},
                        headers={
                            'Content-Type': 'application/json',
                            'X-Webhook-Secret': webhook.secret,
                            'X-Webhook-Event': event,
                            **webhook.headers
                        },
                        timeout=webhook.timeout
                    )
                    duration = int((time.time() - start) * 1000)

                    delivery = WebhookDelivery.objects.create(
                        webhook=webhook,
                        event=event,
                        payload=payload,
                        status='success' if response.status_code < 400 else 'failed',
                        response_status=response.status_code,
                        response_body=response.text[:1000],
                        duration_ms=duration,
                        completed_at=timezone.now()
                    )

                    webhook.last_triggered = timezone.now()
                    if response.status_code < 400:
                        webhook.success_count += 1
                    else:
                        webhook.fail_count += 1
                    webhook.save()

                    triggered.append({"webhook": webhook.name, "status": delivery.status})
                except Exception as e:
                    WebhookDelivery.objects.create(
                        webhook=webhook,
                        event=event,
                        payload=payload,
                        status='failed',
                        response_body=str(e)[:1000],
                        completed_at=timezone.now()
                    )
                    webhook.fail_count += 1
                    webhook.save()
                    triggered.append({"webhook": webhook.name, "status": "failed", "error": str(e)})

        return Response({"event": event, "triggered": triggered})

class WebhookDeliveryViewSet(viewsets.ModelViewSet):
    queryset = WebhookDelivery.objects.all()
    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated]

# ============ FILE UPLOAD ============
class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if file_obj:
            serializer.save(
                original_name=file_obj.name,
                file_type=file_obj.content_type,
                file_size=file_obj.size,
                url=self.request.build_absolute_uri(serializer.instance.file.url) if serializer.instance else '',
                uploaded_by=self.request.user
            )

    @action(detail=False, methods=['post'])
    def upload(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        upload = FileUpload.objects.create(
            file=file_obj,
            original_name=file_obj.name,
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            storage='local',
            url='',
            uploaded_by=request.user
        )

        upload.url = request.build_absolute_uri(upload.file.url)
        upload.save()

        serializer = self.get_serializer(upload)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def attach(self, request, pk=None):
        upload = self.get_object()
        app_label = request.data.get('app_label')
        model_name = request.data.get('model_name')
        object_id = request.data.get('object_id')

        if app_label and model_name:
            try:
                model = apps.get_model(app_label, model_name)
                obj = model.objects.get(id=object_id)
                upload.content_type = ContentType.objects.get_for_model(obj)
                upload.object_id = object_id
                upload.save()
                return Response({"status": "attached"})
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "app_label, model_name, object_id required"}, status=status.HTTP_400_BAD_REQUEST)

# ============ API LOGS ============
class APIRequestLogViewSet(viewsets.ModelViewSet):
    queryset = APIRequestLog.objects.all()
    serializer_class = APIRequestLogSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.db.models import Count, Avg

        total = APIRequestLog.objects.count()
        by_method = APIRequestLog.objects.values('method').annotate(count=Count('id'))
        avg_duration = APIRequestLog.objects.aggregate(avg=Avg('duration_ms'))
        error_rate = APIRequestLog.objects.filter(response_status__gte=400).count() / total * 100 if total else 0

        return Response({
            "total_requests": total,
            "by_method": list(by_method),
            "avg_duration_ms": round(avg_duration['avg'] or 0, 2),
            "error_rate": round(error_rate, 2),
            "top_paths": list(APIRequestLog.objects.values('path').annotate(count=Count('id')).order_by('-count')[:10])
        })

    @action(detail=False, methods=['get'])
    def errors(self, request):
        errors = APIRequestLog.objects.filter(response_status__gte=400)
        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)

# ============ BATCH OPERATIONS ============
class BatchOperationViewSet(viewsets.ModelViewSet):
    queryset = BatchOperation.objects.all()
    serializer_class = BatchOperationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        batch = self.get_object()
        batch.status = 'processing'
        batch.save()

        try:
            with transaction.atomic():
                model = apps.get_model(batch.model_name)
                items = request.data.get('items', [])
                batch.total_count = len(items)
                batch.save()

                errors = []

                for idx, item in enumerate(items):
                    try:
                        if batch.operation == 'create':
                            model.objects.create(**item)
                            batch.success_count += 1
                        elif batch.operation == 'update':
                            obj_id = item.pop('id', None)
                            if obj_id:
                                model.objects.filter(id=obj_id).update(**item)
                                batch.success_count += 1
                        elif batch.operation == 'delete':
                            obj_id = item.get('id')
                            if obj_id:
                                model.objects.filter(id=obj_id).delete()
                                batch.success_count += 1
                    except Exception as e:
                        batch.fail_count += 1
                        errors.append({"index": idx, "error": str(e), "item": item})

                batch.errors = errors
                batch.status = 'completed' if batch.fail_count == 0 else 'partial' if batch.success_count > 0 else 'failed'
                batch.completed_at = timezone.now()
                batch.save()

                return Response({
                    "status": batch.status,
                    "total": batch.total_count,
                    "success": batch.success_count,
                    "failed": batch.fail_count,
                    "errors": errors[:10]
                })
        except Exception as e:
            batch.status = 'failed'
            batch.errors = [{"error": str(e)}]
            batch.completed_at = timezone.now()
            batch.save()
            return Response({"status": "failed", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        model_name = request.data.get('model_name')
        items = request.data.get('items', [])

        batch = BatchOperation.objects.create(
            name=f"Bulk create {model_name}",
            operation='create',
            model_name=model_name,
            total_count=len(items),
            created_by=request.user
        )

        return Response({"batch_id": batch.id, "status": "created", "total": len(items)})

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        model_name = request.data.get('model_name')
        items = request.data.get('items', [])

        batch = BatchOperation.objects.create(
            name=f"Bulk update {model_name}",
            operation='update',
            model_name=model_name,
            total_count=len(items),
            created_by=request.user
        )

        return Response({"batch_id": batch.id, "status": "created", "total": len(items)})

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        model_name = request.data.get('model_name')
        ids = request.data.get('ids', [])

        batch = BatchOperation.objects.create(
            name=f"Bulk delete {model_name}",
            operation='delete',
            model_name=model_name,
            total_count=len(ids),
            created_by=request.user
        )

        return Response({"batch_id": batch.id, "status": "created", "total": len(ids)})
