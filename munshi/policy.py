"""Pure business rules (no I/O, no clock): safe to call inside Temporal workflow code."""
from __future__ import annotations

import math
from datetime import timedelta

from munshi.schema import DepositInfo, HoldPolicy, Inquiry, Quote


def risk_band(p: float, pol: HoldPolicy) -> str:
    if p >= pol.high_threshold:
        return "high"
    return "medium" if p >= pol.low_threshold else "low"


def hold_hours(p: float, pol: HoldPolicy) -> float:
    return {"low": pol.hours_low, "medium": pol.hours_mid, "high": pol.hours_high}[risk_band(p, pol)]


def hold_duration(p: float, pol: HoldPolicy) -> timedelta:
    """Real hold length divided by demo_speed (demo_speed=60 turns a 2 h hold into 2 min)."""
    return timedelta(hours=hold_hours(p, pol) / max(pol.demo_speed, 1e-6))


def clarify_duration(pol: HoldPolicy) -> timedelta:
    return timedelta(hours=pol.hours_clarify / max(pol.demo_speed, 1e-6))


def add_deposit(total: DepositInfo | None, new: DepositInfo) -> DepositInfo:
    """Guests often pay the advance in parts (JazzCash limits); keep a running total and every reference."""
    if total is None:
        return new.model_copy()
    refs = [r for r in (total.reference, new.reference) if r]
    return DepositInfo(amount_pkr=total.amount_pkr + new.amount_pkr, reference=", ".join(refs) or None)


def advance_fraction(p: float, pol: HoldPolicy) -> float:
    return {"low": pol.advance_low, "medium": pol.advance_mid, "high": pol.advance_high}[risk_band(p, pol)]


def nightly_rate(comps_median: int | None, pol: HoldPolicy) -> int:
    if not comps_median or not pol.price_to_market:
        return pol.base_rate_pkr
    target = int(comps_median * (1 - pol.undercut_pct))
    return max(pol.floor_rate_pkr, min(target, int(pol.base_rate_pkr * 1.5)))


def make_quote(inq: Inquiry, comps_median: int | None, p: float, pol: HoldPolicy) -> Quote:
    nights, rooms = inq.nights or 1, inq.rooms or 1
    nightly = nightly_rate(comps_median, pol)
    total = nightly * nights * rooms
    advance = int(math.ceil(total * advance_fraction(p, pol) / 500.0) * 500)
    return Quote(nightly_pkr=nightly, nights=nights, rooms=rooms, total_pkr=total,
                 advance_pkr=advance, hold_hours=hold_hours(p, pol), risk_band=risk_band(p, pol))


def clarification_text(inq: Inquiry) -> str:
    if inq.clarification_question:
        return inq.clarification_question
    if inq.language == "english":
        return "Could you share your check-in date and how many guests?"
    return "Aap kis date ko aur kitne log aana chahte hain?"


def template_reply(inq: Inquiry, quote: Quote | None, kind: str) -> str:
    """Deterministic fallback used when the Gemma draft activity exhausts its retries."""
    en = inq.language == "english"
    if kind == "confirmed":
        return "Advance received, your booking is confirmed. Thank you!" if en else \
            "Advance mil gaya, aap ki booking confirm hai. Shukriya!"
    if kind == "released":
        return "We could not hold the room any longer. Message us if you still want to book." if en else \
            "Room ka hold khatam ho gaya. Agar ab bhi booking chahiye to message kar dein."
    assert quote is not None
    if en:
        return (f"{quote.rooms} room(s), {quote.nights} night(s) from {inq.check_in}: "
                f"Rs {quote.total_pkr:,} total. Send Rs {quote.advance_pkr:,} advance; "
                f"we hold the room for {quote.hold_hours:g} hours.")
    return (f"{inq.check_in} se {quote.nights} raat, {quote.rooms} room: total Rs {quote.total_pkr:,}. "
            f"Rs {quote.advance_pkr:,} advance bhej dein, room {quote.hold_hours:g} ghante hold rahega.")
