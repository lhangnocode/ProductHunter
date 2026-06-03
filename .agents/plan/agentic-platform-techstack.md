# Agentic Telesales Platform Tech Stack Plan

## Goal

Re-orient ProductHunter into an agentic telesales platform for shops and platform operators.

The work should be done step by step with verification after each layer:

1. Build the admin dashboard layout and UI surface first.
2. After the UI flow is clear, add agent services using LangChain and typed tools.
3. Wire the UI to agent services over HTTP and HTTP SSE.

## Product Direction

ProductHunter should become a platform where shops can manage product data and telesales operators can use an AI agent to answer customer questions during sales conversations.

The agent should use ProductHunter data and tools instead of answering from model memory:

- Search product database.
- Retrieve product details.
- Compare prices across shops/platforms.
- Retrieve product specs from trusted online sources when local specs are missing.
- Explain recommendations in a telesales-friendly answer.
- Show sources and tool traces for operator/admin verification.

## Layered Architecture

```text
Admin Dashboard UI
  -> HTTP APIs for admin/product/shop management
  -> Agent chat API over HTTP
  -> Agent streaming API over HTTP SSE

FastAPI Backend
  -> Admin APIs
  -> Product/search APIs
  -> Agent service APIs
  -> Existing SQLAlchemy models and product/search handlers

Agent Services
  -> LangChain orchestration
  -> Product/search/detail/price/spec tools
  -> Model provider client
  -> Stateless request handling for the first iteration

Data Layer
  -> PostgreSQL source of truth
  -> Typesense product search index
  -> Product/catalog tables
  -> Agent config/conversation/message tables
```

## Tech Stack Decisions

### Backend

Keep:

- FastAPI for HTTP APIs.
- SQLAlchemy async models and sessions.
- PostgreSQL as source of truth.
- Typesense for fast product search.
- Existing crawler/pipeline for ingestion and normalization.

Add:

- LangChain for agent orchestration.
- SSE support for streamed agent responses.

### Database Changes

No database modification is needed for the current next phase.

Rules:

- Do not add new tables until the UI and agent-service contracts are verified.
- Use existing `products`, `platforms`, `platform_products`, and `price_records` data for first agent tools.
- Keep conversation persistence and agent configuration out of scope until explicitly approved.
- Revisit migration tooling only when a real schema change is approved.

### Agent Orchestration

Use LangChain for the agent service layer.

Preferred structure:

```text
server/app/agent/
  service.py              # high-level use case orchestration
  events.py               # SSE event formatting and JSON-safe payloads
  model_client.py         # model-provider call boundary
  prompts.py              # system prompts, sales rules, fallback answers
  recommendations.py      # map tool outputs into recommendations and sources
  schemas.py              # agent request/response DTOs
  tool_runner.py          # LangChain tool lookup, execution, and tracing
  tools/
    search_products.py
    product_detail.py
    compare_prices.py
    online_specs.py
    price_history.py
    registry.py           # build LangChain StructuredTool list
```

Initial tools:

- `search_products`: search local product DB through existing search handlers.
- `get_product_detail`: fetch product, offers, prices, stock, image, and known specs.
- `compare_prices`: compare offers for one product or multiple products.
- `get_price_history`: summarize min/avg/current price from `price_records`.
- `get_product_specs_online`: fetch missing product specs from online search or approved sources.

Tool rules:

- Tools must return structured data.
- Agent final answers must include source metadata.
- Agent must not claim price/stock/spec data unless a tool supplied it.
- If data is stale or missing, the agent should say so.

### Model Provider

Keep provider configurable.

Options:

- Reuse current Qwen advisor provider for continuity.
- Add OpenAI-compatible model provider for agent service.
- Keep provider selection env-driven.

Suggested env keys:

```text
AGENT_PROVIDER=openai-compatible
AGENT_MODEL=...
AGENT_BASE_URL=...
AGENT_API_KEY=...
AGENT_TIMEOUT_SECONDS=60
AGENT_STREAMING=true
```

### UI

Use current React/Vite client and evolve `AdminPage`.

First UI layer:

- Convert admin page to a durable dashboard shell.
- Add left sidetab navigation.
- Keep existing Users and Payments functionality.
- Add placeholder sections for:
  - Overview
  - Shops
  - Products
  - Shop Offers
  - Agent
  - Conversations
  - Settings

The first implementation should be UI-only unless a section already has an existing API.

### API Transport

Use both normal HTTP and HTTP SSE.

HTTP:

- Create/read/update/delete admin data.
- Start conversation.
- Send non-streaming agent message.
- Fetch conversation history.
- Fetch agent configuration.

HTTP SSE:

- Stream agent response tokens.
- Stream tool status events.
- Stream final answer and source payload.

Suggested SSE event names:

- `agent.started`
- `tool.started`
- `tool.finished`
- `agent.token`
- `agent.sources`
- `agent.done`
- `agent.error`

## Implementation Sequence

