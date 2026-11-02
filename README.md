# AI-Helper — AI Product Card Assistant

AI-assisted draft generation for B2B product cards of industrial measuring instruments. Built around a simple rule: **technical specifications are source data, not model-generated facts**.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![LLM](https://img.shields.io/badge/LLM-DeepSeek-4C6EF5)
![Status](https://img.shields.io/badge/status-design%20%2F%20MVP%20planned-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

> **Current status:** architecture and README are being prepared. The application, API endpoints, web interface, and tests have **not yet been implemented**. This is a design-stage repository, not a runnable service.

## Project Description / Описание проекта

**EN:** AI-Helper is a lightweight service for preparing SEO-aware draft product descriptions from structured instrument specifications and excerpts of technical documentation. DeepSeek generates editorial text while Python preserves the authoritative specification values, validates response structure, and reports missing or uncertain data. The target user is a content manager in a B2B industrial equipment store.

**RU:** AI-Helper — небольшой сервис для подготовки черновиков карточек контрольно-измерительных приборов по входному JSON с характеристиками и фрагменту технического паспорта. DeepSeek помогает создавать SEO-текст и коммерческое описание, но **не определяет значения технических характеристик**. Исходные данные проходят проверку, а недостаток информации явно отражается в результате. Карточка остаётся черновиком для проверки контент-менеджером.

## Features / Возможности MVP (planned)

- JSON input through `POST /generate` and a simple browser form.
- SEO title, up to **70 characters**.
- SEO description, target **800–1,200 characters**; no artificial padding when reliable data is insufficient.
- Key technical specifications copied from input `specs`, never invented by LLM.
- **3–5** relevant search queries and a concise commercial block.
- Missing fields, warnings, and a validation status: `passed`, `warning`, or `failed`.
- DeepSeek integration using a configurable model and an API key in `.env`.
- `GET /health` for liveness checks, plus structured logs and a request ID.
- Timeouts, bounded retries for transient provider failures, and clear API errors.
- JSON and copy-friendly Markdown output.
- Offline unit/integration tests using a fake LLM provider.

**Outside MVP:** CMS, database, OCR, deployment, Redis, RabbitMQ, RAG, or a background worker. The generation service is designed to allow these integrations later without coupling the core logic to HTTP.

## Architecture / Архитектура

```text
             Web UI / API Client
                      |
                  FastAPI
            GET /health | POST /generate
                      |
             Input validation (Pydantic)
                      |
               GenerationService
               /              \
   Source-of-truth specs       DeepSeek client
       (Python only)           (editorial text)
               \              /
             Output validator
                      |
          Product card + warnings
             JSON / Markdown

      request_id + structured logging
```

**Trust boundary:** `name`, `manufacturer`, and `specs` come from the incoming JSON. The model may use `description` as context but must not introduce unsupported measurements, compatibility claims, certifications, delivery promises, or application-specific assurances. Structured specifications are assembled **deterministically**, outside the model output.

A validator can find many obvious problems, but it cannot mathematically prove semantic correctness of all generated prose. Content-manager review remains mandatory.

Detailed decisions: [MVP specification](docs/MVP_SPEC.md).

## Input & Output Contracts (planned)

Illustrative input **only** — the passport excerpt is incomplete and must not be treated as a real product datasheet:

```json
{
  "name": "Манометр показывающий DM 02",
  "manufacturer": "Манотомь",
  "specs": {
    "диапазон измерений": "0–1,6 МПа",
    "класс точности": "1,5",
    "присоединение": "G1/2",
    "диаметр корпуса": "100 мм"
  },
  "description": "Прибор предназначен для измерения избыточного давления..."
}
```

The planned response contains `request_id`, `status`, `seo_title`, `seo_description`, `specs`, `search_queries`, `commercial_block`, `missing_fields`, and `warnings`. An invalid request returns an explicit HTTP error instead of a fabricated card.

## Quick Start (after implementation)

> **Not executable yet:** the dependencies and application code referenced below will be added in the implementation stage. Commands are a preview of the intended local developer experience.

```bash
git clone https://github.com/SoldatovAlexander/AI-Helper.git
cd AI-Helper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set DEEPSEEK_API_KEY in .env
uvicorn app.main:app --reload
```

On Windows, activate the environment with `.venv\Scripts\activate`.

After implementation, the intended local entry points will be:

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Browser form |
| `GET /health` | Process liveness without a model request |
| `POST /generate` | Generate and validate a product card |
| `GET /docs` | FastAPI interactive API documentation |

Local checks (planned):

```bash
curl http://127.0.0.1:8000/health
pytest -q
```

## Configuration / Конфигурация

See [`.env.example`](.env.example). Store real credentials **only** in the ignored `.env` file or another secret manager; never commit API keys.

Default intended model: `deepseek-flash`. DeepSeek exposes an OpenAI-compatible API; the model name and base URL are configurable. The implementation will use structured JSON responses with additional local schema validation.

References: [DeepSeek API docs](https://api-docs.deepseek.com/) · [JSON Output](https://api-docs.deepseek.com/guides/json_mode/).

## Quality & Testing (planned)

- Reject invalid JSON and empty required identifiers.
- Clearly mark missing and blank optional fields.
- Preserve all source `specs` values byte-for-byte after input normalization.
- Enforce title length, SEO description target range, and 3–5 search queries.
- Detect unsupported technical claims where possible; flag unverified prose for human review.
- Handle blank/non-JSON model output, malformed response structure, timeout, authentication failure, and rate limits.
- Verify that raw API keys and complete technical passports are not written to logs.
- Exercise generation paths with a fake provider; no live API key needed for tests.

See [test matrix and acceptance criteria](docs/MVP_SPEC.md#test-matrix--acceptance-criteria).

## Documentation

| Document | Purpose |
| --- | --- |
| [MVP Specification](docs/MVP_SPEC.md) | Contracts, flow, logging, errors, test matrix, acceptance criteria |
| [`.env.example`](.env.example) | Example local configuration |
| [`.gitignore`](.gitignore) | Exclusions for local secrets and artifacts |

## Roadmap

1. **Documentation and architecture:** README, contracts, configuration template.
2. **MVP implementation:** FastAPI, DeepSeek adapter, generation, validators, health, UI, tests.
3. **Evaluation:** run on both employer-provided products; inspect accuracy and usability.
4. **Later, if justified:** extraction of passport facts, review workflow, persistent jobs, Redis cache or RabbitMQ queue.

The assignment mentions **two** provided products, but only one abbreviated example appears in the task text currently available. Two authentic sample outputs will be added when the complete product inputs are supplied. Synthetic examples, if used for tests, will be explicitly labeled.

## License

[MIT License](LICENSE) — Copyright © 2026 Alexander Soldatov.
