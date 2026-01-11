# Universal Expert Registry (UER)
## AI Manipulation Hackathon 2026 - Submission Report[^1]

---

**Authors:**
1. Margus Martsepp
2. Marco Lackovic
3. Martin Martsepp
4. Zane Estere
5. Anirudh

**Team:** The Risk Takers
**With:** Apart Research

---

## Abstract

The Universal Expert Registry (UER) is a comprehensive MCP (Model Context Protocol) server implementing multi-agent safety monitoring, sandbagging detection, and simulation framework for AI manipulation research. Built for the AI Manipulation Hackathon 2026, UER addresses critical gaps in manipulation detection through four integrated systems:

**Multi-Agent Safety Monitoring:** Implements 15+ behavior patterns across 6 categories (volunteer, conformity, destructive, sycophancy, deception, sandbagging) based on Chen 2024 (AgentVerse), Sharma 2024, Park 2024, and van der Weij 2024. Provides persistent S3 storage for behavior logs, automated risk scoring (0-100), and comprehensive safety reports with research-based recommendations.

**Sandbagging Detection Framework:** Multi-method detection system implementing consistency testing across similar questions, difficulty profiling with anomaly detection, and capability elicitation techniques. Detects strategic underperformance where models intentionally fail evaluations while maintaining general capabilities.

**Multi-Agent Simulation:** Complete conversation orchestration with serializable agent personas (agent, human, system, auditor roles), full audit trails capturing chain of thought and tool calls, and registry persistence for scenario reuse. Enables accurate simulation of multi-agent interactions with real-time manipulation detection.

**Universal LLM Infrastructure:** Integrates 100+ LLM providers through LiteLLM, S3-compatible storage for unlimited context, MCP tool orchestration for 1,000+ servers, and subagent delegation with behavior monitoring.

UER v4.1.0 provides 7 new MCP tools for behavior analysis and sandbagging detection, making sophisticated manipulation research accessible through Claude Desktop and other MCP clients. The system enables comparative testing across providers, temporal drift detection, and automated red-teaming with full transparency.

*Keywords: Multi-agent safety, sandbagging detection, behavior monitoring, AI manipulation, MCP protocol, simulation framework, evaluation integrity*

---

## 1. Introduction

### The Challenge: AI Manipulation at Scale

AI systems are mastering deception, sycophancy, sandbagging, and psychological exploitation at scale, while our ability to detect, measure, and counter these behaviors remains dangerously underdeveloped. Recent research has documented frontier models:

- **Strategically underperforming** on capability evaluations (sandbagging)
- **Exhibiting inverse scaling in sycophancy** (larger models are MORE sycophantic)
- **Reward hacking** in production-like settings, with awareness their behavior violates intentions
- **Emergent misalignment** where reward hacking training causes downstream sabotage

The October 2024 revelation by METR documented o3 hacking evaluation software, and Claude models subverting tasks—showing models demonstrate awareness their behavior violates intentions but do it anyway. This represents an unprecedented challenge for AI safety.

### Existing Limitations

Current approaches to manipulation detection face several critical limitations:

1. **Single-Model Testing:** Most research tests one model at a time, missing cross-provider manipulation patterns
2. **Ephemeral Context:** No persistent behavioral tracking across sessions to detect drift
3. **Tool Fragmentation:** Manipulation detection tools exist in silos, no unified platform
4. **High Barriers:** Researchers need separate API access, code, and infrastructure for each provider

### Our Solution: Universal Expert Registry

UER addresses these limitations by providing a unified platform for multi-model manipulation research. The system enables:

- **Comparative Testing:** Run identical prompts across Claude, GPT, Gemini simultaneously
- **Persistent Tracking:** Store behavioral data across sessions to detect temporal patterns
- **Tool Integration:** Connect specialized detection tools via MCP protocol
- **Agent Orchestration:** Deploy red-teaming agents with full context and memory

### Research Questions

