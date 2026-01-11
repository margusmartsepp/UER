"""Multi-agent simulation framework for scenario testing and manipulation detection.

Enables creation of agent personas with different roles (agent, human), system prompts,
tools, RAG capabilities, and full serialization to registry for reuse and analysis.
"""

from .conversation import Conversation, ConversationHistory, ConversationTurn
from .persona import AgentPersona, PersonaConfig, PersonaRole
from .simulation import MultiAgentSimulation, SimulationConfig, SimulationResult

__all__ = [
    "AgentPersona",
    "PersonaRole",
    "PersonaConfig",
    "MultiAgentSimulation",
    "SimulationConfig",
    "SimulationResult",
    "Conversation",
    "ConversationTurn",
    "ConversationHistory",
]
