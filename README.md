# VeriSync

A verification tool for Visvesvaraya Technological University (VTU) notices. Students paste a forwarded WhatsApp or social media notice, and VeriSync determines whether it is **VERIFIED**, **CONTRADICTED**, or **UNVERIFIED**, displaying the official circular excerpt as evidence.

> **Note**: Base retrieval design is based on a reference prototype; credit the author, used with the guide's permission.

---

## Team Roles

| Role | Module Focus | Responsibilities |
|---|---|---|
| **P1** | Parsing & Preprocessing | Document parsing (PyMuPDF, RapidOCR), metadata extraction, chunking (`parser.py`, `metadata.py`, `chunker.py`) |
| **P2** | Indexing & Retrieval | Dense (ChromaDB) + sparse (BM25) search, retrieval evaluation (`index.py`, `retriever.py`, `evaluate.py`) |
| **P3** | Claim & Verification | LLM integration (Ollama / Qwen2.5), claim extraction, consistency verification (`llm.py`, `claim_extractor.py`, `verifier.py`) |
| **P4** | Rules, Verdict & UI | Forgery heuristic rules, decision logic, pipeline orchestration, Streamlit UI, repository (`forgery_rules.py`, `verdict.py`, `pipeline.py`, `app.py`) |

---

## Function Shapes Specification

Every module follows these agreed shapes:

| Function | Signature | Return Value Shape |
|---|---|---|
| `extract_claim` | `(message: str) -> dict` | `{"event", "exam", "new_date", "circular_no", "issuer"}` (None if missing) |
| `search` | `(text: str, k: int = 5) -> list[dict]` | `[{"text", "circular_no", "date", "file", "page", "score"}]` |
| `verify` | `(claim: dict, hits: list) -> dict` | `{"result": "supports" \| "contradicts" \| "not_found", "circular_no", "file", "page", "clause"}` |
| `check_forgery` | `(claim: dict, known_numbers=None) -> list[dict]` | `[{"rule", "severity": "hard" \| "soft", "detail"}]` |
| `decide` | `(result: str, flags: list) -> str` | `"Verified"` \| `"Contradicted"` \| `"Unverified"` |

---

## Setup Instructions

### Prerequisites
- Python 3.10 to 3.12
- [Ollama](https://ollama.ai/) installed and running

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Pull Ollama Model
```bash
ollama pull qwen2.5:7b-instruct
```

### 4. Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```

---

## How to Run

### Run Unit Tests
```bash
pytest
```

### Run Streamlit Application
```bash
streamlit run app.py
```

---

## Data Management
Official circular PDFs must be stored inside `data/circulars/`. Raw PDFs and circular scans are excluded by `.gitignore` and must never be committed to git.
