# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from rest_framework import serializers

from apps.vlans.models import VLAN


class VLANSerializer(serializers.ModelSerializer[VLAN]):
    class Meta:
        model = VLAN
        fields = ["id", "name", "vid", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        vid, name = attrs.get("vid"), attrs.get("name")
        if vid is not None and name is not None:
            dup = VLAN.objects.filter(vid=vid, name=name)
            if self.instance is not None:
                dup = dup.exclude(pk=self.instance.pk)
            if dup.exists():
                raise serializers.ValidationError(
                    {"vid": f"VLAN {vid} with name {name!r} already exists."}
                )
        return attrs
