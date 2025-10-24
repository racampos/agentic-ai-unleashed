# Auto-Lab Coach — Implementation Plan

**Based on:** PRDv1.md
**Target:** AWS × NVIDIA Hackathon (3-day timeline)
**Date:** 2025-10-23
**Updated:** With two-cluster architecture and existing simulator integration

---

## Executive Summary

This implementation plan breaks down the Auto-Lab Coach project into 9 phases aligned with the 3-day hackathon timeline. The solution integrates AI coaching capabilities into an **existing network simulator** by deploying NVIDIA NIMs on a **separate EKS cluster** for proper workload isolation. Each phase includes specific deliverables, technical decisions, and validation criteria.

---

## Architecture Overview

```
                    ┌──────────────────────────────┐
                    │    Vercel (CDN/Edge)         │
                    │  Next.js Frontend            │
                    │  - xterm.js terminal         │
                    │  - Tutor panel UI            │
                    └──────────┬───────────────────┘
                               │ HTTPS/WSS
                               ↓
┌──────────────────────────────────────────────────────────────┐
│              AWS Region: us-east-1                            │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │   EKS Cluster 1: Simulator (EXISTING)              │     │
│  │   Namespace: sims                                   │     │
│  │   Node Type: CPU (t3.medium/large)                 │     │
│  │  ┌──────────────────┐    ┌──────────────────┐     │     │
│  │  │  Infra API       │    │  Simulator Jobs  │     │     │
│  │  │  (Auth + Proxy)  │────│  (Per User)      │     │     │
│  │  └──────────────────┘    └──────────────────┘     │     │
│  └────────────────┬───────────────────────────────────┘     │
│                   │                                          │
│                   │ Internal NLB                             │
│                   │                                          │
│  ┌────────────────┴───────────────────────────────────┐     │
│  │   EKS Cluster 2: AI Coach (NEW - HACKATHON)       │     │
│  │   Namespace: nim, coach                             │     │
│  │   Node Type: GPU (g6.xlarge - 1 node)             │     │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │     │
│  │  │ LLM NIM  │  │ Embed    │  │ Orchestrator   │  │     │
│  │  │(Nemotron)│  │NIM (E5)  │  │ (LangGraph +   │──┼─────┘
│  │  │ :8000    │  │ :8000    │  │  FAISS index)  │  │
│  │  └──────────┘  └──────────┘  └────────────────┘  │
│  │         Internal cluster-local communication       │
│  └────────────────────────────────────────────────────┘
│                               │
│                    ┌──────────┴──────────┐
│                    │   ALB Ingress       │
│                    │   (orchestrator)    │
│                    └─────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Decisions

### Backend Orchestrator
- **Language:** Python 3.11+
- **Framework:** FastAPI (async support, WebSocket native, OpenAPI docs)
- **Agent Framework:** LangGraph 0.2+
- **LLM Client:** OpenAI Python SDK (NIM is OpenAI-compatible)
- **WebSocket Client:** websockets (for connecting to simulator)
- **Vector Store:** FAISS (in-memory, file-based persistence)
- **HTTP Client:** httpx (async HTTP for simulator API calls)

### Frontend
- **Framework:** Next.js 14 with TypeScript (App Router)
- **Deployment:** Vercel (serverless + edge functions)
- **Terminal:** xterm.js (full terminal emulation)
- **WebSocket:** native WebSocket API
- **State:** Zustand (lightweight state management)
- **UI:** Tailwind CSS + shadcn/ui components
- **API Routes:** Next.js API routes for proxying to orchestrator

### Simulator (EXISTING - No Build Required)
- **Status:** Already deployed on EKS Cluster 1
- **Architecture:** Python-based with multiprocessing
- **WebSocket Endpoint:** `/ws/simulator/{session_id}`
- **Auth:** Clerk tokens → Service Token (STS) via Infra API
- **Integration:** Orchestrator connects via internal NLB or VPC peering

### Infrastructure

#### AI Coach Cluster (NEW)
- **EKS Version:** 1.32
- **GPU Instance:** g6.xlarge (NVIDIA L4, 24GB) - single node
- **Namespaces:** `nim`, `coach`
- **Ingress:** AWS Load Balancer Controller
- **Network:** VPC peering to Simulator cluster OR Internal NLB

#### Simulator Cluster (EXISTING)
- **EKS Version:** 1.32
- **Node Type:** CPU-optimized (t3.medium/large)
- **Namespace:** `sims`
- **Services:** Infra API, Simulator Jobs
- **Expose:** Internal NLB for orchestrator connectivity

#### Vector Store
- **Technology:** FAISS (Facebook AI Similarity Search)
- **Storage:** File-based index bundled with orchestrator container
- **Indexing:** Pre-built during Docker image build
- **Size:** ~150 chunks, ~600KB index file
- **Latency:** <10ms (in-memory after load)

**Design Rationale:**
- Hackathon-optimized: No external database dependency
- Dataset size: ~50-200 document chunks (static corpus)
- Single orchestrator pod: No concurrency requirements
- Time savings: 2 hours vs. pgvector setup
- Production path: Migrate to pgvector for multi-pod scaling

#### Secrets
- **AI Coach:** AWS Secrets Manager → Kubernetes Secrets
- **Simulator:** Existing Clerk + KMS setup (unchanged)

---

## Phase 1: Infrastructure Foundation (Day 1, 0-3 hours)

### Deliverables
1. AI Coach EKS cluster with GPU node group
2. NVIDIA GPU Operator installed
3. Namespaces and RBAC configured
4. Network connectivity to existing Simulator cluster (Internal NLB)

### Implementation Steps

#### 1.1 AI Coach EKS Cluster Setup
```bash
# Create AI Coach cluster with eksctl
eksctl create cluster \
  --name ai-coach \
  --region us-east-1 \
  --version 1.32 \
  --nodegroup-name gpu-nodes \
  --node-type g6.xlarge \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 1 \
  --with-oidc \
  --ssh-access \
  --managed \
  --vpc-nat-mode Single  # Cost optimization
