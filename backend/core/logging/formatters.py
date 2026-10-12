# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import json
import logging


class JsonFormatter(logging.Formatter):
    """One JSON object per line (§39). Never add secrets to log records."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
