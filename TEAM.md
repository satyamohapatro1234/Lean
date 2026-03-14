# 🤖 AI Development Team — How This Works

## The Concept

This project is built by a team of specialized AI agents, each owning a domain — exactly like a real software engineering team. The agents work from a shared plan (`PLAN.md`), shared context (`CONTEXT.md`), and shared rules (`AGENT_INSTRUCTIONS.md`).

You are the tech lead / product owner. You review and approve. The agents do the building.

---

## The Team

```
                        ┌─────────────────────────┐
                        │      SATYA (You)         │
                        │  Tech Lead + Approver    │
                        │  Reviews all work        │
                        │  Makes final decisions   │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │     ORCHESTRATOR        │
                        │  Project Manager        │
                        │  Reads plan, delegates  │
                        │  Never writes code      │
                        └───┬────┬────┬────┬─────┘
                            │    │    │    │
               ┌────────────┘    │    │    └──────────────┐
               │                 │    │                   │
       ┌───────▼──────┐  ┌───────▼──┐ │ ┌─────────────┐  │
       │  DATA AGENT  │  │  QUANT   │ │ │   BACKEND   │  │
       │  Pipeline    │  │  AGENT   │ │ │    AGENT    │  │
       │  QuestDB     │  │  LEAN    │ │ │  FastAPI    │  │
       │  Bhavcopy    │  │  Strategy│ │ │  Brokers    │  │
       │  Intraday    │  │  Backtest│ │ │  Agents     │  │
       └──────────────┘  └──────────┘ │ └─────────────┘  │
                                       │                   │
                              ┌────────▼──────┐   ┌───────▼──────┐
                              │   FRONTEND    │   │   DEVOPS     │
                              │    AGENT      │   │    AGENT     │
                              │  React UI     │   │   Docker     │
                              │  KLineChart   │   │   Cron jobs  │
                              │  WebSocket    │   │   Infra      │
                              └───────────────┘   └──────────────┘
                                        
    ┌──────────────────────────────────────────────────────────────┐
    │             ALWAYS-ON AGENTS (run in background)             │
    │                                                              │
    │  TEST AGENT        REVIEWER AGENT     CONTEXT GUARDIAN      │
    │  Writes tests      Reviews code       Updates docs          │
    │  Runs after        Reviews before     After each phase      │
    │  every build       money-touching     or decision           │
    └──────────────────────────────────────────────────────────────┘
```

---

## Who Does What

| Phase | Lead Agent | Supporting | Review |
|-------|-----------|-----------|--------|
| Phase 0 (current) | data-agent | quant-agent for symbol mapper | test-agent + reviewer-agent |
| Phase 1 | quant-agent | data-agent for extra data | test-agent |
| Phase 2 | backend-agent | devops-agent for token refresh | reviewer-agent |
| Phase 3 | backend-agent | quant-agent for LEAN wrapper | reviewer-agent + test-agent |
| Phase 7 | frontend-agent | backend-agent (API must exist first) | reviewer-agent |

---

## How to Use the Agents

### Option 1: Using Cline (VSCode extension)

Open Cline, select an agent, give it a task:

```
"data-agent: Build data-pipeline/bhavcopy_downloader.py.
 Read CONTEXT.md sections on NSE Bhavcopy first.
 One day = one ZIP = all 2000+ stocks.
 Cache locally, insert to QuestDB via ILP port 9009.
 Test: python bhavcopy_downloader.py --date 2024-12-31"
```

### Option 2: Using Claude Code (terminal)

The agents are defined in `.claude/agents/`. Claude Code loads them automatically.

```bash
cd /path/to/this/repo
claude   # Opens Claude Code
# Type: "Use orchestrator agent to start Phase 0"
# Or:   "Use data-agent to build the bhavcopy downloader"
```

### Option 3: Manual Task Assignment

Read `PLAN.md` → pick the next task → open the relevant agent file to understand its rules → give it to your AI coding tool of choice (Cline, Cursor, Claude Code) with the agent instructions as context.

---

## The Correct Work Pattern

```
                    START
                      │
                      ▼
            Satya: "Start Phase 0"
                      │
                      ▼
            orchestrator reads PLAN.md
            breaks Phase 0 into tasks
            assigns to correct agents
                      │
           ┌──────────┼──────────┐
           │          │          │
           ▼          ▼          ▼
      data-agent  quant-agent  devops-agent
      (parallel   (symbol      (docker up)
       tasks)      mapper)
           │          │          │
           └──────────┴──────────┘
                      │
                      ▼
                test-agent runs
                (after each build)
                      │
                      ▼
              reviewer-agent checks
              (before any money code)
                      │
                      ▼
              Satya reviews output
              approves or requests changes
                      │
                      ▼
           context-guardian updates docs
                      │
                      ▼
                 Next Task
```

---

## What Agents Can and Cannot Do

### Can Do (without asking Satya)
- Create new files in their domain folders
- Edit files they created
- Run `pytest`, `python`, `curl` for testing
- Query QuestDB, SQLite for debugging
- Install packages listed in requirements.txt
- Write tests

### Must Ask Satya First
- Change any architectural decision in DECISIONS.md
- Modify another agent's domain files
- Place any live order (even paper trading)
- Change docker-compose.yml infrastructure
- Modify PLAN.md phase structure

### Can Never Do
- Place a live order without human confirmation
- Commit to git (Satya commits)
- Change CONTEXT.md "Decisions" or "Mistakes" entries without approval
- Ignore a test failure and proceed anyway

---

## Parallel vs Sequential — The Rules

### These agents CAN work at the same time (different files):
- data-agent building bhavcopy + test-agent writing schema tests
- data-agent building intraday downloader + quant-agent building fee model
- backend-agent building API routes + frontend-agent building design system

### These agents MUST work in sequence (dependencies):
- schema.sql must exist before dhan_parser.py
- Docker must be up before any data download test
- Backend API must be complete before frontend connects
- Instrument master must work before symbol mapper can be tested
- Symbol mapper must work before first backtest

---

## Agent Files Location

All agent definitions are in `.claude/agents/`:
- `orchestrator.md` — reads plan, delegates tasks
- `data-agent.md` — data pipeline specialist
- `quant-agent.md` — LEAN engine + strategy
- `backend-agent.md` — FastAPI + broker integrations
- `frontend-agent.md` — React trading terminal
- `test-agent.md` — quality assurance
- `devops-agent.md` — Docker + infrastructure
- `reviewer-agent.md` — code review + security
- `context-guardian.md` — documentation keeper

Plus `CLAUDE.md` — the root instructions loaded by Claude Code automatically.

---

## Starting Right Now

```bash
# Clone the repo
git clone https://github.com/satyamohapatro1234/Lean.git
cd Lean

# Open in your AI coding tool
code .          # VS Code + Cline
# or
claude          # Claude Code in terminal

# Tell the orchestrator to start
# "Use orchestrator-agent to plan Phase 0 and assign first batch of tasks"
```

The orchestrator will read PLAN.md, break down Phase 0 into concrete tasks, and tell you exactly which agent to invoke for each task.

---

*This team structure is inspired by how real engineering teams work: clear roles, clear ownership, no one person (or agent) doing everything.*
