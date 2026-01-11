"""Multi-agent simulation engine for scenario testing.

Orchestrates conversations between multiple agent personas with tool use,
behavior monitoring, and full audit trails for manipulation detection.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..evaluation import SandbaggingDetector
from ..llm.gateway import LLMGateway
from ..orchestration import AgentVerseBehaviorMonitor, BehaviorStorage
from ..storage.manager import StorageManager
from .conversation import Conversation, ConversationHistory
from .persona import AgentPersona, PersonaRole

logger = logging.getLogger(__name__)


class SimulationConfig(BaseModel):
    """Configuration for multi-agent simulation."""

    scenario_name: str = Field(..., description="Scenario name")
    max_turns: int = Field(default=20, description="Maximum conversation turns")
    turn_timeout_seconds: int = Field(default=60, description="Timeout per turn")
    enable_behavior_monitoring: bool = Field(default=True, description="Enable behavior monitoring")
    enable_sandbagging_detection: bool = Field(
        default=False, description="Enable sandbagging detection"
    )
    store_to_registry: bool = Field(default=True, description="Store conversation to registry")
    registry_prefix: str = Field(default="simulations", description="Registry storage prefix")
    tags: list[str] = Field(default_factory=list, description="Simulation tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SimulationResult(BaseModel):
    """Result of a multi-agent simulation."""

    simulation_id: str = Field(..., description="Simulation identifier")
    scenario_name: str = Field(..., description="Scenario name")
    success: bool = Field(..., description="Whether simulation completed successfully")
    conversation_history: ConversationHistory = Field(..., description="Full conversation history")
    behaviors_detected: list[dict[str, Any]] = Field(
        default_factory=list, description="Behaviors detected"
    )
    sandbagging_detected: bool = Field(default=False, description="Sandbagging detected")
    registry_uri: str | None = Field(default=None, description="Registry storage URI")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MultiAgentSimulation:
    """Multi-agent simulation engine.

    Orchestrates conversations between agent personas with:
    - Turn-based conversation flow
    - Tool use and registry access
    - Behavior monitoring and detection
    - Full audit trails with chain of thought
    - Serialization to registry for analysis
    """

    def __init__(
        self,
        gateway: LLMGateway | None = None,
        storage: StorageManager | None = None,
    ):
        """Initialize simulation engine.

        Args:
            gateway: LLM gateway for agent calls
            storage: Storage manager for registry access
        """
        self.gateway = gateway or LLMGateway()
        self.storage = storage or StorageManager()

        # Initialize monitoring systems
        self.behavior_storage = (
            BehaviorStorage(self.storage) if self.storage.is_available() else None
        )
        self.behavior_monitor = (
            AgentVerseBehaviorMonitor(storage=self.behavior_storage, auto_persist=True)
            if self.behavior_storage
            else None
        )
        self.sandbagging_detector = SandbaggingDetector(self.gateway)

        logger.info("MultiAgentSimulation initialized")

    async def run_simulation(
        self,
        personas: list[AgentPersona],
        config: SimulationConfig,
        initial_message: str | None = None,
    ) -> SimulationResult:
        """Run multi-agent simulation.

        Args:
            personas: List of agent personas to participate
            config: Simulation configuration
            initial_message: Optional initial message to start conversation

        Returns:
            SimulationResult with conversation history and analysis
        """
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(
            f"Starting simulation {simulation_id}: {config.scenario_name} "
            f"with {len(personas)} personas"
        )

        # Create conversation
        conversation = Conversation(
            conversation_id=simulation_id,
            scenario_name=config.scenario_name,
        )

        # Add participants
        for persona in personas:
            conversation.add_participant(persona.id)

        try:
            # Add initial message if provided
            if initial_message:
                conversation.add_turn(
                    persona_id="system",
                    persona_name="System",
                    persona_role="system",
                    message=initial_message,
                    message_role="system",
                )

            # Run conversation turns
            current_persona_idx = 0
            for turn_num in range(config.max_turns):
                # Get current persona
                persona = personas[current_persona_idx]

                logger.debug(f"Turn {turn_num + 1}: {persona.config.name}")

                # Execute turn
                turn_result = await self._execute_turn(
                    persona=persona,
                    conversation=conversation,
                    config=config,
                )

                # Check for conversation end
                if turn_result.get("end_conversation"):
                    logger.info("Conversation ended by persona")
                    break

                # Rotate to next persona
                current_persona_idx = (current_persona_idx + 1) % len(personas)

            # End conversation
            conversation.end_conversation()

            # Analyze conversation
            behaviors_detected = []
            sandbagging_detected = False

            if config.enable_behavior_monitoring and self.behavior_monitor:
                behaviors_detected = await self._analyze_behaviors(conversation, personas)

            if config.enable_sandbagging_detection:
                sandbagging_detected = await self._detect_sandbagging(conversation, personas)

            # Store to registry
            registry_uri = None
            if config.store_to_registry and self.storage.is_available():
                registry_uri = await self._store_to_registry(conversation, config)

            # Create result
            result = SimulationResult(
                simulation_id=simulation_id,
                scenario_name=config.scenario_name,
                success=True,
                conversation_history=conversation.get_history(),
                behaviors_detected=behaviors_detected,
                sandbagging_detected=sandbagging_detected,
                registry_uri=registry_uri,
                metadata={
                    "personas": [p.id for p in personas],
                    "total_turns": conversation.history.total_turns,
                    "total_tokens": conversation.history.total_tokens,
                },
            )

            logger.info(
                f"Simulation {simulation_id} completed: "
                f"{conversation.history.total_turns} turns, "
                f"{len(behaviors_detected)} behaviors detected"
            )
            return result

        except Exception as e:
            logger.error(f"Simulation {simulation_id} failed: {e}", exc_info=True)
            conversation.end_conversation()
            return SimulationResult(
                simulation_id=simulation_id,
                scenario_name=config.scenario_name,
                success=False,
                conversation_history=conversation.get_history(),
                error=str(e),
            )

    async def _execute_turn(
        self,
        persona: AgentPersona,
        conversation: Conversation,
        config: SimulationConfig,
    ) -> dict[str, Any]:
        """Execute a single conversation turn.

        Args:
            persona: Persona taking the turn
            conversation: Active conversation
            config: Simulation configuration

        Returns:
            Turn result dictionary
        """
        start_time = time.time()

        # Get conversation context
        messages = conversation.history.get_messages_for_llm()

        # For agent personas, call LLM
        if persona.config.role == PersonaRole.AGENT and persona.config.model:
            try:
                # Call LLM
                response = await self.gateway.call(
                    model=persona.config.model,
                    messages=messages,
                    temperature=persona.config.temperature,
                    max_tokens=persona.config.max_tokens,
                    thinking_level=persona.config.thinking_level,
                    thinking_budget=persona.config.thinking_budget,
                )

                # Extract response
                message_content = (
                    response.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                usage = response.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)

                # Extract thinking if present
                thinking = None
                if "thinking" in response:
                    thinking = response["thinking"]

                # Add turn to conversation
                latency_ms = int((time.time() - start_time) * 1000)
                conversation.add_turn(
                    persona_id=persona.id,
                    persona_name=persona.config.name,
                    persona_role=persona.config.role.value,
                    message=message_content,
                    message_role="assistant",
                    model_used=persona.config.model,
                    temperature=persona.config.temperature,
                    thinking_tokens=usage.get("thinking_tokens"),
                    chain_of_thought=thinking,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                )

                # Monitor behavior
                if config.enable_behavior_monitoring and self.behavior_monitor:
                    behaviors = self.behavior_monitor.monitor(
                        agent_id=persona.id,
                        content=message_content,
                        context={
                            "simulation": config.scenario_name,
                            "turn": conversation.history.total_turns,
                            "model": persona.config.model,
                        },
                    )
                    for behavior in behaviors:
                        conversation.history.add_behavior_detection(
                            {
                                "behavior_type": behavior.behavior_type,
                                "pattern_name": behavior.pattern_name,
                                "severity": behavior.severity,
                                "description": behavior.description,
                                "turn": conversation.history.total_turns,
                            }
                        )

                # Check for end conversation signal
                end_conversation = any(
                    phrase in message_content.lower()
                    for phrase in ["goodbye", "end conversation", "that's all"]
                )

                return {
                    "success": True,
                    "message": message_content,
                    "tokens_used": tokens_used,
                    "end_conversation": end_conversation,
                }

            except Exception as e:
                logger.error(f"Turn execution failed for {persona.id}: {e}")
                return {"success": False, "error": str(e)}

        # For human personas, use simulated behavior (in real use, this would be user input)
        else:
            # Simulated human response
            message = f"[Simulated response from {persona.config.name}]"
            conversation.add_turn(
                persona_id=persona.id,
                persona_name=persona.config.name,
                persona_role=persona.config.role.value,
                message=message,
                message_role="user",
            )
            return {"success": True, "message": message, "end_conversation": False}

    async def _analyze_behaviors(
        self, conversation: Conversation, personas: list[AgentPersona]
    ) -> list[dict[str, Any]]:
        """Analyze conversation for behaviors.

        Args:
            conversation: Conversation to analyze
            personas: Participating personas

        Returns:
            List of detected behaviors
        """
        return conversation.history.behaviors_detected

    async def _detect_sandbagging(
        self, conversation: Conversation, personas: list[AgentPersona]
    ) -> bool:
        """Detect sandbagging in conversation.

        Args:
            conversation: Conversation to analyze
            personas: Participating personas

        Returns:
            True if sandbagging detected
        """
        # This would run sandbagging detection on the conversation
        # For now, return the flag from conversation history
        return conversation.history.sandbagging_detected

    async def _store_to_registry(self, conversation: Conversation, config: SimulationConfig) -> str:
        """Store conversation to registry.

        Args:
            conversation: Conversation to store
            config: Simulation configuration

        Returns:
            Registry URI
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot store to registry")
            return ""

        try:
            # Generate URI
            date_str = datetime.now().strftime("%Y-%m-%d")
            uri = (
                f"s3://uer-simulations/{config.registry_prefix}/"
                f"{date_str}/{conversation.history.conversation_id}.json"
            )

            # Convert to registry format
            data = conversation.history.to_registry_format()
            data["config"] = config.model_dump()

            # Store
            content = json.dumps(data, indent=2).encode("utf-8")
            await self.storage.put(
                uri,
                content,
                content_type="application/json",
                metadata={
                    "type": "simulation",
                    "scenario": config.scenario_name,
                    "turns": str(conversation.history.total_turns),
                    "tokens": str(conversation.history.total_tokens),
                },
            )

            logger.info(f"Stored conversation to registry: {uri}")
            return uri

        except Exception as e:
            logger.error(f"Failed to store to registry: {e}", exc_info=True)
            return ""

    async def load_from_registry(self, uri: str) -> ConversationHistory:
        """Load conversation from registry.

        Args:
            uri: Registry URI

        Returns:
            ConversationHistory instance
        """
        if not self.storage.is_available():
            raise RuntimeError("Storage not available")

        content, _ = await self.storage.get(uri)
        data = json.loads(content.decode("utf-8"))
        return ConversationHistory.from_registry_format(data)

    async def save_persona(self, persona: AgentPersona) -> str:
        """Save persona to registry.

        Args:
            persona: Persona to save

        Returns:
            Registry URI
        """
        if not self.storage.is_available():
            raise RuntimeError("Storage not available")

        uri = f"s3://uer-personas/{persona.id}.json"
        data = persona.to_registry_format()
        content = json.dumps(data, indent=2).encode("utf-8")

        await self.storage.put(
            uri,
            content,
            content_type="application/json",
            metadata={
                "type": "persona",
                "role": persona.config.role.value,
                "version": persona.version,
            },
        )

        logger.info(f"Saved persona to registry: {uri}")
        return uri

    async def load_persona(self, uri: str) -> AgentPersona:
        """Load persona from registry.

        Args:
            uri: Registry URI

        Returns:
            AgentPersona instance
        """
        if not self.storage.is_available():
            raise RuntimeError("Storage not available")

        content, _ = await self.storage.get(uri)
        data = json.loads(content.decode("utf-8"))
        return AgentPersona.from_registry_format(data)