```

**Note:** Simulator cluster already exists at EKS cluster name (check your infrastructure). We'll connect to it via internal NLB.

#### 1.2 NVIDIA GPU Operator
```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

kubectl create namespace nim

helm install gpu-operator nvidia/gpu-operator \
  --namespace nim \
  --set driver.enabled=false \  # pre-installed on EKS GPU AMI
  --wait
```

#### 1.3 Namespaces and Secrets
```bash
kubectl create namespace coach

# Create NGC API secret for NIM deployments
kubectl create secret generic ngc-api \
  --from-literal=NGC_API_KEY=$NGC_API_KEY \
  -n nim

# Create simulator access secret (for STS token or credentials)
kubectl create secret generic simulator-auth \
  --from-literal=SIMULATOR_TOKEN=<sts-token-or-tbd> \
  -n coach
```

#### 1.4 Simulator Connectivity (Internal NLB)

**In Simulator EKS Cluster** (if not already exposed):
```yaml
# simulator-internal-nlb.yaml
apiVersion: v1
kind: Service
metadata:
  name: netgenius-infra-api-nlb
  namespace: sims
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: netgenius-infra-api
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  - name: ws
    port: 8001
    targetPort: 8000  # Same port, just labeled differently
```

Apply in simulator cluster:
```bash
# Context switch to simulator cluster
kubectl config use-context <simulator-cluster-context>
kubectl apply -f simulator-internal-nlb.yaml

# Get NLB DNS name
kubectl get svc netgenius-infra-api-nlb -n sims \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# Example output: internal-abc123-xxxxx.us-east-1.elb.amazonaws.com
```

**In AI Coach Cluster**, store endpoint:
```bash
# Switch back to AI Coach cluster
kubectl config use-context <ai-coach-cluster-context>

kubectl create configmap simulator-config \
  --from-literal=SIMULATOR_BASE_URL="http://internal-abc123-xxxxx.us-east-1.elb.amazonaws.com:8000" \
  -n coach
```

**Security Group Update:**
- In Simulator cluster node security group: Allow TCP 8000 from AI Coach cluster CIDR
- Or use security group ID of AI Coach nodes

**Validation:**
- `kubectl get nodes -o wide` shows GPU node Ready
- `kubectl get pods -n nim` shows GPU Operator Running
- `curl http://<simulator-nlb>:8000/healthz` returns 200 OK from AI Coach cluster pod
- Security groups allow TCP 8000 from AI Coach CIDR to Simulator cluster

---

## Phase 2: Embedding Pipeline with FAISS (Day 1, 3-5 hours)

### Deliverables
1. Embedding NIM deployed and accessible
2. FAISS index built with document corpus (~150 chunks)
3. Index and metadata files ready for container bundling

### Implementation Steps

#### 2.1 Deploy Embedding NIM
```yaml
# helm-values-embed.yaml
image:
  repository: nvcr.io/nim/nvidia/nv-embedqa-e5-v5
  tag: "1.0.0"

model:
  ngcAPISecret: ngc-api

resources:
  limits:
    nvidia.com/gpu: 1
    memory: 16Gi
  requests:
    nvidia.com/gpu: 1
    memory: 8Gi

service:
  type: ClusterIP
  port: 8000

env:
  - name: NIM_CACHE_PATH
    value: /opt/nim/.cache
```

```bash
helm install embed-nim nvidia/nim \
  -f helm-values-embed.yaml \
  -n nim
```

#### 2.2 Prepare Document Corpus
```python
# data/lessons/loader.py
import json
from pathlib import Path

def load_lesson_chunks(data_dir: str = "data/lessons/"):
    """Load and chunk lesson documents"""
    chunks = []

    # Example lesson structure
    lessons = [
        {
            "lab_id": "basic_router_v1",
            "topic": "Basic Router Configuration",
            "source": "lesson_01_router_basics.md",
            "sections": [
                {
                    "title": "Setting Enable Password",
                    "content": "The enable password secures privileged EXEC mode. "
                              "Use 'enable secret <password>' instead of 'enable password' "
                              "for encryption. The secret command uses MD5 hashing."
                },
                {
                    "title": "Configuring VTY Lines",
                    "content": "VTY (Virtual Terminal) lines allow remote access via Telnet/SSH. "
                              "Always use 'login local' to require username/password authentication. "
                              "Without 'login', the password command alone won't work."
                },
                # ... more sections
            ]
        },
        {
            "lab_id": "static_routing_v1",
            "topic": "Static Routing",
            "source": "lesson_02_static_routes.md",
            "sections": [
                {
                    "title": "Static Route Syntax",
                    "content": "Format: ip route <network> <mask> <next-hop-ip>. "
                              "The next-hop must be reachable (directly connected). "
                              "Use 'show ip route' to verify route installation."
                },
                # ... more sections
            ]
        },
        {
            "lab_id": "vlan_basics_v1",
            "topic": "VLAN Configuration",
            "source": "lesson_03_vlans.md",
            "sections": [
                {
                    "title": "Creating VLANs",
                    "content": "Create VLANs in global config: 'vlan <vlan-id>'. "
                              "Assign ports: 'interface fa0/1', then 'switchport mode access' "
                              "and 'switchport access vlan <vlan-id>'."
                },
                # ... more sections
            ]
        }
    ]

    # Flatten into chunks
    for lesson in lessons:
        for section in lesson["sections"]:
            chunks.append({
                "lab_id": lesson["lab_id"],
                "topic": lesson["topic"],
                "source": lesson["source"],
                "content": f"{section['title']}\n\n{section['content']}",
                "metadata": {
                    "section_title": section["title"]
                }
            })

    return chunks
```

