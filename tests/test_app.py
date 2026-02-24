"""
Tests for the Mergington High School API.

Structured using the Arrange-Act-Assert (AAA) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities as original_activities


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    backup = copy.deepcopy(original_activities)
    yield
    original_activities.clear()
    original_activities.update(backup)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRoot:
    def test_redirects_to_index(self, client):
        # Arrange — no setup needed, just hitting the root route

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self, client):
        # Arrange — activities are pre-populated at module load

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9

    def test_each_activity_has_expected_keys(self, client):
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        for activity in data.values():
            assert expected_keys.issubset(activity.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in original_activities[activity_name]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered_returns_400(self, client):
        # Arrange — use an email that is already in the participants list
        activity_name = "Chess Club"
        email = original_activities[activity_name]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_full_activity_returns_400(self, client):
        # Arrange — fill the activity to capacity
        activity_name = "Chess Club"
        activity = original_activities[activity_name]
        activity["participants"] = [
            f"student{i}@mergington.edu"
            for i in range(activity["max_participants"])
        ]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email=extra@mergington.edu"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        # Arrange — use an email that is already in the participants list
        activity_name = "Chess Club"
        email = original_activities[activity_name]["participants"][0]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        assert email not in original_activities[activity_name]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_email_not_registered_returns_404(self, client):
        # Arrange — use an email that is NOT in the participants list
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not signed up for this activity"
