"""Guest-facing reply drafted by Gemma 4 from PARSED FIELDS ONLY.

Data minimisation: the raw WhatsApp text, names and phone numbers are never sent to the Gemini API
(free-tier prompts may be used to improve Google's products). Gemma sees a small JSON of facts.
"""
from __future__ import annotations

import json

from munshi.llm import LLMResult, call_gemma
from munshi.schema import Inquiry, Quote

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


def draft(inq: Inquiry, quote: Quote | None, kind: str, hotel_name: str) -> LLMResult:
    msgs = [{"role": "system", "content": SYSTEM.format(hotel=hotel_name, language=_LANG[inq.language])},
            {"role": "user", "content": f"GOAL: {KIND_GOAL[kind]}\nFACTS: {json.dumps(facts(inq, quote))}"}]
    return call_gemma(msgs, max_tokens=220, temperature=0.4)
