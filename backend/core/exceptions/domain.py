# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Base class for domain errors carrying a stable machine code (§17).

Apps subclass this; core/exceptions/handlers.py maps codes to HTTP statuses,
so no view needs per-error try/except."""

from __future__ import annotations


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}
