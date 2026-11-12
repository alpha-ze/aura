"""
Tools API.
GET  /api/tools           — list all registered tools.
POST /api/tools/execute   — directly execute a tool (for testing/advanced use).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ToolCall, ToolResult
from app.dependencies import get_registry
from app.agent.safety import is_blocked, requires_confirmation

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def list_tools(req: Request):
    """List all registered tools with their descriptions and risk levels."""
    registry = get_registry(req.app.state)
    return registry.list_tools()


@router.post("/execute")
async def execute_tool(tool_call: ToolCall, req: Request) -> ToolResult:
    """
    Directly execute a tool.
    HIGH/CRITICAL risk tools are still blocked without a prior confirmation.
    This endpoint is for Power User mode and diagnostics.
    """
    registry = get_registry(req.app.state)

    if is_blocked(tool_call.tool):
        raise HTTPException(status_code=403, detail=f"Tool '{tool_call.tool}' is blocked.")

    if requires_confirmation(tool_call.tool):
        raise HTTPException(
            status_code=403,
            detail=f"Tool '{tool_call.tool}' requires confirmation. Use /api/chat to invoke it through the agent.",
        )

    return await registry.execute(tool_call, confirmed=False)
