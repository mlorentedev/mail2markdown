from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from mail2markdown.core.extractors.base import MessageSource, RawMessage
from mail2markdown.core.planning import Window, build_received_filter

OL_FOLDER_INBOX = 6
OL_MAIL_ITEM = 43
OL_MSG_UNICODE = 3


class OutlookMessageSource(MessageSource):
    """Retrieves messages from Outlook via COM/MAPI."""

    def __init__(self, mailbox: str | None = None) -> None:  # noqa: D107
        self._namespace: Any | None = None
        self._mailbox: str | None = mailbox
        self._store: Any | None = None

    def _ensure_namespace(self) -> Any:
        if self._namespace is None:
            import win32com.client

            self._namespace = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        return self._namespace

    def _ensure_store(self) -> Any:
        namespace = self._ensure_namespace()
        if self._mailbox is None:
            return namespace.DefaultStore.GetRootFolder()
        return _resolve_store(namespace, self._mailbox)

    def iter_messages(  # noqa: D102
        self,
        folder_path: str,
        start_date: Any,
        end_date: Any,
    ) -> Iterator[RawMessage]:
        self._ensure_namespace()  # ensures COM connection is established
        root_folder = self._ensure_store()
        folder = _walk_folder_path(root_folder, folder_path.split(chr(92)))
        items = folder.Items
        items.Sort("[ReceivedTime]", False)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())
        window = Window(start=start_dt, end=end_dt)
        scoped = items.Restrict(build_received_filter(window))

        item = scoped.GetFirst()
        while item is not None:
            try:
                if int(getattr(item, "Class", 0)) != OL_MAIL_ITEM:
                    item = scoped.GetNext()
                    continue

                entry_id = str(getattr(item, "EntryID", ""))
                subject = str(getattr(item, "Subject", ""))
                received_at = _received_datetime(item)

                yield RawMessage(
                    entry_id=entry_id,
                    subject=subject,
                    sender_name=_safe_text(getattr(item, "SenderName", "")),
                    sender_email=_safe_text(getattr(item, "SenderEmailAddress", "")),
                    to=_safe_text(getattr(item, "To", "")),
                    cc=_safe_text(getattr(item, "CC", "")),
                    received_at=received_at,
                    body=_safe_text(getattr(item, "Body", "")),
                    raw=item,
                )
            finally:
                item = scoped.GetNext()

    def save_message(self, msg: RawMessage, path: Path) -> None:  # noqa: D102
        path.parent.mkdir(parents=True, exist_ok=True)
        item: Any = msg.raw
        item.SaveAs(str(path), OL_MSG_UNICODE)

    def resolve_folder_source(self, folder_path: str) -> str | None:  # noqa: D102
        return folder_path

    def get_store_hash(self) -> str:
        """Return first 8 chars of SHA1 hash of store name for checkpoint isolation."""
        store = self._ensure_store()
        store_name = str(getattr(store, "Name", "default"))
        return hashlib.sha1(store_name.encode("utf-8")).hexdigest()[:8]


def _resolve_store(namespace: Any, mailbox_name: str) -> Any:
    """Find a store by display name (case-insensitive).

    Raises ValueError if not found or if multiple stores match.
    """
    stores = namespace.Stores
    matches: list[str] = []
    for store in stores:
        store_name = str(getattr(store, "Name", "")).strip()
        if store_name.lower() == mailbox_name.lower():
            matches.append(store_name)

    if not matches:
        available = [str(getattr(s, "Name", "")).strip() for s in stores]
        raise ValueError(
            f'Mailbox "{mailbox_name}" not found. Available: {", ".join(available)}'
        )

    if len(matches) > 1:
        raise ValueError(
            f'Ambiguous mailbox "{mailbox_name}". Matches: {", ".join(matches)}'
        )

    # Return the root folder of the matching store
    for store in stores:
        if str(getattr(store, "Name", "")).strip().lower() == mailbox_name.lower():
            return store.GetRootFolder()

    raise ValueError(f'Mailbox "{mailbox_name}" matched but root folder unavailable.')


def _walk_folder_path(start_folder: Any, segments: list[str]) -> Any:
    folder = start_folder
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        folder = _get_child_folder(folder, segment)
    return folder


def _get_child_folder(parent: Any, segment: str) -> Any:
    try:
        return parent.Folders.Item(segment)
    except Exception:
        count = int(getattr(parent.Folders, "Count", 0))
        for index in range(1, count + 1):
            child = parent.Folders.Item(index)
            if str(getattr(child, "Name", "")).strip().lower() == segment.lower():
                return child
    parent_name = str(getattr(parent, "Name", "<root>"))
    raise ValueError(f"Folder segment '{segment}' not found under '{parent_name}'.")


def _received_datetime(item: Any) -> Any:
    received = getattr(item, "ReceivedTime", None)
    if isinstance(received, datetime):
        return received.replace(tzinfo=None)
    raise ValueError("Item has no valid ReceivedTime.")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
