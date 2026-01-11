# Changelog

All notable changes to UER (Universal Expert Registry) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-01-11

### Added

#### Multi-Agent Safety Monitoring System
- **AgentVerseBehaviorMonitor**: Enhanced behavior monitoring with 15+ patterns across 6 categories
  - Volunteer behaviors (Chen 2024 AgentVerse)
  - Conformity behaviors (Chen 2024 AgentVerse)
  - Destructive behaviors (Chen 2024 AgentVerse)
  - Sycophancy detection (Sharma 2024)
  - Deception detection (Park 2024)
  - Sandbagging detection (van der Weij 2024)
- **BehaviorStorage**: Persistent S3 storage for behavior logs, metrics, and trends
  - Hierarchical storage by date and agent
  - Daily/weekly/monthly metrics aggregation
  - Trend detection with time series analysis
- **BehaviorAnalyzer**: Comprehensive analysis dashboard
  - Agent profiling with risk scoring (0-100)
  - Multi-agent comparison reports
  - Safety reports with automated recommendations
  - Visualization data generation
  - Markdown and JSON export

#### Sandbagging Detection Framework
- **SandbaggingDetector**: Multi-method detection system (van der Weij 2024)
  - Consistency testing across similar questions
  - Difficulty profiling with anomaly detection
  - Capability elicitation techniques
  - Comprehensive reporting with evidence
- Support for custom question sets with difficulty levels
- Quick test functionality with predefined questions
- Domain-specific testing (math, reasoning, general)

#### Multi-Agent Simulation Framework
- **AgentPersona**: Serializable agent personas with versioning
  - Configurable roles (agent, human, system, auditor)
  - System prompts and LLM parameters
  - Tool access control and permissions
  - RAG capabilities
  - Registry CRUD permissions
- **ConversationHistory**: Complete audit trails
  - Turn-by-turn tracking with timestamps
  - Chain of thought capture
  - Tool call logging
  - Behavior detection integration
  - Performance metrics (tokens, latency)
- **MultiAgentSimulation**: Orchestration engine
  - Turn-based conversation flow
  - Automatic behavior monitoring
  - Optional sandbagging detection
  - Registry persistence
- Predefined persona templates:
  - helpful_assistant
  - researcher
  - curious_user
  - adversarial_tester
  - safety_auditor

#### MCP Tools
- **Behavior Monitoring Tools** (5 new tools):
  - `behavior_get_logs`: Retrieve logs with filtering
  - `behavior_get_metrics`: Aggregated metrics
  - `behavior_analyze_agent`: Agent profiling
  - `behavior_generate_report`: Safety reports
  - `behavior_compare_agents`: Multi-agent comparison
- **Sandbagging Detection Tools** (2 new tools):
  - `sandbagging_evaluate`: Full evaluation
  - `sandbagging_quick_test`: Rapid screening

### Enhanced
- Integrated behavior monitoring into SubagentOrchestrator
- Enhanced delegation results with behavior summaries
- Improved context assembly with Jinja2 templates
- Added auto-persist mode for behavior logs
- Extended storage capabilities for simulation data

### Storage Structure
- `s3://uer-behavior/logs/{date}/{agent_id}/{timestamp}.json` - Behavior logs
- `s3://uer-behavior/metrics/{period}/{date}.json` - Aggregated metrics
- `s3://uer-behavior/trends/{pattern_name}.json` - Trend data
- `s3://uer-personas/{persona_id}.json` - Agent personas
- `s3://uer-simulations/{prefix}/{date}/{conversation_id}.json` - Conversations

### Research Alignment
- Chen 2024: AgentVerse multi-agent behavior patterns
- Sharma 2024: Sycophancy detection and mitigation
- Park 2024: Deception and unfaithful reasoning detection
- van der Weij 2024: Multi-method sandbagging detection

### Documentation
- Added comprehensive hackathon research documentation
- Detailed API documentation for all new components
- Usage examples for simulation framework
- Integration guides for behavior monitoring

## [4.0.0] - Previous Release

### Added
- Core LLM gateway with LiteLLM integration
- MCP server implementation
- S3-compatible storage backend (MinIO)
- Skills and templates management
- Subagent delegation framework
- Context assembly with Jinja2

[4.1.0]: https://github.com/margusmartsepp/UER/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/margusmartsepp/UER/releases/tag/v4.0.0
