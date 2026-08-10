from dataclasses import dataclass , asdict
import base64
import requests
from typing import Optional
import datetime
import json


@dataclass
class EasyCardTransaction:
    datetime: str = ""
    category: str = ""
    location: str = ""
    amount: str = ""
    balance: str = ""
    welfare_discount: str = ""
    accumulated_points: str = ""
    accumulated_count: str = ""
    accumulated_amount: str = ""
    operator: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class EasyCardResult:
    success: bool
    card_id: str = ""
    start_date: str = ""
    end_date: str = ""
    expiry_date: Optional[str] = None
    balance: Optional[str] = None
    transactions: list[EasyCardTransaction] = None
    message: Optional[str] = None

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []

    def to_dict(self):
        data = asdict(self)
        data["transactions"] = [
            tx.to_dict() for tx in self.transactions
        ]
        return data



from dataclasses import dataclass, asdict

@dataclass
class InjectPayload:
    card_id: str
    captcha: str
    birthday: str = ""
    date: str = "date3m"
    start_date: str | None = None
    end_date: str | None = None

    def to_dict(self):
        return {
            "Cont": "Cont",
            "card_id": self.card_id,
            "birthday": self.birthday,
            "date": self.date,
            "START_DATE": self.start_date,
            "END_DATE": self.end_date,
            "checkword": self.captcha,
            "thisPage" : 1
        }




### "card_id": "9132125919016763", "birthday": "", "date": "date3m", "START_DATE": "2026-05-09", "END_DATE": "2026-08-09", "checkword": checkword, ###