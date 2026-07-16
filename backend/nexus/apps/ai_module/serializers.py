from rest_framework import serializers
from .models import AIModel, AIConversation, AIMessage, AIPromptTemplate

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = '__all__'

class AIConversationSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = AIConversation
        fields = '__all__'

class AIPromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPromptTemplate
        fields = '__all__'
