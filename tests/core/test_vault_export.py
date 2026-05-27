from __future__ import annotations

from pathlib import Path

import pytest

from mail2markdown.core.vault_export import vault_import


def test_vault_import_copies_files_by_product(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "entry_id,received_at,subject,folder,msg_path,md_path\n"
        "e1,2026-01-15T10:00:00,Sub A,Technical support\\TOPAZ,a.msg,a.md\n"
        "e2,2026-02-20T12:00:00,Sub B,Technical support\\EMERALD,b.msg,b.md\n",
        encoding="utf-8",
    )

    md_root = tmp_path / "markdown"
    md_root.mkdir()
    (md_root / "a.md").write_text("content a", encoding="utf-8")
    (md_root / "b.md").write_text("content b", encoding="utf-8")

    vault_root = tmp_path / "vault"
    count = vault_import(manifest, md_root, vault_root)

    assert count == 2
    assert (vault_root / "10_projects" / "mapi-msg-dumper" / "extractions" / "TOPAZ" / "a.md").exists()
    assert (vault_root / "10_projects" / "mapi-msg-dumper" / "extractions" / "EMERALD" / "b.md").exists()


def test_vault_import_skips_missing_markdown(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "entry_id,received_at,subject,folder,msg_path,md_path\n"
        "e1,2026-01-01T00:00:00,Subject,Inbox,a.msg,missing.md\n",
        encoding="utf-8",
    )

    md_root = tmp_path / "markdown"
    md_root.mkdir()

    count = vault_import(manifest, md_root, tmp_path / "vault")
    assert count == 0


def test_vault_import_raises_on_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Manifest not found"):
        vault_import(tmp_path / "none.csv", tmp_path, tmp_path / "vault")


def test_vault_import_raises_on_missing_markdown_root(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("entry_id\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Markdown root not found"):
        vault_import(manifest, tmp_path / "nonexistent", tmp_path / "vault")
