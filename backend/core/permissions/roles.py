# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Role-based DRF permissions (CLAUDE.md §19): every privileged operation is
guarded on the backend, never by hiding UI."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.roles import ROLE_LEVELS, role_level


class RoleBasedPermission(BasePermission):
    """Read requires `read_role`; create/update/delete require `write_role`."""

    read_role: str = "viewer"
    write_role: str = "operator"

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        required = ROLE_LEVELS[self.read_role] if request.method in SAFE_METHODS else ROLE_LEVELS[
            self.write_role
        ]
        return role_level(user) >= required
