from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access_control.models import AccessRule, BusinessResource, Role
from apps.access_control.permissions import IsAccessAdmin
from apps.access_control.serializers import (
    AccessRuleSerializer,
    BusinessResourceSerializer,
    RoleSerializer,
    UserRolesUpdateSerializer,
)
from apps.access_control.services import (
    LastAdministratorError,
    UnknownRolesError,
    replace_user_roles,
)
from apps.users.models import User


class RoleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = Role.objects.order_by("id")
    serializer_class = RoleSerializer


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = Role.objects.order_by("id")
    serializer_class = RoleSerializer

    def perform_destroy(self, instance):
        if instance.code == "admin":
            raise ValidationError({"detail": "The admin role cannot be deleted."})
        instance.delete()


class BusinessResourceListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = BusinessResource.objects.order_by("id")
    serializer_class = BusinessResourceSerializer


class BusinessResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = BusinessResource.objects.order_by("id")
    serializer_class = BusinessResourceSerializer


class AccessRuleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = AccessRule.objects.select_related("role", "resource").order_by("id")
    serializer_class = AccessRuleSerializer


class AccessRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAccessAdmin]
    queryset = AccessRule.objects.select_related("role", "resource").order_by("id")
    serializer_class = AccessRuleSerializer


class UserRolesView(APIView):
    permission_classes = [IsAccessAdmin]

    def get_user(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_user(user_id)
        roles = Role.objects.filter(user_roles__user=user).order_by("id")
        return Response(
            {
                "user_id": str(user.id),
                "roles": RoleSerializer(roles, many=True).data,
            }
        )

    def put(self, request, user_id):
        user = self.get_user(user_id)
        serializer = UserRolesUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            roles = replace_user_roles(
                user=user,
                role_ids=serializer.validated_data["role_ids"],
            )
        except UnknownRolesError as error:
            raise ValidationError(
                {"role_ids": f"Unknown role IDs: {sorted(error.role_ids)}"}
            ) from error
        except LastAdministratorError as error:
            raise ValidationError({"role_ids": str(error)}) from error

        return Response(
            {
                "user_id": str(user.id),
                "roles": RoleSerializer(roles, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
