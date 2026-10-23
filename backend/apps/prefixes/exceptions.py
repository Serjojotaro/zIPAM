# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Domain errors with stable codes (§17). API mapping happens in M3."""

from __future__ import annotations

from core.exceptions.domain import DomainError


class PrefixError(DomainError):
    code = "PREFIX_ERROR"

class PrefixInvalidError(PrefixError):
    code = "PREFIX_INVALID"


class PrefixOverlapError(PrefixError):
    code = "PREFIX_OVERLAP"


class PrefixSplitError(PrefixError):
    code = "PREFIX_SPLIT_INVALID"
