# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""API v1 routes (contract is draft until 1.0.0, roadmap §RC-01)."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.ip_addresses.views import IPAddressViewSet
from apps.organizations.views import OrganizationViewSet, TenantViewSet
from apps.prefixes.views import PrefixViewSet
from apps.sites.views import RegionViewSet, SiteViewSet
from apps.vlans.views import VLANViewSet
from apps.vrfs.views import VRFViewSet
from core.api.search import SearchView

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("tenants", TenantViewSet, basename="tenant")
router.register("regions", RegionViewSet, basename="region")
router.register("sites", SiteViewSet, basename="site")
router.register("vrfs", VRFViewSet, basename="vrf")
router.register("vlans", VLANViewSet, basename="vlan")
router.register("prefixes", PrefixViewSet, basename="prefix")
router.register("ip-addresses", IPAddressViewSet, basename="ipaddress")

urlpatterns = [
    path("search", SearchView.as_view(), name="search"),
    *router.urls,
]
