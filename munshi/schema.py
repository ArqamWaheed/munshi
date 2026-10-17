"""Pydantic models shared by the parser, activities, workflows and the UI."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

RoomType = Literal["any", "single", "double", "twin", "triple", "family", "suite"]
Language = Literal["roman_urdu", "english", "mixed", "urdu_script"]
PARSED_FIELDS = ("check_in", "nights", "guests", "rooms", "room_type",
                 "budget_pkr", "language", "needs_clarification")


class Inquiry(BaseModel):
    """What the parser must return. Conventions live in data/seed_templates.md."""
    check_in: date | None = None
    nights: int | None = Field(default=None, ge=1, le=60)
    guests: int | None = Field(default=None, ge=1, le=60)
    rooms: int | None = Field(default=None, ge=1, le=30)
    room_type: RoomType = "any"
    budget_pkr: int | None = Field(default=None, ge=0)  # per night
    language: Language = "roman_urdu"
    needs_clarification: bool = False
    clarification_question: str | None = None


class Traced(BaseModel):
    trace_headers: dict[str, str] = Field(default_factory=dict)  # sentry-trace + baggage


class Attempted(BaseModel):
    attempt: int = 1  # Temporal activity attempt that produced this result


class GuestContext(BaseModel):
    channel: str = "Direct"  # WhatsApp maps to the dataset's "Direct" segment
    is_repeated_guest: int = 0
    previous_cancellations: int = 0
    special_requests: int = 0


class HoldPolicy(BaseModel):
    low_threshold: float = 0.25
    high_threshold: float = 0.50
    hours_low: float = 12.0
    hours_mid: float = 6.0
    hours_high: float = 2.0
    hours_clarify: float = 24.0  # how long to wait for the guest to answer a clarification question
    max_clarify_rounds: int = 2
    advance_low: float = 0.20
    advance_mid: float = 0.30
    advance_high: float = 0.50
    base_rate_pkr: int = 8000
    floor_rate_pkr: int = 5000
    price_to_market: bool = True
    undercut_pct: float = 0.05
    demo_speed: float = 1.0


class ParseInput(Traced):
    message: str
    today: date
    provider: Literal["tinker", "gemma"] = "tinker"


class ParseOutput(Attempted):
    inquiry: Inquiry
    model: str
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float


class RiskInput(Traced):
    inquiry: Inquiry
    today: date
    guest: GuestContext = Field(default_factory=GuestContext)
    prefer: Literal["tabpfn", "logreg"] = "tabpfn"


class RiskResult(Attempted):
    p_cancel: float
    model: str
    features: dict


class CompsInput(Traced):
    check_in: date
    nights: int = 1
    adults: int = 2


class Comp(BaseModel):
    name: str
    nightly_pkr: int | None = None
    rating: float | None = None
    hotel_class: int | None = None


class CompsResult(Attempted):
    comps: list[Comp] = Field(default_factory=list)
    median_nightly_pkr: int | None = None
    source: Literal["live", "cache", "disabled", "empty", "error"] = "disabled"


class Quote(BaseModel):
    nightly_pkr: int
    nights: int
    rooms: int
    total_pkr: int
    advance_pkr: int
    hold_hours: float
    risk_band: str


class DraftInput(Traced):
    inquiry: Inquiry
    quote: Quote | None = None
    kind: Literal["quote", "confirmed", "released"] = "quote"
    hotel_name: str = ""


class DraftOutput(Attempted):
    text: str
    model: str
    latency_s: float
    rewrites: int = 0  # drafts the checker rejected before this one passed


class DepositInfo(BaseModel):
    amount_pkr: int = Field(default=0, ge=0)
    reference: str | None = None


class GuestReply(BaseModel):
    text: str


class HoldInput(Traced):
    message: str
    today: date
    guest: GuestContext = Field(default_factory=GuestContext)
    policy: HoldPolicy = Field(default_factory=HoldPolicy)
    hotel_name: str = ""
    parser_provider: Literal["tinker", "gemma"] = "tinker"
    allow_gemma_fallback: bool = False  # True sends the REDACTED raw text to Gemma if Tinker fails


class HoldStatus(BaseModel):
    stage: str = "received"
    outcome: Literal["pending", "confirmed", "released", "needs_clarification"] = "pending"
    parsed: Inquiry | None = None
    parser_model: str | None = None
    risk: RiskResult | None = None
    comps: CompsResult | None = None
    quote: Quote | None = None
    draft: str | None = None
    hold_expires_at: datetime | None = None
    guest_message: str = ""  # local owner view only (Temporal history has it anyway); never sent to Gemma
    questions: list[str] = Field(default_factory=list)  # clarification questions asked, in order
    guest_replies: list[str] = Field(default_factory=list)
    reply_expires_at: datetime | None = None  # while waiting for the guest to answer a clarification
    deposit: DepositInfo | None = None  # running total of all deposit signals; confirms once >= advance
    followup: str | None = None
    attempts: dict[str, int] = Field(default_factory=dict)
    template_fallbacks: list[str] = Field(default_factory=list)  # reply kinds sent as the template, not Gemma


class Booking(BaseModel):
    workflow_id: str
    inquiry: Inquiry
    quote: Quote
    p_cancel: float
    deposit: DepositInfo | None = None
    booked_on: date
    confirmed_at: datetime


class ArrivalsQuery(BaseModel):
    day: date


class ArrivalRisk(BaseModel):
    booking: Booking
    p_cancel: float
    band: str


class RescoreInput(Traced):
    bookings: list[Booking]
    today: date
    policy: HoldPolicy = Field(default_factory=HoldPolicy)
    prefer: Literal["tabpfn", "logreg"] = "tabpfn"


class BriefInput(BaseModel):
    policy: HoldPolicy = Field(default_factory=HoldPolicy)
    hotel_name: str = ""


class BriefRequest(Traced):
    day: date
    arrivals: list[ArrivalRisk] = Field(default_factory=list)
    comps: CompsResult = Field(default_factory=CompsResult)
    hotel_name: str = ""


class Brief(BaseModel):
    day: date
    arrivals: int
    path: str
    text: str
