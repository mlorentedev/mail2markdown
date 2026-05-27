from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class RawMessage:
    entry_id: str
    subject: str
    sender_name: str
    sender_email: str
    to: str
    cc: str
    received_at: datetime
    body: str
    raw: object


class MessageSource(ABC):
    """Provider-specific message retrieval interface."""

    @abstractmethod
    def iter_messages(
        self,
        folder_path: str,
        start_date: date,
        end_date: date,
    ) -> Iterator[RawMessage]:
        """Yield messages within [start_date, end_date) for the given folder."""
        ...

    @abstractmethod
    def save_message(self, msg: RawMessage, path: Path) -> None:
        """Save the raw message to the given path."""
        ...

    @abstractmethod
    def resolve_folder_source(self, folder_path: str) -> str | None:
        """Return the underlying store/folder source path, or None if not applicable."""
        ...
