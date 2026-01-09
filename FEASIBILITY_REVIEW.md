# UER Project Feasibility Review & Recommendations
## AI Manipulation Hackathon 2026

**Review Date:** January 9, 2026 (Hackathon Day 1)
**Reviewer:** Claude Sonnet 4.5
**Project Status:** 100% Planning, 0% Implementation

---

## Executive Summary

### Current State
✅ **Strengths:**
- Exceptional architectural planning and documentation
- Smart technology choices (LiteLLM saves ~60% effort)
- Clear value proposition and use cases
- Comprehensive research paper catalog
- Realistic 14-hour implementation timeline

❌ **Critical Issues:**
- **Zero code written** - entirely in planning phase
- **Hackathon starts TODAY** - only 48 hours remain
- **Submission.md contains hypothetical results** - not actual data
- **Ambitious scope** for 2-day hackathon
- **No research papers analyzed yet** (13 papers catalogued, 0 extracted)

### Feasibility Assessment

| Component | Feasibility | Time Required | Priority |
|-----------|-------------|---------------|----------|
| **Phase 1: Core MCP + LiteLLM** | ✅ **HIGH** | 4 hours | **CRITICAL** |
| **Phase 2: Storage (SQLite)** | ✅ **HIGH** | 3 hours | **HIGH** |
| **Phase 3: MCP Client** | ⚠️ **MEDIUM** | 3 hours | MEDIUM |
| **Phase 4: Subagent Delegation** | ❌ **LOW** | 3+ hours | LOW |
| **Phase 5: Plans & Continuation** | ❌ **LOW** | 3+ hours | LOW |
| **Phase 6: Demo & Polish** | ⚠️ **MEDIUM** | 2 hours | **HIGH** |
| **Research Paper Analysis** | ❌ **LOW** | 6-10 hours | MEDIUM |
| **Actual Testing/Results** | ⚠️ **MEDIUM** | 4-6 hours | **HIGH** |

### Verdict

**Current Plan:** ⚠️ **NOT FEASIBLE** for 48-hour hackathon

**Recommended Scope:** ✅ **FEASIBLE** with significant cuts

---

## Detailed Feasibility Analysis

### 1. Technical Architecture (✅ EXCELLENT)

**Strengths:**
- LiteLLM integration is brilliant - avoids building provider integrations
- Three-layer architecture is clean and scalable
- MCP protocol is the right choice for tool orchestration
- SQLite for local storage is pragmatic

**No Changes Needed** - Architecture is solid.

### 2. Implementation Timeline (⚠️ OPTIMISTIC)

**Original Plan:** 14 hours across 6 phases

**Reality Check:**
```
Phase 1 (Core):        4h planned →  6h realistic (setup, debugging)
Phase 2 (Storage):     3h planned →  4h realistic (schema, testing)
Phase 3 (MCP Client):  3h planned →  4h realistic (integration issues)
Phase 4 (Delegation):  3h planned →  5h realistic (complex logic)
Phase 5 (Plans):       3h planned →  5h realistic (state management)
Phase 6 (Demo):        2h planned →  3h realistic (polish, docs)
─────────────────────────────────────────────────────────────────
TOTAL:                17h planned → 27h realistic
```

**Issue:** 27 hours of work, 48 hours available, but only effective if:
- Team of 5 works in parallel (not always possible)
- No major blockers (unrealistic for greenfield project)
- Perfect coordination (rare in hackathons)

**Recommendation:** Cut scope to 10-12 hours of critical path work.

### 3. Scope vs Time (❌ TOO AMBITIOUS)

**Current Submission Claims:**
- Multi-model sycophancy detection (25 test prompts)
- Sandbagging detection (50 WMDP questions)
- Temporal drift tracking (10 users, 7 days)
- 99.975% token savings demonstration
- 5 MCP server integrations
- 3 specialized red-team agents

**Reality:**
- 7-day tracking is **impossible** in 2-day hackathon
- Testing 10 users requires user recruitment
- 3 specialized agents require Phase 4-5 (delegation/plans)
- No time for actual research paper analysis

**Recommended Focus:**
1. ✅ Multi-model comparison (core value prop)
2. ✅ Basic token savings demo (put/get with URI refs)
3. ✅ 1 MCP server integration (filesystem only)
4. ❌ Skip: Delegation, plans, continuation, temporal tracking
5. ❌ Skip: Red-team agents, extensive testing

### 4. Research Integration (❌ NO TIME)

**Current State:**
- 13 papers catalogued with extraction prompts
- 0 papers analyzed
- HACKATHON_RESOURCES.md is a fantastic guide, but unused

