import os
from kafka import KafkaProducer as _KafkaProducer
from dotenv import load_dotenv

from shared.inquiry_event import InquiryEvent

load_dotenv()

TOPIC = "investment.inquiry.captured"


class KafkaProducer:
    def __init__(self):
        self._producer = _KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
            value_serializer=lambda v: v.encode("utf-8"),
        )

    def publish_inquiry(self, event: InquiryEvent) -> None:
        self._producer.send(TOPIC, event.to_json())
        self._producer.flush()
        print(f"[kafka] published inquiry: {event.event_id} | {event.customer.first_name} {event.customer.last_name} <{event.customer.email}>")

    def close(self) -> None:
        self._producer.close()
