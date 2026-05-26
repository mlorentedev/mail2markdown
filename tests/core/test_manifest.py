from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from mapi_msg_dumper.core.manifest import ManifestRow, ManifestWriter


def test_manifest_writer_creates_csv_and_jsonl(tmp_path: Path) -> None:
    csv_path = tmp_path / "manifest.csv"
    jsonl_path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(csv_path, jsonl_path)

    row = ManifestRow(
        entry_id="abc123",
        received_at=datetime(2026, 5, 26, 12, 0, 0),
        subject="Test email",
        sender_name="User",
        sender_email="user@test.com",
        to="me@test.com",
        cc="",
        folder=r"Technical support\TOPAZ",
        tags="test",
        msg_path=r"exports\2026\05\test.msg",
        md_path=r"exports\markdown\2026\05\test.md",
        window_start="2026-05-01",
        window_end="2026-06-01",
    )
    writer.write(row)

    assert csv_path.exists()
    assert jsonl_path.exists()

    csv_text = csv_path.read_text(encoding="utf-8")
    assert "abc123" in csv_text
    assert "Test email" in csv_text
    assert "entry_id" in csv_text.splitlines()[0]

    jsonl_lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(jsonl_lines) == 1
    parsed = json.loads(jsonl_lines[0])
    assert parsed["entry_id"] == "abc123"
    assert parsed["received_at"] == "2026-05-26T12:00:00"


def test_manifest_writer_dedup_on_rerun(tmp_path: Path) -> None:
    csv_path = tmp_path / "manifest.csv"
    jsonl_path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(csv_path, jsonl_path)

    row = ManifestRow(
        entry_id="dedup-1",
        received_at=datetime(2026, 1, 1, 0, 0, 0),
        subject="First",
        sender_name="A",
        sender_email="a@t.com",
        to="me@t.com",
        cc="",
        folder="Inbox",
        tags="",
        msg_path="a.msg",
        md_path="",
        window_start="2026-01-01",
        window_end="2026-02-01",
    )
    writer.write(row)

    assert writer.already_written("dedup-1")
    assert not writer.already_written("dedup-2")

    writer.write(row)
    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_manifest_writer_loads_existing_ids_on_init(tmp_path: Path) -> None:
    csv_path = tmp_path / "manifest.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("entry_id,received_at\nknown-1,2026-01-01\nknown-2,2026-01-02\n", encoding="utf-8")

    jsonl_path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(csv_path, jsonl_path)

    assert writer.already_written("known-1")
    assert writer.already_written("known-2")
    assert not writer.already_written("unknown-3")


def test_manifest_writer_empty_paths(tmp_path: Path) -> None:
    csv_path = tmp_path / "manifest.csv"
    jsonl_path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(csv_path, jsonl_path)

    row = ManifestRow(
        entry_id="no-md",
        received_at=datetime(2026, 3, 15, 10, 30, 0),
        subject="No markdown",
        sender_name="",
        sender_email="",
        to="",
        cc="",
        folder="Inbox",
        tags="",
        msg_path="nopath.msg",
        md_path="",
        window_start="2026-03-01",
        window_end="2026-04-01",
    )
    writer.write(row)
    assert csv_path.exists()
    assert jsonl_path.exists()