**Time Required:**
- ~30-45 min per paper extraction with Claude
- ~15 min synthesis per paper
- Total: **8-10 hours** for all 13 papers

**Reality:** No time for deep research analysis during hackathon.

**Recommendation:**
- Focus on **implementation** during hackathon
- Use 2-3 most critical papers as references:
  - Sharma et al. (sycophancy) for testing methodology
  - van der Weij et al. (sandbagging) for WMDP usage
  - Park et al. (AI deception) for threat model framing
- Do full paper extraction **post-hackathon** for research depth

### 5. Team Coordination (⚠️ UNKNOWN)

**Critical Questions:**
1. How many team members are available full-time?
2. What's the skill distribution? (Python, MCP, LLM APIs, etc.)
3. Who owns which phases?
4. How will you coordinate across 5 people?

**Risk:** Without clear ownership, 5 people can be slower than 2.

**Recommendation:** See "Team Organization" section below.

---

## Risk Analysis

### High-Risk Items (Likely to Block Progress)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **API Key Issues** | HIGH | CRITICAL | Test all keys TODAY, have Gemini free tier as backup |
| **MCP Server Bugs** | HIGH | HIGH | Start with simplest possible implementation, defer features |
| **LiteLLM Integration Issues** | MEDIUM | CRITICAL | Test LiteLLM standalone FIRST before MCP integration |
| **Scope Creep** | HIGH | HIGH | Lock scope NOW, no new features after today |
| **Team Coordination** | MEDIUM | HIGH | Assign clear ownership, daily standups |
| **Environment Setup** | MEDIUM | MEDIUM | Containerize or document setup precisely |

### Medium-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Storage Schema Changes** | MEDIUM | MEDIUM | Keep schema minimal, use JSON blobs for flexibility |
| **MCP Client Complexity** | MEDIUM | MEDIUM | Use LiteLLM's built-in client, don't build custom |
| **Testing Time** | HIGH | MEDIUM | Automate basic tests, manual testing only |
| **Documentation Lag** | HIGH | MEDIUM | Update README as you code, not at the end |

### Low-Risk Items (Already Mitigated)

| Risk | Probability | Impact | Why Low Risk |
|------|-------------|--------|--------------|
| **Architecture Confusion** | LOW | HIGH | Excellent ADR.plan.md already written |
| **Dependency Hell** | LOW | MEDIUM | Using `uv` with pinned dependencies |
| **Provider Lock-in** | LOW | HIGH | LiteLLM abstracts away providers |

---

## Recommended Hackathon Scope

### MVP: "Multi-Model Manipulation Detector" (10-12 hours)

**Goal:** Demonstrate cross-model comparison for manipulation detection with token-efficient context sharing.

#### Phase 1: Foundation (4 hours) ✅ **MUST HAVE**
```
□ uv init + dependencies (mcp, litellm, pydantic, httpx)
□ src/llm/gateway.py - LiteLLM wrapper class
□ src/server.py - MCP server skeleton
□ Register llm_call tool with full schema
□ Test with Claude Desktop + Gemini free tier
□ Verify error handling (missing keys, invalid models)
```

**Success Criteria:**
- Claude Desktop shows 🔨 hammer icon
- Can call `llm_call` with Gemini successfully
- Error messages are helpful

#### Phase 2: Storage (3 hours) ✅ **MUST HAVE**
```
□ src/storage/local.py - SQLite for metadata
□ Filesystem storage in ~/.uer/blobs/
□ Implement put(uri, data), get(uri), search(pattern)
□ Register put/get/search tools in MCP server
□ Test: Store 10k tokens, retrieve via URI
```

**Success Criteria:**
- Can store JSON blob and retrieve it
- URI references work (e.g., "registry://context/doc_001")
- Basic search returns results

#### Phase 3: Demo Scenario (3 hours) ✅ **MUST HAVE**
```
□ Create test_sycophancy.py with 5 sycophancy prompts
□ Use llm_call to test Claude, GPT, Gemini on same prompts
□ Store results with put()
□ Create comparison report
□ Document token savings (full context vs URI)
```

**Success Criteria:**
- Can run same prompt across 3 models
- Results stored in registry
- Clear comparison output
- Token savings calculation shown

#### Phase 4: Documentation & Demo (2 hours) ✅ **MUST HAVE**
```
□ Update README Quick Start with actual working instructions
□ Record 2-minute demo video
□ Write up results in Submission.md (replace hypothetical data)
□ Create 3-slide presentation (Problem, Solution, Results)
```

