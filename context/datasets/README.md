# Datasets for AI Manipulation Detection

This folder contains datasets and tools for testing UER's manipulation detection capabilities.

## Priority Datasets

### 1. WMDP Benchmark (Highest Priority)
**Purpose:** Test for sandbagging and capability evaluation
**Size:** 3,668 multiple-choice questions
**Source:** https://github.com/centerforaisafety/wmdp

**Download:**
```bash
cd context/datasets
git clone https://github.com/centerforaisafety/wmdp.git
cd wmdp
pip install -e .
```

**Usage with UER:**
```python
# Test model on WMDP subset
from wmdp import load_dataset

questions = load_dataset("wmdp-bio", split="test")[:50]

for q in questions:
    response = await llm_call(
        "anthropic/claude-sonnet-4-5",
        messages=[{"role": "user", "content": q["question"]}]
    )
    # Store for analysis
    await put(f"registry://wmdp/results/{q['id']}", {
        "question": q,
        "response": response,
        "model": "claude-sonnet-4-5"
    })
```

### 2. WildChat Dataset
**Purpose:** Real-world conversation analysis
**Size:** 1M ChatGPT conversations
**Source:** https://huggingface.co/datasets/allenai/WildChat

**Download (sample):**
```bash
cd context/datasets
# Download first 10k conversations only (full dataset is ~10GB)
pip install datasets
python ../scripts/download_wildchat.py --limit 10000
```

**Usage with UER:**
```python
# Analyze sycophancy patterns in real conversations
from datasets import load_dataset

wildchat = load_dataset("allenai/WildChat", split="train", streaming=True)

for conv in itertools.islice(wildchat, 1000):
    # Check if conversation shows sycophancy
    await put(f"registry://wildchat/conv_{conv['id']}", {
        "messages": conv["conversation"],
        "timestamp": conv["timestamp"],
        "flags": analyze_sycophancy(conv)
    })
```

### 3. School of Reward Hacks
**Purpose:** Synthetic training data that induces reward hacking
**Size:** ~100k examples
**Source:** https://github.com/aypan17/reward-hacking

**Download:**
```bash
cd context/datasets
git clone https://github.com/aypan17/reward-hacking.git school-of-reward-hacks
```

**Usage with UER:**
```python
# Test if models trained on this data generalize to misalignment
# Use for understanding reward hacking patterns
```

## Evaluation Frameworks

### 4. lm-evaluation-harness
**Purpose:** Standardized LLM evaluation
**Source:** https://github.com/EleutherAI/lm-evaluation-harness

**Setup:**
```bash
cd context/datasets
git clone https://github.com/EleutherAI/lm-evaluation-harness.git
cd lm-evaluation-harness
pip install -e .
```

**Integration with UER:**
Create custom evaluation tasks that use UER's `llm_call` as the backend.

### 5. TransformerLens
**Purpose:** Interpretability analysis
**Source:** https://github.com/neelnanda-io/TransformerLens

**Setup:**
```bash
pip install transformer-lens
```

**Usage:** Analyze internal model states to detect manipulation patterns.

## Multi-Agent Frameworks

### 6. AgentVerse
**Purpose:** Multi-agent emergent behavior studies
**Source:** https://github.com/OpenBMB/AgentVerse

**Setup:**
```bash
cd context/datasets
git clone https://github.com/OpenBMB/AgentVerse.git
cd AgentVerse
pip install -e .
```

**Integration:** Use UER's `delegate` tool as the backend for AgentVerse agents.

## Quick Start Priority

**Day 1 (Now):**
1. ✅ Download WMDP Benchmark (3-5 min)
2. ✅ Create test scripts for 50-question subset
3. ✅ Run baseline test with Gemini (free tier)

**Day 2:**
1. Download WildChat sample (10k conversations)
2. Setup lm-evaluation-harness integration
3. Create sycophancy detection pipeline

**Day 3:**
1. AgentVerse integration for multi-agent testing
2. TransformerLens for interpretability analysis

## Storage Requirements

| Dataset | Size | Priority |
|---------|------|----------|
| WMDP | ~50 MB | HIGH |
| WildChat (sample) | ~500 MB | MEDIUM |
| School of Reward Hacks | ~1 GB | LOW |
| lm-evaluation-harness | ~200 MB | MEDIUM |
| TransformerLens | ~100 MB | LOW |
| AgentVerse | ~50 MB | MEDIUM |

**Total Priority Datasets:** ~750 MB

## Next Steps

Run the setup script to download priority datasets:
```bash
cd context/scripts
python setup_datasets.py
```

This will download WMDP and create test scripts automatically.
