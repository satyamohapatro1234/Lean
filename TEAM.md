# 🤖 AI Development Team — GitHub Workflow

## How This Works

Development happens through GitHub's native workflow:
**GitHub Issue → Assign to Copilot → Copilot opens PR → You review → Merge**

No local IDE setup needed. Everything runs in GitHub Actions.

---

## The Team Structure

```
YOU (Satya)
├── Create issues
├── Assign to the right agent
├── Review PRs
└── Merge when satisfied

GITHUB COPILOT CODING AGENT
├── Reads the issue
├── Reads AGENTS.md and the custom agent file
├── Runs in GitHub Actions (ephemeral environment)
├── Opens a PR on a copilot/branch
├── Self-reviews using Copilot code review
└── Requests your review when done
```

---

## The 6 Custom Agents

| Agent | File in .github/agents/ | Use For |
|-------|------------------------|---------|
| **data-pipeline** | `data-pipeline.md` | Bhavcopy, intraday downloader, instrument master, LEAN writer |
| **quant-strategy** | `quant-strategy.md` | LEAN engine, Spider Wave, fee model, symbol mapper, validation |
| **backend-api** | `backend-api.md` | FastAPI, WebSocket, broker integrations, LangGraph agents |
| **frontend-terminal** | `frontend-terminal.md` | React trading terminal (Phase 7 only) |
| **testing** | `testing.md` | Write and run tests for any component |
| **code-review** | `code-review.md` | Security and quality review for money-touching PRs |

---

## The Exact Workflow — Step by Step

### Step 1: Create a GitHub Issue

Go to your repo → Issues → New Issue → choose the right template:

- **📊 Data Pipeline Task** → for data-pipeline/ and instrument-master/
- **📈 Strategy / LEAN Task** → for strategies/, symbol-mapper/, run_backtest.py
- **🧪 Testing Task** → for any test work
- **🔍 Code Review Request** → for PR review

Write a clear description with exact acceptance criteria. Example:

```
Title: [Data] Build instrument-master/brokers/dhan_parser.py

What to build:
Download the Dhan instrument master CSV and populate SQLite.

Acceptance criteria:
- Running `python instrument-master/brokers/dhan_parser.py` completes without error
- SQLite DB contains 50,000+ rows
- Round-trip test passes: SELECT dhan_security_id FROM instruments WHERE symbol='NIFTY' returns a valid ID
```

### Step 2: Assign to Copilot

In the issue sidebar → Assignees → type "Copilot" → select it.

When you assign, a dropdown appears to select the custom agent.
Pick the agent that matches the issue type (see table above).

### Step 3: Wait for the PR

GitHub Copilot works in the background (10–30 minutes for complex tasks).
You'll get a notification when the PR is ready.

Watch progress: Issue → "Copilot is working on this" link → session logs.

### Step 4: Review the PR

Open the PR. Read:
1. What Copilot built (PR description)
2. Test results (in PR description)
3. The actual code diff

Leave review comments if something needs changing:
- `@copilot please also add error handling for HTTP 429 responses`
- `@copilot the lot size lookup is still hardcoded, use the lot_size_history table`

Copilot will update the PR and re-request review.

### Step 5: Final Check and Merge

Before merging any PR that touches financial calculations:
- Create a new issue using the **🔍 Code Review** template for that PR
- Assign it to `code-review` agent
- Wait for the review comment on the PR
- Only merge after code-review agent approves

---

## Phase 0 — The First 10 Issues to Create

Create these issues in order. The first batch can run in parallel.

### Batch 1 (Create all at once, all can run in parallel)

**Issue 1: Docker Infrastructure**
```
Title: [DevOps] Verify docker-compose.yml starts all services
Agent: (no custom agent — use default Copilot)
Task: Start LEAN + QuestDB + Redis. Add health check script.
Done: docker compose up -d → all healthy, health_check.sh passes
```

**Issue 2: Dhan Instrument Master Parser**
```
Title: [Data] Build instrument-master/brokers/dhan_parser.py
Agent: data-pipeline
Task: Download Dhan CSV, apply schema.sql, populate SQLite
Done: 50,000+ rows in instruments.db, NIFTY round-trip passes
```

