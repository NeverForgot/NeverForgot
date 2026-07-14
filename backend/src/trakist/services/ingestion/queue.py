"""File de messages inter-services (cahier des charges §5.3 : Redis Streams ou
SQS). Implementation de depart sur Redis Streams, suffisante pour le MVP.
"""

from __future__ import annotations

import json
from dataclasses import asdict

import redis

from trakist.config import get_settings
from trakist.services.ingestion.connectors import RawMessage

STREAM_NAME = "trakist:raw-messages"


class MessageQueue:
    def __init__(self, redis_url: str | None = None) -> None:
        self._client = redis.Redis.from_url(redis_url or get_settings().redis_url)

    def publish(self, message: RawMessage) -> str:
        return self._client.xadd(STREAM_NAME, {"payload": json.dumps(asdict(message))})

    def consume(self, count: int = 10, block_ms: int = 5000) -> list[RawMessage]:
        response = self._client.xread({STREAM_NAME: "$"}, count=count, block=block_ms)
        messages: list[RawMessage] = []
        for _stream, entries in response:
            for _entry_id, fields in entries:
                payload = json.loads(fields[b"payload"])
                messages.append(RawMessage(**payload))
        return messages
