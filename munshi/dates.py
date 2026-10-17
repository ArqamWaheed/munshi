"""Deterministic date resolution for booking messages: the model reads, code does the calendar arithmetic.

The first parser eval showed the fine-tuned 4B getting weekday arithmetic and ranges wrong ("hafte ko",
"itwaar se peer tak", "20-22 November") where the rulebook is unambiguous. resolve() applies the rulebook in
code and is deliberately conservative: it returns a date only when the message names exactly one, and nights
only for two dates joined by a range word. Anything ambiguous returns None and the model's answer stands.

Rulebook (SPEC_PROMPT): aaj = today, kal = tomorrow, parso = day after; a weekday = its next date AFTER today;
"is weekend" = the coming Saturday; "agle hafte"/"next week" = next Monday unless a day is named; a bare day
number = this month, or next month if already past; a range sets check-in and nights = difference.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
                                       "nov", "dec"], start=1)}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_RELATIVE = [(r"\b(parso+n?|parsun)\b|day after tomorrow|پرسوں", 2), (r"\b(aa?j|today|tonight)\b|آج", 0),
             (r"\b(kal|kl|kall|tomorrow|tmrw|tmr)\b|کل", 1)]
_WEEKDAYS = [(r"\b(peer|pir|monday)\b|پیر", 0), (r"\b(mangal|tuesday)\b|منگل", 1), (r"\b(budh|wednesday)\b|بدھ", 2),
             (r"\b(jumeraat|jumerat|thursday)\b|جمعرات", 3), (r"\b(jumm?a+h?|friday)\b|جمعہ", 4),
             (r"\b(saturday|hafte ko|hafta ko)\b|ہفتے کو", 5), (r"\b(itwaa?r|sunday)\b|اتوار", 6)]
_WEEKEND = re.compile(r"\b(this|is|coming)\s+weekend\b|اس\s*ویک\s*اینڈ", re.I)
_NEXT_WEEK = re.compile(r"\b(agle|agly|agla)\s+hafte\b|\bnext\s+week\b|اگلے\s+ہفتے", re.I)
_NOWADAYS = re.compile(r"\baa?j\s*kal\b|آج\s*کل", re.I)  # "aaj kal" = "these days", not a date
# "next friday", "agle peer": this coming one or the one after? The rulebook doesn't say, so the model decides.
_NEXT_DAY = re.compile(r"\b(next|agle|agly|agla)\s+(peer|pir|monday|mangal|tuesday|budh|wednesday|jumeraat|"
                       r"jumerat|thursday|jumm?a+h?|friday|saturday|hafte ko|itwaa?r|sunday)\b", re.I)
_CHECK_OUT = re.compile(r"check[\s-]*out|nikal", re.I)  # "kal check in, parso check out"
_RANGE_WORD = re.compile(r"\b(se|to|till|until|tak|and)\b|\bcheck[\s-]*out\b|[-–]|سے|تک", re.I)
_DAY_RANGE_MON = re.compile(rf"\b(\d{{1,2}})\s*(?:st|nd|rd|th)?\s*(?:se|to|till|-|–)\s*(\d{{1,2}})\s*(?:st|nd|rd|th)?\s*"
                            rf"(?:tak\s*)?{_MON}\b", re.I)
_MON_DAY_RANGE = re.compile(rf"\b{_MON}\s*(\d{{1,2}})\s*(?:se|to|till|-|–)\s*(\d{{1,2}})\b", re.I)
_DAY_MON = re.compile(rf"\b(\d{{1,2}})\s*(?:st|nd|rd|th)?\s*(?:of\s+)?{_MON}\b", re.I)
_MON_DAY = re.compile(rf"\b{_MON}\s*(\d{{1,2}})(?:st|nd|rd|th)?\b", re.I)
_DAY_ONLY = re.compile(r"\b(\d{1,2})\s*(?:st|nd|rd|th|tareekh|tarikh|ko)\b", re.I)


def _on_or_after(today: date, month: int | None, day: int) -> date | None:
    """A day (and maybe month) -> the date it means. Bare day: this month, else next month. Past: None."""
    try:
        if month is None:
            d = date(today.year, today.month, day)
            if d < today:
                m = today.month % 12 + 1
                d = date(today.year + (today.month == 12), m, day)
            return d
        d = date(today.year, month, day)
        return d if d >= today else None
    except ValueError:
        return None


def mentions(text: str, today: date) -> list[tuple[int, date | None]]:
    """Every date the message names, with its position; None for a date that is already past."""
    t = _NOWADAYS.sub(" ", text.lower())
    found: list[tuple[int, date | None]] = []
    taken: list[tuple[int, int]] = []

    def add(m: re.Match, d: date | None) -> None:
        if not any(m.start() < e and s < m.end() for s, e in taken):
            found.append((m.start(), d))
            taken.append((m.start(), m.end()))

    for m in _DAY_RANGE_MON.finditer(t):  # "9 se 11 nov", "20-22 November"
        mon = _MONTHS[m.group(3)[:3]]
        add(m, _on_or_after(today, mon, int(m.group(1))))
        found.append((m.end(), _on_or_after(today, mon, int(m.group(2)))))
    for m in _MON_DAY_RANGE.finditer(t):  # "dec 24 se 27"
        mon = _MONTHS[m.group(1)[:3]]
        add(m, _on_or_after(today, mon, int(m.group(2))))
        found.append((m.end(), _on_or_after(today, mon, int(m.group(3)))))
    for rx in (_DAY_MON, _MON_DAY):
        for m in rx.finditer(t):
            day, mon = (m.group(1), m.group(2)) if rx is _DAY_MON else (m.group(2), m.group(1))
            add(m, _on_or_after(today, _MONTHS[mon[:3]], int(day)))
    for m in _DAY_ONLY.finditer(t):
        if 1 <= int(m.group(1)) <= 31:
            add(m, _on_or_after(today, None, int(m.group(1))))
    for rx, days in _RELATIVE:
        for m in re.finditer(rx, t, re.I):
            add(m, today + timedelta(days=days))
    for rx, wd in _WEEKDAYS:
        for m in re.finditer(rx, t, re.I):
            # a weekday after "se/to" is counted from the start of the stay, not from today
            prev = [d for p, d in found if p < m.start() and d is not None and _RANGE_WORD.search(t[p:m.start()])]
            base = prev[-1] if prev else today
            add(m, base + timedelta(days=(wd - base.weekday()) % 7 or 7))
    for m in _WEEKEND.finditer(t):
        add(m, today + timedelta(days=(5 - today.weekday()) % 7))
    return sorted(found, key=lambda x: x[0])


def _ambiguous(text: str, today: date) -> bool:
    t = text.lower()
    if _NEXT_DAY.search(t):
        return True
    if today.weekday() >= 5 and _WEEKEND.search(t):  # "is weekend" said on a Saturday or Sunday
        return True
    if today.weekday() == 6 and _NEXT_WEEK.search(t):  # "next week" said on a Sunday: tomorrow, or in 8 days?
        return True
    # "monday ko" said on a Monday: today, or next week? Only the FIRST weekday named matters: in "peer se budh
    # tak" said on a Wednesday, Wednesday is the end of the stay and is counted from the Monday.
    first = min(((m.start(), wd) for r, wd in _WEEKDAYS for m in re.finditer(r, t, re.I)), default=None)
    return first is not None and first[1] == today.weekday()


def names_no_date(text: str, today: date) -> bool:
    """True when the only date-like words are "aaj kal" ("these days"), so the message names no date at all."""
    return bool(_NOWADAYS.search(text)) and not mentions(text, today) and not _NEXT_WEEK.search(text)


def resolve(text: str, today: date) -> tuple[date | None, int | None]:
    """(check_in, nights) when the message is unambiguous, else None for that part."""
    if _ambiguous(text, today):
        return None, None
    if _NEXT_WEEK.search(text):
        if mentions(text, today):  # "agle hafte jumma": this week's or next week's Friday? Leave it to the model.
            return None, None
        return today + timedelta(days=(7 - today.weekday()) % 7 or 7), None
    found = mentions(text, today)
    if any(d is None for _, d in found):  # names a date that has passed: let normalise() and the model handle it
        return None, None
    dates = sorted({d for _, d in found})
    if len(dates) == 1:
        return dates[0], None
    if len(dates) == 2:
        (p1, d1), (p2, d2) = found[0], found[-1]
        between = text.lower()[min(p1, p2):max(p1, p2) + 12]
        nights = (dates[1] - dates[0]).days
        if (_RANGE_WORD.search(between) or _CHECK_OUT.search(text)) and 1 <= nights <= 30:
            return dates[0], nights
    return None, None
