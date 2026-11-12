"""
Chat API endpoints.
POST /api/chat — send a message to the agent.
"""
from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from app.models.schemas import ChatRequest, ChatResponse, ConfirmationResponse
from app.dependencies import get_agent, get_conversation_store

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_chat(
    request: ChatRequest,
    req: Request,
) -> ChatResponse:
    """
    Process a natural language message through the AURA agent.
    Returns the agent's response, optionally including a plan and
    a confirmation request for risky actions.
    """
    agent = get_agent(req.app.state)
    store = get_conversation_store(req.app.state)

    # Generate or reuse conversation ID
    conversation_id = request.conversation_id or str(uuid4())

    # Load conversation history
    history = store.get(conversation_id, [])

    # Run agent
    response = await agent.process(
        message=request.message,
        conversation_id=conversation_id,
        conversation_history=history,
    )

    # Update history with the new exchange
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response.message})

    # Keep last 20 turns to avoid token overflow
    store[conversation_id] = history[-40:]

    return response
