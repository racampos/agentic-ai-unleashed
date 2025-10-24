# Auto-Lab Coach — Product Requirements Document (Hackathon Draft v0.1)

**Project:** NetGenius – Auto-Lab Coach (Agentic Tutor)

**Author:** Rafael + ChatGPT (co-drafted)

**Date:** 2025‑10‑23

**Target event:** AWS × NVIDIA Hackathon (NIM + EKS)

---

## 1) Executive Summary

Auto‑Lab Coach is an **agentic tutor** that observes a student’s actions in a **simulated router/switch CLI**, provides **Socratic hints** or **Demonstrator actions**, and explains networking concepts in context. The coach runs on **AWS EKS**, calling two NVIDIA NIM microservices: (1) **LLM NIM** — `llama-3.1-nemotron-nano-8B-v1` in reasoning mode; and (2) **Text Embedding NIM** — `nv-embedqa-e5-v5` for retrieval grounding and doc search. The solution targets **CCNA beginners**, small topologies (2–4 devices), and foundational lab domains (basic router setup, IP addressing/subnetting, VLANs, static routing, IPv6 basics).

---

## 2) Hackathon Compliance Checklist

- [x] **Model:** `llama-3.1-nemotron-nano-8B-v1` (reasoning mode via system message).
- [x] **Embeddings:** at least one Retrieval Embedding NIM (`nv-embedqa-e5-v5`).
- [x] **Deployment:** both NIMs deployed on **AWS EKS** as separate microservices (OpenAI‑compatible APIs).
- [x] **Agentic application:** LangGraph‑based multi‑node agent orchestrating tools + retrieval.

---

## 3) Goals & Learning Outcomes (v1)

### Audience

- **Level:** CCNA beginner (primary).

### Initial Lab Domains (scope for v1)

- Basic router configuration (passwords, console/vty, MOTD banner, clock).
- IP addressing/subnetting.
- VLANs (create/assign, verify).
- Static routing (IPv4 & IPv6 basics).
- Common **show** commands and **ping** connectivity checks.

### Learning outcomes

- Set up a router from scratch (security banners & access, basic mgmt).
- Configure IPv4/IPv6 addressing and a static route.
- Create/assign VLANs and verify with show commands.
- Use `ping` and `show` commands to verify state.

### Success metrics (hackathon‑focused)

- Demo: 3 showcase labs completed with the coach in ≤3 minutes total.
- Median agent response time ≤ 1.5 s (goal; non‑blocking if not met).
- ≥80% of agent suggestions result in progress (as judged by rubric state deltas) in demo flows.

---

## 4) In Scope vs Out of Scope (v1)

**In scope**

- Two agent modes: **Socratic** (suggest/answer) and **Demonstrator** (suggest + can execute commands on behalf of the student via simulator API).
- Observability per **command** (command text + output), with on‑demand **history** pull.
- Retrieval grounding from curated lesson text, rubrics, and cheatsheets.
- Partial scoring rubric for each showcase lab.
- EKS deployment of two NIM services + a small orchestrator service.

**Out of scope**

- Large topologies (>4 devices), dynamic routing protocols (OSPF/EIGRP) in v1.
- Robust multi‑tenant auth/roles (beyond a simple session token).
- Full accessibility work; extensive analytics dashboards.

---

## 5) Personas & Primary Journeys

**Student (beginner)**

- Opens a lab → types CLI commands → asks questions → receives hints or requests a demonstrator action.

**Instructor/Judge**

- Starts a showcase scenario → observes agent’s reasoning & retrieval snippet → sees remediation and pass/fail rubric.

**Primary journeys**

1. **Socratic help:** Student tries, agent suggests next minimal step, explains why.
2. **Demonstrator rescue:** Student asks the agent to “show me how,” agent types commands (visible typing), then explains.
3. **Grounded explanation:** Agent cites a short snippet from lesson text to justify a suggestion.

---

## 6) Functional Requirements

### 6.1 Agent Modes

- **Socratic mode** (default): Provide hints, ask guiding questions, do not modify device state.
- **Demonstrator mode** (opt‑in): May type and execute commands on behalf of the student, with a visible “ghost typing” effect.

### 6.2 Observability

- **Event feed:** For each **ENTER** press: capture `command` + `output`.
- **History pull tool:** Agent can request full `command_history` (commands + outputs) per device.

### 6.3 Safety rails

- Running in a simulator; **no destructive command blocks required**. (We may still warn on `erase`/`reload` to preserve learning continuity.)

### 6.4 Retrieval

