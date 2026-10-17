"""WhatsApp text -> Inquiry JSON. Gemma 4 = baseline + teacher; the Tinker LoRA = production parser."""
from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

from pydantic import ValidationError

from munshi.dates import names_no_date, resolve
from munshi.llm import LLMResult, call_gemma, call_tinker, call_tinker_base, extract_json
from munshi.schema import PARSED_FIELDS, Inquiry

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


# Providers: "tinker" = the fine-tune (production). Eval baselines: "gemma" = Gemma 4 + SPEC_PROMPT (the
# teacher), "base" = untuned Qwen3.5-4B + SHORT_PROMPT, "base_spec" = untuned Qwen3.5-4B + SPEC_PROMPT.
LONG_PROMPT_PROVIDERS = {"gemma", "base_spec"}


def messages_for(provider: str, message: str, today: date) -> list[dict]:
    system = SPEC_PROMPT if provider in LONG_PROMPT_PROVIDERS else SHORT_PROMPT
    return [{"role": "system", "content": system}, {"role": "user", "content": user_turn(message, today)}]


def normalise(raw: dict, today: date) -> Inquiry:
    inq = Inquiry.model_validate(raw)
    if inq.check_in and inq.check_in < today:  # "kal" resolved backwards etc.
        inq.check_in = None
    # The flag is a rule, not a judgement: ask only when the date or the head count is missing. The Gemma
    # teacher also asked when only the number of nights was missing (136 of the first 650 training rows).
    inq.needs_clarification = inq.check_in is None or inq.guests is None
    if not inq.needs_clarification:
        inq.clarification_question = None
    if inq.guests and not inq.rooms:
        inq.rooms = 1 if inq.guests <= 4 else -(-inq.guests // 3)
    return inq


# Rulebook conventions that need the message text, so they live here and not in normalise(). The Gemma
# teacher broke them in ~20% of training rows (4 guests -> 2 rooms; "family of 6" -> family room). They change
# none of the 80 hand labels in data/eval.jsonl (tests/test_offline.py checks this).
_NUMBER_WORDS = {"ek": 1, "aik": 1, "one": 1, "a": 1, "an": 1, "do": 2, "two": 2, "teen": 3, "three": 3,
                 "char": 4, "chaar": 4, "four": 4, "paanch": 5, "panch": 5, "five": 5, "chhe": 6, "chay": 6, "che": 6,
                 "six": 6, "saat": 7, "seven": 7, "aath": 8, "eight": 8, "nau": 9, "nine": 9, "das": 10, "ten": 10,
                 "ایک": 1, "دو": 2, "تین": 3, "چار": 4, "پانچ": 5, "چھ": 6, "سات": 7, "آٹھ": 8, "نو": 9, "دس": 10}
_NUM = r"(\d+|ek|aik|do|teen|char|chaar|paanch|panch|chhe|chay|che|saat|aath|nau|das|one|two|three|four|five|six|" \
       r"seven|eight|nine|ten|a|an)"
_UNUM = r"(\d+|ایک|دو|تین|چار|پانچ|چھ|سات|آٹھ|نو|دس)"
# up to two words between the number and "room", but never a digit or a people word ("2 log 1 room" is 1 room)
_MID = r"(?:(?!(?:log|bande|people|persons|adults|guests|ko|tak|se|to|tareekh|tarikh|jan|feb|mar|apr|may|jun|jul|" \
       r"aug|sep|oct|nov|dec)\b)[a-z]+\s+){0,2}"  # "19 ko room" and "27 tak suite" are dates, not room counts
_ROOM_COUNT = re.compile(rf"\b{_NUM}\s+{_MID}(rooms?|kamr[aey]+|suites?)\b|{_UNUM}\s+کمر", re.I)
_ROOMS_STATED = _ROOM_COUNT
_GUEST_COUNT = re.compile(rf"\b(\d+|ek|aik|do|teen|char|chaar|paanch|panch|chhe|chay|che|saat|aath|nau|das|one|two|three|"
                          rf"four|five|six|seven|eight|nine|ten)\s*(log|logon|logo|lg|bande|banday|bnde|afraad|afrad|"
                          rf"persons?|people|ppl|adults?|guests?|dost|friends)\b|{_UNUM}\s*(لوگ|افراد)", re.I)
_KIDS = re.compile(r"bach|kid|child|infant|baby|بچ", re.I)


_FAMILY_ROOM = re.compile(r"family\s*(room|suite)|فیملی\s*روم", re.I)
_URDU_SCRIPT = re.compile(r"[؀-ۿ]")


def _count(token: str) -> int:
    t = token.lower()
    return int(t) if t.isdigit() else _NUMBER_WORDS[t]


def apply_text_rules(inq: Inquiry, message: str) -> Inquiry:
    """Code decides: language from the script, rooms from the head count unless a room count is written,
    and "family" only when the guest wrote "family room"."""
    text = redact(message)
    if _URDU_SCRIPT.search(text):
        inq.language = "urdu_script"
    # a head count written once, with no children mentioned ("chhe log" is 6, whatever the model read)
    guests = {_count(m.group(1) or m.group(3)) for m in _GUEST_COUNT.finditer(text)}
    if len(guests) == 1 and not _KIDS.search(text):
        inq.guests = guests.pop()
    rooms = {n for m in _ROOM_COUNT.finditer(text) if (n := _count(m.group(1) or m.group(3))) <= 20}
    if len(rooms) == 1:  # a room count written once ("do kamray", "a double room") is the answer
        inq.rooms = rooms.pop()
    elif not rooms:  # no room count written: rooms follow the head count, unknown if it is
        inq.rooms = (1 if inq.guests <= 4 else math.ceil(inq.guests / 3)) if inq.guests else None
    # Budget stays as the model read it: "8 hazar mein 2 din" is a total and "budget 6 hazar" a nightly rate,
    # and a rule that undid divisions got the first one wrong on the training data.
    if inq.room_type == "family" and not _FAMILY_ROOM.search(text):
        inq.room_type = "suite" if re.search(r"suite", text, re.I) else "any"
    return inq


def apply_rules(raw: dict, message: str, today: date) -> Inquiry:
    """Everything code decides after the model reads: dates and ranges from the calendar (munshi.dates), the
    normalise() rules, then the text rules. Used in production and for the training targets alike."""
    raw = dict(raw)
    check_in, nights = resolve(redact(message), today)
    if check_in:
        raw["check_in"] = check_in.isoformat()
    elif names_no_date(redact(message), today):  # "kiraya kitna hai aaj kal?": "these days" is not a date
        raw["check_in"] = None
    if nights:
        raw["nights"] = nights
    return apply_text_rules(normalise(raw, today), message)


class BadModelOutput(Exception):
    """Unparseable/invalid JSON: deterministic at temperature 0, so not worth retrying."""


def parse_message(message: str, today: date, provider: str = "tinker") -> tuple[Inquiry, LLMResult]:
    msgs = messages_for(provider, message, today)
    if provider == "gemma":
        res = call_gemma(msgs, json_mode=True, max_tokens=300, temperature=0.0)
    elif provider in ("base", "base_spec"):
        res = call_tinker_base(msgs, max_tokens=300)
    else:
        res = call_tinker(msgs, max_tokens=200)
    try:
        raw = extract_json(res.text)
        if missing := [f for f in PARSED_FIELDS if f not in raw]:  # its own schema, not ours: not "valid"
            raise ValueError(f"missing keys {missing}")
        return apply_rules(raw, message, today), res
    except (ValueError, ValidationError, json.JSONDecodeError) as e:
        raise BadModelOutput(f"{provider}: {e}") from e


def label_to_target(inq: Inquiry) -> str:
    """Canonical assistant target used in training data (stable key order, compact)."""
    return inq.model_dump_json()


def next_weekday(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)
