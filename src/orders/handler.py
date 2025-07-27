"""Lambda handlers for orders."""
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


def create_order(event: Dict[str, Any], context: LambdaContext):
    """Create a new order for a client."""
    body = json.loads(event.get("body", "{}"))

    required = {"client_id", "items"}
    if not required.issubset(body):
        return response(400, {"error": f"Missing fields: {required - set(body)}"})

    order_id = str(uuid.uuid4())
    with db_session() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, client_id TEXT, payload TEXT)"
        )
        conn.execute(
            "INSERT INTO orders (id, client_id, payload) VALUES (:id, :cid, :payload)",
            {"id": order_id, "cid": body["client_id"], "payload": json.dumps(body)},
        )

    return response(201, {"order_id": order_id}) 