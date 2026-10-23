# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from rest_framework import serializers

from apps.vrfs.models import VRF


class VRFSerializer(serializers.ModelSerializer[VRF]):
    class Meta:
        model = VRF
        fields = ["id", "name", "rd", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
