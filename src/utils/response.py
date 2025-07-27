"""Utility helpers for formatting Lambda proxy responses."""

from __future__ import annotations

import json
from typing import Any, Dict


def response(status_code: int, body: Dict[str, Any] | list[Any] | str) -> Dict[str, Any]:
    """Return an API-Gateway/Lambda-proxy compatible response.

    Parameters
    ----------
    status_code: int
        HTTP status code to return.
    body: dict | list | str
        Response payload. Will be JSON-encoded automatically unless already a str.
    """
    if isinstance(body, (dict, list)):
        serialized = json.dumps(body, default=str)
    else:
        serialized = str(body)

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": serialized,
    } 