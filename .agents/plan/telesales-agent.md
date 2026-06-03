# Telesales Agent: Sales-Effectiveness Layer

## Goal

Add a sales-effectiveness reasoning layer on top of the agent skeleton defined in
`agentic-platform-techstack.md`. The base plan covers plumbing (HTTP/SSE, tools,
LangChain). This plan covers *how the agent sells*.

The agent must:

- Score and rank offers as a telesales operator would (deal strength, value, urgency).
- Frame comparisons as sales narratives, not raw tables.
- Anticipate and answer the objections customers actually raise in Vietnamese tech retail.
- Suggest next-step moves (upsell, cross-sell, alternative at lower budget).
- Speak Vietnamese natively. Prompts, templates, and tool descriptions are Vietnamese-first.
- Stay grounded: never invent stock, price, warranty, or spec data not produced by a tool.

## Relationship To Existing Plan

This plan is **additive**. It does not change:

- The layered architecture in `agentic-platform-techstack.md:26-51`.
- The data layer (PostgreSQL, Typesense, no new tables before Phase 7).
- The five base tools (`search_products`, `get_product_detail`, `compare_prices`, `get_price_history`, `get_product_specs_online`).
- The HTTP / SSE transport or event names.

It **extends**:

- `server/app/agent/prompts.py` — adds sales system prompts and Vietnamese templates.
- `server/app/agent/tools/` — enriches existing tools with sales-relevant fields (deal score, stock urgency, warranty).
- `server/app/agent/recommendations.py` → split into a sales-aware composer.
- `server/app/agent/schemas.py` — adds the telesales answer DTO.
- A new module family: `server/app/agent/sales/` for the new components.

It **slots in** between Phase 4 (agent skeleton) and Phase 6 (SSE streaming). Phase 5
(online specs) is unchanged; specs flow through the same composer.

## Sales-Effectiveness Pillars

### 1. Deal Scoring

Every offer gets a 0-100 deal score that combines:

- `discount_pct` from `current_price` vs `original_price` (or vs price-history median).
- `price_trend` from `price_records` (falling = better deal window).
- `stock_urgency` from `in_stock` and recency of last crawl.
- `price_vs_market` from comparing this offer to the same product on other platforms.

Output fields per offer:

```json
{
  "platform_product_id": "...",
  "platform_name": "CellphoneS",
  "current_price": 23990000,
  "original_price": 26990000,
  "discount_pct": 11.1,
  "deal_score": 78,
  "deal_reasons": ["Giá thấp hơn trung bình 90 ngày 6%", "Còn hàng, cập nhật 2 giờ trước"],
  "stock_urgency": "in_stock",
  "price_trend": "falling"
}
```

### 2. Value-For-Money Ranking

For comparison queries, rank alternatives by a value score, not just price:

```text
value_score = spec_density / price_normalized
```

Where `spec_density` is a per-category heuristic (e.g., for phones: battery mAh, RAM,
storage, refresh rate; for laptops: CPU benchmark, RAM, storage, display). Specs come
from `get_product_detail` first, then `get_product_specs_online` if missing.

The agent should never claim a value score without enough spec data; it falls back to
"giá tốt nhất trong các lựa chọn có cùng cấu hình" with a confidence flag.

### 3. Objection Handling

Pre-built Vietnamese response snippets for the most common telesales objections:

| Objection | Response template |
|---|---|
| "Đắt quá" | Khung giá thị trường + so sánh với 2-3 đối thủ + ghi chú khuyến mãi đang chạy |
| "Bên kia rẻ hơn" | So sánh chính sách bảo hành / trả góp / giao hàng + tổng chi phí thực tế |
| "Có hàng chính hãng không?" | Khẳng định từ dữ liệu tool + đường dẫn listing chính hãng |
| "Bảo hành thế nào?" | Trích từ tool nếu có; nếu không, nói rõ "chưa có thông tin từ shop, em sẽ xác minh" |
| "Có trả góp không?" | Trả lời dựa trên cờ `supports_installment` từ `platforms` nếu có; nếu không, đề xuất gọi shop |
| "Giao khi nào?" | Dùng thông tin giao hàng từ platform nếu tool trả về; nếu không, nói rõ |

Objection handlers must always cite the tool that produced the data.

### 4. Upsell And Cross-Sell Signals

After a recommendation, the composer should suggest:

- **Tier-up**: a higher-spec variant in the same product line, with price delta and one-line justification.
- **Tier-down**: a cheaper alternative if the user's question implies a tight budget (price ceiling mentioned, words like "rẻ", "tiết kiệm").
- **Bundle**: compatible accessories (case, screen protector, charger) — only if the product line is known to have them. Defer to Phase 7+ when a real bundle table exists.