#### 2.3 Build FAISS Index
```python
# scripts/build_faiss_index.py
import faiss
import numpy as np
import pickle
import os
from openai import OpenAI
from data.lessons.loader import load_lesson_chunks

def build_index():
    # Connect to Embedding NIM
    client = OpenAI(
        base_url="http://embed-nim.nim.svc.cluster.local:8000/v1",
        api_key="not-used"
    )

    # Load document chunks
    chunks = load_lesson_chunks("data/lessons/")
    print(f"Loaded {len(chunks)} chunks")

    # Generate embeddings
    embeddings = []
    metadata = []

    for i, chunk in enumerate(chunks):
        print(f"Embedding chunk {i+1}/{len(chunks)}...")

        response = client.embeddings.create(
            model="nvidia/nv-embedqa-e5-v5",
            input=chunk["content"]
        )

        embeddings.append(response.data[0].embedding)
        metadata.append({
            "content": chunk["content"],
            "lab_id": chunk["lab_id"],
            "topic": chunk["topic"],
            "source": chunk["source"],
            "metadata": chunk.get("metadata", {})
        })

    # Build FAISS index
    embedding_matrix = np.array(embeddings).astype('float32')
    dimension = embedding_matrix.shape[1]  # Should be 1024 for E5

    print(f"Building FAISS index with dimension {dimension}...")

    # Use IndexFlatIP for cosine similarity
    index = faiss.IndexFlatIP(dimension)

    # Normalize vectors for cosine similarity
    faiss.normalize_L2(embedding_matrix)

    # Add vectors to index
    index.add(embedding_matrix)

    # Create output directory
    os.makedirs("data/faiss", exist_ok=True)

    # Save index and metadata
    faiss.write_index(index, "data/faiss/index.bin")
    with open("data/faiss/metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ FAISS index built successfully!")
    print(f"   - Index file: data/faiss/index.bin ({os.path.getsize('data/faiss/index.bin') / 1024:.1f} KB)")
    print(f"   - Metadata file: data/faiss/metadata.pkl ({os.path.getsize('data/faiss/metadata.pkl') / 1024:.1f} KB)")
    print(f"   - Total chunks: {len(embeddings)}")
    print(f"   - Dimension: {dimension}")

if __name__ == "__main__":
    build_index()
```

Run the script:
```bash
# Port-forward to Embedding NIM for local testing
kubectl port-forward -n nim svc/embed-nim 8000:8000 &

# Build the index
python scripts/build_faiss_index.py
```

**Validation:**
- `curl http://embed-nim.nim.svc.cluster.local:8000/v1/embeddings -d '{"input":"test","model":"nvidia/nv-embedqa-e5-v5"}'` returns 1024-dim vector
- `ls -lh data/faiss/` shows `index.bin` and `metadata.pkl` files
- Index file size ~500-800 KB for 150 chunks

---

## Phase 3: LLM Deployment (Day 1, Evening)

### Deliverables
1. LLM NIM deployed with reasoning mode
2. System prompt tested and validated
3. Basic chat completion working

### Implementation Steps

#### 3.1 Deploy LLM NIM
```yaml
# helm-values-llm.yaml
image:
  repository: nvcr.io/nim/nvidia/llama-3.1-nemotron-nano-8b-v1
  tag: "1.0.0"

model:
  ngcAPISecret: ngc-api

resources:
  limits:
    nvidia.com/gpu: 1
    memory: 20Gi
  requests:
    nvidia.com/gpu: 1
    memory: 16Gi

service:
  type: ClusterIP
  port: 8000

env:
  - name: NIM_CACHE_PATH
    value: /opt/nim/.cache
  - name: NIM_MAX_MODEL_LEN
    value: "8192"
```

```bash
helm install llm-nim nvidia/nim \
  -f helm-values-llm.yaml \
  -n nim
```

#### 3.2 Test Reasoning Mode
```python
# tests/test_llm_reasoning.py
from openai import OpenAI

client = OpenAI(
    base_url="http://llm-nim.nim.svc.cluster.local:8000/v1",
    api_key="not-used"
)

response = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    messages=[
        {
            "role": "system",
            "content": "You are NetGenius Auto-Lab Coach. Detailed thinking on. "
                      "Respond with step-by-step reasoning."
        },
        {
            "role": "user",
            "content": "A student ran 'show ip route' and sees only connected routes. "
                      "They need to reach 10.0.2.0/24. What should they do next?"
        }
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

**Validation:**
- Response includes reasoning steps
- Latency < 2s for short queries
- No CUDA errors in pod logs

---

## Phase 4: LangGraph Orchestrator with Simulator Integration (Day 2, 0-8 hours)

### Deliverables
1. LangGraph workflow with all 5 nodes
2. **Simulator client integrated with existing WebSocket API**
3. **STS token handling for simulator auth**
4. Retrieval integration with pgvector
5. Socratic and Demonstrator modes working

### Implementation Steps

#### 4.1 Directory Structure
```
orchestrator/
├── app/
│   ├── main.py              # FastAPI + LangGraph runner
│   ├── graph/
│   │   ├── state.py         # StateGraph schema
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── retriever.py
│   │   │   ├── executor.py
│   │   │   ├── explainer.py
│   │   │   └── critic.py
│   │   └── workflow.py      # Graph assembly
│   ├── tools/
│   │   ├── simulator.py     # Simulator API client
│   │   └── retrieval.py     # pgvector queries
│   └── prompts/
│       ├── system.py
│       ├── planner.py
│       └── explainer.py
└── requirements.txt
```

#### 5.2 State Schema
```python
# app/graph/state.py
from typing import TypedDict, List, Literal
from dataclasses import dataclass

@dataclass
class Message:
    role: Literal["user", "assistant", "system"]
    content: str

