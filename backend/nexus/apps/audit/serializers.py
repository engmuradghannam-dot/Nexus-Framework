from rest_framework import serializers

from .models import ChangeHeader, ChangeItem


class ChangeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeItem
        fields = '__all__'


class ChangeHeaderSerializer(serializers.ModelSerializer):
    content_type_label = serializers.CharField(source='content_type.model', read_only=True)
    items = ChangeItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChangeHeader
        fields = '__all__'
