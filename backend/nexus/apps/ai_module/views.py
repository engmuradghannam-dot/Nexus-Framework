from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import os
import httpx
from .models import AIModel, AIConversation, AIMessage, AIPromptTemplate
from .serializers import (
    AIModelSerializer, AIConversationSerializer, 
    AIMessageSerializer, AIPromptTemplateSerializer
)

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]

class AIConversationViewSet(viewsets.ModelViewSet):
    queryset = AIConversation.objects.all()
    serializer_class = AIConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        content = request.data.get('content', '')

        if not content:
            return Response({"error": "content required"}, status=status.HTTP_400_BAD_REQUEST)

        # Save user message
        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=content
        )

        # Get conversation history
        messages = conversation.messages.all()
        groq_messages = []
        for msg in messages:
            groq_messages.append({"role": msg.role, "content": msg.content})

        # Call Groq API
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": conversation.model.model_id or "llama3-8b-8192",
                "messages": groq_messages
            }

            response = httpx.post(GROQ_API_URL, json=payload, headers=headers, timeout=60)
            response_data = response.json()

            assistant_content = response_data['choices'][0]['message']['content']
            tokens = response_data.get('usage', {}).get('total_tokens', 0)

            # Save assistant message
            assistant_msg = AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=assistant_content,
                tokens_used=tokens
            )

            return Response({
                "user_message": AIMessageSerializer(user_msg).data,
                "assistant_message": AIMessageSerializer(assistant_msg).data
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_with_message(self, request):
        model_id = request.data.get('model_id')
        title = request.data.get('title', '')
        content = request.data.get('content', '')

        if not model_id or not content:
            return Response({"error": "model_id and content required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            model = AIModel.objects.get(id=model_id)
        except AIModel.DoesNotExist:
            return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)

        conversation = AIConversation.objects.create(
            user=request.user,
            model=model,
            title=title or content[:50]
        )

        # Send first message
        return self.send_message(request, pk=conversation.id)


    @action(detail=True, methods=['post'])
    def stream_message(self, request, pk=None):
        conversation = self.get_object()
        content = request.data.get('content', '')
        if not content:
            return Response({"error": "content required"}, status=status.HTTP_400_BAD_REQUEST)

        # Save user message
        AIMessage.objects.create(conversation=conversation, role='user', content=content)

        # Return streaming response placeholder
        return Response({
            "status": "streaming",
            "conversation_id": conversation.id,
            "message": "Use WebSocket for streaming"
        })

    @action(detail=True, methods=['post'])
    def switch_model(self, request, pk=None):
        conversation = self.get_object()
        model_id = request.data.get('model_id')
        if model_id:
            try:
                model = AIModel.objects.get(id=model_id)
                conversation.model = model
                conversation.save()
                return Response({"status": "model switched", "model": model.name})
            except AIModel.DoesNotExist:
                return Response({"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "model_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def export_conversation(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all()
        data = {
            "title": conversation.title,
            "model": conversation.model.name,
            "created_at": conversation.created_at,
            "messages": [{"role": m.role, "content": m.content, "timestamp": m.created_at} for m in messages]
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def usage_stats(self, request):
        from django.db.models import Count, Sum
        stats = AIMessage.objects.aggregate(
            total_messages=Count('id'),
            total_tokens=Sum('tokens_used')
        )
        by_model = AIMessage.objects.values('conversation__model__name').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        )
        return Response({
            "overall": stats,
            "by_model": list(by_model)
        })


class AIMessageViewSet(viewsets.ModelViewSet):
    queryset = AIMessage.objects.all()
    serializer_class = AIMessageSerializer
    permission_classes = [IsAuthenticated]

class AIPromptTemplateViewSet(viewsets.ModelViewSet):
    queryset = AIPromptTemplate.objects.all()
    serializer_class = AIPromptTemplateSerializer
    permission_classes = [IsAuthenticated]
