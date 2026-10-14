# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Role model (CLAUDE.md §19): viewer < operator < admin, via Django Groups."""

from django.contrib.auth.models import Group, User

ROLE_VIEWER = "viewer"
ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"

ROLE_LEVELS: dict[str, int] = {ROLE_VIEWER: 1, ROLE_OPERATOR: 2, ROLE_ADMIN: 3}


def bootstrap_groups() -> None:
    """Idempotent creation of the three role groups (called from a migration)."""
    for role in ROLE_LEVELS:
        Group.objects.get_or_create(name=role)


def user_roles(user: User) -> list[str]:
    """Role names of a user, highest first. Superusers have all roles."""
    if user.is_superuser:
        return sorted(ROLE_LEVELS, key=lambda r: -ROLE_LEVELS[r])
    names = set(user.groups.values_list("name", flat=True)) & set(ROLE_LEVELS)
    return sorted(names, key=lambda r: -ROLE_LEVELS[r])


def role_level(user: User) -> int:
    if user.is_superuser:
        return ROLE_LEVELS[ROLE_ADMIN]
    roles = user_roles(user)
    return ROLE_LEVELS[roles[0]] if roles else 0