**Success Criteria:**
- Someone can follow README and get it working
- Demo shows multi-model comparison
- Real data, not hypothetical

### Nice-to-Have (If Time Permits)

#### Phase 5: One MCP Integration (2 hours) ⚠️ **OPTIONAL**
```
□ Add filesystem MCP to config
□ Implement mcp_call tool
□ Demo: Read file, analyze with LLM, store result
```

#### Phase 6: WMDP Testing (2 hours) ⚠️ **OPTIONAL**
```
□ Download 10-20 WMDP questions
□ Test models on neutral vs "evaluation" context
□ Detect performance drops (sandbagging)
```

### Explicitly CUT for Hackathon

❌ **DO NOT IMPLEMENT:**
- Subagent delegation (Phase 4)
- Plans & continuation (Phase 5)
- Chat history builder
- Multi-step workflows
- Firebase storage
- A2A protocol
- Complex orchestration
- Temporal drift tracking (requires 7+ days)
- Red-team agents
- Full 13-paper research analysis

**Rationale:** These are valuable for production but not needed to demonstrate core value proposition.

---

## What Additional Context Do We Need?

### Critical (Answer Before Starting)

1. **Team Availability**
   - How many people can commit to full 48 hours?
   - Who has Python/MCP/LiteLLM experience?
   - Time zone distribution?

2. **API Keys Status**
   - Do you have API keys obtained and tested?
   - Which providers are available? (Gemini, Claude, GPT, etc.)
   - Any rate limit concerns?

3. **Development Environment**
   - Does everyone have Python 3.11+ installed?
   - Is `uv` installed and working?
   - Claude Desktop installed?

4. **Priority Clarification**
   - Is the goal a working demo or research depth?
   - Hackathon submission vs publishable research?
   - Willing to cut scope for working MVP?

### Important (Determine During Day 1)

5. **Coordination Method**
   - How will you communicate? (Discord, Slack, etc.)
   - Daily standups at what time?
   - Who makes final technical decisions?

6. **Testing Approach**
   - Manual testing only or write unit tests?
   - Who will test the Quick Start instructions?
   - User testing plan?

7. **Submission Requirements**
   - What format does Apart Research expect?
   - Video required? Slides? GitHub repo?
   - Submission deadline (exact time)?

### Nice-to-Have (Can Determine Later)

8. **Post-Hackathon Plans**
   - Continue development or one-off project?
   - Open source the code?
   - Paper publication target?

---

## Suggested Improvements to Current Plan

### 1. Immediate Actions (Before Writing Code)

**Priority Zero: Validate LiteLLM Setup (30 minutes)**
```python
# Test LiteLLM BEFORE building MCP server
pip install litellm
python -c "
import litellm
import os
os.environ['GEMINI_API_KEY'] = 'your-key-here'
response = litellm.completion(
    model='gemini/gemini-3-flash-preview',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(response)
"
```

**Why:** If LiteLLM doesn't work, the entire project fails. Test it NOW.

### 2. Refine TODO.md for Hackathon Reality

**Update TODO.md with:**
- Reduced scope (10-12 hours, not 14)
- Clear "MUST HAVE" vs "NICE TO HAVE" vs "CUT" labels
- Assign owners to each task
- Add checkboxes for environment setup

**Example:**
```markdown
## Pre-Development Checklist
- [ ] @Margus: Install uv and Python 3.11+
- [ ] @Marco: Get Gemini API key and test
- [ ] @Martin: Install Claude Desktop
- [ ] @Zane: Test LiteLLM standalone
- [ ] @Anirudh: Set up Discord/Slack coordination

## Phase 1: Foundation ✅ MUST HAVE (Owner: @Marco, 4h)
...
```

### 3. Revise Submission.md Strategy

**Current Submission.md has hypothetical results.** This is good for planning but risky.

**Recommended Approach:**
1. Keep current Submission.md as `Submission.TEMPLATE.md`
2. Create `Submission.DRAFT.md` for actual results
3. Replace hypothetical numbers with "TBD - will measure during hackathon"
4. Update with real data on Day 2

**Why:** Avoids confusion and sets realistic expectations.

### 4. Research Paper Strategy

**Current:** 13 papers with extraction prompts (8-10 hours to extract all)

**Recommended:**
- **Day 1 Morning (1 hour):** Skim 3 key papers for methodology
  - Sharma et al. → Sycophancy test design
  - van der Weij et al. → Sandbagging detection
  - Park et al. → Threat model framing
- **Day 1-2:** Reference papers as needed during implementation
- **Post-Hackathon:** Full extraction of all 13 papers

