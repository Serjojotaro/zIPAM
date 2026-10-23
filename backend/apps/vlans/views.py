# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db.models import QuerySet
from rest_framework import viewsets

from apps.vlans.models import VLAN
from apps.vlans.serializers import VLANSerializer
from core.permissions.roles import RoleBasedPermission


class VLANViewSet(viewsets.ModelViewSet[VLAN]):
    queryset = VLAN.objects.all()
    serializer_class = VLANSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self) -> QuerySet[VLAN]:
        qs = super().get_queryset()
        params = self.request.query_params
        if name := params.get("name"):
            qs = qs.filter(name__icontains=name)
        if vid := params.get("vid"):
            qs = qs.filter(vid=vid)
        return qs
