import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

os.environ['DB_PATH'] = ':memory:'

import app as app_module
app_module.DB = ':memory:'

from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app_module.DB = ':memory:'
    with app.test_client() as client:
        init_db()
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200

def test_get_tasks_empty(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert json.loads(response.data) == []

def test_add_task(client):
    response = client.post('/api/tasks',
        data=json.dumps({'title': 'Test', 'subject': 'DevOps', 'due_date': ''}),
        content_type='application/json')
    assert response.status_code == 201

def test_get_tasks_after_adding(client):
    client.post('/api/tasks',
        data=json.dumps({'title': 'Test', 'subject': 'CS', 'due_date': ''}),
        content_type='application/json')
    tasks = json.loads(client.get('/api/tasks').data)
    assert len(tasks) == 1
    assert tasks[0]['title'] == 'Test'