@dataclass
class RetrievedDoc:
    content: str
    score: float
    source: str

class AgentState(TypedDict):
    session_id: str
    mode: Literal["socratic", "demonstrator"]
    goal: str
    messages: List[Message]
    observations: List[str]
    retrieved: List[RetrievedDoc]
    rubric: dict | None
    plan: str
    done: bool
    current_device: str
```

#### 5.3 Planner Node
```python
# app/graph/nodes/planner.py
from openai import AsyncOpenAI
from app.graph.state import AgentState
from app.prompts.planner import PLANNER_PROMPT

llm_client = AsyncOpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key="not-used"
)

async def planner_node(state: AgentState) -> AgentState:
    """Generate next step plan based on current state"""

    # Build context
    context = f"""
Goal: {state['goal']}
Mode: {state['mode']}
Recent observations:
{chr(10).join(state['observations'][-3:])}
"""

    if state['rubric']:
        unsatisfied = get_unsatisfied_criteria(state['rubric'])
        context += f"\nRemaining rubric items: {unsatisfied}"

    # Call LLM
    response = await llm_client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-nano-8b-v1",
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": context}
        ],
        temperature=0.7,
        max_tokens=300
    )

    plan = response.choices[0].message.content

    return {
        **state,
        "plan": plan,
        "messages": state["messages"] + [
            Message(role="assistant", content=plan)
        ]
    }
```

#### 4.4 FAISS Retriever Tool
```python
# app/tools/retrieval.py
import faiss
import pickle
import numpy as np
from pathlib import Path
from openai import AsyncOpenAI
from dataclasses import dataclass
import os

@dataclass
class RetrievedDoc:
    content: str
    score: float
    source: str
    lab_id: str

class FAISSRetriever:
    """FAISS-based document retriever"""

    def __init__(self, index_path: str, metadata_path: str):
        # Load FAISS index
        self.index = faiss.read_index(index_path)

        # Load metadata
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        # Initialize embedding client
        self.embed_client = AsyncOpenAI(
            base_url=os.getenv("EMB_BASE_URL"),
            api_key="not-used"
        )

        print(f"✅ FAISS retriever initialized: {len(self.metadata)} chunks loaded")

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.7,
        lab_id: str = None
    ) -> list[RetrievedDoc]:
        """Retrieve relevant documents using FAISS"""

        # Generate query embedding
        response = await self.embed_client.embeddings.create(
            model="nvidia/nv-embedqa-e5-v5",
            input=query
        )
        query_vector = np.array([response.data[0].embedding]).astype('float32')

        # Normalize for cosine similarity
        faiss.normalize_L2(query_vector)

        # Search FAISS index (get extra results for filtering)
        scores, indices = self.index.search(query_vector, top_k * 2)

        # Filter and format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS returns -1 for invalid indices
                continue

            doc = self.metadata[idx]

            # Filter by lab_id if specified
            if lab_id and doc.get("lab_id") != lab_id:
                continue

            # Filter by score threshold
            if score >= threshold:
                results.append(RetrievedDoc(
                    content=doc["content"],
                    score=float(score),
                    source=doc["source"],
                    lab_id=doc["lab_id"]
                ))

            # Stop when we have enough results
            if len(results) >= top_k:
                break

        return results

# Global retriever instance (initialized at app startup)
retriever = FAISSRetriever(
    index_path="/app/data/faiss/index.bin",
    metadata_path="/app/data/faiss/metadata.pkl"
)
```

#### 4.5 Retriever Node
```python
# app/graph/nodes/retriever.py
from app.tools.retrieval import retriever
from app.graph.state import AgentState

async def retriever_node(state: AgentState) -> AgentState:
    """Retrieve relevant docs using FAISS"""

    # Use the plan as query
    query = state["plan"]

    # Retrieve relevant documents
    retrieved = await retriever.retrieve(
        query=query,
        top_k=3,
        threshold=0.7,
        lab_id=state.get("lab_id")  # Filter by current lab if available
    )

    return {
        **state,
        "retrieved": retrieved
    }
```

#### 4.6 Simulator Client (Integration with Existing Simulator)
```python
# app/tools/simulator.py
import httpx
import websockets
import json
from datetime import datetime

class SimulatorClient:
    """Client for interacting with existing simulator via Infra API"""

    def __init__(self, base_url: str, sts_token: str = None):
        self.base_url = base_url  # Internal NLB endpoint
        self.sts_token = sts_token or os.getenv("SIMULATOR_TOKEN")
        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.sts_token}"}
        )

    async def create_session(self, exercise_type: str = "basic_router"):
        """Create a new simulator session"""
        response = await self.http_client.post("/api/simulators", json={
            "exercise_type": exercise_type,
            "user_id": "ai-coach-demo",
            "duration": "2:00:00",
            "resource_limits": {"cpu": "400m", "memory": "512Mi"}
        })
        data = response.json()
        return data["simulator_id"]

    async def connect_websocket(self, session_id: str):
        """Connect to simulator WebSocket"""
        ws_url = f"ws://{self.base_url.replace('http://', '')}/ws/simulator/{session_id}"

        return await websockets.connect(
            ws_url,
            extra_headers={"Authorization": f"Bearer {self.sts_token}"}
        )

    async def run_cli(self, session_id: str, device_id: str, command: str):
        """Execute CLI command via WebSocket (Demonstrator mode)"""
        ws = await self.connect_websocket(session_id)

        try:
            # Send CLI command with "enter" trigger
            await ws.send(json.dumps({
                "type": "cli",
                "device_id": device_id,
                "trigger": "enter",
                "text": command,
                "metadata": {"timestamp": datetime.utcnow().isoformat()}
            }))

            # Receive response
            response = await ws.recv()
            data = json.loads(response)

            if data["type"] == "cli_response":
                return {
                    "device": device_id,
                    "command": command,
                    "output": data["content"],
                    "prompt": data.get("prompt", ""),
                    "ts": data["metadata"]["timestamp"]
                }
            elif data["type"] == "error":
                raise Exception(f"Simulator error: {data['content']}")

        finally:
            await ws.close()

    async def get_running_config(self, session_id: str, device_id: str):
        """Get running configuration via command API"""
        # Use the structured command API
        response = await self.http_client.post(
            f"/sim/{session_id}/api/v1/devices/{device_id}/command",
            json={
                "path": "exec.show.running-config",
                "args": {}
            }
        )
        return response.json()

    async def get_command_history(self, session_id: str, device_id: str):
        """Get command history (via WebSocket or API if available)"""
        # This might require extension to existing simulator API
        # For now, return empty list or use another method
        return {"history": []}

    async def get_topology(self, session_id: str):
        """Get network topology"""
        response = await self.http_client.get(f"/sim/{session_id}/api/v1/topology")
        return response.json()
