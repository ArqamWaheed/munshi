"""All settings come from the environment (.env is loaded once, here).

Versions/URLs below were verified on 2026-10-16; see playbook_technical.md section 3.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


# --- Gemma 4 on the Gemini API, OpenAI-compatible endpoint (beta) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # TODO: https://aistudio.google.com/apikey
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
GEMMA_RPM = _f("GEMMA_RPM", 14)  # free tier ~15 RPM / 1,500 RPD (secondary source; check AI Studio)
GEMMA_JSON_MODE = os.getenv("GEMMA_JSON_MODE", "1") == "1"  # unverified for Gemma: auto-dropped on HTTP 400
GEMMA_THINKING_LEVEL = os.getenv("GEMMA_THINKING_LEVEL", "minimal")  # Gemma docs: "minimal"=off, "high"=on
GEMMA_ACTUAL_PRICE = (0.0, 0.0)  # USD per 1M tokens (in, out) on the free tier
GEMMA_LIST_PRICE = (0.09, 0.30)  # OpenRouter paid google/gemma-4-26b-a4b-it, read 2026-10-16

# --- Tinker (fine-tuned parser) ---
TINKER_API_KEY = os.getenv("TINKER_API_KEY", "")  # TODO: https://tinker.thinkingmachines.ai/keys
TINKER_OAI_BASE_URL = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"
TINKER_BASE_MODEL = os.getenv("TINKER_BASE_MODEL", "Qwen/Qwen3.5-4B")
TINKER_MODEL_PATH = os.getenv("TINKER_MODEL_PATH", "")  # TODO after training: tinker://<run>/sampler_weights/<name>
TINKER_USE_CHAT_ENDPOINT = os.getenv("TINKER_USE_CHAT_ENDPOINT", "0") == "1"
TINKER_PRICES = {  # USD per 1M tokens: (prefill, sample, train); tinker models.json 2026-10-16
    "Qwen/Qwen3.5-4B": (0.33, 1.005, 0.737),
    "Qwen/Qwen3-8B": (0.195, 0.60, 0.44),
    "Qwen/Qwen3.5-9B": (0.30, 0.807, 1.463),
}

# --- TabPFN (hosted API via tabpfn-client; reads TABPFN_TOKEN itself) ---
TABPFN_VERSION = os.getenv("TABPFN_VERSION", "v3.5")  # v3.5 == TabPFN-3.5-Plus on the API
BOOKINGS_CSV = ROOT / "data" / "hotels.csv"
REGISTER_CSV = os.getenv("REGISTER_CSV", "")  # optional: first user's own register, same columns as hotels.csv
RISK_TRAIN_ROWS = int(os.getenv("RISK_TRAIN_ROWS", "300"))

# --- SerpApi Google Hotels ---
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")  # TODO: https://serpapi.com/manage-api-key
COMPS_QUERY = os.getenv("COMPS_QUERY", "hotels in Murree")
COMPS_GL, COMPS_HL, COMPS_CURRENCY = "pk", "en", "PKR"
COMPS_MAX = int(os.getenv("COMPS_MAX", "8"))
COMPS_CACHE_DIR = ROOT / "data" / "cache" / "serpapi"
COMPS_CACHE_TTL_H = _f("COMPS_CACHE_TTL_H", 24)
SERPAPI_MONTHLY_BUDGET = int(os.getenv("SERPAPI_MONTHLY_BUDGET", "200"))  # plan: 250/month, 50/hour

# --- Hotel + hold policy ---
HOTEL_NAME = os.getenv("HOTEL_NAME", "Hotel Demo Murree")
BASE_RATE_PKR = int(os.getenv("BASE_RATE_PKR", "8000"))
FLOOR_RATE_PKR = int(os.getenv("FLOOR_RATE_PKR", "5000"))
DEMO_SPEED = _f("DEMO_SPEED", 1.0)  # 60 => a 2 h hold expires in 2 min
BOOKINGS_LOG = ROOT / "data" / "bookings.jsonl"
BRIEFS_DIR = ROOT / "results" / "briefs"

# --- Temporal (local dev server) ---
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TASK_QUEUE = os.getenv("TASK_QUEUE", "munshi")
INJECT_FAILURE_RATE = _f("MUNSHI_INJECT_FAILURE_RATE", 0.0)  # demo only: forces visible retries

# --- Sentry ---
SENTRY_DSN = os.getenv("SENTRY_DSN", "")  # TODO: Sentry project DSN (empty = tracing off)
SENTRY_ENV = os.getenv("SENTRY_ENV", "dev")

RESULTS_DIR = ROOT / "results"
