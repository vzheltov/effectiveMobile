from rest_framework import serializers

from apps.access_control.models import AccessRule, BusinessResource, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "description"]
        read_only_fields = ["id"]

    def validate_code(self, value):
        if self.instance and self.instance.code == "admin" and value != "admin":
            raise serializers.ValidationError("The admin role code cannot be changed.")
        return value


class BusinessResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessResource
        fields = ["id", "code", "name", "description"]
        read_only_fields = ["id"]


class AccessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRule
        fields = [
            "id",
            "role",
            "resource",
            "can_read_own",
            "can_read_all",
            "can_create",
            "can_update_own",
            "can_update_all",
            "can_delete_own",
            "can_delete_all",
        ]
        read_only_fields = ["id"]


class UserRolesUpdateSerializer(serializers.Serializer):
    role_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_role_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Role IDs must be unique.")
        return value


class UserRolesResponseSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    roles = RoleSerializer(many=True)
