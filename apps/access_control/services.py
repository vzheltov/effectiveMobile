from enum import StrEnum
from uuid import UUID

from apps.access_control.selectors import get_resource_rules
from apps.users.models import User


class Action(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class AccessScope(StrEnum):
    NONE = "none"
    OWN = "own"
    ALL = "all"


def has_resource_permission(
    *,
    user: User,
    resource_code: str,
    action: Action,
    owner_id: UUID | None = None,
) -> bool:
    if not user.is_active:
        return False

    try:
        action = Action(action)
    except (TypeError, ValueError):
        return False

    rules = get_resource_rules(user=user, resource_code=resource_code)

    if action == Action.CREATE:
        return rules.filter(can_create=True).exists()

    permission_fields = {
        Action.READ: ("can_read_own", "can_read_all"),
        Action.UPDATE: ("can_update_own", "can_update_all"),
        Action.DELETE: ("can_delete_own", "can_delete_all"),
    }
    own_field, all_field = permission_fields[action]

    if rules.filter(**{all_field: True}).exists():
        return True

    is_owner = owner_id is not None and owner_id == user.id
    return is_owner and rules.filter(**{own_field: True}).exists()


def get_read_scope(*, user: User, resource_code: str) -> AccessScope:
    if not user.is_active:
        return AccessScope.NONE

    rules = get_resource_rules(user=user, resource_code=resource_code)

    if rules.filter(can_read_all=True).exists():
        return AccessScope.ALL
    if rules.filter(can_read_own=True).exists():
        return AccessScope.OWN
    return AccessScope.NONE
