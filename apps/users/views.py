from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.services import login_user, revoke_session
from apps.users.serializers import (
    AccessTokenSerializer,
    LoginSerializer,
    RegisterSerializer,
    RegistrationResponseSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)
from apps.users.services import deactivate_user, register_user


class LoginView(APIView):
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return "Bearer"

    @extend_schema(
        request=LoginSerializer,
        responses={status.HTTP_200_OK: AccessTokenSerializer},
        operation_id="auth_login",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_data = login_user(**serializer.validated_data)

        return Response(token_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={status.HTTP_204_NO_CONTENT: None},
        operation_id="auth_logout",
    )
    def post(self, request):
        revoke_session(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={status.HTTP_200_OK: UserProfileSerializer},
        operation_id="user_profile_retrieve",
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserProfileUpdateSerializer,
        responses={status.HTTP_200_OK: UserProfileSerializer},
        operation_id="user_profile_update",
    )
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=None,
        responses={status.HTTP_204_NO_CONTENT: None},
        operation_id="user_profile_delete",
    )
    def delete(self, request):
        deactivate_user(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={status.HTTP_201_CREATED: RegistrationResponseSerializer},
        operation_id="auth_register",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_user(**serializer.validated_data)

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "middle_name": user.middle_name,
            },
            status=status.HTTP_201_CREATED,
        )
