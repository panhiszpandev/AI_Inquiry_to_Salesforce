import httpx
from middleware.config import (
    SALESFORCE_CLIENT_ID,
    SALESFORCE_CLIENT_SECRET,
    SALESFORCE_INSTANCE_URL,
)
from shared.inquiry_event import InquiryEvent

TOKEN_URL = "{instance_url}/services/oauth2/token"


class SalesforceClient:
    def __init__(self):
        self._access_token = None
        self._authenticate()

    def _authenticate(self):
        resp = httpx.post(TOKEN_URL.format(instance_url=SALESFORCE_INSTANCE_URL), data={
            "grant_type": "client_credentials",
            "client_id": SALESFORCE_CLIENT_ID,
            "client_secret": SALESFORCE_CLIENT_SECRET,
        })
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        print("[salesforce] authenticated via client credentials")

    def create_lead_from_inquiry(self, event: InquiryEvent) -> str:
        c = event.customer
        ip = event.investment_profile
        ai = event.ai_insights

        payload = {
            "FirstName": c.first_name,
            "LastName": c.last_name,
            "Company": "Individual",
            "Email": c.email,
            "Description": ai.summary,
        }
        if c.phone:
            payload["Phone"] = c.phone
        if ip.risk_profile:
            payload["Risk_Profile__c"] = ip.risk_profile.capitalize()
        if ip.estimated_amount:
            payload["Estimated_Investment__c"] = ip.estimated_amount
        if ip.time_horizon:
            payload["Time_Horizon__c"] = ip.time_horizon.replace("-", "-").title()
        if ip.investment_intent:
            payload["Investment_Intent__c"] = ip.investment_intent

        resp = httpx.post(
            f"{SALESFORCE_INSTANCE_URL}/services/data/v59.0/sobjects/Lead",
            json=payload,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        if not resp.is_success:
            print(f"[salesforce] error response: {resp.json()}")
        resp.raise_for_status()
        lead_id = resp.json()["id"]
        print(f"[salesforce] created lead: {lead_id} | {c.first_name} {c.last_name} | confidence: {ai.confidence}")
        return lead_id
