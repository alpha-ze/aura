"""
Tasks API.
GET    /api/tasks           — list tasks.
POST   /api/tasks           — create a task.
PUT    /api/tasks/{id}      — update a task.
DELETE /api/tasks/{id}      — delete a task.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(req: Request) -> list[Task]:
    store = req.app.state.task_store
    return await store.list_tasks()


@router.post("", response_model=Task)
async def create_task(payload: TaskCreate, req: Request) -> Task:
    store = req.app.state.task_store
    return await store.create_task(payload)


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, payload: TaskUpdate, req: Request) -> Task:
    store = req.app.state.task_store
    result = await store.update_task(task_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return result


@router.delete("/{task_id}")
async def delete_task(task_id: str, req: Request):
    store = req.app.state.task_store
    deleted = await store.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {"message": "Task deleted."}
