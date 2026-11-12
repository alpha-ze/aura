"""
Activity log API.
GET    /api/activity       — recent activity entries.
DELETE /api/activity       — clear activity log.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("")
async def get_activity(req: Request, limit: int = 100):
    log = req.app.state.activity_log
    entries = await log.get_entries(limit=limit)
    return entries


@router.delete("")
async def clear_activity(req: Request):
    log = req.app.state.activity_log
    await log.clear()
    return {"message": "Activity log cleared."}
