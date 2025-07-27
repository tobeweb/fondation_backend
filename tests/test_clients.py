import json

from src.clients import handler as clients_handler
from src.db.database import get_engine


def test_create_and_get_client():
    # Arrange
    event_create = {
        "body": json.dumps({"first_name": "Alice", "last_name": "Smith"})
    }

    # Act – create client
    result_create = clients_handler.create_client(event_create, None)
    assert result_create["statusCode"] == 201

    payload = json.loads(result_create["body"])
    client_id = payload["client_id"]

    # Act – get client
    event_get = {"pathParameters": {"clientId": client_id}}
    result_get = clients_handler.get_client(event_get, None)

    # Assert
    assert result_get["statusCode"] == 200
    body = json.loads(result_get["body"])
    assert body["id"] == client_id or body["client_id"] == client_id

    # Ensure in-memory DB contains exactly one row
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM clients").scalar_one()
        assert count == 1 