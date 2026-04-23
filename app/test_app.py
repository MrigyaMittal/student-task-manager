import pytest
import json
import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import app as app_module
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Point the app to an in-memory database
    app_module.DB = ':memory:'
    
    with app.test_client() as client:
        # Manually create the table in memory
        conn = sqlite3.connect(':memory:')
        # Patch get_db to return this connection
        def mock_get_db():
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    due_date TEXT,
                    done INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            return conn
        app_module.get_db = mock_get_db
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

def test_get_tasks_empty(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert json.loads(response.data) == []

def test_add_task(client):
    response = client.post('/api/tasks',
        data=json.dumps({'title': 'Test task', 'subject': 'DevOps', 'due_date': ''}),
        content_type='application/json')
    assert response.status_code == 201

def test_get_tasks_after_adding(client):
    client.post('/api/tasks',
        data=json.dumps({'title': 'My task', 'subject': 'CS', 'due_date': ''}),
        content_type='application/json')
    tasks = json.loads(client.get('/api/tasks').data)
    assert len(tasks) == 1
    assert tasks[0]['title'] == 'My task'