# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any

from django.db.models import Exists, OuterRef, QuerySet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.ip_addresses import services as ip_services
from apps.ip_addresses.models import IPAddressStatus
from apps.ip_addresses.serializers import IPAddressSerializer
from apps.prefixes import services
from apps.prefixes.models import Prefix
from apps.prefixes.serializers import PrefixSerializer
from core.api.params import parse_ip_or_cidr
from core.permissions.roles import RoleBasedPermission


class PrefixViewSet(viewsets.ModelViewSet[Prefix]):
    queryset = Prefix.objects.select_related("vrf", "tenant", "site").all()
    serializer_class = PrefixSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self) -> QuerySet[Prefix]:
        qs = super().get_queryset()
        params = self.request.query_params
        if vrf := params.get("vrf"):
            qs = qs.filter(vrf_id=vrf)
        if status := params.get("status"):
            qs = qs.filter(status=status)
        if tenant := params.get("tenant"):
            qs = qs.filter(tenant_id=tenant)
        if site := params.get("site"):
            qs = qs.filter(site_id=site)
        if contains := params.get("contains"):
            qs = qs.filter(prefix__net_contains_or_equals=parse_ip_or_cidr(contains))
        if within := params.get("within"):
            qs = qs.filter(prefix__net_contained_or_equal=parse_ip_or_cidr(within))
        if parent := params.get("parent"):
            qs = qs.filter(pk__in=PrefixViewSet._immediate_children_ids(parent))
        return qs

    @staticmethod
    def _immediate_children_ids(parent_id: str) -> QuerySet[Prefix, int]:
        try:
            parent = Prefix.objects.get(pk=parent_id)
        except (ValueError, Prefix.DoesNotExist) as exc:
            raise NotFound({"detail": "Parent prefix not found."}) from exc
        intermediate = Prefix.objects.filter(
            vrf=OuterRef("vrf"),
            prefix__net_contained=parent.prefix,
            prefix__net_contains=OuterRef("prefix"),
        ).exclude(pk=OuterRef("pk"))
        return (
            Prefix.objects.filter(vrf=parent.vrf, prefix__net_contained=parent.prefix)
            .exclude(Exists(intermediate))
            .values_list("pk", flat=True)
        )

    @action(detail=True, methods=["get"])
    def utilization(self, request: Any, pk: Any = None) -> Response:
        return Response(self.get_object().utilization())

    @action(detail=True, methods=["post"], url_path="available-subnets")
    def available_subnets(self, request: Any, pk: Any = None) -> Response:
        prefix = self.get_object()
        masklen = _int_param(request, "masklen")
        return Response(
            {
                "prefix": str(prefix.prefix),
                "available_subnets": services.available_subnets(prefix, masklen),
            }
        )

    @action(detail=True, methods=["post"])
    def split(self, request: Any, pk: Any = None) -> Response:
        prefix = self.get_object()
        new_prefix_len = _int_param(request, "prefix_len")
        if new_prefix_len is None:
            raise ValidationError({"prefix_len": "This field is required."})
        children = services.split_prefix(prefix, new_prefix_len)
        return Response(self.get_serializer(children, many=True).data, status=201)

    @action(detail=True, methods=["post"])
    def allocate(self, request: Any, pk: Any = None) -> Response:
        prefix = self.get_object()
        payload = _json_payload(request)
        status = str(payload.get("status", IPAddressStatus.ACTIVE))
        if status not in IPAddressStatus.values:
            raise ValidationError(
                {"status": f"Invalid status. Valid: {', '.join(IPAddressStatus.values)}."}
            )
        ip = ip_services.allocate_ip(
            prefix, status=status, description=str(payload.get("description", ""))
        )
        return Response(IPAddressSerializer(ip).data, status=201)


def _json_payload(request: Any) -> dict[str, Any]:
    if not isinstance(request.data, dict):
        raise ValidationError({"detail": "Request body must be a JSON object."})
    return dict(request.data)


def _int_param(request: Any, name: str) -> int | None:
    payload = _json_payload(request)
    value = payload.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError({name: "Must be an integer."})
    return value