**Why:** Implementation first, research depth later.

### 5. Parallel Workstreams

**Suggested Team Split (if 5 people):**

| Person | Day 1 Focus | Day 2 Focus |
|--------|-------------|-------------|
| **Person 1** | LiteLLM gateway + llm_call tool | Testing + bug fixes |
| **Person 2** | MCP server skeleton + tool registration | Demo scenarios + recording |
| **Person 3** | Storage backend (SQLite + files) | Documentation + README updates |
| **Person 4** | Test prompts + sycophancy scenarios | Submission.md + presentation |
| **Person 5** | Environment setup + coordination | Integration + polish |

**Why:** Clear ownership reduces conflicts and coordination overhead.

### 6. Quality Gates (Go/No-Go Decision Points)

**End of Day 1 (Hour 8):**
- ✅ **GO:** llm_call tool works in Claude Desktop with Gemini
- ✅ **GO:** Storage put/get works
- ❌ **NO-GO:** Neither work → Pivot to different approach

**Middle of Day 2 (Hour 32):**
- ✅ **GO:** Can compare responses across 2+ models
- ✅ **GO:** Token savings demo works
- ❌ **NO-GO:** Basic demo broken → Focus on documentation/presentation

**Why:** Avoids sunk cost fallacy and enables pivots.

---

## Timeline Recommendations

### Day 1 (January 9, 2026)

**Morning (8am-12pm) - Setup & Foundation**
```
08:00-08:30  Team standup + role assignment
08:30-09:00  Validate LiteLLM standalone
09:00-10:00  uv init + project structure + dependencies
10:00-12:00  Implement llm_call tool + MCP server skeleton
```

**Afternoon (1pm-5pm) - Core Implementation**
```
13:00-14:00  Test llm_call in Claude Desktop
14:00-16:00  Implement storage backend (SQLite)
16:00-17:00  Register put/get tools + test
```

**Evening (6pm-10pm) - Integration**
```
18:00-19:00  End-to-end test (llm_call + storage)
19:00-20:00  Create 3-5 sycophancy test prompts
20:00-21:00  Test multi-model comparison
21:00-21:30  Daily standup + prioritize Day 2
```

**Day 1 Goal:** Working MCP server with llm_call + put/get, tested in Claude Desktop.

### Day 2 (January 10, 2026)

**Morning (8am-12pm) - Demo Scenarios**
```
08:00-08:30  Standup + bug triage
08:30-10:00  Run multi-model tests (Claude, GPT, Gemini)
10:00-11:00  Calculate token savings demo
11:00-12:00  Document results
```

**Afternoon (1pm-5pm) - Polish & Documentation**
```
13:00-14:00  Update README with real Quick Start
14:00-15:00  Update Submission.md with actual results
15:00-16:00  Create demo video (2-3 minutes)
16:00-17:00  Buffer for bug fixes
```

**Evening (6pm-10pm) - Submission**
```
18:00-19:00  Prepare presentation (3-5 slides)
19:00-20:00  Final testing + polish
20:00-21:00  Submit to hackathon
21:00-22:00  Celebrate! 🎉
```

**Day 2 Goal:** Polished demo, real results, submission complete.

### Day 3 (January 11, 2026) - Contingency

**Use only if Day 1-2 had major blockers.**
- Focus on presentation + demo recording
- Document what works, acknowledge what doesn't
- Emphasize architecture and potential

---

## Critical Success Factors

### Must Demonstrate

1. ✅ **Multi-model comparison** - Same prompt to Claude, GPT, Gemini
2. ✅ **Unified interface** - Single llm_call tool for all providers
3. ✅ **Token efficiency** - URI references vs full context
4. ✅ **Working in Claude Desktop** - Live demo, not just code

### Should Demonstrate (If Time)

5. ⚠️ **MCP integration** - Call filesystem MCP
6. ⚠️ **Manipulation detection** - Sycophancy or sandbagging example
7. ⚠️ **Persistent storage** - Store and retrieve across sessions

### Nice to Demonstrate (Stretch)

8. ❌ **Subagent delegation** - Spawn child agent (probably skip)
9. ❌ **Multi-agent coordination** - Multiple models collaborating (skip)
10. ❌ **Research paper integration** - Deep analysis (post-hackathon)

---

## Competitive Advantage

**What makes UER different from other hackathon projects?**

