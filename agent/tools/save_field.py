from agent.tools.base_tool import BaseTool

REQUIRED_FIELDS = ["first_name", "last_name", "email"]
OPTIONAL_FIELDS = ["phone", "estimated_amount", "currency", "risk_profile", "time_horizon", "investment_intent"]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


class SaveFieldTool(BaseTool):
    name = "save_field"
    description = (
        "Save a single piece of information collected from the client. "
        "Call this each time the client provides a value for any field."
    )

    def __init__(self, inquiry_data: dict):
        self.inquiry_data = inquiry_data

    def run(self, field: str, value: str) -> dict:
        if field not in ALL_FIELDS:
            return {"ok": False, "error": f"Unknown field '{field}'. Valid fields: {ALL_FIELDS}"}
        self.inquiry_data[field] = value
        collected = [f for f in ALL_FIELDS if self.inquiry_data.get(f)]
        missing_required = [f for f in REQUIRED_FIELDS if not self.inquiry_data.get(f)]
        return {"ok": True, "saved": field, "collected": collected, "still_required": missing_required}

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "enum": ALL_FIELDS,
                    "description": "The field to save.",
                },
                "value": {
                    "type": "string",
                    "description": "The value provided by the client.",
                },
            },
            "required": ["field", "value"],
        }
