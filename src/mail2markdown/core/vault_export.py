from __future__ import annotations

import shutil
from pathlib import Path

from mail2markdown.core.routing import _derive_product


def vault_import(manifest_path: Path, markdown_root: Path, vault_root: Path) -> int:
    if not manifest_path.exists():
        raise ValueError(f"Manifest not found: {manifest_path}")
    if not markdown_root.exists():
        raise ValueError(f"Markdown root not found: {markdown_root}")

    import csv

    imported = 0
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            md_rel = (row.get("md_path") or "").strip()
            if not md_rel:
                continue
            md_path = Path(md_rel)
            if not md_path.is_absolute():
                md_path = markdown_root / md_path
            if not md_path.exists():
                continue

            folder = row.get("folder", "")
            product = _derive_product(folder)
            dest = vault_root / "10_projects" / "mapi-msg-dumper" / "extractions" / product
            dest.mkdir(parents=True, exist_ok=True)
            dest_path = dest / md_path.name
            if not dest_path.exists():
                shutil.copy2(md_path, dest_path)
                imported += 1

    return imported
