from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Attachment:
    file_id: str
    file_name: str
    media_type: str


@dataclass
class Message:
    message_id: int
    timestamp: datetime
    text: str
    source_chat: int
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class State:
    last_update_id: int
    last_run_at: datetime


@dataclass
class DailySummary:
    date: str
    messages: list[Message] = field(default_factory=list)
