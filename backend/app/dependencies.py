"""
Application-level dependency accessors.
App state is set up in main.py lifespan and accessed here.
"""
from __future__ import annotations

from typing import Any

from app.agent.agent import AuraAgent
from app.agent.router import ToolRegistry
from app.storage.activity_log import ActivityLogger


def get_agent(state: Any) -> AuraAgent:
    return state.agent


def get_registry(state: Any) -> ToolRegistry:
    return state.registry


def get_conversation_store(state: Any) -> dict:
    return state.conversation_store
