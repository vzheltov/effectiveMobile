from django.urls import path

from apps.access_control.views import (
    AccessRuleDetailView,
    AccessRuleListCreateView,
    BusinessResourceDetailView,
    BusinessResourceListCreateView,
    RoleDetailView,
    RoleListCreateView,
    UserRolesView,
)

urlpatterns = [
    path("roles/", RoleListCreateView.as_view(), name="role-list"),
    path("roles/<int:pk>/", RoleDetailView.as_view(), name="role-detail"),
    path(
        "resources/",
        BusinessResourceListCreateView.as_view(),
        name="resource-list",
    ),
    path(
        "resources/<int:pk>/",
        BusinessResourceDetailView.as_view(),
        name="resource-detail",
    ),
    path("rules/", AccessRuleListCreateView.as_view(), name="rule-list"),
    path("rules/<int:pk>/", AccessRuleDetailView.as_view(), name="rule-detail"),
    path(
        "users/<uuid:user_id>/roles/",
        UserRolesView.as_view(),
        name="user-role-list",
    ),
]