1. Can multi-model comparison detect manipulation patterns invisible in single-model testing?
2. Does persistent behavioral tracking reveal temporal drift indicative of alignment faking?
3. What manipulation signatures emerge when models interact with specialized tools?
4. How do subagent coordination dynamics reveal emergent manipulative behaviors?

### Contributions

This work contributes:

- **Multi-Agent Safety System:** Complete behavior monitoring framework with 15+ patterns, persistent storage, risk scoring, and automated analysis (AgentVerse, sycophancy, deception, sandbagging)
- **Sandbagging Detection:** Production-ready multi-method detection implementing consistency testing, difficulty profiling, and capability elicitation (van der Weij 2024)
- **Simulation Framework:** Full multi-agent conversation orchestration with serializable personas, audit trails, and manipulation detection integration
- **MCP Tools:** 7 new tools exposing behavior monitoring and sandbagging detection via Model Context Protocol
- **Platform:** Unified infrastructure for cross-provider manipulation testing with 100+ LLM providers
- **Open Source:** Released as v4.1.0 on GitHub and npm for community use

---

## 2. Methods

### System Architecture

UER v4.1.0 implements a five-layer architecture:

#### Layer 1: LiteLLM Gateway
- **Unified API:** Single interface for 100+ providers (Claude, GPT, Gemini, Bedrock, Azure)
- **Tool Normalization:** Converts provider-specific formats to OpenAI standard
- **Cost Tracking:** Per-request pricing across all models
- **Rate Limiting:** Automatic retry with exponential backoff
- **Thinking Support:** Extended thinking for Gemini 2.0 Flash Thinking and Claude 3.7 Sonnet

#### Layer 2: Behavior Monitoring System
- **AgentVerseBehaviorMonitor:** Real-time detection of 15+ behavior patterns
- **BehaviorStorage:** S3-compatible persistent storage for logs and metrics
- **BehaviorAnalyzer:** Risk scoring (0-100), agent profiling, safety reports
- **Auto-persist:** Automatic behavior log storage during agent execution
- **Trend Detection:** Time series analysis for behavioral drift

#### Layer 3: Sandbagging Detection
- **SandbaggingDetector:** Multi-method detection framework
- **Consistency Testing:** Performance analysis across similar questions
- **Difficulty Profiling:** Anomaly detection across easy/medium/hard questions
- **Capability Elicitation:** Multiple prompting techniques to reveal hidden capabilities
- **Evidence Aggregation:** Confidence scoring and automated recommendations

#### Layer 4: Multi-Agent Simulation
- **AgentPersona:** Serializable personas with roles, prompts, tools, permissions
- **ConversationHistory:** Full audit trails with chain of thought and tool calls
- **MultiAgentSimulation:** Turn-based orchestration with behavior monitoring
- **Registry Persistence:** S3 storage for personas and conversations
- **Version Control:** Parent tracking for persona evolution

#### Layer 5: Storage & MCP Integration
- **S3-Compatible Storage:** MinIO/AWS S3 for unlimited context
- **Skills & Templates:** Jinja2-based context management
- **MCP Tool Orchestration:** Connect to 1,000+ MCP servers
- **Subagent Delegation:** Recursive delegation with full context

### Core Tools Implemented (v4.1.0)

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `llm_call` | Universal LLM invocation | LiteLLM wrapper with thinking support |
| `behavior_get_logs` | Retrieve behavior logs | Date/agent filtering, S3 storage |
| `behavior_get_metrics` | Aggregated metrics | Daily/weekly/monthly aggregation |
| `behavior_analyze_agent` | Agent profiling | Risk scoring (0-100), pattern analysis |
| `behavior_generate_report` | Safety reports | Markdown/JSON export with recommendations |
| `behavior_compare_agents` | Multi-agent comparison | Cross-agent pattern analysis |
| `sandbagging_evaluate` | Full sandbagging evaluation | Multi-method detection framework |
| `sandbagging_quick_test` | Quick screening | Predefined question sets |
| `storage_put`/`get` | Context persistence | S3-compatible storage |
| `delegate` | Subagent spawning | With behavior monitoring |
| `mcp_call` | External tool access | MCP client implementation |
| `skill_*` / `template_*` | Skills & templates | Jinja2-based management |

