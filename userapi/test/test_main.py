import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import status

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient
from src.main import app, get_db
from src.database import Base
import src.models 

SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.mark.unit
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.unit
def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "memory_usage_mb" in response.json()

@pytest.mark.api
def test_create_user():
    payload = {"name": "Alice", "email": "alice@test.com", "age": 25}
    response = client.post("/users/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.api
def test_invalid_email():
    payload = {"name": "Bad", "email": "not-an-email"}
    response = client.post("/users/", json=payload)
    assert response.status_code == 422

@pytest.mark.api
def test_create_duplicate():
    payload = {"name": "Alice", "email": "alice@test.com"}
    client.post("/users/", json=payload)
    response = client.post("/users/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.api
def test_pagination():
    for i in range(5):
        client.post("/users/", json={"name": f"User{i}", "email": f"user{i}@test.com"})
    response = client.get("/users/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["email"] == "user2@test.com"

@pytest.mark.api
def test_update_user():
    res = client.post("/users/", json={"name": "Bob", "email": "bob@test.com", "age": 30})
    uid = res.json()["id"]
    res = client.put(f"/users/{uid}", json={"name": "BobUpdated", "email": "bob@test.com", "age": 99})
    assert res.status_code == 200
    assert res.json()["name"] == "BobUpdated"
    assert res.json()["age"] == 99

@pytest.mark.api
def test_delete_user():
    res = client.post("/users/", json={"name": "Charlie", "email": "charlie@test.com"})
    uid = res.json()["id"]
    res = client.delete(f"/users/{uid}")
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(f"/users/{uid}").status_code == 404

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="No DB URL")
def test_postgres_connection_real():
    real_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
    with real_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar() == 1
