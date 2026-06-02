from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Todo & Memo API", version="1.0.0")


class Status(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class Owner(BaseModel):
    id: int
    name: str
    email: str


class Tag(BaseModel):
    key: str
    color: Optional[str] = None


class Subtask(BaseModel):
    id: int
    title: str
    done: bool = False


class TodoIn(BaseModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.pending
    owner: Owner
    tags: list[Tag] = []
    subtasks: list[Subtask] = []
    metadata: dict = {}


class Todo(TodoIn):
    id: int
    created_at: datetime
    updated_at: datetime


class StatusPatch(BaseModel):
    status: Status


class SubtaskIn(BaseModel):
    title: str
    done: bool = False


# in-memory store
_todos: dict[int, Todo] = {}
_counter = {"todo": 0, "subtask": 0}


def _next(kind: str) -> int:
    _counter[kind] += 1
    return _counter[kind]


def _now() -> datetime:
    return datetime.now(timezone.utc)


@app.get("/health")
def health():
    return {"status": "ok", "count": len(_todos)}


@app.get("/todos", response_model=list[Todo])
def list_todos(
    status: Optional[Status] = None,
    owner_id: Optional[int] = None,
    limit: int = 50,
):
    items = list(_todos.values())
    if status is not None:
        items = [t for t in items if t.status == status]
    if owner_id is not None:
        items = [t for t in items if t.owner.id == owner_id]
    return items[:limit]


@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(payload: TodoIn):
    now = _now()
    todo = Todo(id=_next("todo"), created_at=now, updated_at=now, **payload.model_dump())
    _todos[todo.id] = todo
    return todo


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    todo = _todos.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoIn):
    existing = _todos.get(todo_id)
    if not existing:
        raise HTTPException(status_code=404, detail="todo not found")
    updated = Todo(
        id=todo_id,
        created_at=existing.created_at,
        updated_at=_now(),
        **payload.model_dump(),
    )
    _todos[todo_id] = updated
    return updated


@app.patch("/todos/{todo_id}/status", response_model=Todo)
def update_status(todo_id: int, patch: StatusPatch):
    todo = _todos.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="todo not found")
    todo.status = patch.status
    todo.updated_at = _now()
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail="todo not found")
    del _todos[todo_id]


@app.get("/todos/{todo_id}/subtasks", response_model=list[Subtask])
def list_subtasks(todo_id: int):
    todo = _todos.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="todo not found")
    return todo.subtasks


@app.post("/todos/{todo_id}/subtasks", response_model=Subtask, status_code=201)
def add_subtask(todo_id: int, payload: SubtaskIn):
    todo = _todos.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="todo not found")
    sub = Subtask(id=_next("subtask"), title=payload.title, done=payload.done)
    todo.subtasks.append(sub)
    todo.updated_at = _now()
    return sub


def _seed():
    alice = Owner(id=1, name="Alice", email="alice@example.com")
    bob = Owner(id=2, name="Bob", email="bob@example.com")
    samples = [
        TodoIn(
            title="Write release notes",
            description="v1.0.0 changelog",
            status=Status.in_progress,
            owner=alice,
            tags=[Tag(key="docs", color="blue"), Tag(key="release")],
            subtasks=[Subtask(id=_next("subtask"), title="draft", done=True),
                      Subtask(id=_next("subtask"), title="review")],
            metadata={"priority": "high", "estimate_h": 3},
        ),
        TodoIn(
            title="Buy groceries",
            owner=bob,
            tags=[Tag(key="home")],
            metadata={"store": "Emart"},
        ),
    ]
    for s in samples:
        now = _now()
        todo = Todo(id=_next("todo"), created_at=now, updated_at=now, **s.model_dump())
        _todos[todo.id] = todo


_seed()
