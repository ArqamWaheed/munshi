"""Guest-facing reply drafted by Gemma 4 from PARSED FIELDS ONLY.

Data minimisation: the raw WhatsApp text, names and phone numbers are never sent to the Gemini API
(free-tier prompts may be used to improve Google's products). Gemma sees a small JSON of facts.

Gemma writes, code decides: check_draft() rejects any number that is not in the facts, a quote that leaves
out the total, advance or hold time, and over-long drafts. draft_checked() gives Gemma one hinted retry;
the caller falls back to the deterministic template if that also fails.
"""
from __future__ import annotations

import json
import re

from munshi.llm import LLMResult, call_gemma
from munshi.schema import Inquiry, Quote
from munshi.tracing import tool_span

_LANG = {"roman_urdu": "Roman Urdu (Urdu in Latin letters, WhatsApp style)", "english": "English",
         "mixed": "Roman Urdu mixed with English, as Pakistani guests write on WhatsApp",
         "urdu_script": "Urdu in Urdu script"}

SYSTEM = """You are the front desk of {hotel}, a small hotel in Pakistan, replying on WhatsApp.
Write ONE short, warm reply (max 70 words) in {language}. Use ONLY the facts in the JSON.
Never invent prices, dates, amenities or policies. Amounts in Rs with thousands separators.
No greeting by name (you do not know it). No emojis except at most one."""

KIND_GOAL = {
    "quote": "Offer the room(s), state the total, the advance needed to confirm, and how many hours we hold it.",
    "confirmed": "Confirm the booking: advance received, see them on the check-in date.",
    "released": "Politely say the hold expired and the room was released; they can message to re-book.",
}


def facts(inq: Inquiry, quote: Quote | None) -> dict:
    f = {"check_in": str(inq.check_in) if inq.check_in else None, "nights": inq.nights,
         "guests": inq.guests, "rooms": inq.rooms, "room_type": inq.room_type}
    if quote:
        f |= {"nightly_rs": quote.nightly_pkr, "total_rs": quote.total_pkr,
              "advance_rs": quote.advance_pkr, "hold_hours": quote.hold_hours}
    return f


def draft(inq: Inquiry, quote: Quote | None, kind: str, hotel_name: str, hint: str = "") -> LLMResult:
    user = f"GOAL: {KIND_GOAL[kind]}\nFACTS: {json.dumps(facts(inq, quote))}"
    if hint:
        user += f"\nYOUR PREVIOUS DRAFT WAS REJECTED: {hint}. Use only the numbers in FACTS."
    msgs = [{"role": "system", "content": SYSTEM.format(hotel=hotel_name, language=_LANG[inq.language])},
            {"role": "user", "content": user}]
    return call_gemma(msgs, max_tokens=220, temperature=0.4)


MAX_WORDS = 90  # the prompt asks for 70; allow some slack before rejecting
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹"
                        "٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_NUM = re.compile(r"(\d[\d,٬]*(?:\.\d+)?)\s*([kK]\b|hazar|ہزار)?")


def numbers_in(text: str) -> set[float]:
    """Every number written in digits (Latin or Urdu), with thousands separators and "16k"/"16 hazar" expanded."""
    out = set()
    for num, suffix in _NUM.findall(text.translate(_DIGITS)):
        v = float(num.replace(",", "").replace("٬", ""))
        out.add(v * 1000 if suffix else v)
    return out


def allowed_numbers(inq: Inquiry, quote: Quote | None, hotel_name: str) -> set[float]:
    vals = [inq.nights, inq.guests, inq.rooms, inq.budget_pkr]
    if inq.check_in:
        vals += [inq.check_in.day, inq.check_in.month, inq.check_in.year, inq.check_in.year % 100]
    if quote:
        vals += [quote.nightly_pkr, quote.total_pkr, quote.advance_pkr, quote.hold_hours, quote.nights, quote.rooms]
    return {float(v) for v in vals if v is not None} | numbers_in(hotel_name)


def check_draft(text: str, inq: Inquiry, quote: Quote | None, kind: str, hotel_name: str = "") -> list[str]:
    """Problems with a drafted reply; empty list = OK to send."""
    problems = []
    found = numbers_in(text)
    if extra := sorted(found - allowed_numbers(inq, quote, hotel_name)):
        problems.append("numbers not in the facts: " + ", ".join(f"{v:g}" for v in extra))
    if kind == "quote" and quote:
        missing = [name for name, v in (("total", quote.total_pkr), ("advance", quote.advance_pkr),
                                        ("hold hours", quote.hold_hours)) if float(v) not in found]
        if missing:
            problems.append("missing " + ", ".join(missing))
    if len(text.split()) > MAX_WORDS:
        problems.append(f"too long ({len(text.split())} words)")
    return problems


def draft_checked(inq: Inquiry, quote: Quote | None, kind: str, hotel_name: str,
                  max_tries: int = 2) -> tuple[LLMResult, list[list[str]]]:
    """Draft, check, and retry once with the checker's complaint as a hint. Returns the last draft and the
    problems found on each try (the last entry is empty when the draft passed)."""
    history: list[list[str]] = []
    hint = ""
    for _ in range(max_tries):
        res = draft(inq, quote, kind, hotel_name, hint)
        with tool_span("reply_check") as span:  # counts and categories only: no reply text in Sentry
            problems = check_draft(res.text, inq, quote, kind, hotel_name)
            span.set_data("munshi.reply_check.passed", not problems)
            span.set_data("munshi.reply_check.problems", ", ".join(p.split(":")[0] for p in problems) or "none")
        history.append(problems)
        if not problems:
            break
        hint = "; ".join(problems)
    return res, history
