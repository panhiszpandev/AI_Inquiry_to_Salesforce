import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.kafka_consumer import KafkaConsumer
from middleware.salesforce_client import SalesforceClient


def run():
    print("[middleware] starting, waiting for investment inquiries...")
    sf = SalesforceClient()
    consumer = KafkaConsumer(group_id="middleware")

    try:
        for event in consumer:
            print(f"[middleware] received inquiry: {event.event_id} | {event.customer.first_name} {event.customer.last_name} | confidence: {event.ai_insights.confidence}")
            try:
                lead_id = sf.create_lead_from_inquiry(event)
                print(f"[middleware] lead created in Salesforce: {lead_id}")
            except Exception as e:
                print(f"[middleware] failed to create lead: {e}")
    finally:
        consumer.close()
