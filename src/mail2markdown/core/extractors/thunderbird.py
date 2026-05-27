from __future__ import annotations

import hashlib
import mailbox
from datetime import datetime
from email.header import decode_header
from email.policy import default
from pathlib import Path
from typing import Any, Iterator

from mail2markdown.core.extractors.base import MessageSource, RawMessage


class ThunderbirdMessageSource(MessageSource):
    """Retrieves messages from Thunderbird .mbox stores."""

    def __init__(self, profile_path: Path) -> None:
        self._profile = profile_path.resolve()

    def iter_messages(  # noqa: D102
        self,
        folder_path: str,
        start_date: Any,
        end_date: Any,
    ) -> Iterator[RawMessage]:
        try:
            mbox_path = self._resolve_mbox_path(folder_path)
        except (ValueError, OSError):
            return
        if not mbox_path.exists():
            return

        mb = mailbox.mbox(str(mbox_path))
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        for msg in mb:
            received_at = self._parse_date(msg.get("Date", ""))
            if received_at is None or received_at < start_dt or received_at >= end_dt:
                continue

            entry_id = self._compute_entry_id(msg)
            subject = self._decode_header_value(msg.get("Subject", ""))
            sender_name, sender_email = self._parse_sender(msg.get("From", ""))

            yield RawMessage(
                entry_id=entry_id,
                subject=subject,
                sender_name=sender_name,
                sender_email=sender_email,
                to=self._decode_header_value(msg.get("To", "")),
                cc=self._decode_header_value(msg.get("CC", "")),
                received_at=received_at,
                body=self._extract_body(msg),
                raw=msg,
            )

    def save_message(self, msg: RawMessage, path: Path) -> None:  # noqa: D102
        path.parent.mkdir(parents=True, exist_ok=True)
        import io

        raw_msg: Any = msg.raw
        buf = io.StringIO()
        if hasattr(raw_msg, "write_to"):
            raw_msg.write_to(buf, policy=default)
        else:
            import email.generator

            email.generator.Generator(buf, policy=default).flatten(raw_msg)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(buf.getvalue())

    def resolve_folder_source(self, folder_path: str) -> str | None:  # noqa: D102
        try:
            return str(self._resolve_mbox_path(folder_path))
        except (ValueError, OSError):
            return None

    def _resolve_mbox_path(self, folder_path: str) -> Path:
        parts = folder_path.replace("\\", "/").split("/")
        parts = [p for p in parts if p]
        if not parts:
            raise ValueError("Folder path cannot be empty.")

        # Check for ImapMail pattern: ImapMail/server.example.com/FolderName
        if parts[0] == "ImapMail":
            if len(parts) < 3:
                raise ValueError("ImapMail path must include server and folder name.")
            server = parts[1]
            folder_name = "/".join(parts[2:])
            base = self._profile / "ImapMail" / server / folder_name
        elif parts[0] == "Mail":
            # local-folders or Mail/accountname/...
            remaining = "/".join(parts[1:])
            base = self._profile / "Mail" / remaining
        else:
            # Assume local-folders shorthand
            base = self._profile / "Mail" / "local-folders" / folder_path.replace("\\", "/")

        # Try without extension first, then .mbox
        if base.exists():
            return base
        mbox_path = base.with_suffix(".mbox")
        if mbox_path.exists():
            return mbox_path
        raise ValueError(f"No mbox found for folder: {folder_path}")

    def _parse_date(self, date_str: str) -> datetime | None:
        if not date_str:
            return None
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%a, %d %b %Y %H:%M:%S %z",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=None)
            except (ValueError, TypeError):
                continue
        return None

    def _compute_entry_id(self, msg: Any) -> str:
        hash_input = f"{msg.get('From', '')}|{msg.get('Subject', '')}|{msg.get('Date', '')}|{self._extract_body(msg)}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

    def _decode_header_value(self, value: str) -> str:
        if not value:
            return ""
        parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                parts.append(part)
        return " ".join(parts).strip()

    def _parse_sender(self, from_header: str) -> tuple[str, str]:
        if not from_header:
            return ("", "")
        from email.utils import parseaddr
        name, email_addr = parseaddr(from_header)
        name = self._decode_header_value(name) if name else ""
        return (name, email_addr)

    def _extract_body(self, msg: Any) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    continue
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(charset, errors="replace")
                if content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        text = payload.decode(charset, errors="replace")
                        return self._strip_html(text)
            # Fallback: first text part
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(charset, errors="replace")
            return ""
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(charset, errors="replace")
        return ""

    @staticmethod
    def _strip_html(html: str) -> str:
        result = html
        for tag in ["br", "p", "div", "blockquote"]:
            result = result.replace(f"<{tag}>", "\n").replace(f"</{tag}>", "\n")
        import re

        result = re.sub(r"<[^>]+>", "", result)
        result = result.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()
