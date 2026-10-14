# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""PostgreSQL native network fields.

Django core has no inet/cidr fields; psycopg3 adapts ``ipaddress`` objects to
inet/cidr with proper type OIDs, so lookups and operators resolve correctly
(ADR-0002). Values are exposed to Python as canonical strings.
"""

from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import models

from core.db.postgres import (
    NetContained,
    NetContainedOrEqual,
    NetContains,
    NetContainsOrEquals,
    NetOverlap,
)

if TYPE_CHECKING:
    _FieldBase = models.Field[Any, Any]
else:  # Field is generic in django-stubs only, not at runtime
    _FieldBase = models.Field


class _NetworkField(_FieldBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)

    def from_db_value(
        self, value: Any, expression: Any, connection: Any
    ) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _parse(value: Any) -> str:
        raise NotImplementedError

    @staticmethod
    def _parse_obj(value: Any) -> Any:
        raise NotImplementedError

    def to_python(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return self._parse(value)

    def get_prep_value(self, value: Any) -> Any:
        if value in (None, ""):
            return None
        return self._parse_obj(value)

    def validate(self, value: Any, model_instance: Any) -> None:
        if value not in (None, ""):
            self._parse(value)
        super().validate(value, model_instance)

    def deconstruct(self) -> tuple[str, str, tuple[Any, ...], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("max_length", None)
        return name, path, tuple(args), kwargs


class CidrField(_NetworkField):
    """Network prefix stored as PG ``inet`` with its mask (ADR-0002).

    inet (not cidr) is used deliberately: the only GiST operator family
    supporting && for overlap detection is inet_ops, and values are strictly
    normalized (host bits rejected in model clean) before they reach the DB.
    """

    description = "A CIDR prefix (IPv4 or IPv6)."

    def db_type(self, connection: Any) -> str:
        return "inet"

    @staticmethod
    def _parse(value: Any) -> str:
        return str(CidrField._parse_obj(value))

    @staticmethod
    def _parse_obj(value: Any) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        if isinstance(value, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            return value
        try:
            return ipaddress.ip_network(str(value))
        except ValueError as exc:
            raise ValidationError(f"{value!r} is not a valid CIDR prefix: {exc}") from exc


class InetField(_NetworkField):
    """PG ``inet`` — a single host address (ADR-0002)."""

    description = "An IPv4 or IPv6 address."

    def db_type(self, connection: Any) -> str:
        return "inet"

    @staticmethod
    def _parse(value: Any) -> str:
        return str(InetField._parse_obj(value))

    @staticmethod
    def _parse_obj(value: Any) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return value
        try:
            return ipaddress.ip_address(str(value))
        except ValueError as exc:
            raise ValidationError(f"{value!r} is not a valid IP address: {exc}") from exc


def register_network_lookups() -> None:
    for field in (CidrField, InetField):
        field.register_lookup(NetContains)
        field.register_lookup(NetContained)
        field.register_lookup(NetContainsOrEquals)
        field.register_lookup(NetContainedOrEqual)
        field.register_lookup(NetOverlap)


register_network_lookups()
