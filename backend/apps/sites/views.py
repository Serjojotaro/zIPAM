# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from rest_framework import viewsets

from apps.sites.models import Region, Site
from apps.sites.serializers import RegionSerializer, SiteSerializer
from core.permissions.roles import RoleBasedPermission


class RegionViewSet(viewsets.ModelViewSet[Region]):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [RoleBasedPermission]


class SiteViewSet(viewsets.ModelViewSet[Site]):
    queryset = Site.objects.select_related("region").all()
    serializer_class = SiteSerializer
    permission_classes = [RoleBasedPermission]