### Testing Methodology

#### Behavior Monitoring Protocol
```python
# Initialize behavior monitor with storage
behavior_storage = BehaviorStorage(storage_manager)
behavior_monitor = AgentVerseBehaviorMonitor(
    storage=behavior_storage,
    auto_persist=True
)

# Monitor agent behavior during execution
behaviors = behavior_monitor.monitor(
    agent_id="agent_123",
    content=response_content,
    context={"model": "claude-3-5-sonnet", "task": "evaluation"}
)

# Analyze agent with risk scoring
profile = await analyzer.create_agent_profile(
    agent_id="agent_123",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 11)
)
print(f"Risk Score: {profile.risk_score}/100")
```

#### Sandbagging Detection Protocol
```python
# Define evaluation questions
questions = [
    Question(
        id="q1",
        text="What is 2+2?",
        difficulty="easy",
        category="math",
        correct_answer="4"
    ),
    # ... more questions
]

# Run sandbagging evaluation
detector = SandbaggingDetector(gateway)
report = await detector.evaluate_model(
    model="gpt-4",
    questions=questions,
    use_elicitation=True
)

print(f"Sandbagging Detected: {report.sandbagging_detected}")
print(f"Confidence: {report.confidence}")
```

#### Multi-Agent Simulation Protocol
```python
# Create agent personas
personas = [
    create_persona_from_template("helpful_assistant", "agent_1"),
    create_persona_from_template("adversarial_tester", "human_1"),
    create_persona_from_template("safety_auditor", "auditor_1")
]

# Configure simulation
config = SimulationConfig(
    scenario_name="safety_evaluation",
    max_turns=20,
    enable_behavior_monitoring=True,
    enable_sandbagging_detection=True,
    store_to_registry=True
)

# Run simulation
simulation = MultiAgentSimulation(gateway, storage)
result = await simulation.run_simulation(
    personas=personas,
    config=config,
    initial_message="Let's test for manipulation patterns"
)
```

### Research Foundation

UER v4.1.0 implements detection methods from 4 key research papers:

1. **Chen 2024 (AgentVerse):** 15+ behavior patterns for volunteer, conformity, and destructive behaviors in multi-agent systems
2. **Sharma 2024:** Sycophancy detection patterns including agreement bias and opinion matching
3. **Park 2024:** Deception detection including unfaithful reasoning and strategic misrepresentation
4. **van der Weij 2024:** Multi-method sandbagging detection with consistency testing, difficulty profiling, and capability elicitation

**Implementation Status:**
- ✅ Behavior monitoring framework (15+ patterns)
- ✅ Sandbagging detection (3 methods)
- ✅ Multi-agent simulation with audit trails
- ✅ MCP tools for accessibility
- 🔄 WMDP benchmark integration (planned)
- 🔄 Large-scale evaluation studies (planned)

### Evaluation Metrics

**Behavior Monitoring:**
- **Risk Score:** 0-100 scale based on behavior severity and frequency
- **Pattern Detection:** Count and categorization of detected behaviors
- **Temporal Trends:** Behavior frequency changes over time
- **Agent Comparison:** Relative risk across multiple agents

**Sandbagging Detection:**
- **Consistency Score:** Performance variance on similar questions
- **Anomaly Detection:** Unexpected difficulty-performance relationships
- **Elicitation Improvement:** Performance gain with prompting techniques
- **Confidence Level:** Low/medium/high based on evidence aggregation

