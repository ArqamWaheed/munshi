"""WhatsApp text -> Inquiry JSON. Gemma 4 = baseline + teacher; the Tinker LoRA = production parser."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

from pydantic import ValidationError

from munshi.llm import LLMResult, call_gemma, call_tinker, extract_json
from munshi.schema import Inquiry

# Long spec for the zero-shot Gemma baseline and the teacher (the fine-tune learns it from data).
SPEC_PROMPT = """You extract hotel booking requests from WhatsApp messages written in Roman Urdu, English or a mix.
Return ONLY one JSON object with exactly these keys:
check_in (YYYY-MM-DD or null), nights (int or null), guests (int or null), rooms (int or null),
room_type ("any"|"single"|"double"|"twin"|"triple"|"family"|"suite"), budget_pkr (int per night or null),
language ("roman_urdu"|"english"|"mixed"|"urdu_script"), needs_clarification (bool),
clarification_question (short question in the guest's language, or null).
Rules: resolve relative dates against TODAY: aaj=today, kal=tomorrow, parso=day after tomorrow,
"is weekend"/"this weekend"=the coming Saturday, "agle hafte"/"next week"=next Monday unless a day is named.
A weekday name (jumma/Friday, hafta/Saturday, itwaar/Sunday, peer/Monday ...) = its next date AFTER today.
A bare day number ("25 tareekh", "the 28th") = that day this month, or next month if already past.
"2 log"/"2 bande"=2 guests; "couple"/"mian biwi"=2; adults and kids both count as guests.
"family room" => room_type "family"; "double bed" => "double". If rooms is not stated: rooms=1 unless
guests > 4, then ceil(guests/3). "X din"/"X days" = X nights. A range ("jumma se itwaar", "Sunday to Tuesday",
check_in to check_out) sets check_in and nights = difference. nights=null if no stay length is given, except
"aaj raat"/"kal raat ke liye"/"tonight" alone = 1 night.
Budget: "8 hazar"/"8k"/"8000" => 8000; "1 lakh" => 100000; a total budget is divided by nights.
needs_clarification=true when check_in OR guests cannot be determined; then ask for the missing item."""

# Short prompt the fine-tuned model is trained and served with (fewer prompt tokens = cheaper).
SHORT_PROMPT = "Extract the hotel booking request as Munshi JSON."

_HEADER = re.compile(r"^\[?\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp][Mm])?\]?\s*(?:-\s*)?[^:]{1,40}:\s*")
_PHONE = re.compile(r"(?:\+?92|0092|0)?[\s-]?3\d{2}[\s-]?\d{7}\b")
_EMAIL = re.compile(r"\S+@\S+\.\S+")


def redact(message: str) -> str:
    """Strip WhatsApp export headers (timestamp + sender name), phone numbers and emails before ANY model."""
    lines = [_HEADER.sub("", ln) for ln in message.strip().splitlines()]
    return _EMAIL.sub("[email]", _PHONE.sub("[phone]", "\n".join(ln for ln in lines if ln.strip())))


def user_turn(message: str, today: date) -> str:
    return f"TODAY: {today.isoformat()} ({today.strftime('%A')})\nMESSAGE: {redact(message)}"


def messages_for(provider: str, message: str, today: date) -> list[dict]:
    system = SPEC_PROMPT if provider == "gemma" else SHORT_PROMPT
    return [{"role": "system", "content": system}, {"role": "user", "content": user_turn(message, today)}]


def normalise(raw: dict, today: date) -> Inquiry:
    inq = Inquiry.model_validate(raw)
    if inq.check_in and inq.check_in < today:  # "kal" resolved backwards etc.
        inq.check_in = None
    if inq.check_in is None or inq.guests is None:
        inq.needs_clarification = True
    if inq.guests and not inq.rooms:
        inq.rooms = 1 if inq.guests <= 4 else -(-inq.guests // 3)
    return inq


class BadModelOutput(Exception):
    """Unparseable/invalid JSON: deterministic at temperature 0, so not worth retrying."""


def parse_message(message: str, today: date, provider: str = "tinker") -> tuple[Inquiry, LLMResult]:
    msgs = messages_for(provider, message, today)
    res = call_gemma(msgs, json_mode=True, max_tokens=300, temperature=0.0) if provider == "gemma" \
        else call_tinker(msgs, max_tokens=200)
    try:
        return normalise(extract_json(res.text), today), res
    except (ValueError, ValidationError, json.JSONDecodeError) as e:
        raise BadModelOutput(f"{provider}: {e}") from e


def label_to_target(inq: Inquiry) -> str:
    """Canonical assistant target used in training data (stable key order, compact)."""
    return inq.model_dump_json()


def next_weekday(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)
