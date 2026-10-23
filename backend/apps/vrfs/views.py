# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db.models import QuerySet
from rest_framework import viewsets

from apps.vrfs.models import VRF
from apps.vrfs.serializers import VRFSerializer
from core.permissions.roles import RoleBasedPermission


class VRFViewSet(viewsets.ModelViewSet[VRF]):
    queryset = VRF.objects.all()
    serializer_class = VRFSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self) -> QuerySet[VRF]:
        qs = super().get_queryset()
        params = self.request.query_params
        if name := params.get("name"):
            qs = qs.filter(name__icontains=name)
        if rd := params.get("rd"):
            qs = qs.filter(rd=rd)
        return qs
