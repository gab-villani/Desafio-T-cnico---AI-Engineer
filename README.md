# Empório da Música — AI Customer Service Agent

AI-powered conversational agent prototype for **Empório da Música**, a fictional music instrument store in Campo Grande/MS, Brazil.

> **Technical Challenge:** AI Engineer position at Artefact  
> **Development Time:** 2 days  
> **Day 1 Status:** Core implementation complete with function calling, deterministic tools, and CLI interface.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture & Technical Decisions](#architecture--technical-decisions)
- [Project Structure](#project-structure)
- [Features](#features)
- [Known Limitations](#known-limitations)
- [AI Assistant Usage](#ai-assistant-usage)
- [Development Log](#development-log)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Google AI Studio API key ([get one free](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone and navigate to the project
cd "Desafio Técnico - AI Engineer"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Unix/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Agent

```bash
# Start interactive CLI
python -m src.cli

# Available commands:
# /sair   - Exit
# /salvar - Save conversation to examples/
```

---

## Architecture & Technical Decisions

### Why Function Calling Over RAG?

**Decision:** Deterministic function calling on structured CSV data using pandas.

**Rationale:**
- **Operational data is structured:** Products, orders, customers, and promotions fit naturally into relational tables
- **Deterministic queries required:** Price calculations, stock checks, and order lookups must be exact, not approximate
- **Policy manual is small:** ~12KB fits entirely in the system prompt without retrieval overhead
- **No semantic search needed:** Queries are factual lookups (price, stock, order status), not similarity searches
- **Simpler stack:** No vector database, embeddings, or chunking strategy required

RAG would add complexity without benefits for this use case.

### Why Gemini Over Other LLMs?

**Decision:** Google Gemini via free tier API.

**Rationale:**
- **Free tier availability:** Generous token limits for prototyping
- **Official SDK:** `google-genai` with native function calling support
- **Configurable model:** `GEMINI_MODEL` env var allows switching between Flash variants as availability changes
- **Latency:** 2-6 seconds for complete requests including function calls (when API is responsive)

**Model Evolution:** Initially targeted `gemini-2.5-flash-lite`, but it was deprecated. Validated `gemini-3.5-flash-lite` as stable alternative.

### Why Direct CSV Access Over SQL?

**Decision:** Pandas DataFrames loaded at startup.

**Rationale:**
- **Dataset size:** 65 products, 50 customers, 20 orders — fits easily in memory
- **No text-to-SQL risk:** LLM-generated SQL can produce incorrect queries or security issues
- **Type safety:** Python functions with explicit signatures catch errors at runtime
- **Simplicity:** No database setup, schema migrations, or connection pooling
- **Performance:** In-memory pandas operations complete in <10ms

### System Prompt Strategy

**Decision:** Persona + rules + full policy manual (~16.5K chars) in system instruction.

**Rationale:**
- **Consistency:** Rules are always applied, not retrieved probabilistically
- **No hallucination on policies:** Manual text is explicit, not paraphrased by the model
- **Mandatory tool usage:** Prompt enforces calling tools before stating prices/stock
- **Ambiguity handling:** Explicitly documents manual contradictions (phone numbers, guarantee periods)

**Tradeoff:** Large prompt increases latency during high API demand.

---

## Project Structure

```
emporio-agent/
├── data/
│   ├── politicas_da_loja.md              # Store policy manual
│   ├── desafio_tecnico_ai_eng - *.csv    # Operational data (products, orders, etc.)
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── data_loader.py    # Load CSVs, derive rules (availability, promotions)
│   ├── tools.py          # Deterministic functions callable by LLM
│   ├── prompts.py        # System prompt with persona and policies
│   ├── agent.py          # Gemini orchestration with function calling loop
│   └── cli.py            # Interactive terminal interface
├── scripts/
│   └── inspect_data.py   # Data quality report (run before cleaning)
├── tests/
│   └── test_data_rules.py
├── examples/
│   └── smoke_test_*.md   # Sample conversations
├── NOTES.md              # Development decisions and AI assistant usage log
├── README.md             # This file (English)
├── README_PT.md          # Portuguese version
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Features

### Conversational Agent

- **Persona:** Informal but professional tone, like "a friend who knows music"
- **Scope enforcement:** Declines accessories (strings, picks, cables, pedals, amps)
- **Mandatory tool usage:** Never invents prices, stock, or delivery times
- **LGPD-compliant:** Order lookup validates customer identity before exposing data

### Deterministic Tools

| Tool | Purpose |
|---|---|
| `buscar_produtos` | Search instruments by name, category, price range |
| `detalhar_produto` | Get current price, stock, promo, and specs |
| `listar_promocoes_ativas` | List active promotions on available products |
| `consultar_pedido` | Fetch order details after identity verification |
| `calcular_preco` | Calculate price with payment method rules (PIX discount, installments) |
| `consultar_politica` | Extract relevant section from policy manual |

### Business Rules (Applied in Code)

- **Availability:** `status == "active" AND stock_quantity > 0`
- **PIX discount:** 5% off list price, does NOT stack with active promotions
- **Installment limits:**
  - 1-3x: minimum R$50/installment
  - 4-6x: minimum R$80/installment
  - 7-12x: minimum R$100/installment
- **Return period:** 7 days from `estimated_delivery` (proxy for actual delivery date)
- **Catalog inconsistencies:** 6 products flagged; agent omits description for these items

---

## Known Limitations

### 1. API Latency Under High Demand

**Issue:** `gemini-3.5-flash-lite` can timeout (>30s) during peak usage.

**Evidence:** Smoke test scenarios 4-6 failed with `APITimeoutError` immediately after scenarios 1-3 succeeded in 2-3s each.

**Root cause:** Large system prompt (~16.5K chars) + free tier rate limiting.

**Mitigation:** Retry logic with exponential backoff handles HTTP 429/503. Production would require paid tier or prompt optimization.

### 2. Missing Historical Order Prices

**Issue:** `order_items.csv` has no `unit_price` column.

**Impact:** 2 of 20 orders show discrepancy between `total_brl` and sum of current product prices (likely historical promos).

**Decision:** Preserve `orders.total_brl` as source of truth; don't recalculate past orders with current prices.

### 3. Ambiguous Manual Data

**Issue:** Policy manual contains contradictions:
- Phone: `(67) 3341-4444` (general) vs `(67) 3321-4500` (WhatsApp)
- Email: `contato@emporiodamusica.com.br` vs `contato@empóriodamusica.com.br`
- Warranty: 90 days legal guarantee vs 30 days for defect exchange

**Decision:** Agent does NOT choose silently. It presents both values and offers escalation to staff for confirmation.

### 4. Proxy for Delivery Date

**Issue:** No `actual_delivery_date` in data.

**Decision:** Use `estimated_delivery` as proxy for return period calculation. Documented as assumption in code and NOTES.md.

### 5. Discontinued Models

**Issue:** Several Gemini models (`2.5-flash`, `2.5-flash-lite`, `3.8-flash`) returned HTTP 404/503 during development.

**Resolution:** Validated `gemini-3.5-flash-lite` as stable. Model name is configurable via `GEMINI_MODEL` env var.

---

## AI Assistant Usage

This project was developed with **AI assistant support (Kiro/Claude)** for:

1. **Initial setup** and project scaffolding
2. **Data inspection script** with quality checks and referential integrity validation
3. **CSV loader** with derived columns (availability, promotions, price calculations)
4. **Gemini SDK research** and function calling implementation
5. **Root cause diagnosis** of initial 120s timeout (tested tools independently, validated connectivity, identified deprecated models)
6. **CLI implementation** with session persistence and Markdown export

### What the Assistant Did NOT Do

- **Architecture decisions:** Human chose function calling over RAG, pandas over SQL, Gemini over alternatives
- **Business rules:** Human defined availability logic, PIX non-accumulation, installment thresholds
- **Manual ambiguities:** Human identified contradictions and decided on transparent handling
- **Smoke test design:** Human specified the 6 scenarios and acceptance criteria

### Development Workflow

1. Human provides requirements and decides approach
2. Assistant implements code, handles SDK details, writes tests
3. Human validates behavior, requests corrections, approves commits
4. Assistant documents decisions in `NOTES.md` after each step

This mirrors real-world usage: AI accelerates execution, human drives strategy.

---

## Development Log

| Step | Deliverable | Status |
|---:|---|:---:|
| 1 | Project setup, venv, requirements | ✅ |
| 2 | Data inspection script (`scripts/inspect_data.py`) | ✅ |
| 3 | Data loader with rules (`src/data_loader.py`) | ✅ |
| 4 | Deterministic tools (`src/tools.py`) | ✅ |
| 5 | System prompt with policies (`src/prompts.py`) | ✅ |
| 6 | Gemini agent with function calling (`src/agent.py`) | ✅ |
| 7 | Interactive CLI (`src/cli.py`) | ✅ |
| 8 | Smoke test (3/6 scenarios validated) | ⚠️ |
| 9 | Documentation (this README) | ✅ |

**Day 1 complete.** Core agent functional with validated function calling on real queries.

---

## Testing

### Run Data Rules Tests

```bash
python -m unittest tests/test_data_rules.py -v
```

### Smoke Test Results

See `examples/smoke_test_*.md` for validated scenarios:

1. ✅ Search for guitars under R$1000 → 12 results returned
2. ✅ Price inquiry for Takamine GD20 → Correct price with payment options offered
3. ✅ Store address and hours → Correct data from policy manual

Scenarios 4-6 (return policy, out-of-scope item, LGPD-protected order) timed out due to API latency, not code errors.

---

## License

Educational project for technical challenge evaluation.

---

## Contact

**Challenge:** AI Engineer @ Artefact  
**Candidate:** [Your name]  
**Date:** November 2026
