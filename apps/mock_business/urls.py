from django.urls import path

from apps.mock_business.views import (
    OrderDetailView,
    OrderListCreateView,
    ProductListView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="mock-order-list"),
    path(
        "orders/<int:order_id>/",
        OrderDetailView.as_view(),
        name="mock-order-detail",
    ),
    path("products/", ProductListView.as_view(), name="mock-product-list"),
]
