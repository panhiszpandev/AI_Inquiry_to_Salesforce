# AI Inquiry to Salesforce

An end-to-end demo of AI-powered investment inquiry capture. A CLI conversational agent collects a potential client's data through natural dialogue, publishes a structured event to Apache Kafka, and a separate middleware service consumes it and creates a Lead in Salesforce CRM.

---

## Architecture overview

```
┌─────────────────────────────┐
│         CLI Agent           │  ← user types in terminal
│  (OpenRouter / Claude/GPT)  │
│                             │
│  Tools:                     │
│   • save_field              │
│   • finish_conversation     │
└────────────┬────────────────┘
             │ publishes InquiryEvent (JSON)
             ▼
┌─────────────────────────────┐
│     Apache Kafka (Docker)   │
│  topic: investment.inquiry  │
│         .captured           │
└────────────┬────────────────┘
             │ consumes InquiryEvent
             ▼
┌─────────────────────────────┐
│        Middleware           │
│  (Python consumer service)  │
│                             │
│  • deserializes event       │
│  • authenticates with SF    │
│  • creates Lead via REST    │
└────────────┬────────────────┘
             │ POST /sobjects/Lead
             ▼
┌─────────────────────────────┐
│        Salesforce CRM       │
│   Lead with custom fields   │
└─────────────────────────────┘
```

---

## Example conversation

> The agent conducts a natural dialogue, saves each field behind the scenes, and submits the inquiry automatically when ready.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                      AI Investment Advisory — CLI                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Agent  │ Hello! I'm here to help connect you with our investment advisory
         │ team. Could I start with your name?

  You    │ Sure, I'm Anna Kowalska.

  Agent  │ Nice to meet you, Anna! What brings you to us today — are you
         │ looking to grow your savings, plan for retirement, or something else?

  You    │ Mainly retirement. I'd also like some passive income on the side.
         │ I've been thinking about dividend stocks and maybe some bonds.

  Agent  │ That's a great starting point. How much are you looking to invest,
         │ and in which currency?

  You    │ Around 50 000 CHF.

  Agent  │ Understood. How would you describe your appetite for risk —
         │ low, medium, or high?

  You    │ I'd say medium. I don't want to lose sleep over it, but I'm open
         │ to some growth.

  Agent  │ And what's your investment horizon — are you thinking short-term
         │ (under 3 years) or long-term?

  You    │ Definitely long-term. At least 15–20 years.

  Agent  │ Do you have any constraints I should note — liquidity needs,
         │ ethical preferences, anything like that?

  You    │ I'd prefer to avoid companies with poor ESG ratings if possible.

  Agent  │ Got it. Could I get your email address so an advisor can follow up?

  You    │ anna.kowalska@example.com

  Agent  │ And optionally, a phone number?

  You    │ +48 600 123 456

  Agent  │ Perfect, let me confirm the details before I submit:
         │
         │   Name          Anna Kowalska
         │   Email         anna.kowalska@example.com
         │   Phone         +48 600 123 456
         │   Amount        50 000 CHF
         │   Risk profile  Medium
         │   Horizon       Long-term
         │   Goals         Retirement savings and passive income via dividend
         │                 stocks and bonds, with a preference for ESG-aligned
         │                 companies.
         │
         │ Shall I go ahead and submit?

  You    │ Yes, please.

  Agent  │ Your inquiry has been submitted successfully! One of our advisors
         │ will be in touch with you shortly. Thank you, Anna!

