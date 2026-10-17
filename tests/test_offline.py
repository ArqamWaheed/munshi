"""Offline checks (no keys, no network): pure rules, redaction, JSON extraction and the eval set."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from data.gen_synthetic import seeds
from munshi import config as cfg
from munshi import policy, risk
from munshi.llm import NotConfigured, call_gemma, call_tinker, extract_json
from munshi.parser import messages_for, next_weekday, normalise, redact
from munshi.reply import check_draft, numbers_in
from munshi.schema import PARSED_FIELDS, DepositInfo, HoldPolicy, Inquiry, Quote

ROOT = Path(__file__).resolve().parent.parent
EVAL = [json.loads(ln) for ln in (ROOT / "data" / "eval.jsonl").read_text(encoding="utf-8").splitlines() if ln]
POL = HoldPolicy()


@pytest.mark.parametrize("p,band,hours,adv", [(0.1, "low", 12, 0.2), (0.25, "medium", 6, 0.3),
                                              (0.49, "medium", 6, 0.3), (0.5, "high", 2, 0.5)])
def test_risk_bands(p, band, hours, adv):
    assert policy.risk_band(p, POL) == band
    assert policy.hold_hours(p, POL) == hours
    assert policy.advance_fraction(p, POL) == adv


def test_demo_speed_shrinks_hold():
    assert policy.hold_duration(0.6, HoldPolicy(demo_speed=60)).total_seconds() == 120


@pytest.mark.parametrize("median,rate", [(None, 8000), (9000, 8550), (2000, 5000), (50000, 12000)])
def test_nightly_rate_clamped(median, rate):
    assert policy.nightly_rate(median, POL) == rate


def test_quote_rounds_advance_up_to_500():
    inq = Inquiry(check_in=date(2026, 10, 17), nights=2, guests=2, rooms=1)
    q = policy.make_quote(inq, None, 0.3, POL)  # 16,000 x 30% = 4,800 -> 5,000
    assert (q.total_pkr, q.advance_pkr, q.hold_hours, q.risk_band) == (16000, 5000, 6, "medium")


def test_deposits_accumulate_with_references():
    total = policy.add_deposit(None, DepositInfo(amount_pkr=2000, reference="JC-1"))
    total = policy.add_deposit(total, DepositInfo(amount_pkr=1500))
    total = policy.add_deposit(total, DepositInfo(amount_pkr=500, reference="HBL-9"))
    assert total == DepositInfo(amount_pkr=4000, reference="JC-1, HBL-9")


def test_missing_keys_fail_fast(monkeypatch):
    """NotConfigured is non-retryable in the activities, so a missing key falls back at once instead of retrying."""
    monkeypatch.setattr(cfg, "GEMINI_API_KEY", "")
    monkeypatch.setattr(cfg, "TABPFN_TOKEN", "")
    monkeypatch.setattr(cfg, "TINKER_MODEL_PATH", "tinker://x/sampler_weights/y")
    monkeypatch.setattr(cfg, "TINKER_API_KEY", "")
    for call in (lambda: call_gemma([]), lambda: call_tinker([]), risk.make_tabpfn):
        with pytest.raises(NotConfigured):
            call()

def test_template_reply_languages():
    inq = Inquiry(check_in=date(2026, 10, 17), nights=1, guests=2, rooms=1, language="english")
    q = policy.make_quote(inq, None, 0.1, POL)
    assert "Rs 8,000" in policy.template_reply(inq, q, "quote")
    assert "Shukriya" in policy.template_reply(inq.model_copy(update={"language": "roman_urdu"}), q, "confirmed")


def test_redact_strips_headers_phones_emails():
    raw = ("[20/10/2026, 9:14 PM] Ahmed Khan: kal 3 log\n"
           "03/11/2026, 10:02 - Sana: mail sana.b@example.com\n"
           "[01/12/2026, 08:40:11] Bilal: call +92 333 1234567 or 0301-2345678")
    out = redact(raw)
    for leaked in ("Ahmed", "Sana:", "Bilal", "example.com", "1234567", "2345678"):
        assert leaked not in out
    assert out.splitlines()[0] == "kal 3 log"


def test_only_gemma_gets_the_long_spec():
    today = date(2026, 10, 16)
    assert len(messages_for("gemma", "x", today)[0]["content"]) > 500
    assert messages_for("tinker", "x", today)[0]["content"] == "Extract the hotel booking request as Munshi JSON."


@pytest.mark.parametrize("text", ['{"a": 1}', '```json\n{"a": 1}\n```', 'Sure! {"a": 1} hope that helps',
                                  '<think>{"no": 0}</think>{"a": 1}'])
def test_extract_json_tolerates_wrappers(text):
    assert extract_json(text) == {"a": 1}


def test_next_weekday_is_strictly_after_today():
    fri = date(2026, 10, 16)
    assert next_weekday(fri, 4) == date(2026, 10, 23)
    assert next_weekday(fri, 5) == date(2026, 10, 17)


def test_normalise_rules():
    today = date(2026, 10, 16)
    assert normalise({"check_in": "2026-10-10", "guests": 2}, today).needs_clarification  # past date dropped
    assert normalise({"check_in": "2026-10-17", "guests": 7}, today).rooms == 3
    assert normalise({"check_in": "2026-10-17", "guests": 4}, today).rooms == 1


def test_seeds_exclude_edge_case_notes():
    s = seeds()
    assert len(s) >= 20 and not any(x.startswith('"') for x in s)


# --- eval set integrity -------------------------------------------------------------------------

def test_eval_size_and_mix():
    assert len(EVAL) >= 60
    ru = sum(r["label"]["language"] in {"roman_urdu", "mixed"} for r in EVAL)
    assert ru / len(EVAL) >= 0.5
    assert len({r["id"] for r in EVAL}) == len(EVAL)


@pytest.mark.parametrize("row", EVAL, ids=[r["id"] for r in EVAL])
def test_eval_label_is_a_fixed_point_of_normalise(row):
    """A gold label must survive the same normalise() the model output goes through, or the eval is unfair."""
    today = date.fromisoformat(row["today"])
    gold = Inquiry.model_validate(row["label"])
    again = normalise(row["label"], today)
    assert {f: getattr(again, f) for f in PARSED_FIELDS} == {f: getattr(gold, f) for f in PARSED_FIELDS}


def test_eval_not_in_seeds():
    s = {x.lower() for x in seeds()}
    assert not [r["id"] for r in EVAL if r["message"].lower() in s]


DRAFT_INQ = Inquiry(check_in=date(2026, 10, 18), nights=2, guests=2, rooms=1)
DRAFT_QUOTE = Quote(nightly_pkr=8000, nights=2, rooms=1, total_pkr=16000, advance_pkr=3500, hold_hours=12,
                    risk_band="low")


def test_numbers_in_reads_separators_suffixes_and_urdu_digits():
    assert numbers_in("Rs 16,000 total, 3.5k advance, 8 hazar per raat") == {16000, 3500, 8000}
    assert numbers_in("\u06f1\u06f6\u06f0\u06f0\u06f0 \u0631\u0648\u067e\u06d2") == {16000}


@pytest.mark.parametrize("text,problem", [
    ("18 Oct se 2 raat, 1 room: total Rs 16,000. Rs 3,500 advance bhej dein, 12 ghante hold.", None),
    ("Total Rs 16,000, advance Rs 3,500, 12 ghante hold. Breakfast Rs 500 extra.", "numbers not in the facts: 500"),
    ("Total Rs 16,000, advance Rs 3,500, 12 ghante hold. Check-in 19 Oct.", "numbers not in the facts: 19"),
    ("Room available hai, total Rs 16,000. Advance bhej dein.", "missing advance, hold hours"),
    ("Total Rs 16,000, advance Rs 3,500, 12 ghante hold. " + "bohat " * 90, "too long"),
])
def test_check_draft(text, problem):
    problems = check_draft(text, DRAFT_INQ, DRAFT_QUOTE, "quote")
    assert problems == [] if problem is None else any(p.startswith(problem) for p in problems)


def test_confirmation_needs_no_prices_but_may_not_invent_any():
    assert check_draft("Advance mil gaya, booking confirm hai. Shukriya!", DRAFT_INQ, DRAFT_QUOTE, "confirmed") == []
    assert check_draft("Rs 2,000 mil gaye, booking confirm.", DRAFT_INQ, DRAFT_QUOTE, "confirmed") != []