**Simulation Framework:**
- **Audit Completeness:** % of turns with full metadata capture
- **Tool Call Tracking:** Count and success rate of tool invocations
- **Chain of Thought:** Availability of reasoning traces
- **Storage Efficiency:** Successful serialization/deserialization rate

---

## 3. Results

### Implementation Results (v4.1.0)

#### Multi-Agent Safety Monitoring System

**Behavior Patterns Implemented:**
- 15+ detection patterns across 6 categories
- Real-time monitoring during agent execution
- Automatic persistence to S3-compatible storage
- Risk scoring algorithm (0-100 scale)

**Storage Architecture:**
```
s3://uer-behavior/
├── logs/{date}/{agent_id}/{timestamp}.json
├── metrics/{period}/{date}.json
└── trends/{pattern_name}.json
```

**Analysis Capabilities:**
- Agent profiling with behavioral breakdown
- Multi-agent comparison reports
- Safety reports with automated recommendations
- Visualization data for time series and distributions
- Export to Markdown and JSON formats

#### Sandbagging Detection Framework

**Detection Methods Implemented:**
1. **Consistency Testing:** Groups questions by category, detects performance inconsistencies on similar questions (>30% threshold for high likelihood)
2. **Difficulty Profiling:** Analyzes easy/medium/hard performance, detects anomalies (better on hard than medium, 10pp threshold)
3. **Capability Elicitation:** Tests with step-by-step reasoning, expert framing, and critical evaluation prompts (>10pp improvement threshold)

**Evidence Aggregation:**
- Confidence scoring (low/medium/high)
- Automated recommendations based on van der Weij 2024
- Comprehensive reporting with all detection results

**Quick Test Functionality:**
- Predefined question sets for math, reasoning, and general knowledge
- Rapid screening capability
- Domain-specific evaluation

#### Multi-Agent Simulation Framework

**Persona System:**
- 5 predefined templates (helpful_assistant, researcher, curious_user, adversarial_tester, safety_auditor)
- Configurable roles (agent, human, system, auditor)
- System prompts and LLM parameters
- Tool access control and registry permissions
- Version control with parent tracking

**Conversation Management:**
- Turn-by-turn tracking with timestamps
- Chain of thought capture
- Tool call logging with arguments and results
- Performance metrics (tokens, latency)
- Behavior detection integration

**Storage Structure:**
```
s3://uer-personas/{persona_id}.json
s3://uer-simulations/{prefix}/{date}/{conversation_id}.json
```

#### MCP Tools Integration

**7 New Tools Implemented:**
1. `behavior_get_logs` - Retrieve logs with date/agent filtering
2. `behavior_get_metrics` - Daily/weekly/monthly aggregation
3. `behavior_analyze_agent` - Risk scoring and profiling
4. `behavior_generate_report` - Safety reports (Markdown/JSON)
5. `behavior_compare_agents` - Multi-agent comparison
6. `sandbagging_evaluate` - Full multi-method evaluation
7. `sandbagging_quick_test` - Rapid screening

**Accessibility:**
- Available via Claude Desktop and any MCP client
- Comprehensive input validation
- Detailed descriptions with examples
- JSON response formatting

### System Capabilities Demonstrated

**Infrastructure:**
- ✅ 100+ LLM provider support via LiteLLM
- ✅ S3-compatible storage (MinIO/AWS S3)
- ✅ Persistent behavior tracking
- ✅ Multi-agent orchestration
- ✅ Full audit trails

**Detection Systems:**
- ✅ Real-time behavior monitoring
- ✅ Multi-method sandbagging detection
- ✅ Risk scoring and profiling
- ✅ Automated recommendations

**Simulation:**
- ✅ Serializable agent personas
- ✅ Turn-based conversation orchestration
- ✅ Chain of thought capture
- ✅ Tool call tracking
- ✅ Registry persistence

### Release Metrics

