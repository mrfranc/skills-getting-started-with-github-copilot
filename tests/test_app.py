from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Test Activity"
ACTIVITY_URL = f"/activities/{quote(ACTIVITY_NAME, safe='')}/signup"
EXISTING_EMAIL = "existing@example.com"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(
        app_module.activities,
        ACTIVITY_NAME,
        {
            "description": "A test activity",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": [EXISTING_EMAIL],
        },
    )

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_includes_activity_and_participants(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]


def test_signup_adds_participant(client):
    email = "new@example.com"

    response = client.post(ACTIVITY_URL, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert app_module.activities[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL, email]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(ACTIVITY_URL, params={"email": EXISTING_EMAIL})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown/signup", params={"email": "new@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    response = client.delete(ACTIVITY_URL, params={"email": EXISTING_EMAIL})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_EMAIL} from {ACTIVITY_NAME}"
    }
    assert app_module.activities[ACTIVITY_NAME]["participants"] == []


def test_unregister_rejects_missing_participant(client):
    response = client.delete(ACTIVITY_URL, params={"email": "missing@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert app_module.activities[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown/signup", params={"email": EXISTING_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"