### Phase 1: Admin Dashboard Layout

Goal:

Make the platform direction visible in the UI without changing database contracts yet.

Scope:

- Update `client/src/components/AdminPage.tsx`.
- Add left sidetab layout.
- Preserve existing Users and Payments behavior.
- Add UI placeholders for Shops, Products, Shop Offers, Agent, Conversations, and Settings.
- Keep state local unless route integration is needed.

Verification:

- `npm run lint` in `client`.
- `npm run test` in `client` if affected tests need updates.
- Manual browser check for admin dashboard layout.

Stop point:

- User verifies the dashboard layout and tab naming before backend work starts.

### Phase 2: Agent Service Foundation Without DB Changes

Goal:

Add the first backend agent-service layer using existing product data only.

Scope:

- Add LangChain dependency.
- Add `server/app/agent` package.
- Add typed tool interfaces over existing handlers:
  - `search_products`
  - `get_product_detail`
  - `compare_prices`
- Add non-streaming and SSE endpoints for the agent service.
- Do not add tables, migrations, conversation persistence, or agent config persistence.

Verification:

- Unit tests for tools with mocked/model-free responses.
- API test for response shape with mocked LLM call.
- SSE response-shape test for streamed tool and answer events.
- Manual request with a product question.

Stop point:

- User verifies tool behavior and response shape before streaming or persistence.

### Phase 3: Product And Shop Management APIs

Goal:

Let admins manage platform/shop products manually, separate from crawler-only ingestion.

Scope:

- Add admin APIs for shops/platforms.
- Add admin APIs for products.
- Add admin APIs for shop offers/platform products.
- Do not add schema changes unless explicitly approved.
- Add frontend service methods.
- Replace UI placeholders with tables/forms one section at a time.

Verification:

- Backend tests for CRUD endpoints.
- Frontend tests for service calls and key UI states.
- Manual admin flow: create shop, create product, create offer.

Stop point:

- User verifies product/shop management flow before agent service is built.

### Phase 4: Agent Service Skeleton With LangChain

Goal:

Add agent-service architecture without fully wiring UI streaming yet.

Scope:

- Add `server/app/agent` package.
- Add LangChain dependency.
- Add tool interfaces and first local tools:
  - `search_products`
  - `get_product_detail`
  - `compare_prices`
- Add non-streaming endpoint:
  - `POST /api/v1/agent/chat`
- Return answer, recommendations, sources, and tool trace.

Verification:

- Unit tests for tool functions.
- API tests for agent chat with mocked model provider.
- Manual request with a product question.

Stop point:

- User verifies agent tool behavior and response shape.

### Phase 5: Online Specs Tool

Goal:

Allow the agent to fetch product specs when local database specs are missing.

Scope:

- Add `get_product_specs_online` tool.
- Prefer approved sources or search API configuration.
- Cache retrieved specs if appropriate.
- Mark online specs as external and timestamped.

Verification:

- Tool tests with mocked online responses.
- Agent response includes source labels.
- Agent handles missing or conflicting specs safely.

Stop point:

- User verifies whether online spec lookup quality is acceptable.

### Phase 6: HTTP SSE Agent Streaming

Goal:

Make telesales interaction feel live in the dashboard.

Scope:

- Add SSE endpoint:
  - `GET` or `POST /api/v1/agent/conversations/{id}/stream`
- Stream model tokens and tool events.
- Add frontend SSE client.
- Add Agent tab chat UI.
- Show tool progress and final sources.

Verification:

- Manual stream test.
- Frontend interaction test if practical.
- Confirm reconnect/error behavior.

Stop point:

- User verifies UI/agent interaction before persistence and analytics expansion.

### Phase 7: Conversation Persistence And Agent Config

Goal:

Persist telesales conversations and make agent behavior configurable.

Scope:

- Add persistence for:
  - `agent_configs`
  - `agent_conversations`
  - `agent_messages`
- Choose migration workflow when this schema change is approved.
- Add admin Agent settings UI.
- Add Conversations UI.
- Persist messages, tool calls, sources, and operator feedback.

Verification:

- Migration tests or local migration run.
- Backend tests for conversation persistence.
- Manual conversation replay from admin UI.

Stop point:

- User verifies persistence and admin review workflow.

## First Confirmed Work Item

Start with Phase 1 only:

> Update the dashboard layout/UI to have sidetab navigation and placeholders for the future agentic platform sections, while preserving existing Users and Payments functionality.

No LangChain, new database tables, or agent APIs should be implemented until the user verifies the dashboard direction.

## Open Questions For Later Phases

- Should shops be separate from platforms, or should shops extend the existing `platforms` model?
- Should the agent be internal-only for telesales operators first, or also customer-facing?
- Which online source/search provider should power `get_product_specs_online`?
- Should agent provider reuse Qwen settings or use a new OpenAI-compatible provider config?
- Should SSE be implemented as native FastAPI streaming or with an SSE helper library?