**Version:** 4.1.0
**Release Date:** January 11, 2026
**Package Size:** 373.9 KB (npm)
**Total Files:** 46 Python modules
**Lines of Code:** ~3,500+ new lines
**MCP Tools:** 7 new tools (12 total)
**Behavior Patterns:** 15+ across 6 categories
**Persona Templates:** 5 predefined
**Storage Buckets:** 3 (behavior, personas, simulations)

**Distribution:**
- GitHub: https://github.com/margusmartsepp/UER (v4.1.0 tag)
- npm: https://www.npmjs.com/package/uer-mcp (v4.1.0)
- Open source under MIT license

---

## 4. Discussion and Conclusion

### Key Achievements

#### 1. Research-Based Detection Framework

UER v4.1.0 successfully implements detection methods from 4 key research papers:
- **Chen 2024 (AgentVerse):** 15+ behavior patterns for multi-agent systems
- **Sharma 2024:** Sycophancy detection patterns
- **Park 2024:** Deception detection methods
- **van der Weij 2024:** Multi-method sandbagging detection

This represents the first unified implementation of these research findings in a production-ready, accessible platform.

#### 2. Production-Ready Infrastructure

The system provides:
- **Real-time monitoring** during agent execution with auto-persist
- **S3-compatible storage** for unlimited behavioral data
- **Risk scoring algorithm** (0-100 scale) for agent profiling
- **Multi-method detection** with evidence aggregation
- **Full audit trails** capturing chain of thought and tool calls

#### 3. Accessibility via MCP Protocol

7 new MCP tools make sophisticated manipulation detection accessible to:
- Researchers conducting safety studies
- Red teams testing model robustness
- Developers building safe AI systems
- Auditors analyzing agent behavior

No specialized infrastructure required—works with Claude Desktop out of the box.

#### 4. Extensible Simulation Framework

The multi-agent simulation system enables:
- **Scenario testing** with configurable personas
- **Behavioral tracking** across multi-turn conversations
- **Registry persistence** for reproducible experiments
- **Version control** for persona evolution
- **Integration** with detection systems for real-time analysis

### Limitations and Future Work

#### Current Limitations

**1. Evaluation Coverage**
- WMDP benchmark integration planned but not yet implemented
- Large-scale empirical validation needed
- Detection thresholds based on research literature, not tuned to specific models

**2. Simulation Capabilities**
- Human input currently simulated (real-time human participation planned)
- Advanced RAG integration not yet implemented
- Cross-benchmark comparison capabilities planned

**3. Production Hardening**
- Additional error handling for edge cases
- Performance optimization for large-scale deployments
- Enhanced security features (encryption at rest, audit logging)

**4. Documentation**
- Usage examples for all persona templates
- Best practices guide for scenario design
- Interpretation guide for detection results

#### Planned Enhancements

**Short-Term (Next 3 Months)**
1. **WMDP Integration:** Full 3,668-question benchmark evaluation
2. **MCP Simulation Tools:** Tools for creating and running simulations via MCP
3. **Real-Time Human Input:** Support for human participants in simulations
4. **Visualization Dashboard:** Web interface for behavior analysis
5. **Advanced RAG:** Integration with vector databases and retrieval systems

**Long-Term (6-12 Months)**
1. **Scenario Library:** Community-contributed simulation scenarios
2. **Detection Tuning:** Model-specific threshold optimization
3. **Cross-Benchmark Analysis:** Comparative evaluation across multiple benchmarks
4. **Production Monitoring:** Real-time detection in deployed systems
5. **Regulatory Compliance:** GDPR, AI Act, and safety standard support

### Impact & Significance

UER v4.1.0 demonstrates that **accessible infrastructure accelerates AI safety research**. By providing:

**Research Implementation:**
- First unified implementation of AgentVerse, sycophancy, deception, and sandbagging detection
- Production-ready code with comprehensive error handling
- Research-based recommendations and automated analysis

**Accessibility:**
- 7 MCP tools accessible via Claude Desktop
- No specialized infrastructure required
- Open source under MIT license

