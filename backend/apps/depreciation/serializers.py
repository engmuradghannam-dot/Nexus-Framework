from rest_framework import serializers

from .models import DepreciableAsset


class DepreciableAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepreciableAsset
        fields = "__all__"
