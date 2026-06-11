import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DB_PATH", path)
    # Re-import to pick up the new DB_PATH
    import importlib
    import app as app_module
    importlib.reload(app_module)
    yield
    os.unlink(path)


@pytest.fixture
def app():
    import app as app_module
    return app_module.app


@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"


def test_index_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Task Manager" in res.data


def test_list_empty(client):
    res = client.get("/tasks")
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_task(client):
    res = client.post("/tasks", json={"title": "Write tests"})
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Write tests"
    assert body["completed"] is False
    assert body["id"] == 1


def test_create_task_requires_title(client):
    res = client.post("/tasks", json={"title": ""})
    assert res.status_code == 400


def test_update_task(client):
    client.post("/tasks", json={"title": "Deploy"})
    res = client.put("/tasks/1", json={"completed": True})
    assert res.status_code == 200
    assert res.get_json()["completed"] is True


def test_update_missing_task(client):
    res = client.put("/tasks/999", json={"completed": True})
    assert res.status_code == 404


def test_delete_task(client):
    client.post("/tasks", json={"title": "Delete me"})
    res = client.delete("/tasks/1")
    assert res.status_code == 204
    assert client.get("/tasks").get_json() == []


def test_delete_missing_task(client):
    res = client.delete("/tasks/999")
    assert res.status_code == 404