╚══════════════════════════════════════════════════════════════════════════════╝
```

**What happened behind the scenes:**

```
save_field(first_name, "Anna")
save_field(last_name, "Kowalska")
save_field(investment_intent, "**Goals:** Retirement savings and passive income
                               **Interests:** Dividend stocks, bonds
                               **Constraints:** Prefers ESG-aligned companies")
save_field(estimated_amount, "50000")
save_field(currency, "CHF")
save_field(risk_profile, "medium")
save_field(time_horizon, "long-term")
save_field(email, "anna.kowalska@example.com")
save_field(phone, "+48 600 123 456")
finish_conversation()   ──► publishes InquiryEvent to Kafka
                        ──► middleware creates Lead in Salesforce  ✓
```

**Resulting Salesforce Lead:**

```
┌─────────────────────────────────────────────────────────────┐
│  Lead: Anna Kowalska                                        │
├──────────────────────────┬──────────────────────────────────┤
│ Email                    │ anna.kowalska@example.com        │
│ Phone                    │ +48 600 123 456                  │
│ Company                  │ Individual                       │
│ Risk_Profile__c          │ Medium                           │
│ Estimated_Investment__c  │ 50000.00                         │
│ Time_Horizon__c          │ Long-Term                        │
│ Investment_Intent__c     │ **Goals:** Retirement savings    │
│                          │ and passive income               │
│                          │ **Interests:** Dividend stocks,  │
│                          │ bonds                            │
│                          │ **Constraints:** Prefers ESG     │
│                          │ companies                        │
│ Description              │ Investment amount: 50000.0 CHF.  │
│                          │ Risk profile: medium.            │
│                          │ Time horizon: long-term.         │
├──────────────────────────┴──────────────────────────────────┤
│  AI confidence score: 0.94  │  source: ai-chatbot           │
└─────────────────────────────────────────────────────────────┘
```

**Screenshot — Lead record in Salesforce CRM:**

![Salesforce Lead record](assets/Salesforce%20001.png)

---

## How it works — step by step

### 1. Agent conversation (CLI)

The agent greets the user and conducts a natural conversation to gather:

| Field | Type | Description |
|---|---|---|
| `first_name` | required | Client first name |
| `last_name` | required | Client last name |
| `email` | required | Client email address |
| `phone` | optional | Client phone number |
| `estimated_amount` | optional | Amount to invest (numeric) |
| `currency` | optional | Currency (CHF, EUR, USD, ...) |
| `risk_profile` | optional | `low` / `medium` / `high` |
| `time_horizon` | optional | `short-term` / `long-term` |
| `investment_intent` | optional | Structured summary of goals and motivations |

Each time the client provides a value, the agent calls `save_field` to record it in a shared in-memory dictionary.

The agent asks about investment goals and motivations (why they want to invest, desired outcome, sectors of interest, constraints) and composes a structured multi-point `investment_intent` description, for example:

```
**Goals:** Retirement savings and passive income
**Desired outcome:** Stable growth with moderate returns over 20 years
**Interests:** Dividend stocks, bonds, real estate funds
**Constraints:** Prefers ethical/ESG investments
```

### 2. Finishing the conversation

Once all required fields are collected (and as many optional fields as possible), the agent calls `finish_conversation`. This tool:

1. Validates that `first_name`, `last_name`, and `email` are present
2. Computes an AI confidence score: `0.7 + (optional fields filled / 5) * 0.3`
3. Builds a human-readable `AiInsights.summary` from investment profile fields
4. Constructs an `InquiryEvent` (nested dataclass, serialized to JSON)
5. Publishes the event to the Kafka topic `investment.inquiry.captured`

### 3. Kafka event

The event schema (`shared/inquiry_event.py`):

```json
{
  "event_id": "evt-a1b2c3d4",
  "event_type": "investment.inquiry.captured",
  "occurred_at": "2026-03-29T10:00:00+00:00",
  "source": "ai-chatbot",
  "customer": {
    "first_name": "Anna",
    "last_name": "Kowalska",
    "email": "anna@example.com",
    "phone": "+48 600 123 456"
  },
  "investment_profile": {
    "estimated_amount": 50000.0,
    "currency": "CHF",
    "risk_profile": "medium",
    "time_horizon": "long-term",
    "investment_intent": "**Goals:** Retirement savings\n**Desired outcome:** Stable growth"
  },
  "ai_insights": {
    "intent": "investment",
    "confidence": 0.94,
    "summary": "Investment amount: 50000.0 CHF. Risk profile: medium. Time horizon: long-term."
  }
}
```

### 4. Middleware consumer

The middleware (`middleware/`) runs as a separate long-lived process:

1. Authenticates with Salesforce using **OAuth 2.0 Client Credentials Flow** (External Client App)
2. Subscribes to the Kafka topic and blocks, waiting for events
3. On each event: deserializes the JSON back to `InquiryEvent` and calls `SalesforceClient.create_lead_from_inquiry()`

### 5. Salesforce Lead creation

The middleware posts to `POST /services/data/v59.0/sobjects/Lead` with these standard and custom fields:

| Salesforce field | Source |
|---|---|
| `FirstName` | `customer.first_name` |
| `LastName` | `customer.last_name` |
| `Email` | `customer.email` |
| `Phone` | `customer.phone` |
| `Company` | hardcoded `"Individual"` |
| `Description` | `ai_insights.summary` |
| `Risk_Profile__c` | `investment_profile.risk_profile` (capitalized) |
| `Estimated_Investment__c` | `investment_profile.estimated_amount` |
| `Time_Horizon__c` | `investment_profile.time_horizon` (title-cased) |
| `Investment_Intent__c` | `investment_profile.investment_intent` |

---

## Project structure

```
AI_Inquiry_to_Salesforce/
├── agent/
│   ├── agent.py               # CLI agent loop with tool-calling
│   ├── main.py                # Entry point: python -m agent.main
│   ├── openrouter_client.py   # httpx-based OpenRouter API client
│   ├── config.py              # Model, timeouts, paths
│   ├── prompts/
│   │   └── system.md          # System prompt for the LLM agent
│   └── tools/
│       ├── base_tool.py       # BaseTool with to_schema() and reset()
│       ├── save_field.py      # Saves a single collected field
│       └── finish_conversation.py  # Builds event, publishes to Kafka
├── middleware/
│   ├── main.py                # Entry point: python -m middleware.main
│   ├── consumer.py            # Kafka consumer loop
│   ├── salesforce_client.py   # Salesforce auth + Lead creation
│   └── config.py              # Loads Salesforce env vars
├── shared/
│   ├── inquiry_event.py       # InquiryEvent dataclass + JSON serialization
│   ├── kafka_producer.py      # Publishes InquiryEvent to Kafka
│   └── kafka_consumer.py      # Consumes and deserializes InquiryEvent
├── docker-compose.yml         # Kafka 3.9.0 (KRaft mode, no ZooKeeper)
├── requirements.txt
└── .env.example
```

---

## Salesforce setup

### External Client App (OAuth 2.0 Client Credentials)

1. Go to **Setup → App Manager → New External Client App**
2. Enable **OAuth Settings**
3. Select flow: **Client Credentials**
4. Grant access to a dedicated integration user
5. Copy **Consumer Key** (`SALESFORCE_CLIENT_ID`) and **Consumer Secret** (`SALESFORCE_CLIENT_SECRET`)

### Custom Lead fields

Create these fields on the **Lead** object (**Setup → Object Manager → Lead → Fields & Relationships → New**):

| Label | API Name | Type | Notes |
|---|---|---|---|
| Risk Profile | `Risk_Profile__c` | Picklist | Values: `Low`, `Medium`, `High` |
| Estimated Investment | `Estimated_Investment__c` | Number (16, 2) | |
| Time Horizon | `Time_Horizon__c` | Picklist | Values: `Short-Term`, `Long-Term` |
| Investment Intent | `Investment_Intent__c` | Long Text Area (32768) | |

> **Important:** Picklist values are case-sensitive. Use `Low` / `Medium` / `High` and `Short-Term` / `Long-Term` exactly — the middleware applies `.capitalize()` and `.title()` to match these.

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

```env
# OpenRouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o-mini   # or e.g. google/gemini-3-flash-preview

# Kafka
KAFKA_BROKER=localhost:9092

# Salesforce
SALESFORCE_CLIENT_ID=your-consumer-key
SALESFORCE_CLIENT_SECRET=your-consumer-secret
SALESFORCE_INSTANCE_URL=https://your-instance.my.salesforce.com
```

> Do not wrap values in quotes in `.env`.

---

## Running the project

### Prerequisites

- Python 3.11+
- Docker Desktop running

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Kafka

```bash
docker compose up -d
```

### 3. Start the middleware (in a separate terminal)

```bash
source venv/bin/activate
python3 -m middleware.main
```

Expected output:
```
[salesforce] authenticated via client credentials
[middleware] starting, waiting for investment inquiries...
```

### 4. Start the agent (in another terminal)

```bash
source venv/bin/activate
python3 -m agent.main
# or with verbose tool-call logging:
python3 -m agent.main --verbose
```

Expected output:
```
Agent: Hello! I'm here to help connect you with our investment advisory team. May I start with your name?
You: _
```

### 5. Have a conversation

Talk to the agent. Once all required fields are collected and the agent calls `finish_conversation`, you will see in the middleware terminal:

```
[middleware] received inquiry: evt-a1b2c3d4 | Anna Kowalska | confidence: 0.94
[salesforce] created lead: 00Q... | Anna Kowalska | confidence: 0.94
[middleware] lead created in Salesforce: 00Q...
```

The Lead will appear in Salesforce under **Leads** with all custom fields populated.

---

## Technology stack

| Component | Technology |
|---|---|
| LLM | OpenRouter (Claude, GPT, Gemini — configurable) |
| Agent framework | Custom tool-calling loop (function calling via OpenRouter) |
| Event bus | Apache Kafka 3.9.0 (KRaft mode, Docker) |
| Kafka client | kafka-python |
| HTTP client | httpx |
| CRM | Salesforce (REST API v59.0) |
| Auth | OAuth 2.0 Client Credentials Flow |