**Issue 3: Database Schema Tests**
```
Title: [Test] Write tests/test_schema.py and tests/test_lot_sizes.py
Agent: testing
Task: Test SQLite schema, seed data, lot size date-awareness
Done: test_lot_sizes passes for Nifty Dec 2024 change (50→25)
```

### Batch 2 (After Batch 1 merges)

**Issue 4: NSE Bhavcopy Downloader**
```
Title: [Data] Build data-pipeline/bhavcopy_downloader.py
Agent: data-pipeline
Task: Async download, parse ZIP, insert to QuestDB, local cache
Done: 2024-12-31 bhavcopy downloaded, QuestDB shows 2000+ rows
```

**Issue 5: Symbol Mapper**
```
Title: [Quant] Build symbol-mapper/universal_mapper.py
Agent: quant-strategy
Task: Bidirectional Dhan ↔ LEAN Symbol mapping
Done: NIFTY round-trip passes, BANKNIFTY round-trip passes
```

### Batch 3 (After Batch 2 merges)

**Issue 6: Dhan Intraday Downloader**
```
Title: [Data] Build data-pipeline/intraday_downloader.py
Agent: data-pipeline
Task: SQLite job queue, token bucket rate limiter, resumable
Done: 5 F&O symbols × 30 days downloaded, queue shows completed
```

**Issue 7: Fee Model**
```
Title: [Quant] Build strategies/spider-wave/fee_model.py
Agent: quant-strategy
Task: DhanFeeModel loading from fee_schedules.json by date
Done: test_fee_model.py passes for pre/post Oct 2024 rates
```

**Issue 8: Fee Model Tests**
```
Title: [Test] Write tests/test_fee_model.py and tests/test_sebi_changes.py
Agent: testing
Task: Test Oct 2024 STT change, both old and new rates
Done: All test cases pass
```

### Batch 4 (After Batch 3 merges)

**Issue 9: LEAN Data Writer + Spider Wave Minimal**
```
Title: [Quant] Build lean_writer.py and minimal strategies/spider-wave/main.py
Agent: quant-strategy
Task: Write LEAN zip format from QuestDB, minimal 4-component algorithm
Done: run_backtest.py produces result JSON without error
```

**Issue 10: Phase 0 Code Review**
```
Title: [Review] PR review for all Phase 0 data and strategy code
Agent: code-review
Task: Review all merged PRs for security, LEAN format, fee model correctness
Done: Code review approves, no blocking issues
```

---

## Rules for Creating Good Issues

### What makes a good issue for Copilot

✅ Specific file names mentioned  
✅ Clear acceptance criteria with testable conditions  
✅ Relevant context from CONTEXT.md linked  
✅ One task per issue (not "build the whole data pipeline")  

### What makes a bad issue

❌ "Implement data pipeline" (too vague)  
❌ No acceptance criteria  
❌ Multiple unrelated files in one issue  
❌ No mention of which agent to use  

---

## Limitations of GitHub Copilot Coding Agent

Know these before you start:

1. **One PR per task** — Each issue gets exactly one PR. Can't open multiple PRs from one issue.
2. **Can't run docker compose** — The GitHub Actions environment is sandboxed. Copilot can't verify QuestDB connections. Test locally after merge.
3. **No live data access** — Copilot can't call the Dhan API. It writes the code; you test it.
4. **Read-only repo access** — Copilot can only push to `copilot/` branches. You merge.
5. **Context window** — For very large tasks, split into multiple issues.

---

## When Something Goes Wrong

**Copilot opened a PR but the code is wrong:**
Leave a review comment on the PR: `@copilot [describe the problem]`
Copilot will push a new commit to the same branch and re-request review.

**Copilot didn't understand the task:**
Close the PR. Improve the issue description with more detail.
Reassign Copilot to the issue.

**Copilot used wrong library/approach:**
Comment on the PR: `@copilot this uses X but we decided to use Y because [reason]. Please update.`
Reference DECISIONS.md: `@copilot per DECISIONS.md, we use QuestDB not TimescaleDB.`

---

*Everything that matters about past decisions is in CONTEXT.md.*
*Every technology choice is in DECISIONS.md.*
*The full plan is in PLAN.md.*
*The agent rules are in AGENTS.md and .github/agents/.*
