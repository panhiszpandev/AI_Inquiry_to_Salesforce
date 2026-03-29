from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime, timezone
import json
import uuid


@dataclass
class CustomerProfile:
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None


@dataclass
class InvestmentProfile:
    estimated_amount: Optional[float] = None
    currency: Optional[str] = None
    risk_profile: Optional[str] = None   # low / medium / high
    time_horizon: Optional[str] = None   # short-term / long-term
    investment_intent: Optional[str] = None


@dataclass
class AiInsights:
    intent: str = "investment"
    confidence: float = 0.0
    summary: str = ""


@dataclass
class InquiryEvent:
    customer: CustomerProfile
    investment_profile: InvestmentProfile
    ai_insights: AiInsights
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    event_type: str = "investment.inquiry.captured"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "ai-chatbot"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "InquiryEvent":
        raw = json.loads(data)
        return cls(
            customer=CustomerProfile(**raw["customer"]),
            investment_profile=InvestmentProfile(**raw["investment_profile"]),
            ai_insights=AiInsights(**raw["ai_insights"]),
            event_id=raw["event_id"],
            event_type=raw["event_type"],
            occurred_at=raw["occurred_at"],
            source=raw["source"],
        )
