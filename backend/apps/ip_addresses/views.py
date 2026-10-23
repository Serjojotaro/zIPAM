# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db.models import QuerySet
from rest_framework import viewsets

from apps.ip_addresses.models import IPAddress
from apps.ip_addresses.serializers import IPAddressSerializer
from core.api.params import parse_ip_or_cidr
from core.permissions.roles import RoleBasedPermission


class IPAddressViewSet(viewsets.ModelViewSet[IPAddress]):
    """DELETE releases the address (the allocation row *is* the allocation).
    Free-address allocation is a prefix action: POST /prefixes/{id}/allocate/."""

    queryset = IPAddress.objects.select_related("vrf").all()
    serializer_class = IPAddressSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self) -> QuerySet[IPAddress]:
        qs = super().get_queryset()
        params = self.request.query_params
        if vrf := params.get("vrf"):
            qs = qs.filter(vrf_id=vrf)
        if status := params.get("status"):
            qs = qs.filter(status=status)
        if address := params.get("address"):
            qs = qs.filter(address=parse_ip_or_cidr(address))
        if within := params.get("within"):
            qs = qs.filter(address__net_contained_or_equal=parse_ip_or_cidr(within))
        return qs
