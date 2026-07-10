from rest_framework import serializers

from .models import Branch, CompanyProfile, User, Warehouse


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "department",
            "job_title",
            "permissions_level",
            "is_department_head",
            "avatar",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CompanyProfileSerializer(serializers.ModelSerializer):
    industry_vertical_name = serializers.CharField(
        source="industry_vertical.name", read_only=True
    )
    super_admin_email = serializers.CharField(
        source="super_admin.email", read_only=True
    )
    effective_modules = serializers.ReadOnlyField()
    effective_features = serializers.ReadOnlyField()
    branch_count = serializers.IntegerField(source="branches.count", read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "name",
            "code",
            "industry_vertical",
            "industry_vertical_name",
            "super_admin",
            "super_admin_email",
            "currency",
            "timezone",
            "modules_enabled",
            "features_enabled",
            "effective_modules",
            "effective_features",
            "multi_branch_enabled",
            "multi_warehouse_enabled",
            "branch_count",
            "logo",
            "address",
            "phone",
            "email",
            "website",
            "is_active",
            "created_at",
            "updated_at",
        ]


class CompanyProfileListSerializer(serializers.ModelSerializer):
    """Lightweight list view"""

    industry_vertical_name = serializers.CharField(
        source="industry_vertical.name", read_only=True
    )

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "name",
            "code",
            "industry_vertical",
            "industry_vertical_name",
            "is_active",
            "created_at",
        ]


class BranchSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    manager_name = serializers.CharField(source="manager.get_full_name", read_only=True)
    warehouse_count = serializers.IntegerField(
        source="warehouses.count", read_only=True
    )

    class Meta:
        model = Branch
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "code",
            "address",
            "latitude",
            "longitude",
            "phone",
            "manager",
            "manager_name",
            "warehouse_count",
            "is_active",
            "created_at",
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    parent_name = serializers.CharField(source="parent_warehouse.name", read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)
    sub_warehouse_count = serializers.IntegerField(
        source="sub_warehouses.count", read_only=True
    )

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "code",
            "branch",
            "branch_name",
            "parent_warehouse",
            "parent_name",
            "capacity",
            "current_occupancy",
            "occupancy_rate",
            "sub_warehouse_count",
            "is_active",
            "created_at",
        ]
