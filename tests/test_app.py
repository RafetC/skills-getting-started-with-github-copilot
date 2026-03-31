import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import copy

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from app import app, activities

# Store the original activities data
ORIGINAL_ACTIVITIES = {
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
    },
    "Debate Club": {
        "description": "Develop critical thinking and public speaking skills through structured debates",
        "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
        "max_participants": 18,
        "participants": ["alex@mergington.edu", "jessica@mergington.edu"]
    }
}

@pytest.fixture
def client():
    """Fixture to provide TestClient for API tests"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to default state before each test"""
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield

def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Debate Club" in data
    assert len(data) == 3

def test_get_activities_include_participants(client):
    """Test that activities include participant lists"""
    response = client.get("/activities")
    data = response.json()
    chess_club = data["Chess Club"]
    assert "participants" in chess_club
    assert "michael@mergington.edu" in chess_club["participants"]
    assert len(chess_club["participants"]) == 2

def test_signup_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert "newstudent@mergington.edu" in response.json()["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    assert len(activities_data["Chess Club"]["participants"]) == 3

def test_signup_duplicate_email(client):
    """Test that duplicate signup is rejected"""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Club/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_signup_multiple_activities(client):
    """Test that a student can sign up for multiple activities"""
    # Sign up for Chess Club
    response1 = client.post(
        "/activities/Chess Club/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response1.status_code == 200
    
    # Sign up for Programming Class
    response2 = client.post(
        "/activities/Programming Class/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response2.status_code == 200
    
    # Verify in both activities
    activities_response = client.get("/activities")
    data = activities_response.json()
    assert "alice@mergington.edu" in data["Chess Club"]["participants"]
    assert "alice@mergington.edu" in data["Programming Class"]["participants"]

def test_unregister_activity_success(client):
    """Test successfully unregistering from an activity"""
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    assert len(activities_data["Chess Club"]["participants"]) == 1

def test_unregister_participant_not_found(client):
    """Test unregistering non-existent participant"""
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "notpresent@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_activity_not_found(client):
    """Test unregistering from non-existent activity"""
    response = client.delete(
        "/activities/Fake Club/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_then_reregister(client):
    """Test that a student can re-register after unregistering"""
    # First, unregister
    response1 = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response1.status_code == 200
    
    # Then, re-register
    response2 = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response2.status_code == 200
    
    # Verify participant is back
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