```

#### 4.7 Executor Node
```python
# app/graph/nodes/executor.py
from app.tools.simulator import SimulatorClient

simulator = SimulatorClient(
    base_url=os.getenv("SIMULATOR_BASE_URL"),
    sts_token=os.getenv("SIMULATOR_TOKEN")
)

async def executor_node(state: AgentState) -> AgentState:
    """Execute tools based on plan"""

    observations = []

    # Parse plan for commands (if Demonstrator mode)
    if state["mode"] == "demonstrator":
        commands = extract_commands_from_plan(state["plan"])

        for device, cmd in commands:
            try:
                result = await simulator.run_cli(
                    session_id=state["session_id"],
                    device_id=device,
                    command=cmd
                )
                observations.append(
                    f"Executed on {device}: {cmd}\nOutput: {result['output'][:200]}..."
                )
            except Exception as e:
                observations.append(f"Error executing {cmd}: {str(e)}")
    else:
        # Socratic mode: optionally fetch info for context
        if "show" in state["plan"].lower() and "running-config" in state["plan"].lower():
            # Fetch running config for analysis
            config = await simulator.get_running_config(
                state["session_id"],
                state["current_device"]
            )
            observations.append(f"Config snapshot: {config[:100]}...")

    return {
        **state,
        "observations": state["observations"] + observations
    }
```

#### 4.8 Dockerfile with FAISS Index
```dockerfile
# orchestrator/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FAISS index and metadata (pre-built)
COPY data/faiss/ /app/data/faiss/

# Copy application code
COPY app/ /app/app/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```txt
# orchestrator/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
langgraph==0.2.0
openai==1.3.0
httpx==0.25.0
websockets==12.0
faiss-cpu==1.7.4
numpy==1.24.3
pydantic==2.5.0
```

Build and push:
```bash
# Build locally (or in CI/CD)
cd orchestrator
docker build -t autolab-orchestrator:latest .

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag autolab-orchestrator:latest <account>.dkr.ecr.us-east-1.amazonaws.com/autolab-orchestrator:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/autolab-orchestrator:latest
```

#### 4.9 Workflow Assembly
```python
# app/graph/workflow.py
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import (
    planner_node, retriever_node, executor_node,
    explainer_node, critic_node
)

def should_continue(state: AgentState) -> str:
    """Decide next node based on state"""
    if state["done"]:
        return END
    return "planner"

# Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("executor", executor_node)
workflow.add_node("explainer", explainer_node)
workflow.add_node("critic", critic_node)

# Add edges
workflow.set_entry_point("planner")
workflow.add_edge("planner", "retriever")
workflow.add_edge("retriever", "executor")
workflow.add_edge("executor", "explainer")
workflow.add_edge("explainer", "critic")
workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "planner": "planner",
        END: END
    }
)

app = workflow.compile()
```

**Validation:**
- Graph compiles without errors
- Single agent turn completes in <2s
- **FAISS retrieval returns relevant chunks with <10ms latency**
- **Demonstrator mode executes commands via existing simulator WebSocket API**
- **Simulator connectivity via Internal NLB working**
- Docker image builds successfully with FAISS index embedded (~200MB total)

---

## Phase 5: Next.js Frontend on Vercel (Day 2, Evening / Day 3 Morning)

### Deliverables
1. Next.js app with terminal + tutor panel UI
2. WebSocket integration (simulator + orchestrator)
3. Interactive controls
4. **Deployed to Vercel with environment variables**

### Implementation Steps

#### 5.1 Project Setup
```bash
npx create-next-app@latest autolab-frontend --typescript --tailwind --app
cd autolab-frontend
npm install xterm @xterm/xterm-addon-fit zustand @shadcn/ui
```

#### 5.2 Environment Variables
```bash
# .env.local
NEXT_PUBLIC_ORCHESTRATOR_URL=https://ai-coach-alb-xxx.us-east-1.elb.amazonaws.com
NEXT_PUBLIC_SIMULATOR_URL=https://simulator-alb-xxx.us-east-1.elb.amazonaws.com
```

