# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""API v1 routes (contract is draft until 1.0.0, roadmap §RC-01)."""

from rest_framework.routers import DefaultRouter

from apps.organizations.views import OrganizationViewSet, TenantViewSet
from apps.sites.views import RegionViewSet, SiteViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("tenants", TenantViewSet, basename="tenant")
router.register("regions", RegionViewSet, basename="region")
router.register("sites", SiteViewSet, basename="site")

urlpatterns = router.urls