- Use embeddings to fetch **1–3** short snippets (lesson, rubric, cheatsheet, vendor doc extracts) per step; display the top snippet inline as “Why this step?”.

### 6.5 Grading

- **Intelligent partial scoring** per lab: criteria with weights (e.g., `passwords_configured` 0.2, `vty_secured` 0.2, `static_route_correct` 0.3, `ping_success` 0.3). See Appendix A for a sample rubric JSON.

---

## 7) Non‑Functional Requirements

- **Latency target:** Aim ≤ 1.5 s end‑to‑end for an agent suggestion (soft goal; acceptable up to 2.5 s in demo).
- **Reliability:** If a tool call fails, retry with exponential backoff (jitter); show a helpful message if still failing.
- **Security/PII:** No PII stored; session logs retained **30 days** (see §15). “PII” = personally identifiable information (names, emails, etc.).

---

## 8) Simulator Integration (WS‑first)

- **Transport:** WebSocket (frontend ⇄ backend); the orchestrator connects server‑side to the same backend or via a mirror feed.
- **Runtime flow:**

  1. Student types → backend emits `{device, command, output}` events.
  2. Orchestrator subscribes; agent consumes the event stream.
  3. In Demonstrator mode, agent calls `run_cli()` tool **against the backend’s “type into terminal” endpoint** (so the student sees the typed command and its output); never bypass the terminal.

---

## 9) Tooling / API Contracts (Agent ⇄ Simulator)

> All tools are executed with **concurrency = 1** per session.

### 9.1 `run_cli`

**Intent:** Type a command into the student’s terminal and return the produced output.

```json
{
  "name": "run_cli",
  "params": {
    "session_id": "string",
    "device": "string",
    "command": "string"
  },
  "returns": {
    "device": "string",
    "command": "string",
    "output": "string",
    "ts": "iso-datetime"
  }
}
```

### 9.2 `get_running_config`

```json
{
  "name": "get_running_config",
  "params": { "session_id": "string", "device": "string" },
  "returns": { "device": "string", "config": "string", "ts": "iso-datetime" }
}
```

### 9.3 `get_topology`

```json
{
  "name": "get_topology",
  "params": { "session_id": "string" },
  "returns": {
    "nodes": [{ "id": "R1", "type": "router" }],
    "links": [{ "a": "R1", "b": "S1" }]
  }
}
```

### 9.4 `get_command_history`

```json
{
  "name": "get_command_history",
  "params": { "session_id": "string", "device": "string" },
  "returns": {
    "history": [{ "command": "show ip int br", "output": "...", "ts": "..." }]
  }
}
```

---

## 10) LangGraph Architecture

### 10.1 Nodes & Edges

- **Planner** → decide the next minimal diagnostic/config step (Socratic by default; Demonstrator when asked).
- **Retriever** → fetch 1–3 grounding snippets using Embedding NIM (score threshold; top‑1 shown to user).
- **Executor** → call `run_cli` (Demonstrator only) and/or fetch information tools.
- **Explainer** → summarize what outputs mean; propose the next action.
- **Critic** → check stop conditions (rubric met, “Goal achieved”, or user stop).

**Loop:** `Planner → Retriever → (Executor?) → Explainer → Critic → [Planner|END]`

### 10.2 State Schema (sketch)

```ts
interface State {
  session_id: string;
  mode: "socratic" | "demonstrator";
  goal: string;
  history: Array<{ role: "user" | "assistant" | "system"; content: string }>;
  observations: string[]; // last N command outputs
  retrieved: Array<{ text: string; score: number }>;
  rubric: Rubric | null;
  done: boolean;
}
```

---

## 11) Prompting Strategy (suggested defaults)

### Global System Preamble (LLM NIM)

> _You are NetGenius Auto‑Lab Coach. detailed thinking on. Respond first with a concise plan or question. Prefer the smallest next step that increases certainty. When in Socratic mode, guide with questions and hints without revealing full solutions; when in Demonstrator mode, propose exact commands and, if approved, execute via `run_cli`. Always include a one‑sentence rationale and optionally a short retrieved snippet labeled “Why this step”._

### Planner (few‑shot style)

- _Input:_ latest command/output + goal + mode + (optionally) rubric criteria not yet satisfied.
- _Output format:_ bullet list of ≤2 steps. For Demonstrator: `Device: command` lines.

**Mini exemplar**

