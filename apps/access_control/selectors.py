from django.db.models import QuerySet

from apps.access_control.models import AccessRule
from apps.users.models import User


def get_resource_rules(
    *,
    user: User,
    resource_code: str,
) -> QuerySet[AccessRule]:
    return AccessRule.objects.filter(
        role__user_roles__user=user,
        resource__code=resource_code,
    )
