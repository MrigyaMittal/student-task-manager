import pytest
import os
import tempfile
from app import app, init_db

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True

    import app as app_module
    app_module.DB = db_path
    init_db()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_health_check(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.get_json()['status'] == 'ok'

def test_get_tasks_empty(client):
    res = client.get('/api/tasks')
    assert res.status_code == 200
    assert res.get_json() == []

def test_add_task(client):
    res = client.post('/api/tasks', json={
        'title': 'Test Task',
        'subject': 'DevOps',
        'due_date': '2026-05-01'
    })
    assert res.status_code == 201

def test_get_tasks_after_adding(client):
    client.post('/api/tasks', json={
        'title': 'Test Task',
        'subject': 'DevOps',
        'due_date': '2026-05-01'
    })
    res = client.get('/api/tasks')
    tasks = res.get_json()
    assert len(tasks) == 1
    assert tasks[0]['title'] == 'Test Task'