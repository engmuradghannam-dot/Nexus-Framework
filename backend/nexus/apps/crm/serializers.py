from rest_framework import serializers

from .models import Contact, Customer, CustomerInteraction, Opportunity


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class CustomerInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInteraction
        fields = '__all__'
        read_only_fields = ['created_at']


class CustomerSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    assigned_sales_rep_name = serializers.CharField(source='assigned_sales_rep.full_name', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    credit_available = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['customer_id']

    def get_credit_available(self, obj):
        return str(obj.credit_available())

    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        instance_pk = self.instance.pk if self.instance else None
        if email or phone:
            duplicates = Customer.find_duplicates(email=email, phone=phone, exclude_pk=instance_pk)
            if duplicates.exists():
                raise serializers.ValidationError(
                    'Potential duplicate customer detected by email/phone'
                )
        return attrs


class OpportunitySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    requires_discount_approval = serializers.BooleanField(read_only=True)

    class Meta:
        model = Opportunity
        fields = '__all__'

    def validate(self, attrs):
        new_stage = attrs.get('stage')
        if self.instance and new_stage and not self.instance.validate_stage_transition(new_stage):
            raise serializers.ValidationError('Invalid stage transition')
        return attrs
