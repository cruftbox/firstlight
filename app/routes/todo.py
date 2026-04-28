from flask import Blueprint, render_template, request, jsonify
from pathlib import Path
import json
import uuid

todo_bp = Blueprint("todo", __name__)
TODOS_PATH = Path("/app/config/todos.json")


def _load() -> list:
    if not TODOS_PATH.exists():
        return []
    try:
        return json.loads(TODOS_PATH.read_text())
    except Exception:
        return []


def _save(todos: list) -> None:
    TODOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TODOS_PATH.write_text(json.dumps(todos, indent=2))


@todo_bp.route("/todo")
def index():
    return render_template("todo.html", todos=_load())


@todo_bp.route("/api/todos", methods=["GET"])
def get_todos():
    return jsonify(_load())


@todo_bp.route("/api/todos", methods=["POST"])
def create_todo():
    data = request.get_json(silent=True) or {}
    todos = _load()
    todo = {
        "id": str(uuid.uuid4()),
        "text": (data.get("text") or "").strip(),
        "done": False,
    }
    todos.append(todo)
    _save(todos)
    return jsonify(todo), 201


@todo_bp.route("/api/todos", methods=["DELETE"])
def delete_todo():
    data = request.get_json(silent=True) or {}
    todo_id = data.get("id")
    todos = [t for t in _load() if t["id"] != todo_id]
    _save(todos)
    return jsonify({"status": "ok"})
