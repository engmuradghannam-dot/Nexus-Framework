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

class AIMessageViewSet(viewsets.ModelViewSet):
    queryset = AIMessage.objects.all()
    serializer_class = AIMessageSerializer
    permission_classes = [IsAuthenticated]

class AIPromptTemplateViewSet(viewsets.ModelViewSet):
    queryset = AIPromptTemplate.objects.all()
    serializer_class = AIPromptTemplateSerializer
    permission_classes = [IsAuthenticated]
