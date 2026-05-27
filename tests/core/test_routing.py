from __future__ import annotations

from pathlib import Path

import pytest

from mail2markdown.core.routing import build_routing_report


def test_build_routing_report_creates_summary_and_product_files(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "entry_id,received_at,subject,folder\n"
        "e1,2026-01-15T10:00:00,Sub A,Technical support\\TOPAZ\n"
        "e2,2026-02-20T12:00:00,Sub B,Technical support\\EMERALD\n"
        "e3,2026-03-10T08:00:00,Sub C,Technical support\\TOPAZ\n",
        encoding="utf-8",
    )

    routing_root = tmp_path / "routing"
    build_routing_report(manifest, routing_root)

    summary = routing_root / "summary.csv"
    assert summary.exists()
    summary_text = summary.read_text(encoding="utf-8")
    assert "product,count,first_date,last_date" in summary_text
    assert "TOPAZ,2,2026-01-15,2026-03-10" in summary_text
    assert "EMERALD,1,2026-02-20,2026-02-20" in summary_text

    topaz = routing_root / "topaz.csv"
    assert topaz.exists()
    emerald = routing_root / "emerald.csv"
    assert emerald.exists()
    topaz_text = topaz.read_text(encoding="utf-8")
    assert topaz_text.count("TOPAZ") == 2


def test_build_routing_report_skips_inbox(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "entry_id,received_at,subject,folder\n"
        "e1,2026-01-01T00:00:00,Inbox mail,Inbox\n",
        encoding="utf-8",
    )

    routing_root = tmp_path / "routing"
    build_routing_report(manifest, routing_root)

    summary = routing_root / "summary.csv"
    assert "Inbox" in summary.read_text(encoding="utf-8")
    inbox = routing_root / "inbox.csv"
    assert inbox.exists()


def test_build_routing_report_raises_on_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Manifest not found"):
        build_routing_report(tmp_path / "nonexistent.csv", tmp_path / "routing")


def test_build_routing_report_empty_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("entry_id,received_at,subject,folder\n", encoding="utf-8")

    routing_root = tmp_path / "routing"
    build_routing_report(manifest, routing_root)

    summary = routing_root / "summary.csv"
    assert summary.exists()
    assert summary.read_text(encoding="utf-8").strip().endswith("product,count,first_date,last_date")
