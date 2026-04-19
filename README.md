# Enterprise Knowledge Agent 🤖

> **Multi-Agent RAG system** built with LangGraph + LlamaIndex + Qdrant + FastAPI + React
>
> Combined architecture from [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies) (Repo 1) + [Multi-Agentic-RAG](https://github.com/Abdullah-47/Multi-Agentic-RAG) (Repo 2) with production additions.

---

## Architecture

```
User Query
    │
    ▼
SafetyCheckAgent ──(blocked)──► "I can't help with that"
    │ (safe)
    ▼
RouterAgent ──► retrieval | web_search | direct
    │
    ├──(retrieval)──► RetrieverAgent (Qdrant hybrid dense+BM25)
    │                      │
    │              FactCheckAgent ──(fail)──► RewriterAgent ──► RetrieverAgent
    │                      │ (pass)
    │                      ▼
    ├──(web_search)──► WebSearchAgent (Tavily / DuckDuckGo)
    │
    └──(direct)──► SynthesizerAgent (no retrieval needed)
                       │
                       ▼
                  Final Answer + Sources + Agent Trace
```

## Agent Responsibilities

| Agent | Source | Role |
|---|---|---|
| `SafetyCheckAgent` | Repo 2 | Guardrails — blocks harmful/injection queries |
| `RouterAgent` | Repo 2 | Classifies query: retrieval / web_search / direct |
| `RetrieverAgent` | Repo 1 | Hybrid dense+BM25 Qdrant search + context compression |
| `RewriterAgent` | Repo 2 | Self-corrects bad queries (up to 2 attempts) |
| `FactCheckAgent` | Repo 2 | Verifies docs are sufficient before synthesis |
| `WebSearchAgent` | Repo 2 | Tavily / DuckDuckGo fallback for real-time info |
| `SynthesizerAgent` | Repo 1+2 | Generates final cited answer with memory |

## Tech Stack

```
Backend   FastAPI + LangGraph + LangChain + LlamaIndex
LLM       Groq (LLaMA 3) / OpenAI GPT-4o / Ollama (local)
Vectors   Qdrant (hybrid dense + BM25 sparse)
Embed     sentence-transformers/all-MiniLM-L6-v2 (free, local)
Observ.   LangSmith (end-to-end tracing)
Eval      RAGAS (context precision, recall, faithfulness)
Frontend  React.js + Tailwind CSS
Deploy    Docker + AWS EC2 + GitHub Actions CI/CD
```

---

## Quickstart (15 minutes)

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/enterprise-knowledge-agent.git
cd enterprise-knowledge-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — minimum required:
#   GROQ_API_KEY   (free at console.groq.com)
#   LANGCHAIN_API_KEY  (free at smith.langchain.com)
```

### 3. Start Qdrant (Docker)

```bash
docker run -d -p 6333:6333 qdrant/qdrant
# Dashboard → http://localhost:6333/dashboard
```

### 4. Start the backend

```bash
make dev
# API → http://localhost:8000
# Docs → http://localhost:8000/docs
```

### 5. Upload a document

```bash
make ingest FILE=data/hr_docs/sample_policy.txt
```

### 6. Ask a question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the employee notice period?"}'
```

---

## Full Docker Deploy

```bash
# Start everything: Qdrant + Backend + Frontend
make docker-up

# Backend  → http://localhost:8000/docs
# Frontend → http://localhost:3000
# Qdrant   → http://localhost:6333/dashboard
```

---

## Evaluation

Run RAGAS to measure retrieval quality:

```bash
make eval
# Outputs: context_precision, context_recall, faithfulness, answer_relevancy
```

Run before/after benchmark (generates the "improved accuracy by X%" number):

```bash
make benchmark
# Compares: simple RAG vs full multi-agent pipeline
# Saves:    data/benchmark_report.json
```

---

## Swapping the Domain

Change `core/prompts.py` `DOMAIN_CONTEXT` and replace files in `data/`:

```
Legal    → put contract PDFs in data/legal_docs/
Medical  → put clinical guidelines in data/
Finance  → put annual reports in data/
HR       → put policy documents in data/hr_docs/
```

No code changes required — the agent adapts to whatever you ingest.

---

## Swapping the LLM

Edit `.env`:

```bash
# Use Groq (free, fast — recommended for dev)
LLM_PROVIDER=groq
LLM_MODEL=llama3-8b-8192

# Use OpenAI GPT-4o
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o

# Use local Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

---

## Project Structure

```
enterprise-knowledge-agent/
├── main.py                    # FastAPI entry point
├── config.py                  # All settings via .env
├── requirements.txt
├── Makefile                   # make dev / test / eval / ingest
│
├── agents/
│   ├── graph.py               # LangGraph state machine (main orchestrator)
│   ├── router.py              # Query routing (Repo 2)
│   ├── retriever.py           # Hybrid search agent (Repo 1)
│   ├── rewriter.py            # Self-correcting query rewriter (Repo 2)
│   ├── fact_check.py          # Document relevance verifier (Repo 2)
│   ├── safety_check.py        # Guardrails (Repo 2)
│   ├── synthesizer.py         # Final answer generation (Repo 1+2)
│   └── web_search.py          # Tavily / DDG fallback (Repo 2)
│
├── core/
│   ├── llm_factory.py         # Swappable LLM provider (Repo 1)
│   ├── indexer.py             # Dual ingestion: LlamaIndex + LangChain
│   ├── retriever.py           # Qdrant hybrid retriever (Repo 1)
│   ├── compressor.py          # Context compression (Repo 1)
│   ├── memory.py              # Conversation memory (Repo 1)
│   ├── llamaindex_loader.py   # LlamaIndex PageIndex (NEW)
│   └── prompts.py             # Domain-swappable prompt templates
│
├── db/
│   ├── qdrant.py              # Qdrant client + collection setup
│   └── parent_store.py        # Parent-child chunk mapping
│
├── observability/
│   ├── tracer.py              # LangSmith tracing init (NEW)
│   └── metrics.py             # Accuracy + latency tracking (NEW)
│
├── ui/
│   └── src/components/
│       ├── ChatPanel.jsx      # Main chat UI
│       ├── WorkflowLog.jsx    # Live agent trace panel (Repo 2)
│       └── UploadKnowledge.jsx# PDF upload UI
│
├── eval/
│   ├── ragas_eval.py          # RAGAS scoring (NEW)
│   └── benchmark_report.py   # Before/after comparison (NEW)
│
├── tests/
│   ├── test_agents.py         # Unit tests per agent
│   └── test_rag.py            # Integration tests
│
└── deploy/
    ├── Dockerfile
    ├── docker-compose.yml     # Qdrant + backend + frontend
    ├── aws_deploy.sh          # One-time EC2 setup
    └── ci_cd.yml              # GitHub Actions pipeline
```

---

## Resume Bullet Points (fill in your actual RAGAS numbers)

After running `make benchmark`, replace X with your real numbers:

```
• Built self-correcting multi-agent RAG system using LangGraph with 6 specialised agents
  (router, retriever, rewriter, fact-check, safety, synthesizer), improving answer
  faithfulness by X% vs baseline RAG as measured by RAGAS evaluation framework

• Implemented dual ingestion pipeline combining LlamaIndex PageIndex and LangChain
  parent-child chunking with Qdrant hybrid dense+BM25 retrieval, reducing irrelevant
  context by X% via LLM-based compression

• Integrated LangSmith end-to-end tracing with custom latency/accuracy metrics dashboard;
  deployed Dockerised microservice on AWS EC2 with CloudWatch monitoring and GitHub
  Actions CI/CD achieving <2s p95 response latency
```

---

## Credits

- [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies) — modular RAG backbone, LLM factory, context compression
- [Multi-Agentic-RAG](https://github.com/Abdullah-47/Multi-Agentic-RAG) — multi-agent architecture, router, rewriter, fact-check, safety agents
- Production additions: LlamaIndex PageIndex ingestion, LangSmith observability, RAGAS evaluation, AWS CI/CD
