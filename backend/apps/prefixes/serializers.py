# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import ipaddress
from typing import Any

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.prefixes import services
from apps.prefixes.models import Prefix


class PrefixSerializer(serializers.ModelSerializer[Prefix]):
    """`prefix` is write-once: re-parenting an existing prefix (e.g. after a
    split) is done by delete+create, not by editing the network in place —
    in-place edits race with children/allocations and have no safe semantics
    for a draft API."""

    prefix = serializers.CharField(max_length=43)

    class Meta:
        model = Prefix
        fields = [
            "id",
            "vrf",
            "prefix",
            "status",
            "tenant",
            "site",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_fields(self) -> dict[str, Any]:
        fields = super().get_fields()
        if self.instance is not None:
            fields["prefix"].read_only = True
        return fields

    def validate_prefix(self, value: str) -> str:
        try:
            network = ipaddress.ip_network(value.strip(), strict=True)
        except ValueError as exc:
            raise serializers.ValidationError(
                f"Invalid strict CIDR prefix: {exc}"
            ) from exc
        return str(network)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        target_vrf = attrs.get("vrf")
        if (
            self.instance is None
            or target_vrf is None
            or target_vrf == self.instance.vrf
        ):
            return attrs
        if Prefix.objects.filter(vrf=target_vrf, prefix=self.instance.prefix).exists():
            raise serializers.ValidationError(
                {"vrf": "This prefix already exists in the target VRF."}
            )
        return attrs

    def get_validators(self) -> list[Any]:
        # Duplicate detection belongs to the service/DB (stable 409 codes,
        # §17); DRF's UniqueTogetherValidator pre-check would 400 first.
        return [
            validator
            for validator in super().get_validators()
            if not isinstance(validator, UniqueTogetherValidator)
        ]

    def create(self, validated_data: dict[str, Any]) -> Prefix:
        vrf = validated_data.pop("vrf")
        prefix_str = validated_data.pop("prefix")
        return services.create_prefix(vrf, prefix_str, **validated_data)
