from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DB = os.environ.get("DB_PATH", "/data/tasks.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                due_date TEXT,
                done INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium'
            )
        """)
        # If the table already exists without the priority column, add it
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        except Exception:
            pass  # Column already exists, that's fine
        conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    with get_db() as conn:
        tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return jsonify([dict(t) for t in tasks])

@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.json
    priority = data.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        priority = "medium"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO tasks (title, subject, due_date, priority) VALUES (?, ?, ?, ?)",
            (data["title"], data["subject"], data.get("due_date", ""), priority)
        )
        conn.commit()
    return jsonify({"message": "Task added"}), 201

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return jsonify({"message": "Task deleted"})

@app.route("/api/tasks/<int:task_id>/done", methods=["PUT"])
def toggle_done(task_id):
    with get_db() as conn:
        conn.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
        conn.commit()
    return jsonify({"message": "Updated"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if not app.config.get('TESTING'):
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)