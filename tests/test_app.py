import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Store the original activities data
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test to ensure isolation"""
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        # Arrange
        # (No setup needed - using default activities from fixture)

        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) > 0
        
        first_activity = next(iter(data.values()))
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        activities_response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities_response.json()[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup fails when activity doesn't exist"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "user@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up(self, client):
        """Test signup fails when student is already registered"""
        # Arrange
        activity_name = "Chess Club"
        email = "newuser@mergington.edu"

        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert - First signup succeeds
        assert response1.status_code == 200

        # Act - Second signup with same email
        response2 = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert - Second signup fails
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test signup fails when activity reaches max capacity"""
        # Arrange
        activity_name = "Test Activity"
        activities[activity_name] = {
            "description": "Test activity",
            "schedule": "Test time",
            "max_participants": 2,
            "participants": ["user1@mergington.edu", "user2@mergington.edu"]
        }
        email = "user3@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # Sign up first
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Act
        unregister_response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        activities_response = client.get("/activities")

        # Assert
        assert unregister_response.status_code == 200
        assert "Unregistered" in unregister_response.json()["message"]
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister fails when activity doesn't exist"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "user@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_signed_up(self, client):
        """Test unregister fails when student is not enrolled"""
        # Arrange
        activity_name = "Chess Club"
        email = "notaparticipant@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
