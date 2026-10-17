"""P(cancel or no-show) with TabPFN-3.5 (hosted API) trained on a small booking history.

Feature set is shared by training (hotels.csv rows) and scoring (a parsed inquiry), so the same
columns mean the same thing on both sides. WhatsApp inquiries map to market_segment "Direct".
"""
from __future__ import annotations

import threading
from datetime import date, timedelta

import pandas as pd

from munshi import config as cfg
from munshi.llm import NotConfigured
from munshi.schema import GuestContext, Inquiry

NUM = ["lead_time", "nights", "weekend_nights", "guests", "arrival_dow", "arrival_month",
       "is_repeated_guest", "previous_cancellations", "special_requests"]
CAT = ["channel", "deposit_type"]
FEATURES = NUM + CAT
TARGET = "is_canceled"  # 1 = Canceled or No-Show in the dataset
_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}


def features_from_bookings(df: pd.DataFrame) -> pd.DataFrame:
    arrival = pd.to_datetime(dict(year=df["arrival_date_year"], month=df["arrival_date_month"].map(_MONTHS),
                                  day=df["arrival_date_day_of_month"]))
    out = pd.DataFrame({
        "lead_time": df["lead_time"],
        "nights": df["stays_in_weekend_nights"] + df["stays_in_week_nights"],
        "weekend_nights": df["stays_in_weekend_nights"],
        "guests": df["adults"] + df["children"].fillna(0) + df["babies"],
        "arrival_dow": arrival.dt.dayofweek,
        "arrival_month": arrival.dt.month,
        "is_repeated_guest": df["is_repeated_guest"],
        "previous_cancellations": df["previous_cancellations"],
        "special_requests": df["total_of_special_requests"],
        "channel": df["market_segment"].astype(str),
        "deposit_type": df["deposit_type"].astype(str),
    })
    out[TARGET] = df[TARGET]
    return out


def features_from_inquiry(inq: Inquiry, today: date, guest: GuestContext,
                          deposit_type: str = "No Deposit") -> pd.DataFrame:
    check_in = inq.check_in or today + timedelta(days=1)
    nights = inq.nights or 1
    weekend = sum((check_in + timedelta(days=i)).weekday() >= 5 for i in range(nights))  # Sat/Sun nights
    row = {"lead_time": (check_in - today).days, "nights": nights, "weekend_nights": weekend,
           "guests": inq.guests or 2, "arrival_dow": check_in.weekday(), "arrival_month": check_in.month,
           "is_repeated_guest": guest.is_repeated_guest, "previous_cancellations": guest.previous_cancellations,
           "special_requests": guest.special_requests, "channel": guest.channel, "deposit_type": deposit_type}
    return pd.DataFrame([row])[FEATURES]


def load_history(n_rows: int = cfg.RISK_TRAIN_ROWS, seed: int = 0) -> pd.DataFrame:
    """The 'small hotel' history: the first user's register if given, else a sample of hotels.csv."""
    src = cfg.REGISTER_CSV or cfg.BOOKINGS_CSV
    df = features_from_bookings(pd.read_csv(src))
    return df.sample(n=min(n_rows, len(df)), random_state=seed)


def make_tabpfn():
    from tabpfn_client import TabPFNClassifier  # reads TABPFN_TOKEN from the environment

    if not cfg.TABPFN_TOKEN:
        raise NotConfigured("TABPFN_TOKEN is empty (.env)")

    return TabPFNClassifier.create_default_for_version(cfg.TABPFN_VERSION)


def make_logreg():
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    pre = ColumnTransformer([("num", StandardScaler(), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return make_pipeline(pre, LogisticRegression(max_iter=2000))


def make_hgb():
    from sklearn.ensemble import HistGradientBoostingClassifier

    return HistGradientBoostingClassifier(categorical_features="from_dtype", random_state=0)


def as_category(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    for c in CAT:
        X[c] = X[c].astype("category")
    return X


class RiskModel:
    """Fit once per worker process (2 TabPFN API calls/inquiry after that: predict only)."""

    _lock = threading.Lock()
    _model = None
    _name = ""

    @classmethod
    def get(cls, prefer: str = "tabpfn"):
        with cls._lock:
            if cls._model is None or not cls._name.startswith(prefer):
                hist = load_history()
                X, y = hist[FEATURES], hist[TARGET]
                if prefer == "tabpfn":
                    cls._model, cls._name = make_tabpfn().fit(X, y), f"tabpfn-{cfg.TABPFN_VERSION}"
                else:
                    cls._model, cls._name = make_logreg().fit(X, y), "logreg-fallback"
            return cls._model, cls._name


def score(inq: Inquiry, today: date, guest: GuestContext, prefer: str = "tabpfn") -> tuple[float, str, dict]:
    model, name = RiskModel.get(prefer)
    X = features_from_inquiry(inq, today, guest)
    p = float(model.predict_proba(X)[0][1])
    return p, name, X.iloc[0].to_dict()
