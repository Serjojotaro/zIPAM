# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import ipaddress
from typing import Any

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.ip_addresses import services
from apps.ip_addresses.models import IPAddress


class IPAddressSerializer(serializers.ModelSerializer[IPAddress]):
    """`address` is write-once: moving an address between prefixes/VRFs is a
    release+assign pair so every step keeps the UNIQUE/race guarantees."""

    address = serializers.CharField(max_length=45)

    class Meta:
        model = IPAddress
        fields = [
            "id",
            "vrf",
            "address",
            "status",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_fields(self) -> dict[str, Any]:
        fields = super().get_fields()
        if self.instance is not None:
            fields["address"].read_only = True
        return fields

    def validate_address(self, value: str) -> str:
        try:
            return str(ipaddress.ip_address(value.strip()))
        except ValueError as exc:
            raise serializers.ValidationError(f"Invalid IP address: {exc}") from exc

    def get_validators(self) -> list[Any]:
        # Duplicate detection belongs to the service/DB (stable 409 codes,
        # §17); DRF's UniqueTogetherValidator pre-check would 400 first.
        return [
            validator
            for validator in super().get_validators()
            if not isinstance(validator, UniqueTogetherValidator)
        ]

    def create(self, validated_data: dict[str, Any]) -> IPAddress:
        return services.assign_ip(**validated_data)
