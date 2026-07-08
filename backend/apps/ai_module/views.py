from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import AIModel, Prediction, Insight
from .serializers import AIModelSerializer, PredictionSerializer, InsightSerializer


class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.select_related('owner').prefetch_related('predictions', 'insights')
    serializer_class = AIModelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['model_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['accuracy', 'created_at', 'last_trained']

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        total = AIModel.objects.count()
        deployed = AIModel.objects.filter(status='deployed').count()
        avg_accuracy = AIModel.objects.filter(accuracy__gt=0).aggregate(
            avg=models.Avg('accuracy')
        )['avg'] or 0
        total_predictions = Prediction.objects.count()
        unread_insights = Insight.objects.filter(is_read=False).count()
        return Response({
            'total_models': total,
            'deployed_models': deployed,
            'average_accuracy': round(avg_accuracy, 2),
            'total_predictions': total_predictions,
            'unread_insights': unread_insights,
        })

    @action(detail=True, methods=['get'])
    def predictions(self, request, pk=None):
        model = self.get_object()
        predictions = model.predictions.all()[:50]
        serializer = PredictionSerializer(predictions, many=True)
        return Response(serializer.data)


class PredictionViewSet(viewsets.ModelViewSet):
    queryset = Prediction.objects.select_related('model')
    serializer_class = PredictionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model']


class InsightViewSet(viewsets.ModelViewSet):
    queryset = Insight.objects.select_related('source_model', 'related_project')
    serializer_class = InsightSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['severity', 'is_read', 'source_model']
    ordering_fields = ['created_at']

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Insight.objects.filter(is_read=False).update(is_read=True)
        return Response({'status': 'all insights marked as read'})
