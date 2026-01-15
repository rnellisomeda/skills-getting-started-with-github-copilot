"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


def test_root_redirects_to_static(client):
    """Test that root path redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "Basketball Team" in data
    assert "Art Club" in data
    
    # Check structure of an activity
    soccer = data["Soccer Team"]
    assert "description" in soccer
    assert "schedule" in soccer
    assert "max_participants" in soccer
    assert "participants" in soccer
    assert isinstance(soccer["participants"], list)


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    activity_name = "Soccer Team"
    email = "newstudent@mergington.edu"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_participants = initial_response.json()[activity_name]["participants"]
    initial_count = len(initial_participants)
    
    # Sign up
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify participant was added
    updated_response = client.get("/activities")
    updated_participants = updated_response.json()[activity_name]["participants"]
    assert len(updated_participants) == initial_count + 1
    assert email in updated_participants


def test_signup_duplicate_participant(client):
    """Test that signing up the same participant twice fails"""
    activity_name = "Soccer Team"
    email = "alex@mergington.edu"  # Already in Soccer Team
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test successfully unregistering from an activity"""
    activity_name = "Soccer Team"
    email = "alex@mergington.edu"  # Already in Soccer Team
    
    # Verify participant exists
    initial_response = client.get("/activities")
    initial_participants = initial_response.json()[activity_name]["participants"]
    assert email in initial_participants
    initial_count = len(initial_participants)
    
    # Unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify participant was removed
    updated_response = client.get("/activities")
    updated_participants = updated_response.json()[activity_name]["participants"]
    assert len(updated_participants) == initial_count - 1
    assert email not in updated_participants


def test_unregister_nonexistent_participant(client):
    """Test unregistering a participant who isn't signed up"""
    activity_name = "Soccer Team"
    email = "notregistered@mergington.edu"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 400
    assert "Student not found" in response.json()["detail"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_activity_has_correct_fields(client):
    """Test that activities have all required fields"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity_data in data.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        
        assert isinstance(activity_data["description"], str)
        assert isinstance(activity_data["schedule"], str)
        assert isinstance(activity_data["max_participants"], int)
        assert isinstance(activity_data["participants"], list)
        
        # Verify max_participants is positive
        assert activity_data["max_participants"] > 0


def test_signup_and_unregister_workflow(client):
    """Test a complete signup and unregister workflow"""
    activity_name = "Chess Club"
    email = "workflow@mergington.edu"
    
    # Get initial state
    initial_response = client.get("/activities")
    initial_participants = initial_response.json()[activity_name]["participants"]
    assert email not in initial_participants
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Verify signup
    after_signup = client.get("/activities")
    assert email in after_signup.json()[activity_name]["participants"]
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    
    # Verify unregister
    after_unregister = client.get("/activities")
    assert email not in after_unregister.json()[activity_name]["participants"]
