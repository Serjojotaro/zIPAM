# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Global search aggregator (§14): one request, grouped bounded results.

Cross-domain by nature, so it lives in core and only reads app models. Backend
filtering only (§14: never ship whole datasets to the client); each group is
capped. Draft shape — the response contract stabilizes before 1.0.0."""

from __future__ import annotations

import ipaddress
from typing import Any

from django.db.models import QuerySet, TextField
from django.db.models.functions import Cast
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ip_addresses.models import IPAddress
from apps.organizations.models import Organization, Tenant
from apps.prefixes.models import Prefix
from apps.sites.models import Region, Site
from apps.vlans.models import VLAN
from apps.vrfs.models import VRF
from core.permissions.roles import RoleBasedPermission

LIMIT = 10


def _rows(qs: QuerySet[Any], fields: list[str]) -> list[dict[str, Any]]:
    return list(qs.values(*fields)[:LIMIT])


class SearchView(APIView):
    permission_classes = [RoleBasedPermission]

    def get(self, request: Request) -> Response:
        q = str(request.query_params.get("q", "")).strip()
        if len(q) < 2:
            return Response(
                {
                    "error": {
                        "code": "QUERY_TOO_SHORT",
                        "message": "q must be at least 2 characters.",
                        "details": {},
                    }
                },
                status=400,
            )

        ip: ipaddress.IPv4Address | ipaddress.IPv6Address | None = None
        network: ipaddress.IPv4Network | ipaddress.IPv6Network | None = None
        try:
            if "/" in q:
                network = ipaddress.ip_network(q, strict=False)
            else:
                ip = ipaddress.ip_address(q)
        except ValueError:
            pass

        if network is not None:
            prefixes = Prefix.objects.filter(prefix__net_overlap=str(network))
            addresses = IPAddress.objects.filter(address__net_contained_or_equal=str(network))
        elif ip is not None:
            prefixes = Prefix.objects.filter(prefix__net_contains_or_equals=str(ip))
            addresses = IPAddress.objects.filter(address=str(ip))
        else:
            # inet has no pattern-matching operator; compare as text (§14).
            prefixes = Prefix.objects.annotate(
                net_text=Cast("prefix", output_field=TextField())
            ).filter(net_text__icontains=q)
            addresses = IPAddress.objects.annotate(
                addr_text=Cast("address", output_field=TextField())
            ).filter(addr_text__icontains=q)

        vlans = VLAN.objects.filter(name__icontains=q)
        if q.isdigit():
            vlans = VLAN.objects.filter(name__icontains=q) | VLAN.objects.filter(vid=int(q))

        return Response(
            {
                "query": q,
                "results": {
                    "ip_addresses": _rows(
                        addresses.select_related("vrf"), ["id", "address", "status", "vrf"]
                    ),
                    "prefixes": _rows(
                        prefixes.select_related("vrf"), ["id", "prefix", "status", "vrf"]
                    ),
                    "vrfs": _rows(VRF.objects.filter(name__icontains=q), ["id", "name"]),
                    "vlans": _rows(vlans, ["id", "name", "vid"]),
                    "organizations": _rows(
                        Organization.objects.filter(name__icontains=q), ["id", "name"]
                    ),
                    "tenants": _rows(Tenant.objects.filter(name__icontains=q), ["id", "name"]),
                    "regions": _rows(Region.objects.filter(name__icontains=q), ["id", "name"]),
                    "sites": _rows(Site.objects.filter(name__icontains=q), ["id", "name"]),
                },
            }
        )
