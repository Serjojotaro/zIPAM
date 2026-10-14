# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from rest_framework import serializers

from apps.organizations.models import Organization, Tenant


class OrganizationSerializer(serializers.ModelSerializer[Organization]):
    class Meta:
        model = Organization
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantSerializer(serializers.ModelSerializer[Tenant]):
    class Meta:
        model = Tenant
        fields = ["id", "organization", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
