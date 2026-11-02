"""Minimal HTTP bootstrap for the AI-Helper MVP.

Only the liveness endpoint is implemented at this stage. The product-card
API and DeepSeek provider will be added in a separate implementation step.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI-Helper",
    version="0.1.0",
    description="B2B product-card generator (HTTP bootstrap; generation pending).",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Report API process liveness without checking external dependencies."""
    return {"status": "ok", "service": "ai-helper"}
