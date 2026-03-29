from agent.tools.base_tool import BaseTool
from shared.inquiry_event import InquiryEvent, CustomerProfile, InvestmentProfile, AiInsights
from shared.kafka_producer import KafkaProducer

REQUIRED_FIELDS = ["first_name", "last_name", "email"]
OPTIONAL_INVESTMENT_FIELDS = ["estimated_amount", "currency", "risk_profile", "time_horizon", "investment_intent"]


def _compute_confidence(data: dict) -> float:
    filled_optional = sum(1 for f in OPTIONAL_INVESTMENT_FIELDS if data.get(f))
    return round(0.7 + (filled_optional / len(OPTIONAL_INVESTMENT_FIELDS)) * 0.3, 2)


def _build_summary(data: dict) -> str:
    parts = []
    if data.get("estimated_amount") and data.get("currency"):
        parts.append(f"Investment amount: {data['estimated_amount']} {data['currency']}")
    if data.get("risk_profile"):
        parts.append(f"Risk profile: {data['risk_profile']}")
    if data.get("time_horizon"):
        parts.append(f"Time horizon: {data['time_horizon']}")
    return ". ".join(parts) if parts else "Client expressed interest in investment opportunities."


class FinishConversationTool(BaseTool):
    name = "finish_conversation"
    description = (
        "Finish the conversation and submit the investment inquiry. "
        "Only call this when all required fields (first_name, last_name, email) have been collected "
        "and you have gathered as much investment profile information as possible."
    )

    def __init__(self, inquiry_data: dict):
        self.inquiry_data = inquiry_data

    def run(self) -> dict:
        missing = [f for f in REQUIRED_FIELDS if not self.inquiry_data.get(f)]
        if missing:
            return {"ok": False, "error": f"Cannot finish — still missing required fields: {missing}"}

        event = InquiryEvent(
            customer=CustomerProfile(
                first_name=self.inquiry_data["first_name"],
                last_name=self.inquiry_data["last_name"],
                email=self.inquiry_data["email"],
                phone=self.inquiry_data.get("phone"),
            ),
            investment_profile=InvestmentProfile(
                estimated_amount=float(self.inquiry_data["estimated_amount"]) if self.inquiry_data.get("estimated_amount") else None,
                currency=self.inquiry_data.get("currency"),
                risk_profile=self.inquiry_data.get("risk_profile"),
                time_horizon=self.inquiry_data.get("time_horizon"),
                investment_intent=self.inquiry_data.get("investment_intent"),
            ),
            ai_insights=AiInsights(
                intent="investment",
                confidence=_compute_confidence(self.inquiry_data),
                summary=_build_summary(self.inquiry_data),
            ),
        )

        producer = KafkaProducer()
        producer.publish_inquiry(event)
        producer.close()

        return {
            "ok": True,
            "event_id": event.event_id,
            "message": "Investment inquiry submitted successfully.",
        }
