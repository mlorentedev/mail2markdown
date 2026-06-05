from __future__ import annotations

from pathlib import Path

from mail2markdown.core.extractors.base import MessageSource, RawMessage
from mail2markdown.core.extractors.outlook import OutlookMessageSource
from mail2markdown.core.extractors.thunderbird import ThunderbirdMessageSource

__all__ = [
    "MessageSource",
    "RawMessage",
    "OutlookMessageSource",
    "ThunderbirdMessageSource",
    "create_source",
]


def create_source(provider: str, **kwargs: object) -> MessageSource:
    """Factory function to create the appropriate MessageSource."""
    if provider == "outlook":
        mailbox = kwargs.get("mailbox")
        return OutlookMessageSource(mailbox=mailbox if isinstance(mailbox, str) else None)
    if provider == "thunderbird":
        profile_path = kwargs.get("profile_path")
        if not profile_path:
            raise ValueError("Thunderbird provider requires 'profile_path' argument.")
        assert isinstance(profile_path, (str, Path))
        return ThunderbirdMessageSource(profile_path=Path(profile_path))
    raise ValueError(f"Unknown provider: {provider}. Supported: outlook, thunderbird.")
