from enum import StrEnum
from uuid import UUID

from django.db import transaction

from apps.access_control.models import Role, UserRole
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


class UnknownRolesError(ValueError):
    def __init__(self, role_ids: set[int]):
        self.role_ids = role_ids
        super().__init__(f"Unknown role IDs: {sorted(role_ids)}")


class LastAdministratorError(ValueError):
    pass


def ensure_not_last_active_administrator(*, user: User) -> None:
    if not user.is_active:
        return

    admin_role = Role.objects.filter(code="admin").first()
    if admin_role is None:
        return

    active_admin_assignments = list(
        UserRole.objects.select_for_update().filter(
            role=admin_role,
            user__is_active=True,
        )
    )
    target_is_admin = any(assignment.user_id == user.id for assignment in active_admin_assignments)
    if target_is_admin and len(active_admin_assignments) == 1:
        raise LastAdministratorError("The last active administrator cannot be removed.")


@transaction.atomic
def replace_user_roles(*, user: User, role_ids: list[int]) -> list[Role]:
    requested_ids = set(role_ids)
    roles = list(Role.objects.filter(id__in=requested_ids).order_by("id"))
    found_ids = {role.id for role in roles}
    missing_ids = requested_ids - found_ids
    if missing_ids:
        raise UnknownRolesError(missing_ids)

    admin_role = Role.objects.filter(code="admin").first()
    removes_admin = admin_role is not None and admin_role.id not in requested_ids
    if removes_admin:
        ensure_not_last_active_administrator(user=user)

    UserRole.objects.filter(user=user).exclude(role_id__in=requested_ids).delete()
    UserRole.objects.bulk_create(
        [UserRole(user=user, role=role) for role in roles],
        ignore_conflicts=True,
    )
    return roles


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
