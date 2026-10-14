# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from rest_framework import viewsets

from apps.organizations.models import Organization, Tenant
from apps.organizations.serializers import OrganizationSerializer, TenantSerializer
from core.permissions.roles import RoleBasedPermission


class OrganizationViewSet(viewsets.ModelViewSet[Organization]):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [RoleBasedPermission]


class TenantViewSet(viewsets.ModelViewSet[Tenant]):
    queryset = Tenant.objects.select_related("organization").all()
    serializer_class = TenantSerializer
    permission_classes = [RoleBasedPermission]