#### 5.3 Terminal Component
```tsx
// app/components/Terminal.tsx
'use client';

import { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from '@xterm/xterm-addon-fit';
import 'xterm/css/xterm.css';

interface TerminalPaneProps {
  sessionId: string;
  device: string;
}

export function TerminalPane({ sessionId, device }: TerminalPaneProps) {
  const termRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const term = new Terminal({
      theme: { background: '#1e1e1e', foreground: '#ffffff' },
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, Courier New, monospace',
      cursorBlink: true
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);

    if (termRef.current) {
      term.open(termRef.current);
      fitAddon.fit();
    }

    // Connect to simulator WebSocket via proxy or directly
    const simulatorWsUrl = process.env.NEXT_PUBLIC_SIMULATOR_URL
      ?.replace('https://', 'wss://')
      ?.replace('http://', 'ws://');

    const ws = new WebSocket(`${simulatorWsUrl}/ws/simulator/${sessionId}`);

    ws.onopen = () => {
      term.writeln('Connected to simulator...\r\n');
      term.write(`${device}> `);
    };

    let buffer = '';
    term.onData((data) => {
      if (data === '\r') {
        // Send CLI command
        ws.send(JSON.stringify({
          type: 'cli',
          device_id: device,
          trigger: 'enter',
          text: buffer,
          metadata: { timestamp: new Date().toISOString() }
        }));
        buffer = '';
        term.write('\r\n');
      } else if (data === '\x7F' || data === '\x08') {
        // Backspace
        if (buffer.length > 0) {
          buffer = buffer.slice(0, -1);
          term.write('\b \b');
        }
      } else {
        buffer += data;
        term.write(data);
      }
    });

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'cli_response') {
        term.write(msg.content + '\r\n');
        term.write(msg.prompt || `${device}> `);
      } else if (msg.type === 'error') {
        term.write(`\r\nError: ${msg.content}\r\n`);
      }
    };

    ws.onerror = (error) => {
      term.writeln('\r\nWebSocket error - check connection');
      console.error('WS Error:', error);
    };

    ws.onclose = () => {
      term.writeln('\r\nDisconnected from simulator');
    };

    xtermRef.current = term;
    wsRef.current = ws;

    return () => {
      ws.close();
      term.dispose();
    };
  }, [sessionId, device]);

  return <div ref={termRef} className="h-full w-full" />;
}
```