In early phases, upsell/cross-sell are gated: only enabled when `agent_config.allow_upsell` (from Phase 7 schema) is true, or hard-coded `True` while persistence is out of scope.

### 5. Urgency And Closer Cues

Surface, in Vietnamese, only when supported by tool data:

- "Còn {n} sản phẩm, cập nhật {t} trước." when stock is low or crawl is fresh.
- "Giá đã giảm {pct}% trong {n} ngày qua." when price trend is falling.
- "Giá đang ở mức thấp nhất 90 ngày." when current price ≤ min(price_records).
- "Khuyến mãi kết thúc {date}." only when a `promotion_end_at` field exists on `platform_products` (future schema).

Never fabricate urgency. If no tool supports the cue, the composer omits the line.

### 6. Trust Signals

Each recommendation should end with a one-line trust block when available:

- "Hàng chính hãng, bảo hành {n} tháng tại {center}." — from tool data only.
- "Có thể đổi trả trong {n} ngày." — from `platforms.return_policy` if present.

## Vietnamese-First Design

### Prompt Language

- All system prompts in `prompts.py` are written in Vietnamese.
- Tool descriptions in `tools/registry.py` are Vietnamese.
- The few-shot examples in prompts are in Vietnamese and reference real Vietnamese
  e-commerce phrasing: "rẻ hơn không", "có trả góp không", "so với bên FPT thì sao".

### Output Style

- Default tone: telesales consultant, lịch sự, ngắn gọn, thân thiện.
- Numbers in VND formatted with thousand separators and "đ" suffix: `23.990.000đ`.
- Use "em" / "anh chị" naturally in the operator-facing answer; never in admin reviews.
- The final answer must always contain: gợi ý chính, bằng chứng (giá/spec/ưu đãi), nguồn.

### Bilingual Safety

Until Phase 7 introduces agent config, the agent assumes Vietnamese-only input.
If a query is detected as English (simple heuristic: >50% ASCII letters and no
Vietnamese diacritics), the agent answers in English but still produces the same
structured payload. No code-switching mid-answer.

## New Modules

```text
server/app/agent/
  sales/
    deal_score.py          # compute deal_score from offer + price history
    value_score.py         # value-for-money per category
    objections.py          # objection templates and routing
    upsell.py              # tier-up / tier-down / bundle suggestion
    trust.py               # warranty / return / authentic formatting
    urgency.py             # closer cues from stock / trend
  composer.py              # telesales-friendly answer shape (replaces recommendations.py)
  clarify.py               # clarification policy (smarter-agent.md cross-ref)
  trace.py                 # structured trace: intent -> plan -> tools -> verify -> answer
```

The base `recommendations.py` is refactored into `composer.py`; the old module is
deleted in the same commit.

## Enriched Tool Outputs

Existing tools grow optional sales fields; they remain backward-compatible.

| Tool | New optional fields |
|---|---|
| `search_products` | `deal_score_max` (best score across offers), `in_stock_count` |
| `get_product_detail` | `value_score`, `warranty_months`, `is_authentic`, `return_days` |
| `compare_prices` | ranked list with `deal_score`, `value_score`, `price_trend` per offer |
| `get_price_history` | `min_90d`, `max_90d`, `current_vs_min_pct`, `trend` (`falling`/`rising`/`flat`) |
| `get_product_specs_online` | `source_url`, `source_label`, `fetched_at` (already partly specified) |

If a field cannot be computed from current data, the tool returns `null` and the
composer omits the corresponding line — it does not invent it.

## Telesales Answer DTO

```json
{
  "answer_text": "Anh chị ơi, em gợi ý ...",
  "recommendations": [
    {
      "product_id": "...",
      "product_name": "iPhone 15 Pro Max 256GB",
      "best_offer": { "platform": "CellphoneS", "price": 23990000, "deal_score": 78 },
      "value_score": 82,
      "warranty_months": 12,
      "is_authentic": true
    }
  ],
  "alternatives": [
    { "product_id": "...", "reason": "Cùng tầm giá, pin lớn hơn 15%" }
  ],
  "objection_answers": [
    { "objection": "Đắt quá", "answer": "So với FPT Shop ...", "source_tool": "compare_prices" }
  ],
  "upsell": { "tier_up": null, "tier_down": null, "bundle": [] },
  "urgency_cues": ["Giá thấp nhất 90 ngày"],
  "trust": { "authentic": true, "warranty_months": 12, "return_days": 30 },
  "sources": [
    { "tool": "compare_prices", "platform": "CellphoneS", "url": "..." }
  ],
  "tool_trace": [
    { "tool": "search_products", "args": {"q": "iPhone 15 Pro Max"}, "duration_ms": 142 }
  ],
  "disclaimer": "Giá và tồn kho cập nhật lúc ..."
}
```

