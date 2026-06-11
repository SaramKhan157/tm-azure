import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/tmp/tasks.db")


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )


init_db()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Task Manager</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
    header { background: linear-gradient(135deg, #0078d4, #50e6ff); padding: 1.5rem 2rem; }
    header h1 { font-size: 1.8rem; font-weight: 700; }
    header p { font-size: 0.9rem; opacity: 0.85; }
    .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    .card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    input[type=text] { width: 100%; padding: 0.7rem 1rem; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #e2e8f0; font-size: 1rem; }
    button.primary { margin-top: 0.75rem; padding: 0.7rem 1.5rem; background: #0078d4; color: #fff; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
    button.primary:hover { background: #106ebe; }
    .task-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 0; border-bottom: 1px solid #334155; }
    .task-item:last-child { border-bottom: none; }
    .task-item input[type=checkbox] { width: 18px; height: 18px; accent-color: #0078d4; cursor: pointer; }
    .task-title { flex: 1; }
    .task-title.done { text-decoration: line-through; color: #64748b; }
    .badge { font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 9999px; background: #0078d410; color: #50e6ff; border: 1px solid #50e6ff40; }
    .delete-btn { background: none; border: none; color: #64748b; cursor: pointer; font-size: 1.1rem; }
    .delete-btn:hover { color: #ef4444; }
    .empty { text-align: center; color: #64748b; padding: 2rem 0; }
    .health { font-size: 0.8rem; color: #50e6ff; margin-top: 0.5rem; }
  </style>
</head>
<body>
  <header>
    <h1>Task Manager</h1>
    <p>CoderCo Assignment — Deployed on Azure Container Apps</p>
  </header>
  <div class="container">
    <div class="card">
      <h2>Add Task</h2>
      <input type="text" id="taskInput" placeholder="Enter task title..." onkeydown="if(event.key==='Enter') addTask()" />
      <button class="primary" onclick="addTask()">Add Task</button>
    </div>
    <div class="card">
      <h2>Tasks <span class="badge" id="count">0</span></h2>
      <div id="taskList"><div class="empty">No tasks yet. Add one above!</div></div>
    </div>
  </div>
  <script>
    async function load() {
      const res = await fetch('/tasks');
      const tasks = await res.json();
      const list = document.getElementById('taskList');
      const count = document.getElementById('count');
      count.textContent = tasks.length;
      if (!tasks.length) { list.innerHTML = '<div class="empty">No tasks yet. Add one above!</div>'; return; }
      list.innerHTML = tasks.map(t => `
        <div class="task-item" id="task-${t.id}">
          <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="toggle(${t.id}, this.checked)" />
          <span class="task-title ${t.completed ? 'done' : ''}">${t.title}</span>
          <button class="delete-btn" onclick="del(${t.id})">✕</button>
        </div>`).join('');
    }
    async function addTask() {
      const input = document.getElementById('taskInput');
      const title = input.value.trim();
      if (!title) return;
      await fetch('/tasks', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({title}) });
      input.value = '';
      load();
    }
    async function toggle(id, completed) {
      await fetch(`/tasks/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({completed}) });
      load();
    }
    async function del(id) {
      await fetch(`/tasks/${id}`, { method: 'DELETE' });
      load();
    }
    load();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


@app.route("/tasks", methods=["GET"])
def list_tasks():
    with db() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return jsonify([row_to_task(r) for r in rows])


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, completed, created_at) VALUES (?, 0, ?)",
            (title, datetime.utcnow().isoformat()),
        )
        task_id = cur.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(row)), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(force=True)
    with db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            return jsonify({"error": "not found"}), 404
        if "completed" in data:
            conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if data["completed"] else 0, task_id))
        if "title" in data:
            conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (data["title"], task_id))
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(row))


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            return jsonify({"error": "not found"}), 404
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return "", 204


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
