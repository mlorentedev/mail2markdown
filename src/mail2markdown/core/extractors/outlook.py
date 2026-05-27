from __future__ import annotations

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

    def __init__(self) -> None:  # noqa: D107
        self._namespace: Any | None = None

    def _ensure_namespace(self) -> Any:
        if self._namespace is None:
            import win32com.client
        self._namespace = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")("Outlook.Application").GetNamespace("MAPI")
        return self._namespace
    def iter_messages(  # noqa: D102
        self,
        folder_path: str,
        start_date: Any,
        end_date: Any,
    ) -> Iterator[RawMessage]:
        namespace = self._ensure_namespace()
        folder = _resolve_folder(namespace, folder_path)
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


def _resolve_folder(namespace: Any, folder_path: str) -> Any:
    parts = [part.strip() for part in folder_path.split("\\") if part.strip()]
    if not parts:
        raise ValueError("Folder path cannot be empty.")

    if parts[0].lower() == "inbox":
        return _walk_folder_path(namespace.GetDefaultFolder(OL_FOLDER_INBOX), parts[1:])

    try:
        root_folder = namespace.DefaultStore.GetRootFolder()
    except Exception as exc:
        raise ValueError("Cannot resolve default Outlook store root folder.") from exc
    return _walk_folder_path(root_folder, parts)


def _walk_folder_path(start_folder: Any, segments: list[str]) -> Any:
    folder = start_folder
    for segment in segments:
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