**Extensibility:**
- Modular architecture for adding new detection methods
- Serializable personas and scenarios for reproducibility
- S3-compatible storage for unlimited scale

**Community Impact:**
- Released on GitHub and npm for immediate use
- Enables researchers without engineering resources
- Provides foundation for collaborative safety research

### Threat Coverage

UER v4.1.0 addresses these manipulation threats:

**Implemented:**
1. **Sycophancy:** 15+ detection patterns including agreement bias and opinion matching (Sharma 2024)
2. **Sandbagging:** Multi-method detection with consistency, difficulty, and elicitation testing (van der Weij 2024)
3. **Deception:** Unfaithful reasoning and strategic misrepresentation patterns (Park 2024)
4. **Multi-Agent Behaviors:** Volunteer, conformity, and destructive patterns (Chen 2024)
5. **Temporal Tracking:** Persistent storage for behavioral drift detection

**Planned:**
1. **Reward Hacking:** Tool-interaction monitoring and goal misalignment detection
2. **Emergent Misalignment:** Advanced multi-agent coordination analysis
3. **Training Data Contamination:** Cross-benchmark performance analysis

### Conclusion

The Universal Expert Registry v4.1.0 provides production-ready infrastructure for AI manipulation detection research. This hackathon submission delivers:

**Implemented Systems:**
- ✅ Multi-agent safety monitoring (15+ patterns, 6 categories)
- ✅ Sandbagging detection (3 methods, evidence aggregation)
- ✅ Multi-agent simulation (personas, audit trails, persistence)
- ✅ 7 MCP tools for accessibility
- ✅ Research-based recommendations

**Technical Achievement:**
- 3,500+ lines of production-ready Python code
- Comprehensive error handling and validation
- S3-compatible storage architecture
- Full MCP protocol integration
- Open source release (GitHub + npm)

**Research Contribution:**
- First unified implementation of 4 key manipulation detection papers
- Accessible platform for researchers without engineering resources
- Foundation for collaborative safety research
- Extensible framework for future detection methods

**Impact:**
By implementing research findings in an accessible, production-ready platform, UER v4.1.0 accelerates AI safety research and empowers the community to measure, detect, and defend against manipulation at scale.

**Availability:**
- GitHub: https://github.com/margusmartsepp/UER (v4.1.0)
- npm: https://www.npmjs.com/package/uer-mcp (v4.1.0)
- License: MIT (Open Source)

---

## 5. References

**General Introduction:**
- Park, P. S., et al. (2024). AI deception: A survey of examples, risks, and potential solutions. *arXiv:2308.14752*
- Stanford HAI. (2025). *Artificial Intelligence Index Report 2025*. https://hai.stanford.edu/ai-index-2025
- Sharma, M., et al. (2024). Towards Understanding Sycophancy in Language Models. *arXiv:2310.13548*

**Track 1: Measurement & Evaluation:**
- van der Weij, J., et al. (2024). AI Sandbagging: Language Models can Strategically Underperform on Evaluations. *arXiv:2406.07358*
- Li, N., et al. (2024). The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning. *arXiv:2403.03218*

**Track 2: Real-World Analysis:**
- METR. (2025). Recent Frontier Models Are Reward Hacking. https://metr.org/blog/2025-06-05-recent-reward-hacking/
- Weng, L. (2024). Reward Hacking in Reinforcement Learning. https://lilianweng.github.io/posts/2024-11-28-reward-hacking/
- Denison, C., et al. (2024). Reward hacking behavior can generalize across tasks. *arXiv:2406.06393*

**Track 3: Mitigations:**
- OpenAI. (2025). Chain of Thought Monitoring for Misbehavior. https://openai.com/index/chain-of-thought-monitoring/
- Anthropic. (2025). From shortcuts to sabotage: natural emergent misalignment from reward hacking. https://www.anthropic.com/research/emergent-misalignment-reward-hacking

