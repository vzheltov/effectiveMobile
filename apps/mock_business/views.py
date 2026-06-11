from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access_control.services import (
    AccessScope,
    Action,
    get_read_scope,
    has_resource_permission,
)
from apps.mock_business.data import MOCK_ORDERS, MOCK_PRODUCTS
from apps.mock_business.serializers import (
    MockOrderActionResponseSerializer,
    MockOrderCreateResponseSerializer,
    MockOrderInputSerializer,
    MockOrderSerializer,
    MockProductSerializer,
)
from apps.users.models import User


def ensure_permission(*, user, resource_code, action, owner_id=None) -> None:
    if not has_resource_permission(
        user=user,
        resource_code=resource_code,
        action=action,
        owner_id=owner_id,
    ):
        raise PermissionDenied("You do not have permission for this resource")


def get_mock_object(items, object_id):
    try:
        return next(item for item in items if item["id"] == object_id)
    except StopIteration as error:
        raise NotFound("Mock object not found.") from error


def get_owner_id(item):
    owner = get_object_or_404(
        User,
        email=item["owner_email"],
        is_active=True,
    )
    return owner.id


def filter_for_read_scope(*, items, user, resource_code):
    scope = get_read_scope(user=user, resource_code=resource_code)
    if scope == AccessScope.NONE:
        raise PermissionDenied("You do not have permission for this resource")
    if scope == AccessScope.ALL:
        return items

    owner_ids = {
        owner.email: owner.id
        for owner in User.objects.filter(
            email__in=[item["owner_email"] for item in items],
            is_active=True,
        )
    }
    return [item for item in items if owner_ids.get(item["owner_email"]) == user.id]


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={status.HTTP_200_OK: MockOrderSerializer(many=True)},
        operation_id="mock_order_list",
    )
    def get(self, request):
        orders = filter_for_read_scope(
            items=MOCK_ORDERS,
            user=request.user,
            resource_code="orders",
        )
        return Response(MockOrderSerializer(orders, many=True).data)

    @extend_schema(
        request=MockOrderInputSerializer,
        responses={status.HTTP_200_OK: MockOrderCreateResponseSerializer},
        operation_id="mock_order_create",
    )
    def post(self, request):
        ensure_permission(
            user=request.user,
            resource_code="orders",
            action=Action.CREATE,
        )
        serializer = MockOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "mock": True,
                "detail": "Order would be created",
                "order": serializer.validated_data,
            },
            status=status.HTTP_200_OK,
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_order(self, order_id):
        return get_mock_object(MOCK_ORDERS, order_id)

    @extend_schema(
        responses={status.HTTP_200_OK: MockOrderSerializer},
        operation_id="mock_order_retrieve",
    )
    def get(self, request, order_id):
        order = self.get_order(order_id)
        ensure_permission(
            user=request.user,
            resource_code="orders",
            action=Action.READ,
            owner_id=get_owner_id(order),
        )
        return Response(MockOrderSerializer(order).data)

    @extend_schema(
        request=MockOrderInputSerializer,
        responses={status.HTTP_200_OK: MockOrderActionResponseSerializer},
        operation_id="mock_order_update",
    )
    def patch(self, request, order_id):
        order = self.get_order(order_id)
        ensure_permission(
            user=request.user,
            resource_code="orders",
            action=Action.UPDATE,
            owner_id=get_owner_id(order),
        )
        serializer = MockOrderInputSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "mock": True,
                "detail": "Order would be updated",
                "order_id": order_id,
            }
        )

    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: MockOrderActionResponseSerializer},
        operation_id="mock_order_delete",
    )
    def delete(self, request, order_id):
        order = self.get_order(order_id)
        ensure_permission(
            user=request.user,
            resource_code="orders",
            action=Action.DELETE,
            owner_id=get_owner_id(order),
        )
        return Response(
            {
                "mock": True,
                "detail": "Order would be deleted",
                "order_id": order_id,
            }
        )


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={status.HTTP_200_OK: MockProductSerializer(many=True)},
        operation_id="mock_product_list",
    )
    def get(self, request):
        products = filter_for_read_scope(
            items=MOCK_PRODUCTS,
            user=request.user,
            resource_code="products",
        )
        return Response(MockProductSerializer(products, many=True).data)
