# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Domain errors with stable codes (§17). API mapping happens in M3."""

from __future__ import annotations

from core.exceptions.domain import DomainError


class IPAllocationError(DomainError):
    code = "IP_ALLOCATION_ERROR"

class IPAlreadyAllocatedError(IPAllocationError):
    code = "IP_ALREADY_ALLOCATED"


class IPAllocationExhaustedError(IPAllocationError):
    code = "IP_ALLOCATION_EXHAUSTED"


class IPInvalidError(IPAllocationError):
    code = "IP_INVALID"
