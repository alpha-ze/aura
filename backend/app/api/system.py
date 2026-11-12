"""
System information API endpoints.
GET /api/system — returns current system info snapshot.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.tools.system import get_system_info, get_running_processes
from app.models.schemas import SystemInfo

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("")
async def system_info():
    """Return a snapshot of system information."""
    result = await get_system_info()
    if result.success:
        return result.data
    return {"error": result.message}


@router.get("/processes")
async def running_processes(top_n: int = 15):
    """Return top N processes by memory usage."""
    result = await get_running_processes(top_n=top_n)
    if result.success:
        return result.data
    return {"error": result.message}
