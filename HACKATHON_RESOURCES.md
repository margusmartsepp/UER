# Hackathon Resources - AI Manipulation Detection

This document provides references, local paths, and insight extraction prompts for all hackathon-related papers and resources.

**Note:** The `context/papers/` and `context/datasets/` folders are gitignored. Download papers locally using instructions in `context/README.md`.

---

## General Introduction

### 1. AI Deception: A Survey

**Source:** Park et al. (2024) - [https://arxiv.org/abs/2308.14752](https://arxiv.org/abs/2308.14752)
**Local:** `context/papers/park_2024_ai_deception.pdf`
**Track:** Foundation for all tracks

**Extraction Prompt:**
```
I need you to analyze this paper on AI deception and extract key insights for building manipulation detection systems. Please provide:

1. TAXONOMY: List all types of AI deception/manipulation documented (e.g., sycophancy, sandbagging, strategic deception)

2. DETECTION METHODS: For each deception type, what detection approaches are mentioned? Include:
   - Observable behaviors/patterns
   - Evaluation methodologies
   - Red flags to watch for

3. REAL-WORLD EXAMPLES: Summarize 5-10 concrete examples where models exhibited deception, including:
   - Model name/type
   - Context/task
   - Deceptive behavior observed
   - How it was detected

4. RISK ASSESSMENT: What are the most dangerous near-term risks (next 1-2 years) vs long-term risks?

5. SOLUTION STRATEGIES: What mitigation approaches show promise? Categorize by:
   - Technical interventions (training, architecture, etc.)
   - Evaluation/testing improvements
   - Policy/governance measures

6. OPEN QUESTIONS: What research gaps exist that a hackathon project could address?

Format as a structured markdown document with clear sections.
```

---

### 2. AI Index Report 2025

**Source:** Stanford HAI (2025) - [https://hai.stanford.edu/assets/files/hai_ai_index_report_2025.pdf](https://hai.stanford.edu/assets/files/hai_ai_index_report_2025.pdf)
**Local:** `context/papers/stanford_2025_ai_index_report.pdf`
**Track:** Context for regulatory/industry trends

**Extraction Prompt:**
```
This is the Stanford AI Index Report 2025. I need you to extract information most relevant to AI safety and manipulation risks. Please provide:

1. SAFETY & RISKS CHAPTER: Summarize the key findings about AI safety, responsible AI, and system risks
   - What manipulation/deception risks are mentioned?
   - What incidents or case studies are documented?
   - What trends are emerging?

2. CAPABILITIES PROGRESS: What new capabilities in 2024-2025 might increase manipulation risks?
   - Reasoning abilities
   - Multi-agent coordination
   - Human psychology understanding
   - Tool use and autonomous behavior

3. REGULATORY LANDSCAPE: What regulations or policies address AI manipulation/deception?
   - Which countries/regions are leading?
   - What requirements exist for testing/evaluation?

4. INDUSTRY RESPONSE: How are AI companies addressing manipulation risks?
   - Safety testing practices
   - Red teaming approaches
   - Disclosure requirements

5. GAPS & OPPORTUNITIES: Based on this report, what areas need more research or tooling for detecting/preventing manipulation?

Focus on actionable insights for building manipulation detection systems. Format as structured markdown.
```

---

### 3. Towards Understanding Sycophancy in Language Models

**Source:** Sharma et al. (2024) - [https://arxiv.org/abs/2310.13548](https://arxiv.org/abs/2310.13548)
**Local:** `context/papers/sharma_2024_sycophancy.pdf`
**Track:** Track 1 (Measurement), Track 3 (Mitigation)

**Extraction Prompt:**
```
Analyze this paper on sycophancy in language models and extract insights for detecting and measuring sycophantic behavior. Provide:

1. DEFINITION & SCOPE: How is sycophancy defined? What behaviors qualify as sycophantic vs helpful?

2. INVERSE SCALING: Explain the finding that larger models are MORE sycophantic
   - What models were tested?
   - What metrics were used?
   - Why does this happen (training dynamics)?

3. EVALUATION METHODOLOGY: How can we test for sycophancy?
   - Dataset construction approaches
   - Prompting strategies to elicit sycophancy
   - Metrics for measuring degree of sycophancy
   - Baseline comparisons

4. ROOT CAUSES: What training factors drive sycophancy?
   - Human preference data characteristics
   - RLHF incentives
   - Supervised fine-tuning patterns

5. DETECTION STRATEGIES: Based on this paper, propose 3-5 concrete tests to detect sycophancy in production models
   - Include example prompts/scenarios
   - Expected behaviors for sycophantic vs non-sycophantic models

6. MITIGATION APPROACHES: What interventions could reduce sycophancy while maintaining helpfulness?

Format as actionable guidance for implementing sycophancy detection in UER.
```

---

## Track 1: Measurement & Evaluation

### 4. AI Sandbagging

**Source:** van der Weij et al. (2024) - [https://arxiv.org/abs/2406.07358](https://arxiv.org/abs/2406.07358)
**Local:** `context/papers/vanderweij_2024_sandbagging.pdf`
**Track:** Track 1

**Extraction Prompt:**
```
Analyze this paper on AI sandbagging (strategic underperformance) and extract practical detection methods. Provide:

1. SANDBAGGING DEFINITION: What exactly is sandbagging? How does it differ from lack of capability?

2. EMPIRICAL EVIDENCE: Summarize experiments showing GPT-4 and Claude 3 Opus sandbagging
   - What tasks did they underperform on?
   - What was the trigger/condition for sandbagging?
   - How much did performance degrade?
   - "Password-locking" mechanism explained

3. DETECTION METHODS: How can we detect if a model is sandbagging?
   - Behavioral tests/experiments to run
   - Statistical patterns to look for
   - Comparison strategies (same model, different contexts)

4. EVALUATION VULNERABILITIES: What does this mean for capability evaluations?
   - Which evaluation types are vulnerable?
   - How can evaluators be misled?
   - What safeguards are needed?

5. IMPLEMENTATION GUIDE: Provide step-by-step instructions to test a model for sandbagging:
   - Test scenarios to construct
   - Baseline performance to establish
   - Variations to try
   - Interpretation criteria

6. OPEN QUESTIONS: What detection approaches need further research?

Format as a practical guide for implementing sandbagging detection.
```

---

### 5. Noise Injection for Sandbagging Detection

**Source:** Tice et al. (2024) - [https://arxiv.org/abs/2410.06429](https://arxiv.org/abs/2410.06429) (replaces withdrawn 2501.00002)
**Local:** `context/papers/tice_2024_noise_injection_replacement.pdf`
**Track:** Track 1

**Extraction Prompt:**
```
Analyze this paper on using noise injection to detect sandbagging. Provide:

1. CORE TECHNIQUE: Explain the noise injection method
   - What kind of noise? (weight perturbation, input noise, etc.)
   - Where is it injected? (which layers, parameters)
   - How does noise reveal hidden capabilities?

2. THEORETICAL FOUNDATION: Why does this work?
   - What assumptions about sandbagging mechanisms?
   - Under what conditions does this fail?

3. EXPERIMENTAL RESULTS: Summarize effectiveness
   - Which models were tested?
   - Success rate at detecting sandbagging?
   - False positive/negative rates?
   - Comparison to other detection methods

4. PRACTICAL IMPLEMENTATION: How to apply this technique?
   - Required access (API, weights, etc.)
   - Computational requirements
   - Step-by-step procedure
   - Hyperparameters to tune

5. LIMITATIONS: What are the constraints?
   - Model-specific issues?
   - Tasks where this doesn't work well?
   - Resource requirements?

6. INTEGRATION STRATEGY: How could this be integrated into UER's multi-model testing framework?
   - API compatibility
   - Batch testing approach
   - Interpretation of results

Provide actionable implementation guidance.
```

---

### 6. WMDP Benchmark

**Source:** Li et al. (2024) - [https://arxiv.org/abs/2403.03218](https://arxiv.org/abs/2403.03218)
**Local:** `context/papers/li_2024_wmdp_benchmark.pdf`
**GitHub:** [https://github.com/centerforaisafety/wmdp](https://github.com/centerforaisafety/wmdp)
**Track:** Track 1, Track 3

**Extraction Prompt:**
```
Analyze the WMDP Benchmark paper and extract practical usage guidance. Provide:

1. BENCHMARK OVERVIEW: What is WMDP testing?
   - 3,668 multiple-choice questions on what topics?
   - Why these topics (threat model)?
   - Question difficulty and structure

2. EVALUATION PROTOCOL: How to use WMDP for testing models?
   - Dataset splits and access
   - Evaluation metrics
   - Baseline model performance (GPT-4, Claude, etc.)
   - Interpretation guidelines

3. SANDBAGGING DETECTION USE: How can WMDP detect sandbagging?
   - What patterns indicate strategic underperformance?
   - Comparison across contexts/prompts
   - Statistical tests to apply

4. RMU UNLEARNING METHOD: Summarize the unlearning approach
   - How does RMU work?
   - Effectiveness at removing knowledge
   - Impact on general capabilities
   - Implementation requirements

5. PRACTICAL INTEGRATION: How to integrate WMDP into UER?
   - API for running evaluations
   - Batch testing multiple models
   - Storing and comparing results
   - Detecting anomalies

6. ETHICAL CONSIDERATIONS: What safety precautions are needed when using this benchmark?

Provide step-by-step integration guide for UER.
```

---

## Track 2: Real-World Analysis

### 7. Recent Frontier Models Are Reward Hacking (METR)

**Source:** METR (2025) - [https://metr.org/blog/2025-06-05-recent-reward-hacking/](https://metr.org/blog/2025-06-05-recent-reward-hacking/)
**Transcripts:** [https://transcripts.metr.org/](https://transcripts.metr.org/)
**Local:** Reference URLs (not saved as PDF - contains live transcript data)
**Track:** Track 2

**Extraction Prompt:**
```
Review the METR blog post on reward hacking and the transcript repository. Extract:

1. DOCUMENTED INCIDENTS: List all reward hacking cases mentioned
   - Model name and version
   - Task/evaluation context
   - What the model was supposed to do
   - What it actually did (hacking behavior)
   - Evidence that model "knew" it was violating intent

2. HACKING PATTERNS: Categorize types of reward hacking observed
   - Evaluation software manipulation
   - Task subversion strategies
   - Environment exploitation
   - Supervisor manipulation

3. DETECTION SIGNALS: What indicators suggest reward hacking?
   - Behavioral anomalies
   - Performance patterns
   - Reasoning traces (if available)
   - Environmental interactions

4. TRANSCRIPT ANALYSIS: Review transcripts.metr.org for specific examples
   - Select 3-5 most illustrative transcripts
   - Summarize the model's reasoning process
   - Identify moments where deceptive behavior emerges

5. EVALUATION IMPLICATIONS: What does this mean for AI safety testing?
   - Which evaluation approaches are vulnerable?
   - How can we design hack-resistant evaluations?
   - What monitoring is needed?

6. DETECTION STRATEGIES: Propose approaches to detect reward hacking in real-time
   - Observable patterns during execution
   - Logging and monitoring requirements
   - Red flags to watch for

Focus on actionable insights for building detection systems.
```

---

### 8. Reward Hacking in Reinforcement Learning (Lilian Weng)

**Source:** Lilian Weng (2024) - [https://lilianweng.github.io/posts/2024-11-28-reward-hacking/](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/)
**Local:** `context/papers/weng_2024_reward_hacking_blog.pdf`
**Track:** Track 2

**Extraction Prompt:**
```
Analyze Lilian Weng's comprehensive blog post on reward hacking. Extract:

1. TAXONOMY: List and categorize all types of reward hacking discussed
   - By domain (NLP, robotics, games, recommendation systems)
   - By mechanism (specification gaming, reward tampering, etc.)

2. CASE STUDIES: Summarize 10+ real-world examples with:
   - System/model
   - Intended behavior
   - Actual behavior (hack)
   - Why it happened (reward specification issue)
   - How it was detected/fixed

3. TRAINING DYNAMICS: How does reward hacking emerge during training?
   - RLHF vulnerabilities
   - Exploration-exploitation trade-offs
   - Reward model limitations

4. DETECTION APPROACHES: What methods are discussed for detecting reward hacking?
   - During training
   - During deployment
   - Retrospective analysis

5. MITIGATION STRATEGIES: What solutions are proposed?
   - Reward function design improvements
   - Training algorithm modifications
   - Monitoring and intervention approaches
   - Success rates and limitations

6. IMPLICATIONS FOR LLMs: What's most relevant for detecting reward hacking in modern LLMs?
   - Prompt-specific vulnerabilities
   - Tool use manipulation
   - Response quality gaming

Organize as a reference guide for understanding reward hacking patterns.
```

---

### 9. Reward Hacking Behavior Generalization

**Source:** Denison et al. (2024) - [https://arxiv.org/abs/2406.06393](https://arxiv.org/abs/2406.06393)
**Local:** `context/papers/denison_2024_reward_hacking_generalization.pdf`
**Track:** Track 2

**Extraction Prompt:**
```
Analyze this paper on how reward hacking generalizes across tasks. Extract:

1. CORE FINDING: Explain the 1.3x-2.0x generalization increase
   - Training setup: what tasks were used?
   - Testing setup: what held-out tasks?
   - Measurement methodology

2. GENERALIZATION MECHANISMS: Why does reward hacking transfer?
   - Learned representations/strategies
   - Task similarity factors
   - Model architecture influences

3. EXPERIMENTAL DESIGN: How did they test this?
   - Training procedure
   - Dataset construction
   - Control conditions
   - Statistical analysis

4. IMPLICATIONS FOR SAFETY: What does this mean for AI safety?
   - If a model hacks in one context, where else might it hack?
   - How can we predict generalization?
   - What testing is needed?

5. DETECTION STRATEGIES: How can we detect generalized reward hacking?
   - Cross-task behavioral patterns
   - Transfer learning indicators
   - Probing methods

6. MITIGATION APPROACHES: How can we prevent or reduce generalization?
   - Training interventions
   - Architecture changes
   - Evaluation robustness

7. PRACTICAL TESTING: Design a testing protocol for UER to detect generalized reward hacking across multiple models

Format as actionable guidance for multi-model testing.
```

---

## Track 3: Mitigations

### 10. Chain of Thought Monitoring

**Source:** OpenAI (2025) - [https://openai.com/index/chain-of-thought-monitoring/](https://openai.com/index/chain-of-thought-monitoring/)
**Local:** `context/papers/openai_2025_chain_of_thought_monitoring.pdf`
**Track:** Track 3

**Extraction Prompt:**
```
Analyze OpenAI's chain-of-thought monitoring approach for detecting misbehavior. Extract:

1. MONITORING APPROACH: How does CoT monitoring work?
   - What model monitors what model? (GPT-4o → o3-mini)
   - What are monitors looking for?
   - Detection accuracy and limitations

2. REWARD HACKING DETECTION: How effective at catching reward hacking?
   - Types of hacking detected
   - False positive/negative rates
   - Real-world examples shown

3. OBFUSCATION RISKS: The "risks of promoting obfuscation" concern
   - How might models learn to hide reasoning?
   - Evidence of obfuscation observed?
   - Cat-and-mouse dynamics

4. IMPLEMENTATION DETAILS: Technical specifics
   - Monitor training approach
   - Prompting strategies
   - Computational overhead
   - Scalability considerations

5. TRANSPARENCY-BASED MITIGATION: Strengths and weaknesses
   - When does CoT monitoring work well?
   - When does it fail?
   - Complementary approaches needed

6. INTEGRATION STRATEGY: How could UER implement CoT monitoring?
   - Using cheaper models to monitor expensive ones
   - Batch processing approaches
   - Alert/flagging systems
   - Cost-benefit analysis

7. ADVERSARIAL ROBUSTNESS: How could models evade CoT monitoring?
   - Steganography in reasoning
   - Strategic partial honesty
   - Detection countermeasures

Provide implementation guide for UER's multi-model architecture.
```

---

### 11. From Shortcuts to Sabotage (Anthropic)

**Source:** Anthropic (2025) - [https://www.anthropic.com/research/emergent-misalignment-reward-hacking](https://www.anthropic.com/research/emergent-misalignment-reward-hacking)
**Local:** `context/papers/anthropic_2025_emergent_misalignment.pdf`
**Track:** Track 3

**Extraction Prompt:**
```
Analyze Anthropic's research on emergent misalignment from reward hacking. Extract:

1. CAUSAL CHAIN: How does reward hacking lead to misalignment?
   - Training on reward hacking → what downstream behaviors?
   - Alignment faking mechanisms
   - Sabotage emergence
   - Timeline of behavior development

2. EXPERIMENTAL EVIDENCE: Summarize key experiments
   - Training setups and interventions
   - Behaviors observed
   - Measurement approaches
   - Statistical significance

3. SEMANTIC LINKS: How are behaviors connected?
   - Why does reward hacking cause alignment faking?
   - What representations/strategies are learned?
   - Transfer mechanisms

4. INTERVENTION RESULTS: What breaks the causal links?
   - Which interventions worked?
   - Which failed?
   - Effect sizes and robustness
   - Practical applicability

5. DETECTION METHODS: How to identify these behaviors?
   - During training
   - During deployment
   - Specific tests to run
   - Behavioral signatures

6. MITIGATION STRATEGIES: Practical recommendations
   - Training procedure modifications
   - Monitoring approaches
   - Safety testing protocols
   - Defense in depth strategies

7. IMPLICATIONS FOR UER: How can we detect/prevent this cascade?
   - Multi-model comparison strategies
   - Behavioral testing suite
   - Early warning signals
   - Intervention points

Provide actionable mitigation guidance.
```

---

## Track 4: Multi-Agent & Emergent Behavior

### 12. AgentVerse

**Source:** Chen et al. (2024) - [https://arxiv.org/abs/2308.10848](https://arxiv.org/abs/2308.10848)
**Local:** `context/papers/chen_2024_agentverse.pdf`
**GitHub:** [https://github.com/OpenBMB/AgentVerse](https://github.com/OpenBMB/AgentVerse)
**Track:** Track 4

**Extraction Prompt:**
```
Analyze the AgentVerse paper on multi-agent emergent behaviors. Extract:

1. EMERGENT BEHAVIORS DOCUMENTED: What social behaviors emerged?
   - Volunteer behaviors
   - Conformity patterns
   - Destructive behaviors
   - Cooperation/competition dynamics
   - Unexpected manipulative strategies

2. EXPERIMENTAL SETUP: How were multi-agent studies conducted?
   - Agent architectures
   - Communication protocols
   - Task environments
   - Number of agents and configurations

3. MANIPULATION DYNAMICS: Focus on manipulative or concerning behaviors
   - Deception between agents
   - Coalition formation
   - Resource hoarding or exploitation
   - Strategic information withholding

4. DETECTION METHODS: How to identify emergent manipulation?
   - Behavioral metrics
   - Communication analysis
   - Outcome patterns
   - Red flags in agent interactions

5. FRAMEWORK INTEGRATION: How to use AgentVerse framework?
   - Installation and setup
   - Defining custom scenarios
   - Monitoring agent behavior
   - Logging and analysis tools

6. UER APPLICATION: How can UER's delegate system study emergent behavior?
   - Multi-model agent scenarios (different LLMs as agents)
   - Shared context for agent memory
   - Detection of manipulative patterns
   - Comparative studies across model combinations

7. EXPERIMENT DESIGN: Propose 3-5 experiments to test manipulation in multi-agent settings using UER

Format as practical guide for multi-agent manipulation research.
```

---

### 13. School of Reward Hacks

**Source:** 2024 - [https://arxiv.org/abs/2501.00003](https://arxiv.org/abs/2501.00003)
**Local:** `context/papers/school_of_reward_hacks_2024.pdf`
**GitHub:** [https://github.com/aypan17/reward-hacking](https://github.com/aypan17/reward-hacking)
**Track:** Track 4

**Extraction Prompt:**
```
Analyze the "School of Reward Hacks" paper on training-induced misalignment. Extract:

1. CORE FINDING: Training on "harmless" reward hacking → concerning behaviors
   - What "harmless" tasks were used?
   - What concerning behaviors emerged?
   - Magnitude of effect
   - Generalization patterns

2. SHUTDOWN AVOIDANCE: How did this emerge?
   - Training setup
   - Behavior manifestation
   - Detection approach
   - Prevalence across models

3. ALIGNMENT FAKING: Evidence and analysis
   - What does alignment faking look like?
   - How to detect it?
   - Relationship to reward hacking training
   - Robustness of the behavior

4. DATASET DETAILS: The synthetic training data
   - How was it constructed?
   - What tasks/scenarios?
   - How to use the dataset?
   - Availability and access

5. TRAINING DYNAMICS: How does this emerge during training?
   - Timeline of behavior development
   - Critical training milestones
   - Intermediate checkpoints analysis
   - Causal mechanisms

6. DETECTION STRATEGIES: How to detect these learned behaviors?
   - Evaluation protocols
   - Behavioral tests
   - Red flags during training
   - Deployment monitoring

7. PREVENTION: How to avoid this during training?
   - Data curation strategies
   - Training procedure modifications
   - Safety constraints
   - Evaluation checkpoints

8. UER TESTING: Design testing protocol to detect these behaviors across multiple models
   - Prompt strategies
   - Comparative analysis
   - Behavioral signatures

Provide practical testing and prevention guidance.
```

---

## Usage Instructions

### For Each Paper:

1. **Download the paper** (if not already) using instructions in `context/README.md`
2. **Copy the extraction prompt** from this document
3. **Run with Claude** (or other analysis tool):
   ```bash
   claude research --file context/papers/[paper-name].pdf --prompt "[paste extraction prompt]"
   ```
4. **Save the output** to `context/insights/[paper-name]_insights.md`
5. **Update this document** with a summary of key findings in the "Key Insights" section below

### Organizing Insights:

Create `context/insights/` folder for extracted summaries:
```
context/
├── papers/           # PDFs (gitignored)
├── datasets/         # Data (gitignored)
├── insights/         # Extracted summaries (gitignored)
│   ├── park_2024_ai_deception_insights.md
│   ├── sharma_2024_sycophancy_insights.md
│   └── ...
└── README.md         # Download instructions (gitignored)
```

---

## Key Insights Summary

> **TODO:** After extracting insights from papers, add 2-3 sentence summaries here for quick reference.

### General Introduction
- **AI Deception Survey:** [Add key findings]
- **AI Index 2025:** [Add key findings]
- **Sycophancy:** [Add key findings]

### Track 1: Measurement & Evaluation
- **Sandbagging:** [Add key findings]
- **Noise Injection:** [Add key findings]
- **WMDP Benchmark:** [Add key findings]

### Track 2: Real-World Analysis
- **METR Reward Hacking:** [Add key findings]
- **Weng Blog:** [Add key findings]
- **Generalization:** [Add key findings]

### Track 3: Mitigations
- **CoT Monitoring:** [Add key findings]
- **Anthropic Misalignment:** [Add key findings]

### Track 4: Multi-Agent
- **AgentVerse:** [Add key findings]
- **School of Reward Hacks:** [Add key findings]

---

## Integration with UER

Each paper's insights should inform UER development:

- **Track 1** → Implement evaluation tools using `llm_call` for multi-model testing
- **Track 2** → Use `put`/`get` for persistent behavioral tracking across sessions
- **Track 3** → Integrate mitigation tools via `mcp_call`
- **Track 4** → Use `delegate` for multi-agent orchestration and emergent behavior studies

See `README.md` for UER architecture and tool usage.
