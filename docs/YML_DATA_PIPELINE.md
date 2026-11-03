# YML Feed → Product Facts: import design

**Status:** Proposed architecture only. The importer is **not implemented**.
**Candidate feed:** https://www.souz-pribor.ru/yml/any/feed.xml
**Validation status:** The remote feed content was not retrieved; actual tag distribution, item count, field completeness, and manufacturer/model values are **unknown**. Do not publish claims about its contents until a local copy is inspected.

## 1. Purpose and scope

The test assignment requires product-card generation for **two actual products**, with the technical values grounded in the supplied input. A YML catalog can provide data, but a source description is **not** a verified technical passport and must never be treated as proof of a specific configuration.

**MVP decision:** keep the public input contract (JSON) and the synchronous DeepSeek generation flow. Build a **small optional offline converter** from a user-provided local YML file into two JSON examples. Do not add a catalog crawler, feed scheduler, worker, Redis, RabbitMQ, database, or automatic bulk publishing.

## 2. Proposed processing

```text
Local feed.xml (obtained by user)
    |
    v
Safe XML parser (streaming, no external entities)
    |
    v
offer extraction + normalized fields
    |
    v
Fact classification + source references + data-quality warnings
    |
    +--> selection of 2 representative products
    |
    v
Existing ProductInput: name, manufacturer, specs, description
    |
    v
GenerationService → DeepSeek copy → validators → human review
```

Where a field is absent, keep an empty/missing marker. Never substitute model guesses for missing values.

## 3. Candidate field mapping — verify against actual XML

The following are **common YML element names**, not assertions about the linked feed. The format may contain a simplified, custom, or category-specific offer schema.

| Possible YML field | Proposed normalized field | Handling |
| --- | --- | --- |
| `offer/@id` | `source_offer_id` | Keep source identifier as string |
| `offer/name` | `name` | Prefer explicitly supplied product name |
| `offer/typePrefix` + `offer/model` | `name` fallback | Construct only if needed; report fallback |
| `offer/vendor` | `manufacturer` | Empty/missing remains unresolved |
| `offer/vendorCode` | `vendor_code` | Keep separate from `name` unless clearly part of model |
| `offer/description` | `description` | Strip markup safely; preserve technical meaning |
| `offer/param[@name]` | raw technical parameters | Preserve value and `unit` independently |
| `offer/categoryId` | `category_id` | Metadata only; do not infer measurement category blindly |
| `offer/url` | `source_url` | Traceability only |
| `offer/price`, `currencyId` | excluded from SEO copy | Do not invent availability, sale terms, or guarantees |

Do not silently collapse repeated `param` names; retain every source occurrence until a resolution rule is applied. Do not assume all `param` values describe a **single** configuration.

## 4. Provenance and classification

A proposed **internal** fact record (not a replacement for the simple external JSON API):

```json
{
  "field": "класс точности",
  "value": "1,5",
  "source": "offer.param[@name='класс точности']",
  "source_offer_id": "ILLUSTRATIVE_ONLY",
  "scope": "specific_execution",
  "evidence_status": "declared_in_feed",
  "review_status": "needs_review"
}
```

**This object is schematic. Its number, name and identifier do not originate from the referenced feed.**

Distinct dimensions are essential:

- **Evidence:** `declared_in_feed`, `from_document_text`, `missing`, or `conflict`. A value being declared in a feed does **not** mean it was independently checked against a manufacturer datasheet.
- **Scope:** `specific_execution`, `model_family`, `variant_option`, `unknown`.
- **Review status:** `ready_for_editor` / `needs_review` / `blocked`.

Example of a variant statement: a model-family description may advertise **RS-232 or RS-485** as possible interfaces. Neither interface should automatically be included as an installed feature of the particular offer. If the exact execution is not specified, mark interface as `variant_option` and add a warning.

**Conflict policy:** If `param` and description differ, keep both raw records, emit a conflict, and do not choose a technical value through LLM inference.

## 5. Safe normalization rules

1. Preserve the source text for audit, including original decimal separators, ranges, units and article numbers. Normalize only a **copy** for searching and checks.
2. Treat `0–1,6 МПа` and `0-1.6 MPa` as potentially equivalent only under explicit normalization rules; never automatically assume an engineering conversion or application equivalence.
3. Maintain distinct meanings of accuracy **class**, measurement **range**, maximum permissible **pressure**, power supply, and connection size.
4. Clean embedded HTML/CDATA without executing scripts or allowing source markup to control the output UI; preserve bullet lists as text where useful.
5. Do not derive manufacturer, certifications, warranty, compatibility, availability or delivery time from product category.
6. Detect empty / duplicate / overlong / malformed `offer` records, logging source ID and issue type, not full confidential content.
7. Use a safe XML parser (e.g., `defusedxml`) with a configured input-file size limit; use iterative parsing when volume warrants it. Disallow external entities and DTD-driven expansion.
8. Keep the initial tool **local-file-only**. A future URL-fetch mode would require host allowlisting, redirect restrictions, network timeouts and response-size limits to avoid SSRF and unbounded downloads.

## 6. Backward-compatible JSON contract

The public `POST /generate` contract remains:

```json
{
  "name": "Illustrative product name",
  "manufacturer": "Illustrative manufacturer",
  "specs": {
    "Illustrative parameter": "Illustrative value"
  },
  "description": "Illustrative source description."
}
```

This JSON is a **shape example**, not a real catalog item.

Source metadata may be stored in an optional preprocessing sidecar (e.g., one `*.evidence.json` per product) for review and evaluation. It should **not** be sent blindly to the text-generation model or appended to the existing API without a contract revision. Only facts safe for the specific product execution enter the confirmed `specs` map. Variant / uncertain facts are reported separately.

## 7. Two-product selection strategy

Once the feed is available locally:

1. Parse it, count offers, and measure the share with `name`, `vendor`, `description`, and meaningful parameters.
2. Choose **one information-rich** product with a clear specific execution.
3. Choose **one incomplete or variant-heavy** product to exercise conservative generation.
4. Export original source identifiers and normalized JSON, preserve any relevant warnings.
5. Review the extraction with the full source XML fragment; if needed, consult a manufacturer datasheet outside MVP.
6. Run both through the **same** generation interface and record outputs and check results.

No actual product examples are committed at this point because the feed has not been parsed. Synthetic test fixtures must be labeled synthetic.

## 8. Implementation backlog (not done yet)

- `scripts/yml_to_json.py`: CLI accepting a **local** `feed.xml` path and explicit offer IDs/selection criteria.
- `app/services/yml_adapter.py`: isolated parser and normalization, no network access.
- `tests/fixtures/yml/`: small synthetic XML fixture exercising optional fields, duplicate parameters, variants, CDATA and malformed records.
- Tests for deterministic mapping, no lost units, stable IDs, repeated param handling, parser errors and no invented fields.
- Two output examples based on **verified supplied product data**, then an input/output review report.

## 9. References

- Source catalog URL supplied for this exercise: https://www.souz-pribor.ru/yml/any/feed.xml (contents not inspected).
- General YML format documentation: https://yandex.ru/support/marketplace/ru/assortment/auto/yml-file
- General feed description: https://yandex.ru/support/marketplace/ru/assortment/auto/yml
