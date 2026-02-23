"""
Test suite for Mergington High School API

Uses the AAA (Arrange-Act-Assert) pattern for test structure:
- Arrange: Set up test data and state
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to Python path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """
    Fixture providing a TestClient instance with a fresh copy of the app.
    Each test gets a new client, ensuring test isolation.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets activities to a known state before each test.
    This ensures tests don't interfere with each other through shared state.
    """
    # Store original state
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }
    yield
    # Restore original state after test
    for name, activity in activities.items():
        activity["participants"] = original_participants[name]


# ============================================================================
# Tests for GET /activities endpoint
# ============================================================================

class TestGetActivities:
    """Test cases for retrieving activities list"""

    def test_get_activities_returns_200(self, client, reset_activities):
        """
        Arrange: Client is ready to make requests
        Act: Make GET request to /activities
        Assert: Status code is 200 OK
        """
        # Arrange
        expected_status = 200

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == expected_status

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Activities database exists with predefined activities
        Act: Make GET request to /activities
        Assert: Response contains all activity names
        """
        # Arrange
        expected_activity_names = {
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Drama Club", "Art Studio", "Debate Club", "Science Club"
        }

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert set(activities_data.keys()) == expected_activity_names

    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """
        Arrange: Activities database with full activity records
        Act: Make GET request to /activities
        Assert: Each activity has required fields (description, schedule, max_participants, participants)
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(set(activity_data.keys())), \
                f"Activity '{activity_name}' missing required fields"

    def test_get_activities_participants_is_list(self, client, reset_activities):
        """
        Arrange: Activities database with participant lists
        Act: Make GET request to /activities
        Assert: All participants fields are lists
        """
        # Arrange
        # (activities are already set up)

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list), \
                f"Activity '{activity_name}' participants should be a list"


# ============================================================================
# Tests for POST /activities/{activity_name}/signup endpoint - Success Cases
# ============================================================================

class TestSignupSuccess:
    """Test cases for successful activity signup"""

    def test_signup_new_student_returns_200(self, client, reset_activities):
        """
        Arrange: A student email not yet signed up for an activity
        Act: POST signup request with valid activity and new email
        Assert: Status code is 200 OK
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200

    def test_signup_new_student_adds_to_participants(self, client, reset_activities):
        """
        Arrange: A student email not yet signed up for an activity
        Act: POST signup request with valid activity and new email
        Assert: Student email is added to activity's participants list
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "alice@mergington.edu"
        initial_participants = activities[activity_name]["participants"].copy()

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == len(initial_participants) + 1

    def test_signup_returns_success_message(self, client, reset_activities):
        """
        Arrange: A student email not yet signed up for an activity
        Act: POST signup request with valid activity and new email
        Assert: Response contains success message with student email and activity name
        """
        # Arrange
        activity_name = "Tennis Club"
        new_email = "bob@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        response_data = response.json()

        # Assert
        assert "message" in response_data
        assert new_email in response_data["message"]
        assert activity_name in response_data["message"]

    def test_signup_multiple_different_students_same_activity(self, client, reset_activities):
        """
        Arrange: Multiple distinct student emails for the same activity
        Act: POST signup requests for each student
        Assert: All students are added to the activity's participants list
        """
        # Arrange
        activity_name = "Drama Club"
        new_emails = ["charlie@mergington.edu", "diana@mergington.edu", "event@mergington.edu"]

        # Act
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # Assert each signup returns 200
            assert response.status_code == 200

        # Assert
        for email in new_emails:
            assert email in activities[activity_name]["participants"]


# ============================================================================
# Tests for POST /activities/{activity_name}/signup endpoint - Error Cases
# ============================================================================

class TestSignupActivityNotFound:
    """Test cases for signup with invalid activity name"""

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: An activity name that doesn't exist in the database
        Act: POST signup request with invalid activity name
        Assert: Status code is 404 Not Found
        """
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "frank@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404

    def test_signup_nonexistent_activity_error_detail(self, client, reset_activities):
        """
        Arrange: An activity name that doesn't exist in the database
        Act: POST signup request with invalid activity name
        Assert: Response contains appropriate error detail message
        """
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "frank@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        response_data = response.json()

        # Assert
        assert "detail" in response_data
        assert "not found" in response_data["detail"].lower()

    def test_signup_case_sensitive_activity_name_returns_404(self, client, reset_activities):
        """
        Arrange: An activity name with incorrect casing (activity names are case-sensitive)
        Act: POST signup request with incorrectly cased activity name
        Assert: Status code is 404 Not Found
        """
        # Arrange
        correct_name = "Chess Club"
        incorrect_case = "chess club"  # lowercase
        email = "grace@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{incorrect_case}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404


class TestSignupDuplicate:
    """Test cases for duplicate signup attempts"""

    def test_signup_duplicate_student_returns_400(self, client, reset_activities):
        """
        Arrange: A student already signed up for an activity
        Act: POST signup request for the same student-activity combination
        Assert: Status code is 400 Bad Request
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club participants

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400

    def test_signup_duplicate_student_error_detail(self, client, reset_activities):
        """
        Arrange: A student already signed up for an activity
        Act: POST signup request for the same student-activity combination
        Assert: Response contains appropriate error detail message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club participants

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        response_data = response.json()

        # Assert
        assert "detail" in response_data
        assert "already signed up" in response_data["detail"].lower()

    def test_signup_duplicate_after_first_signup(self, client, reset_activities):
        """
        Arrange: A student successfully signs up for an activity
        Act: Attempt to sign up the same student for the same activity again
        Assert: Second signup returns 400 (first signup at 200, second at 400)
        """
        # Arrange
        activity_name = "Art Studio"
        new_email = "henry@mergington.edu"

        # First signup should succeed
        first_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        assert first_response.status_code == 200

        # Act - Attempt duplicate signup
        second_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert second_response.status_code == 400

    def test_signup_same_student_different_activities_allowed(self, client, reset_activities):
        """
        Arrange: A student not signed up for multiple different activities
        Act: POST signup requests for the same student but different activities
        Assert: Both signups succeed (200 OK) and student is in both activity participant lists
        """
        # Arrange
        student_email = "iris@mergington.edu"
        activity1 = "Science Club"
        activity2 = "Debate Club"

        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": student_email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": student_email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert student_email in activities[activity1]["participants"]
        assert student_email in activities[activity2]["participants"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_get_reflects_recent_signup(self, client, reset_activities):
        """
        Arrange: Client ready, activities endpoint ready
        Act: Sign up a new student, then GET activities
        Assert: GET response shows the new student in that activity's participants
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "jack@mergington.edu"

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        assert signup_response.status_code == 200

        get_response = client.get("/activities")
        activities_data = get_response.json()

        # Assert
        assert new_email in activities_data[activity_name]["participants"]

    def test_workflow_signup_list_verify(self, client, reset_activities):
        """
        Arrange: Fresh activities data
        Act: 1) Get initial activities, 2) Sign up new student, 3) Get activities again
        Assert: 1) Initial list has activity, 2) Signup succeeds, 3) Updated list shows new student
        """
        # Arrange
        activity_name = "Gym Class"
        new_email = "kate@mergington.edu"

        # Act - Step 1: Get initial state
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()

        # Act - Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Act - Step 3: Get updated state
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity_name]["participants"]

        # Assert
        assert signup_response.status_code == 200
        assert new_email not in initial_participants
        assert new_email in final_participants
        assert len(final_participants) == len(initial_participants) + 1
