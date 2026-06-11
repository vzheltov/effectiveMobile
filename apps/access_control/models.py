from django.db import models

from apps.users.models import User


class Role(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "roles"

    def __str__(self) -> str:
        return self.code


class UserRole(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    class Meta:
        db_table = "user_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role",
            )
        ]


class BusinessResource(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "business_resources"

    def __str__(self) -> str:
        return self.code


class AccessRule(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="access_rules",
    )
    resource = models.ForeignKey(
        BusinessResource,
        on_delete=models.CASCADE,
        related_name="access_rules",
    )
    can_read_own = models.BooleanField(default=False)
    can_read_all = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update_own = models.BooleanField(default=False)
    can_update_all = models.BooleanField(default=False)
    can_delete_own = models.BooleanField(default=False)
    can_delete_all = models.BooleanField(default=False)

    class Meta:
        db_table = "access_rules"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "resource"],
                name="unique_role_resource_rule",
            )
        ]
