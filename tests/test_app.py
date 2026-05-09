import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

DEFAULT_ACTIVITIES = copy.deepcopy(activities)
client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset the in-memory activities to their default state before each test.
    """
    activities.clear()
    activities.update(copy.deepcopy(DEFAULT_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(DEFAULT_ACTIVITIES))


def test_root_redirects_to_static_index():
    """
    Test that the root endpoint redirects to the static index page.
    """
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_initial_data():
    """
    Test that GET /activities returns the initial activity data.
    """
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    """
    Test that POST /activities/{activity_name}/signup adds a new participant.
    """
    email = "newstudent@mergington.edu"
    activity_name = quote("Chess Club", safe="")
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    """
    Test that signing up a participant twice returns a 400 error.
    """
    email = "michael@mergington.edu"
    activity_name = quote("Chess Club", safe="")
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already signed up for this activity"


def test_signup_nonexistent_activity_returns_404():
    """
    Test that signing up for a nonexistent activity returns a 404 error.
    """
    activity_name = quote("Nonexistent Club", safe="")
    response = client.post(f"/activities/{activity_name}/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_for_activity_removes_participant():
    """
    Test that DELETE /activities/{activity_name}/signup removes a participant.
    """
    email = "michael@mergington.edu"
    activity_name = quote("Chess Club", safe="")
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    """
    Test that unregistering a participant who is not signed up returns a 404 error.
    """
    activity_name = quote("Chess Club", safe="")
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": "absent@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unregister_nonexistent_activity_returns_404():
    """
    Test that unregistering from a nonexistent activity returns a 404 error.
    """
    activity_name = quote("Nonexistent Club", safe="")
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"