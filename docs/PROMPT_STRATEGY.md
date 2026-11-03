# DeepSeek prompt strategy: grounded, one-pass SEO copy

**Status:** Design proposal; prompt has **not** been integrated or evaluated against DeepSeek yet.

## 1. Decision

Use a **single generation request** per normal product-card draft. Let Python own the authoritative `name`, `manufacturer`, and `specs`. Let DeepSeek generate only:

- `seo_title`
- `seo_description`
- `search_queries`
- `commercial_block`

The prompt itself is a versioned artifact at [`prompts/product_card_v1.md`](../prompts/product_card_v1.md). The model should receive input facts as an explicitly delimited **data payload** (not as additional system instructions). The raw YML or HTML description is untrusted.

## 2. Editorial constraints

- Clear, technically restrained Russian for procurement specialists and B2B content managers.
- SEO title: **up to 70 characters**.
- SEO description: **target 800–1,200 characters**; do not invent details to reach 800.
- **3–5** distinct, relevant natural-language search queries.
- Commercial paragraph: intended user and supported use cases **only when source data justifies them**.
- No generic assertions about calibration, warranties, certificates, operating environments, compatibility or delivery terms if unsupported.
- If data is insufficient, return empty or concise copy plus a reason; Python adds corresponding warnings.

## 3. Three layers of information

| Layer | Example | How model may use it |
| --- | --- | --- |
| Confirmed for exact execution | Instrument has a specific connection size in `specs` | Describe precisely without changing value |
| Model-family / variant option | RS-232 or RS-485 selectable in the family | Explicitly mention only as possible variants, not features installed in this offer |
| Missing / unverified | A warranty duration not provided | Must not assert |

The adapter may choose to **exclude variant facts** from the MVP prompt entirely where the execution cannot be established. It is safer to omit such facts than to blur scopes.

## 4. Response contract

Raw LLM output is parsed as JSON and validated by Pydantic. Expected structure:

```json
{
  "seo_title": "text or empty string",
  "seo_description": "text or empty string",
  "search_queries": ["query 1", "query 2", "query 3"],
  "commercial_block": "text or empty string"
}
```

The strings above are **placeholders**, not real generated content.

Important: JSON mode helps with syntactic JSON correctness but **does not enforce the full application schema**. The service must detect empty responses, parse failure, schema mismatch, SEO length mismatch, wrong keyword count, and suspicious technical claims. Hard truncation is prohibited if it changes the meaning or cuts units and numbers.

A detected technical contradiction must prevent the result being labeled automatically safe. A deterministic number/unit heuristic cannot prove that all prose is correct; editorial review remains necessary.

## 5. Source-preserving evaluation

During implementation, compare this prompt against a simple baseline prompt using the **same** two source products, config and rubric, recording outcomes in [QUALITY_EVALUATION.md](QUALITY_EVALUATION.md).

Store only safe metadata in logs: request ID, model, prompt version, attempts, token counts, latency, warning count and sanitized provider errors. Never log raw passports, full prompts or credentials by default.

## 6. Prompt revisions

Keep `product_card_v1.md` immutable once a tested release is tagged. Later modifications should be committed with an explicit version bump and a small regression suite. Avoid fine-tuning, RAG or multi-agent orchestration for this test assignment.
