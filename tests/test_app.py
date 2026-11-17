import os, tempfile, pytest
from app import app, init_db

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("app.DB_PATH", str(db_path))
    monkeypatch.setattr("app.UPLOAD_DIR", str(tmp_path / "uploads"))
    os.makedirs(str(tmp_path / "uploads"), exist_ok=True)
    init_db()
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app.test_client() as client:
        yield client

def login(client):
    return client.post("/login", data={"email":"learner@skill.gov","password":"Learner@123"}, follow_redirects=True)

def test_health_endpoint(client):
    response=client.get("/health")
    assert response.status_code==200
    assert response.json["status"]=="ok"

def test_login_and_dashboard(client):
    response=login(client)
    assert response.status_code==200
    assert b"Dashboard" in response.data

def test_learner_cannot_open_admin(client):
    login(client)
    response=client.get("/admin", follow_redirects=True)
    assert response.status_code==200
    assert b"permission" in response.data.lower()

def test_profile_update(client):
    login(client)
    response=client.post("/profile",data={"designation":"Analyst","department":"MoSPI","experience":"3","qualification":"MSc"},follow_redirects=True)
    assert response.status_code==200
    assert b"Profile updated" in response.data

def test_competency_api_requires_login(client):
    response=client.get("/api/competencies")
    assert response.status_code in (301,302)
