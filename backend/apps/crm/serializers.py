from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Lead, Opportunity


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = "__all__"

    def validate(self, data):
        """CRM-RULE-002 is preventive: refuse the stage change itself."""
        new_status = data.get("status")
        if self.instance and new_status:
            probe = self.instance
            for k, v in data.items():
                if k != "status":
                    setattr(probe, k, v)
            try:
                probe.check_stage_transition(new_status)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"status": exc.messages[0]})
        return data