```
Goal: Configure a static route from R1 to 10.0.2.0/24 via 10.0.1.2
Student output: 'show ip route' shows only connected 10.0.1.0/24
Plan:
- Ask: Do we have the next‑hop interface IP? If yes, propose: R1: conf t → ip route 10.0.2.0 255.255.255.0 10.0.1.2
Rationale: Static routes require a next hop; output shows only directly connected networks.
```

### Retriever

- _Instruction:_ Retrieve up to 3 chunks (300–500 tokens) most relevant to the plan; expose top‑1 as a 1–2 sentence quote.

### Explainer

- _Instruction:_ 3–5 sentences max; explain what the output indicates; propose the next minimal step.

### Critic

- _Instruction:_ Stop if rubric is satisfied, if the assistant explicitly states “Goal achieved”, or if the user says stop.

---

## 12) Retrieval & Data (Embeddings + pgvector)

### Sources (v1)

- Your lesson/rubric text (first‑party).
- Curated cheatsheets.
- Vendor docs (confirm license; include short extracts only).

### Ingestion

- Chunk size: **300–500 tokens**; store metadata: `{source, topic, lab_id, level}`.
- Compute embeddings via `nv-embedqa-e5-v5`; store in **pgvector**.

### pgvector Schema (sketch)

```sql
CREATE TABLE docs (
  id UUID PRIMARY KEY,
  lab_id TEXT,
  topic TEXT,
  source TEXT,
  content TEXT,
  embedding VECTOR(1024),  -- adjust if model reports different dim
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX docs_idx ON docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Query

```sql
SELECT id, content, 1 - (embedding <=> $1) AS score
FROM docs
WHERE lab_id = $2
ORDER BY embedding <=> $1
LIMIT 3;
```

---

## 13) AWS EKS Deployment

### 13.1 Cluster & Nodes

- **Region:** us‑east‑1
- **GPU:** **g6.xlarge (L4 24GB)** single‑node (fixed) for hackathon.
- Install **NVIDIA GPU Operator**; create namespace `nim` and `coach`.

### 13.2 Services

- **LLM NIM service**: `llama-3.1-nemotron-nano-8B-v1` (OpenAI `/v1/chat/completions`).
- **Embedding NIM service**: `nv-embedqa-e5-v5` (OpenAI `/v1/embeddings`).
- **Orchestrator** service: Python/Node app hosting LangGraph + WS client to simulator.

### 13.3 Ingress & TLS

- **ALB Ingress Controller** with **ACM** cert; expose `/v1/chat/completions`, `/v1/embeddings`, and `/api/orchestrator` behind separate paths/hosts as needed.

### 13.4 Secrets & Config

- **Kubernetes Secrets**: `NGC_API_KEY`, `OPENAI_COMPAT_KEYS` (if any), DB creds for pgvector.
- **ConfigMaps**: model names, rate limits, temperature, max_tokens.

### 13.5 Observability

- **CloudWatch Logs** for NIM pods and orchestrator.

### 13.6 Minimal Helm values (sketch)

```yaml
# values-llm.yaml
image:
  repository: nvcr.io/nim/nvidia/llama-3.1-nemotron-nano-8b-v1
  tag: "<tag>"
model:
  ngcAPISecret: ngc-api
resources:
  limits:
    nvidia.com/gpu: 1
service:
  type: ClusterIP
  ports:
    - name: http-openai
      port: 8000
      targetPort: 8000
```

```yaml
# values-embed.yaml
image:
  repository: nvcr.io/nim/nvidia/nv-embedqa-e5-v5
  tag: "<tag>"
model:
  ngcAPISecret: ngc-api
resources:
  limits:
    nvidia.com/gpu: 1
service:
  type: ClusterIP
  ports:
    - name: http-openai
      port: 8000
      targetPort: 8000