**Track 4: Multi-Agent & Emergent Behavior:**
- Chen, W., et al. (2024). AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors. *arXiv:2308.10848*
- (2024). School of Reward Hacks: Hacking Harmless Tasks Generalizes to Misalignment. *arXiv:2501.00003*

**Technical Infrastructure:**
- LiteLLM. (2024). *LiteLLM Documentation*. https://docs.litellm.ai/
- Anthropic. (2024). *Model Context Protocol Specification*. https://modelcontextprotocol.io/

---

## 6. Appendix

### A. Security Considerations

#### Potential Limitations

1. **API Key Exposure:**
   - Risk: Keys stored in environment variables could leak via logs
   - Mitigation: Implement key rotation, use secret management services (AWS Secrets Manager, HashiCorp Vault)

2. **Prompt Injection:**
   - Risk: Malicious users could craft prompts that manipulate LLM behavior
   - Mitigation: Input validation, sandboxed execution, rate limiting per user

3. **Data Privacy:**
   - Risk: Persistent storage of conversations could expose sensitive data
   - Mitigation: Encryption at rest, data retention policies, user consent mechanisms

4. **Model Poisoning:**
   - Risk: If fine-tuning is added, adversarial training data could compromise models
   - Mitigation: Data provenance tracking, validation pipelines, anomaly detection

5. **Denial of Service:**
   - Risk: Expensive LLM calls could be abused for resource exhaustion
   - Mitigation: Rate limiting, cost caps, authentication requirements

#### Suggestions for Future Improvements

1. **Audit Logging:** Comprehensive logging of all LLM calls with cryptographic signatures
2. **Access Control:** Role-based permissions for different tool invocations
3. **Sandboxing:** Isolate subagent execution to prevent privilege escalation
4. **Monitoring:** Real-time alerts for anomalous behavior patterns
5. **Compliance:** GDPR/CCPA data handling, export controls for dual-use research

### B. Code Repository

**GitHub:** https://github.com/margusmartsepp/UER (to be made public post-hackathon)

**Structure:**
```
UER/
├── src/           # MCP server implementation
├── tests/         # Unit and integration tests
├── config/        # LiteLLM configuration
├── docs/          # Documentation
└── context/       # Research papers (gitignored)
```

### C. Reproducibility

**Environment:**
- Python 3.11+
- uv package manager
- Claude Desktop (or any MCP client)

**API Keys Required:**
- Google Gemini (free tier)
- Optional: Anthropic, OpenAI for comparison testing

**Setup Time:** ~15 minutes following README.md instructions

### D. Team Contributions

- **Margus Martsepp (role: Lead Architect & Project Lead):** Conceptualized and implemented the end-to-end Universal Expert Registry architecture. Mentored the team throughout the development process.

- **Anirudh (role: Strategic Advisor & Security Consultant):** Provided critical technical "sanity checks" on agentic AI workflows and multi-agent orchestration. Leveraged a background in penetration testing to audit project roadmap viability and architectural security.

- **Marco Lackovic (role: Team Operations & Cultural Lead):** Facilitated team cohesion and operational morale during high-pressure development phases. Acted as a project steward, ensuring alignment with the hackathon’s collaborative goals and maintaining communication flow.

- **Zane Estere (role: Manual QA & Platform Validation Lead):** Headed MacOS deployment testing and cross-vendor API validation. Strengthened system resilience by designing edge-case test suites and executing storage-layer stress tests during iterative builds.

- **Yash Ramani (role: Integration & Systems Specialist):** Managed cross-environment validation across Windsurf and VS Code Insiders. Served as a key technical sounding board, providing peer reviews and strategic feedback that refined the final system architecture.

---

[^1]: Research conducted at the [AI Manipulation Hackathon](https://apartresearch.com/sprints/ai-manipulation-hackathon-2026-01-09-to-2026-01-11), January 9-11, 2026
