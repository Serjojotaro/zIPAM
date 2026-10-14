# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.contrib import admin
from django.urls import include, path

from core.health.views import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health),
    path("ready", ready),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("config.api_urls")),
]
