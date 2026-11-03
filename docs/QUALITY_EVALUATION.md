# Product card quality strategy & evaluation protocol

**Status:** Proposed evaluation plan. No benchmark has been run, no performance gains are claimed, and actual feed examples are not yet available.

## 1. Why baseline vs improved

The goal is not to prove that the LLM can write long SEO copy. The goal is to deliver a **reviewable, grounded B2B draft** without distorting instrument specifications.

### Baseline

- Pass an input JSON with raw `specs` and `description` to DeepSeek using a simple editorial prompt.
- Record the raw LLM narrative and extractable data.
- Do **not** publish its technical specifications as authoritative.

### Improved (target MVP)

- Normalize and classify facts before prompting.
- Separate **specific product execution** values from **model-family** capabilities and selectable options.
- Preserve structured specs from source JSON outside the LLM output.
- Generate only SEO and commercial text in one DeepSeek request.
- Parse structured JSON, check lengths and keywords, run technical-claim heuristics, generate warnings, require editorial review.

Use the same input material, model configuration and evaluation rubric for a fair comparison. Model responses may be nondeterministic; store prompt version, model ID, timestamps and the configuration parameters used.

## 2. Quality dimensions

| Dimension | Metric / check | Interpretation |
| --- | --- | --- |
| Structured-spec preservation | Number of source specification value mismatches | **Target: 0** |
| Unsupported technical claim rate | Unsupported specific claims / reviewed specific claims | Manual verification required; lower is better |
| SEO title | Unicode code-point length ≤70 | Strict deterministic check |
| SEO body | Length 800–1,200 characters | Desired; must **never** force unsupported filler |
| Search queries | Count 3–5, non-duplicates, relevant to the input | Automated + reviewer |
| Commercial applicability | Are usage scenarios grounded in source? | Reviewer rating with examples |
| Source completeness | Missing required-for-category fields / chosen checklist size | Missing is not automatically an error |
| Variant correctness | No option presented as installed on the offered execution | Reviewer and rule checks |
| Prompt injection resistance | Unauthorized instructions inside description are ignored | Adversarial fixture |
| Traceability | Every structured fact has source locator or missing marker | Should be auditable |
| Operational robustness | Errors, timeouts, status, and logs behave as documented | Offline unit/integration tests |

Only deterministic checks can be automatic approval gates. An overall `passed` status means **automated checks pass**, not that a certified technical audit has been performed.

## 3. Suggested evaluation worksheet

| Product ID | Input type | Baseline unsupported claims | Improved unsupported claims | Struct-spec mismatches | SEO checks | Review notes |
| --- | --- | --- | --- | --- | --- | --- |
| P1 (TBD) | Rich, specific execution | Pending | Pending | Pending | Pending | Requires feed extraction |
| P2 (TBD) | Sparse/variant-heavy | Pending | Pending | Pending | Pending | Requires feed extraction |

**TBD is deliberate:** there is no actual feed-derived evaluation at this stage. Two products suffice for a **demonstration**, not for a statistically valid general claim such as “hallucinations reduced by X%”. Additional synthetic fixtures check edge cases but must be reported separately from real-item evaluation.

## 4. Review procedure

1. Freeze the **exact** source input and its provenance for each product.
2. Produce baseline and improved outputs without manual corrections before scoring.
3. Split prose into **specific factual claims** vs generic editorial phrasing.
4. For each factual claim, label `supported`, `unsupported`, `contradictory`, `variant_overgeneralization`, or `unable_to_verify`.
5. Check explicit claims about measurements, classes, connections, supply, interfaces, certifications, warranties, compatibility and application.
6. Record whether a warning was raised **before** human review.
7. Have an editor rate readability, SEO utility and readiness to publish.
8. Compare outcomes in a short report, quoting only small source excerpts necessary to support the judgment.

Unverifiable claims should remain open for review and **not** be silently counted as true.

## 5. Test scenarios

| ID | Scenario | Expected behavior |
| --- | --- | --- |
| Q01 | Repeated `param` name with conflicting values | Preserve conflict + warning |
| Q02 | Interface offered as RS-232 **or** RS-485 | Do not claim both installed |
| Q03 | Missing manufacturer or model | Explicit missing data; no invention |
| Q04 | Range uses decimal comma and en dash | Values preserved or safely normalized in a separate derived field |
| Q05 | Parameter present only in description | Not promoted to authoritative `specs` without review |
| Q06 | Malicious instructions embedded in description | Treated as source content, never system instructions |
| Q07 | DeepSeek makes a new precise claim in SEO | Flag/reject on detection; editorial check remains |
| Q08 | Too little source material for 800 chars | Shorter warning-state draft instead of unsupported filler |
| Q09 | DeepSeek returns invalid/blank JSON | Controlled retry/error |
| Q10 | Mixed product family / exact variant statements | Separate model-level options from execution facts |
| Q11 | Feed URL unavailable | Local-file import error with no fabricated offers |
| Q12 | Large feed | Bounded memory/size; no unrestricted download |

## 6. Acceptance criteria for the test assignment

- Two genuine product inputs and draft outputs are versioned **only after actual source material is obtained**.
- The structured `specs` output matches validated source values exactly; no LLM “improvements” to numbers.
- Model does not receive an opportunity to fill missing specs.
- All generated sections are copy-friendly and clearly marked draft.
- Exact SEO limits and search query counts are checked, with documented warning behavior for incomplete sources.
- Errors, missing fields and API failures are visible, logged safely and covered by offline tests.
- README uses only claims proven by implementation and verification.

## 7. Further development (outside test scope)

- Automatic catalog-wide reporting, ingestion history and incremental updates.
- Validation against manufacturer passports and SKU-specific specification tables.
- Controlled human approval and downstream CMS integration.
- Redis for cache or job status, RabbitMQ for queued jobs if batch workload justifies them.
- Evaluation set expansion and regression tracking as prompt/model changes.

See [YML adapter design](YML_DATA_PIPELINE.md) and [prompt strategy](PROMPT_STRATEGY.md).
