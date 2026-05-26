from __future__ import annotations

import csv
import json
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ManifestRow:
    entry_id: str
    received_at: datetime
    subject: str
    sender_name: str
    sender_email: str
    to: str
    cc: str
    folder: str
    tags: str
    msg_path: str
    md_path: str
    window_start: str
    window_end: str


FIELD_NAMES = [f.name for f in fields(ManifestRow)]


class ManifestWriter:
    def __init__(self, csv_path: Path, jsonl_path: Path) -> None:
        self._csv_path = csv_path
        self._jsonl_path = jsonl_path
        self._known_ids: set[str] = set()
        self._loaded = False

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._csv_path.exists():
            return
        with self._csv_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                eid = (row.get("entry_id") or "").strip()
                if eid:
                    self._known_ids.add(eid)

    def already_written(self, entry_id: str) -> bool:
        self.ensure_loaded()
        return entry_id in self._known_ids

    def write(self, row: ManifestRow) -> None:
        self.ensure_loaded()
        if row.entry_id in self._known_ids:
            return
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self._csv_path.exists()
        with self._csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(_row_to_dict(row))

        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self._jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(_row_to_dict(row), ensure_ascii=False) + "\n")

        self._known_ids.add(row.entry_id)


def _row_to_dict(row: ManifestRow) -> dict[str, str]:
    d: dict[str, str] = {}
    for f in fields(ManifestRow):
        value = getattr(row, f.name)
        if isinstance(value, datetime):
            d[f.name] = value.isoformat()
        else:
            d[f.name] = str(value)
    return d
