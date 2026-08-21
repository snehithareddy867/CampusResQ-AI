import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.utils.enums import DepartmentName

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.models.department import Department
    
    db = TestingSessionLocal()
    
    # Create medical department
    med_dept = Department(name=DepartmentName.MEDICAL, description="Medical")
    db.add(med_dept)
    db.commit()
    db.refresh(med_dept)
    
    # Create normal user
    normal = User(
        email="testuser@example.com",
        name="Test Normal",
        campus_id="N123",
        hashed_password=get_password_hash("password123"),
        department_id=None
    )
    db.add(normal)
    
    # Create medical user
    med = User(
        email="medical1@example.com",
        name="Test Med",
        campus_id="M123",
        hashed_password=get_password_hash("password123"),
        department_id=med_dept.id
    )
    db.add(med)
    db.commit()
    db.close()


def test_signup_no_department():
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "campus_id": "TEST1234",
            "email": "testuser_signup@example.com",
            "password": "password123",
            "department": "NONE"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["department"] == "NONE"

def test_login():
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()

def test_report_incident():
    # Login first
    login_res = client.post(
        "/api/auth/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    token = login_res.json()["token"]
    
    # Report incident
    inc_res = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Student fell",
            "description": "Student collapsed near the library.",
            "location_name": "Main Library"
        }
    )
    assert inc_res.status_code == 200
    assert "id" in inc_res.json()
    assert inc_res.json()["status"] == "REPORTED"

def test_full_workflow():
    # Login normal user
    login_res = client.post(
        "/api/auth/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    token = login_res.json()["token"]
    
    # Create incident
    inc_res = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Medical Emergency",
            "description": "Student collapsed near the library.",
            "location_name": "Main Library"
        }
    )
    assert inc_res.status_code == 200
    inc_id = inc_res.json()["id"]
    
    # Get incident
    get_inc = client.get(
        f"/api/incidents/{inc_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_inc.status_code == 200
    
    # Simulate disruption (Replanning)
    replan_res = client.post(
        f"/api/incidents/{inc_id}/simulate-disruption",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "ROUTE_BLOCKED",
            "description": "Main road is blocked"
        }
    )
    assert replan_res.status_code == 200
    assert "reason" in replan_res.json()
    
    # Login medical user to accept and resolve
    med_login_res = client.post(
        "/api/auth/login",
        data={"username": "medical1@example.com", "password": "password123"}
    )
    med_token = med_login_res.json()["token"]
    
    # Accept incident
    acc_res = client.post(
        f"/api/incidents/{inc_id}/accept",
        headers={"Authorization": f"Bearer {med_token}"}
    )
    assert acc_res.status_code == 200
    
    # Start incident
    start_res = client.post(
        f"/api/incidents/{inc_id}/start",
        headers={"Authorization": f"Bearer {med_token}"}
    )
    assert start_res.status_code == 200
    
    # Resolve incident
    res_res = client.post(
        f"/api/incidents/{inc_id}/resolve",
        headers={"Authorization": f"Bearer {med_token}"}
    )
    assert res_res.status_code == 200
    
    # Check status
    final_inc = client.get(
        f"/api/incidents/{inc_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert final_inc.json()["status"] == "RESOLVED"

def test_authorization_rules():
    # Login normal user
    login_res = client.post(
        "/api/auth/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    token = login_res.json()["token"]
    
    # Create incident
    inc_res = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Medical Emergency",
            "description": "Student collapsed near the library.",
            "location_name": "Main Library"
        }
    )
    inc_id = inc_res.json()["id"]
    
    # Normal user attempts to accept -> must be 403 Forbidden
    acc_res = client.post(
        f"/api/incidents/{inc_id}/accept",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert acc_res.status_code == 403
    
    # Normal user attempts to resolve -> must be 403 Forbidden
    res_res = client.post(
        f"/api/incidents/{inc_id}/resolve",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_res.status_code == 403
