"""Lambda handlers for the on-site queue management system."""
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

# ---------------------------------------------------------------------------
# POST /queue  → add_to_queue
# ---------------------------------------------------------------------------

def add_to_queue(event: Dict[str, Any], context: LambdaContext):
    """Add a client to the current on-site queue."""
    body = json.loads(event.get("body", "{}"))
    client_id = body.get("client_id")
    if not client_id:
        return response(400, {"error": "client_id is required"})

    queue_id = str(uuid.uuid4())
    with db_session() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS queue (id TEXT PRIMARY KEY, client_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "INSERT INTO queue (id, client_id) VALUES (:id, :cid)",
            {"id": queue_id, "cid": client_id},
        )

    return response(201, {"queue_id": queue_id, "client_id": client_id})

# ---------------------------------------------------------------------------
# GET /queue/next  → next_in_queue
# ---------------------------------------------------------------------------

def next_in_queue(event: Dict[str, Any], context: LambdaContext):
    """Pop and return the next client in queue."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, client_id FROM queue ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            return response(404, {"message": "Queue is empty"})

        # Remove the entry
        conn.execute("DELETE FROM queue WHERE id=:id", {"id": row.id})

    return response(200, {"queue_id": row.id, "client_id": row.client_id}) 