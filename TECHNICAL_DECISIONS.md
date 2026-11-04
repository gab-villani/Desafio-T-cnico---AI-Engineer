# Technical Decisions and Rationale

This document explains why the project uses its current methods and technologies, what alternatives were considered, and which assumptions should be revisited before production use.

## 1. Agent architecture: Gemini function calling with deterministic Python tools

Gemini interprets the customer's request and chooses whether to call one of the declared tools. The application executes the selected Python function and returns its result to the model, which then prepares the customer-facing response.

This division was chosen because natural-language understanding benefits from an LLM, while prices, availability, order lookup, and identity checks must be derived from the supplied data and rules. Keeping those operations in Python makes them inspectable and testable, and avoids asking the model to invent or calculate operational facts.

The tool surface is explicit and limited to product search, product detail, active promotions, price calculation, order lookup, and policy lookup. Order lookup requires matching an email address or phone number to the customer linked to the requested order; failure returns a generic message that does not confirm whether the order exists.

The loop is bounded to six tool-calling iterations. Selected rate-limit or temporary-unavailability errors (429/503) receive at most two application attempts with a short exponential backoff; each Gemini request has a 60-second timeout. These are resilience limits, not an availability guarantee.

### Why not a fully autonomous ReAct agent?

The prototype has a small, known set of customer-support operations. An explicit function schema and bounded orchestration make the allowed actions easier to reason about than an open-ended planner with dynamically selected actions.

## 2. Model provider and SDK: Google Gemini through `google-genai`

The Gemini API and the official `google-genai` Python SDK were selected to provide a hosted language model with function-calling support. Provider credentials and the model identifier are configuration, not constants in the source code, so a model can be changed without editing the agent implementation.

The choice also avoids requiring local model hardware or deployment infrastructure for this evaluation prototype. It introduces external dependencies: an API key, network connectivity, quota, provider availability, and potentially variable latency. A production deployment should review cost, privacy, data-retention, latency, and service-level requirements before selecting a provider and model.

## 3. Structured data: CSV files loaded with pandas

The supplied operational data is a small, finite set of structured CSV tables. pandas provides direct filtering and joins without introducing a database service or query-generation layer.

`data_loader.py` centralizes loading and in-memory preparation. It trims text, parses date columns, derives availability and active-promotion pricing fields, normalizes customer contact values for matching, and validates identifiers, references, and basic numeric constraints. The source CSV files are not rewritten.

### Why not text-to-SQL or a database?

The dataset is small and already supplied as CSV, so loading it locally is straightforward and avoids schema-generation errors, database setup, and unnecessary infrastructure. If the dataset grows, changes frequently, or needs concurrent writes, a database with explicit access controls and migrations would be a more suitable source of truth.

### Why not RAG or a vector database for policies?

The policy manual is a compact Markdown document. It can be included directly in the system context, while `consultar_politica` extracts a named policy section for a targeted lookup. For this scale and content, embeddings and a vector store would add complexity without a demonstrated retrieval benefit. A larger or frequently updated knowledge base could justify a retrieval system with source citations and evaluation.

## 4. Business rules remain in code

Python tools compute prices and installment values, apply availability filters, validate payment inputs, and perform order-identity checks. The model receives the results and explains them; it is instructed not to calculate discounts or installments mentally or provide operational facts without a tool result.

This design keeps arithmetic reproducible and places rules in functions that can be unit tested. It does not make the current business assumptions authoritative: rules such as promotion stacking and installment minimums should be verified with the store before real customer use.

## 5. Prompt design and policy ambiguity

`prompts.py` combines a stable persona and operational instructions with the store's policy manual. The prompt requires tool use for prices, stock, order status, delivery information, promotions, and policy questions. It also covers out-of-scope requests, catalog inconsistencies, privacy, complaints, and conflicting statements in the manual.

The conflicting phone, email, and warranty statements are not silently resolved by the agent. Where the source is ambiguous, the intended behavior is to be transparent and offer human confirmation. The prompt is not a substitute for fixing the source manual; authoritative policy data should be confirmed by the business owner.

## 6. Interfaces and persistence

The core `responder` function is separate from the interfaces. This lets both the CLI and Streamlit UI use the same agent behavior without duplicating business logic.

- **CLI:** useful for a minimal, direct evaluation workflow. The session history is stored locally in `.session_history.json`; `/salvar` exports the conversation to `examples/`.
- **Streamlit:** provides a simple browser-based chat, language selector, new-chat action, and loading of saved conversations. UI conversation files are stored locally under `chat_history/`.

These are prototype-level local persistence mechanisms, not multi-user storage. They do not provide authentication, access control, encryption-at-rest guarantees, retention management, or concurrent-user coordination.

## 7. Data-quality safeguards and explicit assumptions

- Availability means active status and positive stock. A zero-stock active product is not offered as available.
- Promotions rely on the source `is_active` flag because the CSV has no promotion start or end dates.
- Six identified catalog entries have a mismatch between the product name and descriptive text. The data loader flags them, and product tools omit their description while returning a notice. This is a conservative presentation choice, not a correction of the source records.
- `estimated_delivery` is not proof of actual receipt. Date-based return guidance that relies on it is therefore an approximation.
- Contact matching normalizes email and phone formatting to make verification practical. The generic failure response limits order-existence disclosure, but this prototype is not a complete authentication system.
- PIX and promotion discounts do not stack in the implementation. Installment minimums are implemented as R$50 for 1–3 installments, R$80 for 4–6, and R$100 for 7–12. These assumptions require business approval; the policy manual itself contains overlapping payment rules.
- `REFERENCE_DATE` defaults to `2026-03-01` for date-related behavior. Set it explicitly for reproducible evaluation; do not treat the default as a live clock.

## 8. Technology summary

| Area | Choice | Reason |
|---|---|---|
| Language | Python | Required by the assignment and well suited to data handling and integration. |
| LLM | Google Gemini | Hosted model with function-calling capability. |
| SDK | `google-genai` | Official Python integration for the Gemini API. |
| Tabular data | pandas and CSV | Simple, local processing for the small supplied dataset. |
| Configuration | `python-dotenv` | Loads API credentials and runtime settings from `.env`. |
| Browser UI | Streamlit | Minimal web chat without a separate frontend stack. |
| Policy retrieval | Markdown in prompt plus topic-based extraction | Sufficient for a compact, stable policy manual. |
| Conversation persistence | Local JSON files | Simple prototype persistence; not intended for multi-user production. |

## 9. Production follow-up

Before production use, confirm the business assumptions and resolve the conflicting policy source; replace local files with approved, access-controlled operational data; implement proper authentication and authorization for customer records; add observability and privacy-safe logging; evaluate model quality and prompt-injection resilience; and establish latency, cost, retention, and availability requirements.