```

---

## 14) Rate Limiting & Error Handling

- **Per user:** LLM up to **1 rps burst**, embeddings up to **2 rps**.
- **Retries:** exponential backoff (100ms, 300ms, 900ms) with jitter; circuit‑break on 5xx bursts.
- **Graceful messages:** If a tool fails, show “Temporary issue contacting simulator; try again.”

---

## 15) Security, Data, & Compliance

- **PII:** None collected by design; session IDs only.
- **Data retention:** Session logs (commands + outputs + agent messages) retained **30 days**.
- **Content policy:** Networking topics only.
- **Licensing:** Use first‑party docs and your authored content; if vendor extracts are used, ensure permitted usage.

---

## 16) UX Spec (MVP)

- **Layout:** CLI left (full terminal); **Tutor panel** docked right (chat‑like).
- **Controls:** “Run suggested command” (Demonstrator), “Why this step?” (shows top retrieved snippet), “Ask a question”.
- **Presentation:** Each agent turn shows: Plan (≤2 bullets) → Rationale (1 sentence) → [Optional] Why‑snippet → Button(s).

---

## 17) Demo Plan (Judges)

1. **Basic router config**: Student sets passwords/MOTD; misses VTY login — agent hints; on 2nd try, agent demonstrates enabling `login local` with explanation.
2. **Static route**: No reachability; agent proposes checking interface IPs, then adding a route; demonstrates `ip route` and validates with `ping`.
3. **VLAN lab**: Student creates VLAN but forgets to assign access port; agent suggests `switchport access vlan X` and verification with `show vlan brief`.

Each step briefly shows a retrieved snippet (2 lines) justifying the suggestion.

---

## 18) Test Plan

- **Unit:** Tool adapters (mock WS), rubric evaluator, embedding queries.
- **Integration:** End‑to‑end loop on a tiny topology; record golden transcripts.
- **Load (light):** 2 concurrent sessions; verify no starvation with concurrency=1 per session.
- **Failover:** Kill NIM pod; ensure orchestrator surfaces a friendly error and retries.

---

## 19) Timeline (Hackathon)

- **Day 1:** EKS cluster, GPU Operator, Embedding NIM up, pgvector seeded; orchestrator skeleton; Socratic mode working.
- **Day 2:** LLM NIM up; Demonstrator mode wiring (visible typing); first lab complete; partial scoring rubric.
- **Day 3:** Polish prompts; add 2 more labs; record 3‑min video; README with architecture diagram + curl proofs.

---

## 20) Risks & Mitigations

- **NIM image pull or GPU quirks:** Pre‑pull images; keep a smaller region fallback (e.g., g5.xlarge) and a recorded demo.
- **Time constraints:** Limit scope to 3 labs; hardcode rubrics; minimal UI polish.
- **Retrieval quality:** Curate short, high‑signal snippets; cap snippet length; tune chunk size.

**Plan B:** If EKS blocks, deploy **SageMaker endpoints** for LLM & Embeddings and point orchestrator there; keep a recorded simulator session to narrate while endpoints respond live to small requests.

---

## Appendix A — Sample Rubric (JSON)

```json
{
  "lab_id": "static_route_v1",
  "criteria": [
    {
      "id": "ip_configured",
      "desc": "Interfaces have correct IP/mask",
      "weight": 0.25,
      "check": "show ip int br | expect up/up on G0/0 and G0/1 with correct subnets"
    },
    {
      "id": "route_present",
      "desc": "Static route to 10.0.2.0/24 via 10.0.1.2 exists",
      "weight": 0.35,
      "check": "show run | include ^ip route 10.0.2.0 255.255.255.0 10.0.1.2$"
    },
    {
      "id": "ping_success",
      "desc": "Ping to 10.0.2.10 succeeds",
      "weight": 0.4,
      "check": "ping 10.0.2.10 | expect success >= 80%"
    }
  ],
  "pass_threshold": 0.8
}
```

## Appendix B — Example Prompts

**System (global):**

```
You are NetGenius Auto‑Lab Coach. detailed thinking on.
Operate in two modes: Socratic (guide with questions, do not reveal full solutions) and Demonstrator (propose exact commands, and if approved, execute via run_cli).
Always: (1) propose the smallest next step; (2) give a one‑sentence rationale; (3) when available, include a short retrieved snippet labeled "Why this step".
```

**Planner (format):**

```
Return up to two next steps. If Demonstrator mode and the step is a command, format as:
- R1: conf t
- R1: ip route 10.0.2.0 255.255.255.0 10.0.1.2
```

**Explainer:**

```
Explain what the latest outputs indicate in <=5 sentences and propose one next action.
```

## Appendix C — Env Vars & Config

```
# NIM endpoints
LLM_BASE_URL=http://llm-nim.nim.svc.cluster.local:8000/v1
EMB_BASE_URL=http://embed-nim.nim.svc.cluster.local:8000/v1
LLM_MODEL=nvidia/llama-3.1-nemotron-nano-8b-v1
EMB_MODEL=nvidia/nv-embedqa-e5-v5

# Retrieval
PGVECTOR_DSN=postgres://user:pass@host:5432/db
EMBED_DIM=1024   # adjust at runtime if model reports different
CHUNK_TOKENS=400
TOPK=3

# Rate limits
LLM_RPS_BURST=1
EMB_RPS_BURST=2

# Misc
NGC_API_KEY=...
```
