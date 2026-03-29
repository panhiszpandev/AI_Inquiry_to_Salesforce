import os
from kafka import KafkaConsumer as _KafkaConsumer
from dotenv import load_dotenv

from shared.inquiry_event import InquiryEvent

load_dotenv()

TOPIC = "investment.inquiry.captured"


class KafkaConsumer:
    def __init__(self, group_id: str = "middleware"):
        self._consumer = _KafkaConsumer(
            TOPIC,
            bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda v: v.decode("utf-8"),
        )

    def __iter__(self):
        for record in self._consumer:
            yield InquiryEvent.from_json(record.value)

    def close(self) -> None:
        self._consumer.close()