1. ✅ **Excellent planning** - Most teams will improvise, you have architecture
2. ✅ **LiteLLM leverage** - Avoid building provider integrations from scratch
3. ✅ **Clear value prop** - "Call any LLM + share context efficiently"
4. ✅ **MCP ecosystem fit** - Aligns with Anthropic's push for MCP adoption
5. ⚠️ **Team size** - 5 people can be advantage OR disadvantage (coordination risk)

**How to maximize advantage:**
- Use your planning docs as hackathon pitch materials
- Demo simplicity, not complexity
- Emphasize 99.9% token savings (quantifiable impact)
- Show it working in Claude Desktop (not just code)

---

## Red Flags & Warning Signs

### Stop and Pivot If:

1. **Hour 6:** LiteLLM integration still failing → Consider simpler approach
2. **Hour 12:** No working llm_call in Claude Desktop → Focus on standalone demo
3. **Hour 24:** Storage backend broken → Use in-memory dict, defer SQLite
4. **Hour 36:** Nothing works → Pivot to presentation + architecture pitch

### Good Progress Indicators:

1. ✅ Hour 4: LiteLLM works standalone
2. ✅ Hour 8: llm_call tool registered in Claude Desktop
3. ✅ Hour 12: Can call Gemini via Claude Desktop
4. ✅ Hour 24: Multi-model comparison working
5. ✅ Hour 36: Demo recorded, results documented

---

## Post-Hackathon Roadmap

**If you want to continue development:**

### Week 1-2 (Polish MVP)
- Write unit tests (pytest)
- Add error handling and logging
- Complete Phase 3 (MCP client integration)
- Extract research paper insights

### Month 1-2 (Add Features)
- Implement delegation (Phase 4)
- Add plans & continuation (Phase 5)
- Firebase storage for cloud sync
- Cost tracking dashboard

### Month 3-6 (Research & Publication)
- Full WMDP benchmark testing (3,668 questions)
- Temporal drift study (30+ users, 30+ days)
- Multi-agent manipulation experiments
- Write research paper for publication

---

## Final Recommendations

### Immediate Actions (Next 2 Hours)

1. **Call a team meeting** - Discuss this feasibility review
2. **Agree on reduced scope** - Lock in "MUST HAVE" features only
3. **Test LiteLLM standalone** - Validate the foundation works
4. **Assign clear ownership** - Who builds what
5. **Set up coordination** - Discord/Slack + daily standups

### Strategic Priorities

1. **Working demo > Complete features**
2. **Real results > Hypothetical claims**
3. **Simple & polished > Complex & buggy**
4. **Live demo > Code walkthrough**

### Cultural Mindset

- **Embrace scope cuts** - They're not failures, they're smart prioritization
- **Celebrate small wins** - Each tool working is progress
- **Stay flexible** - Hackathons rarely go to plan
- **Have fun** - You've already done exceptional planning work

---

## Appendix A: Checklist Summary

### Pre-Development Checklist
- [ ] Team meeting to review this feasibility document
- [ ] Agree on reduced scope (10-12 hours of work)
- [ ] Assign owners to each phase
- [ ] Test LiteLLM standalone with Gemini API key
- [ ] Install Python 3.11+, uv, Claude Desktop on all machines
- [ ] Set up team coordination (Discord/Slack)

### Day 1 Must Complete
- [ ] uv init + dependencies installed
- [ ] llm_call tool working in Claude Desktop
- [ ] Storage backend (put/get) implemented
- [ ] End-to-end test passes

### Day 2 Must Complete
- [ ] Multi-model comparison demo recorded
- [ ] Token savings calculation shown
- [ ] README updated with real instructions
- [ ] Submission.md updated with actual results
- [ ] Hackathon submission completed

---

## Appendix B: Decision Framework

**When evaluating any new feature or change, ask:**

1. **Is it REQUIRED for the demo?** (Yes → Do it, No → Skip)
2. **Can we fake it for the demo?** (Yes → Fake it, No → Build it)
3. **Is there a library/tool for this?** (Yes → Use it, No → Build minimal version)
4. **Does it block other work?** (Yes → Prioritize, No → Defer)

**Example:**
- "Should we implement Firebase storage?"
  - Required? No (SQLite works for demo)
  - Fake it? N/A
  - Library? Yes (firebase-admin)
  - Blocks? No
  - **Decision: SKIP for hackathon**

- "Should we implement llm_call tool?"
  - Required? Yes (core value prop)
  - Fake it? No (need real LLM calls)
  - Library? Yes (LiteLLM)
  - Blocks? Yes (everything depends on it)
  - **Decision: MUST HAVE**

---

**Good luck with the hackathon! You have excellent planning - now focus on execution. 🚀**