The disclaimer is mandatory whenever a recommendation includes price or stock data,
to make staleness obvious to the operator.

## Sales-Aware Prompts

System prompt skeleton (Vietnamese, full text drafted in implementation phase):

```text
Bạn là trợ lý tư vấn bán hàng cho điện thoại, laptop, phụ kiện.
Quy tắc bắt buộc:
- Mọi con số về giá, tồn kho, bảo hành, thông số phải đến từ tool. Không bịa.
- Khi tool trả về null, hãy nói "em chưa có thông tin này" thay vì đoán.
- Luôn trả lời với cấu trúc: gợi ý chính, bằng chứng, nguồn, disclaimer.
- Giọng điệu: lịch sự, ngắn gọn, dùng "em" với khách.
- Không so sánh sản phẩm ngoài danh sách tool trả về.
- Khi khách phản đối, dùng objection template tương ứng.
- Cuối câu trả lời phải có disclaimer về thời điểm cập nhật dữ liệu.
```

Few-shot examples are in Vietnamese and cover: simple find, price check, comparison,
objection ("bên kia rẻ hơn"), upsell request, and out-of-scope questions.

## Verification

Each sales-specific module has:

- Unit tests with deterministic inputs (no LLM in the loop).
- A small golden set in `server/app/agent/evals/sales/`:
  - "Gợi ý điện thoại tầm 10 triệu chơi game" → expect ≥1 recommendation with `value_score` set.
  - "So sánh iPhone 15 Pro Max và 16 Pro Max" → expect `recommendations.length == 2`, ranked by `value_score`.
  - "Bên FPT rẻ hẻn 500k, sao bên mình đắt hơn?" → expect `objection_answers` to contain a `compare_prices`-sourced answer.
  - "Có hàng chính hãng không?" → expect `trust.authentic == true` or explicit "chưa xác minh được".
- API tests with mocked LLM that assert the DTO shape and required fields.
- Sales-quality rubric (manual, weekly): answer relevance, objection coverage, no hallucinations, disclaimer present.

A new `server/app/agent/evals/run_sales_evals.py` script is runnable in CI; it is
gated off in early phases and turned on once Phase 4 of the base plan is verified.

## Implementation Sub-Phases

These sit between Phase 4 and Phase 6 of the base plan. They are independently
verifiable and each has a stop point.

### S1. Deal & Value Score Modules

Scope: `deal_score.py`, `value_score.py`, enriched tool outputs, unit tests.

Stop point: scoring functions are pure, deterministic, and covered by tests with
representative price-history fixtures.

### S2. Composer DTO And Refactor

Scope: `composer.py` replacing `recommendations.py`, sales DTO, sales-aware
prompts skeleton, manual request returning the new shape.

Stop point: a manually crafted question returns the new DTO end-to-end with
backward-compatible non-sales fields.

### S3. Objection, Trust, Urgency Modules

Scope: `objections.py`, `trust.py`, `urgency.py`, Vietnamese templates,
tests for each cue rule.

Stop point: a small Vietnamese question set produces the expected cues and
omits lines when underlying data is missing.

### S4. Upsell Module (Gated)

Scope: `upsell.py` with tier-up / tier-down logic, gated by a config flag that
defaults to off until Phase 7.

Stop point: upsell suggestion is generated only for product lines with enough
data; never empty or invented.

### S5. Sales Eval Harness

Scope: golden Q&A set in Vietnamese, `run_sales_evals.py`, CI integration
behind a marker file.

Stop point: harness runs locally and in CI; sales-quality rubric template
documented for the operator team.

## Out Of Scope

- Persisting agent conversations or upsell feedback (handled by base plan Phase 7).
- Customer-facing deployment of the agent (open question in base plan).
- Real-time price-prediction / "should I wait?" reasoning (requires richer data).
- Sentiment-aware tone adaptation (deferred until a real user-feedback loop exists).

## Open Questions

- Where does `value_score` get its category-specific spec weights from? Hard-coded
  constants for now, but a `category_spec_weights` table may be needed later.
- Should `objections.py` be configurable per shop (different shops face different
  objections), or stay platform-wide?
- Do we want the agent to suggest "gọi shop xác minh" explicitly, or leave that to
  the operator? This affects the disclaimer contract.
- Should the disclaimer be Vietnamese-only, or include the data timestamp in
  ISO 8601 for the admin UI?
- For Phase S1, do we have enough `price_records` history to compute `min_90d`
  reliably, or do we fall back to `min_available`?
