# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from rest_framework import serializers

from apps.sites.models import Region, Site


class RegionSerializer(serializers.ModelSerializer[Region]):
    class Meta:
        model = Region
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SiteSerializer(serializers.ModelSerializer[Site]):
    class Meta:
        model = Site
        fields = ["id", "name", "region", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
