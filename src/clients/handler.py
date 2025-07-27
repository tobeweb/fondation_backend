"""Lambda handlers for client onboarding & management."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict

from aws_lambda_powertools.utilities.typing import LambdaContext

from src.db.database import db_session
from src.utils.response import response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(event.get("body", "{}"))
    except json.JSONDecodeError as exc:  # noqa: BLE001
        logger.warning("Invalid JSON body: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# POST /client  →  create_client
# ---------------------------------------------------------------------------

def create_client(event: Dict[str, Any], context: LambdaContext):  # noqa: D401
    """Create a new client record.

    Expects JSON body like::
        {
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@doe.com",
          "phone": "+33123456789"
        }
    """
    body = _parse_body(event)

    if not body.get("first_name") or not body.get("last_name"):
        return response(400, {"error": "first_name and last_name are required"})

    client_id = str(uuid.uuid4())
    # NOTE: Real implementation would insert into DB. Stubbed for now.
    logger.info("[create_client] id=%s payload=%s", client_id, body)

    with db_session() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS clients (id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT)"
        )
        conn.execute(
            "INSERT INTO clients (id, first_name, last_name) VALUES (:id, :fn, :ln)",
            {"id": client_id, "fn": body["first_name"], "ln": body["last_name"]},
        )

    return response(201, {"client_id": client_id, **body})


# ---------------------------------------------------------------------------
# GET /client/{clientId}  →  get_client
# ---------------------------------------------------------------------------

def get_client(event: Dict[str, Any], context: LambdaContext):  # noqa: D401
    """Return a single client by id."""
    client_id = event["pathParameters"].get("clientId")
    if not client_id:
        return response(400, {"error": "clientId path parameter missing"})

    with db_session() as conn:
        result = conn.execute(
            "SELECT id, first_name, last_name FROM clients WHERE id=:id", {"id": client_id}
        ).fetchone()

    if result is None:
        return response(404, {"error": "Client not found"})

    return response(200, dict(result._mapping)) 