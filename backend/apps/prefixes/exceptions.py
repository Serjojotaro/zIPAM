# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Domain errors with stable codes (§17). API mapping happens in M3."""

from __future__ import annotations


class PrefixError(Exception):
    code = "PREFIX_ERROR"

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}


class PrefixInvalidError(PrefixError):
    code = "PREFIX_INVALID"


class PrefixOverlapError(PrefixError):
    code = "PREFIX_OVERLAP"


class PrefixSplitError(PrefixError):
    code = "PREFIX_SPLIT_INVALID"