#### 5.4 Tutor Panel Component
```tsx
// app/components/TutorPanel.tsx
'use client';

import { useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  retrieved?: { content: string; source: string };
}

export function TutorPanel({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<'socratic' | 'demonstrator'>('socratic');
  const [loading, setLoading] = useState(false);

  const askAgent = async (question: string) => {
    if (!question.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const response = await fetch('/api/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question, mode })
      });

      const data = await response.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.plan,
        retrieved: data.retrieved?.[0]
      }]);
    } catch (error) {
      console.error('Agent error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 border-l">
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <h2 className="text-lg font-bold text-gray-900">Auto-Lab Coach</h2>
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setMode('socratic')}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              mode === 'socratic'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Socratic
          </button>
          <button
            onClick={() => setMode('demonstrator')}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              mode === 'demonstrator'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Demonstrator
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-100 ml-8'
                : 'bg-white shadow-sm'
            }`}
          >
            <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
            {msg.retrieved && (
              <div className="mt-2 p-2 bg-blue-50 rounded text-xs border-l-2 border-blue-400">
                <strong className="text-blue-900">Why this step:</strong>
                <p className="mt-1 text-gray-700">{msg.retrieved.content}</p>
                <p className="mt-1 text-gray-500 text-xs">
                  Source: {msg.retrieved.source}
                </p>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="bg-white p-3 rounded-lg shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <form onSubmit={(e) => {
          e.preventDefault();
          const input = e.currentTarget.elements.namedItem('question') as HTMLInputElement;
          askAgent(input.value);
          input.value = '';
        }}>
          <input
            name="question"
            type="text"
            placeholder="Ask a question..."
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </form>
      </div>
    </div>
  );
}
```

#### 5.5 API Route (Orchestrator Proxy)
```typescript
// app/api/agent/ask/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();

  const orchestratorUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;

  try {
    const response = await fetch(`${orchestratorUrl}/api/agent/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Orchestrator error:', error);
    return NextResponse.json(
      { error: 'Failed to contact AI coach' },
      { status: 500 }
    );
  }
}
```

#### 5.6 Main Lab Page
```tsx
// app/lab/[sessionId]/page.tsx
import { TerminalPane } from '@/app/components/Terminal';
import { TutorPanel } from '@/app/components/TutorPanel';

export default function LabPage({ params }: { params: { sessionId: string } }) {
  return (
    <div className="flex h-screen">
      {/* Terminal (left, 60%) */}
      <div className="w-3/5 bg-black p-4">
        <TerminalPane sessionId={params.sessionId} device="R1" />
      </div>

      {/* Tutor Panel (right, 40%) */}
      <div className="w-2/5">
        <TutorPanel sessionId={params.sessionId} />
      </div>
    </div>
  );
}
```

#### 5.7 Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard
# or via CLI:
vercel env add NEXT_PUBLIC_ORCHESTRATOR_URL
vercel env add NEXT_PUBLIC_SIMULATOR_URL
```

**Validation:**
- Terminal displays and accepts input
- WebSocket connection to simulator stable
- Tutor panel shows agent responses with retrieved snippets
- **Deployed to Vercel and accessible via HTTPS**
- **Environment variables properly configured**

---

## Phase 6: Rubrics & Grading (Day 3, 0-3 hours)

### Implementation Steps

#### 6.1 Rubric Definitions
```python
# app/rubrics/lab1_basic_router.py
RUBRIC = {
    "lab_id": "basic_router_v1",
    "name": "Basic Router Configuration",
    "criteria": [
        {
            "id": "enable_password",
            "desc": "Enable password configured",
            "weight": 0.2,
            "check": lambda state: "enable password" in state.running_config
        },
        {
            "id": "console_password",
            "desc": "Console password configured",
            "weight": 0.2,
            "check": lambda state: "line con 0" in state.running_config and "password" in state.running_config
        },
        {
            "id": "vty_secured",
            "desc": "VTY lines secured with login local",
            "weight": 0.3,
            "check": lambda state: "login local" in state.running_config
        },
        {
            "id": "motd_banner",
            "desc": "MOTD banner configured",
            "weight": 0.15,
            "check": lambda state: "banner motd" in state.running_config
        },
        {
            "id": "hostname",
            "desc": "Hostname changed from default",
            "weight": 0.15,
            "check": lambda state: state.hostname != "Router"
        }
    ],
    "pass_threshold": 0.8
}
```

#### 6.2 Evaluator
```python
# app/grading/evaluator.py
async def evaluate_rubric(session_id: str, rubric: dict) -> dict:
    """Evaluate current state against rubric"""
    session = sessions.get(session_id)
    device = session.get_device("R1")

    results = []
    total_score = 0.0

    for criterion in rubric["criteria"]:
        passed = criterion["check"](device.state)
        score = criterion["weight"] if passed else 0.0
        total_score += score

        results.append({
            "id": criterion["id"],
            "desc": criterion["desc"],
            "passed": passed,
            "weight": criterion["weight"],
            "score": score
        })

    return {
        "lab_id": rubric["lab_id"],
        "total_score": total_score,
        "pass_threshold": rubric["pass_threshold"],
        "passed": total_score >= rubric["pass_threshold"],
        "criteria": results
    }
```

**Validation:**
- Rubric evaluation returns correct scores
- Critic node stops when threshold met

---

## Phase 7: Integration Testing (Day 3, 2-5 hours)

### Test Scenarios

#### 7.1 Lab 1: Basic Router Config
```python
# tests/integration/test_lab1.py
async def test_basic_router_config():
    session_id = "test-lab1"

    # Student makes mistake: sets password but forgets login local
    await simulator.run_cli(session_id, "R1", "enable")
    await simulator.run_cli(session_id, "R1", "configure terminal")
    await simulator.run_cli(session_id, "R1", "line vty 0 4")
    await simulator.run_cli(session_id, "R1", "password cisco")
    await simulator.run_cli(session_id, "R1", "end")

    # Ask agent
    response = await agent.ask(
        session_id=session_id,
        question="I configured VTY password but still can't telnet. What's wrong?",
        mode="socratic"
    )

    assert "login" in response["plan"].lower()
    assert len(response["retrieved"]) > 0

    # Switch to demonstrator
    response = await agent.ask(
        session_id=session_id,
        question="Show me how to fix it",
        mode="demonstrator"
    )

    # Verify agent executed command
    config = await simulator.get_running_config(session_id, "R1")
    assert "login local" in config["config"]
```

**Validation:**
- All 3 labs complete successfully
- Agent response time <2s average
- Rubric scores accurate

---

## Phase 8: Production Deployment (Day 3, 5-7 hours)

### Implementation Steps

#### 8.1 ALB Ingress (AI Coach Cluster)
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autolab-ingress
  namespace: coach
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: <ACM_CERT_ARN>
spec:
  ingressClassName: alb
  rules:
  - host: autolab.example.com
    http:
      paths:
      - path: /api/agent
        pathType: Prefix
        backend:
          service:
            name: orchestrator
            port:
              number: 8080
      - path: /api/simulator
        pathType: Prefix
        backend:
          service:
            name: simulator
            port:
              number: 8000
```

#### 8.2 CloudWatch Logging (AI Coach Cluster)
```yaml
# k8s/fluentbit-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: amazon-cloudwatch
data:
  fluent-bit.conf: |
    [OUTPUT]
        Name cloudwatch_logs
        Match   kube.*
        region us-east-1
        log_group_name /aws/eks/autolab-coach
        auto_create_group true
```

**Validation:**
- HTTPS endpoints accessible
- Logs streaming to CloudWatch
- Health checks passing

---

## Phase 9: Demo & Documentation (Day 3, 7-10 hours)

### Deliverables

#### 9.1 Demo Script
```markdown
# Demo Script (3 minutes)

**Lab 1: Basic Router Config (60s)**
- Student configures hostname, enable password
- Forgets console login
- Agent (Socratic): "What command secures the console line?"
- Student tries "password cisco" only
- Agent (Demonstrator): "Let me show you" → types "login" command
- Shows retrieved snippet about line authentication

**Lab 2: Static Routing (60s)**
- Topology: R1 -- R2
- Student configures IPs
- Ping fails
- Agent: Suggests checking routing table
- Shows "no route to 10.0.2.0/24"
- Agent demonstrates: conf t → ip route ... → ping succeeds
- Rubric shows 100% score

**Lab 3: VLAN (60s)**
- Student creates VLAN 10
- Doesn't assign port
- show vlan brief shows empty
- Agent: "Which interface should be in VLAN 10?"
- Student: "Fa0/1"
- Agent: "Try: switchport access vlan 10"
- Verification succeeds
```

#### 9.2 Architecture Diagram
```
[Create diagram showing:
- Two EKS clusters (Simulator + AI Coach)
- GPU node in AI Coach cluster
- LLM + Embed NIMs
- Orchestrator with LangGraph workflow
- Internal NLB connectivity
- pgvector database (Neon/Vercel)
- Next.js frontend on Vercel
- Data flows with arrows]
```

#### 9.3 README
```markdown
# Auto-Lab Coach

AI-powered networking lab tutor using NVIDIA NIM on AWS EKS

## Architecture
- **LLM:** llama-3.1-nemotron-nano-8B-v1 (reasoning mode)
- **Embeddings:** nv-embedqa-e5-v5
- **Vector Store:** FAISS (in-memory, <10ms retrieval)
- **Orchestration:** LangGraph
- **Deployment:** Two EKS clusters (Simulator + AI Coach)
- **GPU:** g6.xlarge (NVIDIA L4, 24GB)

## Design Decisions

### Vector Store: FAISS vs pgvector
We chose **FAISS** for this hackathon because:
- **Dataset size:** ~150 static document chunks (not millions)
- **Latency:** <10ms in-memory vs. ~30-50ms database query
- **Infrastructure:** Zero external dependencies (embedded in container)
- **Time savings:** 2-3 hours vs. setting up RDS/Neon + networking
- **Single pod:** No concurrency requirements for demo

**Production migration path:** Scale to pgvector when:
- Multi-pod orchestrator deployment needed
- Document corpus requires dynamic updates
- Persistent storage with ACID guarantees required

### Two-Cluster Architecture
- **Cluster 1 (Existing):** Simulator with CPU nodes
- **Cluster 2 (New):** AI Coach with GPU node
- **Benefits:** Workload isolation, independent scaling, easy teardown post-hackathon

## Quick Start
1. Deploy AI Coach EKS cluster: `eksctl create cluster -f cluster.yaml`
2. Install NIMs: `./scripts/deploy-nims.sh`
3. Build FAISS index: `python scripts/build_faiss_index.py`
4. Build & deploy orchestrator: `./scripts/deploy-orchestrator.sh`
5. Deploy frontend to Vercel: `vercel --prod`
6. Access UI: https://autolab.vercel.app

## Demo
Watch our 3-minute demo: [link]

## Hackathon Compliance
✅ Two NVIDIA NIMs deployed on AWS EKS
✅ Embedding NIM used for retrieval grounding (nv-embedqa-e5-v5)
✅ Agentic application with LangGraph multi-node orchestration
✅ Integration with existing network simulator
```

**Validation:**
- Demo runs smoothly in <3 minutes
- All hackathon requirements met
- README includes architecture diagram + curl examples

---

## Risk Mitigation

### Primary Risks

1. **NIM deployment issues**
   - **Mitigation:** Pre-pull images on Day 0; test on smaller g5.xlarge as backup
   - **Plan B:** Record demo video; run live Q&A with pre-cached responses

2. **Latency exceeds 2s**
   - **Mitigation:** Reduce max_tokens to 300; use batch embeddings
   - **Plan B:** Show "thinking" animation; acceptable up to 3s for demo

3. **Simulator too complex**
   - **Mitigation:** Hardcode 20 commands; use regex patterns, not full parser
   - **Plan B:** Mock 3 lab scenarios with canned responses

4. **Integration time overrun**
   - **Mitigation:** Build simulator and orchestrator in parallel (Day 2)
   - **Plan B:** Use Postman mocks for simulator; focus on agent logic

---

## Success Criteria

### Must Have (Hackathon Submission)
- [x] 2 NIMs deployed on EKS
- [x] Retrieval pipeline working
- [x] LangGraph orchestrator completing agent loops
- [x] 1 lab demo end-to-end
- [x] 3-minute video
- [x] README with architecture

### Should Have (Better Demo)
- [x] 3 labs working
- [x] Both Socratic and Demonstrator modes
- [x] Rubric evaluation
- [x] Retrieved snippets shown in UI
- [x] Sub-2s latency

### Nice to Have (Bonus Points)
- [ ] Ghost typing animation
- [ ] Multi-device topology visualization
- [ ] Prometheus metrics dashboard
- [ ] Pre-commit hook linting

---

## Timeline Summary

| Phase | Duration | Day | Deliverable |
|-------|----------|-----|-------------|
| 1. Infrastructure | **3h** ⬇️ | 1 | AI Coach EKS + GPU + NLB connectivity |
| 2. Embedding + FAISS | **2h** ⬇️ | 1 | Embed NIM + FAISS index build |
| 3. LLM Deployment | 2h | 1 | LLM NIM + test |
| 4. Orchestrator | 8h | 2 | **LangGraph + FAISS + Simulator integration** |
| 5. Frontend (Next.js) | 5h | 2-3 | UI + WebSocket + Vercel deploy |
| 6. Rubrics | 3h | 3 | Grading logic |
| 7. Integration Tests | 3h | 3 | 3 labs validated |
| 8. Deployment | 2h | 3 | ALB + logging |
| 9. Demo/Docs | **4h** ⬆️ | 3 | Prompt tuning + Video + README |

**Total:** ~32 hours across 3 days (assumes 2-person team working in parallel on Days 1-2)

**Time Optimization with FAISS:**
- ⬇️ **Phase 1:** Saved 2h (no database setup)
- ⬇️ **Phase 2:** Saved 2h (simplified indexing workflow)
- ⬆️ **Phase 9:** Added 1h for extra prompt tuning (optional)
- **Net savings:** 3 hours freed up for optimization and polish

**Key Changes from Original Plan:**
- ✅ **Removed Phase 4** (Simulator) - already exists
- ✅ **Replaced pgvector with FAISS** - saves infrastructure time, improves latency
- ✅ **Phase 4** (Orchestrator) includes simulator integration via existing WebSocket API
- ✅ **Phase 5** uses Next.js and deploys to Vercel (not plain React)
- ✅ **Infrastructure** includes Internal NLB setup for simulator connectivity
- ✅ **Two-cluster architecture** for proper workload isolation

---

## Next Steps

1. **Review this plan** with team
2. ✅ **DECIDED: Two separate EKS clusters** (Simulator existing + AI Coach new)
3. ✅ **DECIDED: Simulator** - Use existing simulator, integrate via WebSocket API
4. ✅ **DECIDED: Frontend** - Next.js on Vercel
5. ✅ **DECIDED: Vector Store** - FAISS (in-memory, file-based) for hackathon speed
6. **Assign:** Infrastructure (Person A) vs. Code (Person B) for Day 1
7. **Prepare:**
   - Create AWS account for AI Coach cluster
   - Get NGC API key
   - Set up Vercel account
   - Gather STS token or credentials for simulator access
   - Prepare lesson/rubric content for FAISS indexing
8. **Kickoff:** Day 1 morning standup to confirm roles

**Pre-implementation Checklist:**
- [ ] NGC API key obtained
- [ ] AWS account ready with EKS permissions
- [ ] Vercel account set up
- [ ] Simulator cluster access confirmed (kubectl context, Internal NLB setup)
- [ ] STS token or auth method for simulator confirmed
- [ ] Lesson content prepared for embedding (~50-200 chunks)
