"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 2

    def test_get_activities_includes_participant_data(self, client):
        """Test that activities include participant information"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Test successful signup for a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=john@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up john@mergington.edu for Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "john@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up an already registered participant fails"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_existing_participant_success(self, client):
        """Test successful removal of an existing participant"""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed michael@mergington.edu from Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_remove_nonexistent_participant_fails(self, client):
        """Test that removing a non-existent participant fails"""
        response = client.delete(
            "/activities/Chess Club/participants/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_participant_from_nonexistent_activity_fails(self, client):
        """Test that removing from a non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestActivityCapacity:
    """Tests for activity participant limits"""

    def test_activity_has_available_spots(self, client):
        """Test that activities track available spots correctly"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        current_participants = len(chess_club["participants"])
        max_participants = chess_club["max_participants"]
        
        assert current_participants < max_participants
        assert max_participants == 12
        assert current_participants == 2

    def test_can_fill_activity_to_capacity(self, client):
        """Test that an activity can be filled to capacity"""
        # Add participants up to capacity
        for i in range(10):  # Already has 2, add 10 more to reach 12
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/Chess Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify at capacity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Chess Club"]["participants"]) == 12
