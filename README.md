# Empório da Música — Customer Support Agent

A Python prototype of a text-based customer support agent for the fictional Empório da Música music store in Campo Grande, Brazil. The agent uses Google Gemini to understand customer requests and deterministic Python tools to look up catalog, order, pricing, and store-policy information.

> **Language note:** This is the primary README and is written in English. See [README.pt-BR.md](./README.pt-BR.md) for the Portuguese copy.

## Requirements

- Python 3.11 or newer
- A Google Gemini API key and a model identifier available to your account
- Internet access when sending requests to Gemini

## Setup

Run these commands from the repository root.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the repository root and add your Gemini credentials:

```dotenv
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=your_available_gemini_model
REFERENCE_DATE=2026-03-01
```

`GEMINI_API_KEY` and `GEMINI_MODEL` are required. Choose a model currently available to your Google AI Studio account; model availability can change. `REFERENCE_DATE` is optional and defaults to `2026-03-01`. It is used by the prototype's date-related business rules.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the same `.env` file in the repository root.

## Run the application

### Command-line interface

Start a Portuguese conversation:

```bash
python src/cli.py
```

Start an English conversation:

```bash
python src/cli.py --idioma en
```

The CLI also accepts `--idioma pt-BR`. Type a message and press Enter. Use `/salvar` to export the current conversation as a Markdown file in `examples/`, or `/sair` to end the session. The CLI stores its session history in `.session_history.json`.

### Web interface

Start Streamlit from the repository root:

```bash
streamlit run ui/app.py
```

Open the local URL printed by Streamlit. The sidebar language selector switches between Portuguese (`pt-BR`) and English (`en`); the interface defaults to Portuguese. The UI can start a new conversation and load saved conversations from `chat_history/`.

## Run the focused data-rule tests

The following test checks deterministic data-loading and business-rule behavior without calling the Gemini API:

```bash
python -m unittest discover -s tests -p test_data_rules.py
```

Other tests may make live Gemini requests and require valid credentials, network access, and sufficient API quota.

## Project structure

```text
src/
  agent.py       Gemini orchestration, conversation context, and tool-call loop
  cli.py         Command-line interface and session history
  data_loader.py CSV loading, normalization, derived fields, and integrity checks
  prompts.py     Agent instructions and store-policy context
  tools.py       Deterministic catalog, order, payment, and policy tools
ui/
  app.py         Streamlit chat interface and saved conversations
data/
  *.csv          Product, category, customer, order, order-item, and promotion data
  politicas_da_loja.md
                 Store policy manual
examples/        Sample conversations and CLI exports
tests/           Data-rule, privacy, language, and UI tests
```

## Technical decisions

The agent uses Gemini function calling to select from a small set of explicit operations. Python performs the actual filtering, validation, identity checks, and arithmetic. The CSV dataset is loaded with pandas; the policy manual is included in the system context and can also be queried by topic. The project does not use a vector database or text-to-SQL because its supplied data is small, structured, and locally available.

For the detailed rationale, trade-offs, and assumptions, see:

- [Technical decisions (English)](./TECHNICAL_DECISIONS.md)
- [Decisões técnicas (Português)](./DECISOES_TECNICAS.md)

## Important behavior and limitations

- Product availability requires both `status == "active"` and positive stock.
- Only promotions marked active in the source data are treated as active; the promotion CSV has no validity dates.
- Price and installment calculations are performed in Python. The implemented rules do not combine the PIX discount with an active promotion.
- Order details are returned only after the supplied email address or phone number matches the customer associated with that order. Failed validation uses a generic response.
- Inconsistent catalog descriptions are withheld by the product tools; a notice is returned instead.
- The policy source contains conflicting contact and warranty details. The prompt directs the agent not to silently resolve these conflicts and to recommend confirmation where appropriate.
- The agent depends on an external Gemini API. Network issues, rate limits, model availability, and provider latency can affect responses. The code retries selected temporary failures and limits the tool-call loop; these safeguards do not guarantee availability or low latency.
- This is a prototype, not a production service. It does not integrate with a live inventory system, payment provider, shipping carrier, complaint-management system, or ERP.

## AI coding assistant disclosure

AI coding assistance (Kiro/Claude) was used during the project's initial scaffolding, data inspection, implementation, testing, and debugging. Findings were reviewed and inaccurate early claims were corrected. The development notes and audit documents record those corrections and the assumptions that remain unapproved.

