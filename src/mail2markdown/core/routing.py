from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from mail2markdown.core.folders_config import normalize_folder_path


def build_routing_report(manifest_path: Path, routing_root: Path) -> None:
    if not manifest_path.exists():
        raise ValueError(f"Manifest not found: {manifest_path}")

    products: dict[str, list[dict[str, str]]] = defaultdict(list)

    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            folder = row.get("folder", "")
            product = _derive_product(folder)
            products[product].append(row)

    _write_summary(products, routing_root)

    for product, rows in sorted(products.items()):
        _write_product_csv(product, rows, routing_root)


def _derive_product(folder: str) -> str:
    normalized = normalize_folder_path(folder)
    parts = normalized.split("\\")
    return parts[-1] if parts else "Unknown"


def _write_summary(products: dict[str, list[dict[str, str]]], routing_root: Path) -> None:
    routing_root.mkdir(parents=True, exist_ok=True)
    path = routing_root / "summary.csv"

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product", "count", "first_date", "last_date"])
        for product, rows in sorted(products.items()):
            dates = [_parse_date(r.get("received_at", "")) for r in rows]
            valid_dates = [d for d in dates if d is not None]
            first = min(valid_dates).date().isoformat() if valid_dates else ""
            last = max(valid_dates).date().isoformat() if valid_dates else ""
            writer.writerow([product, len(rows), first, last])


def _write_product_csv(product: str, rows: list[dict[str, str]], routing_root: Path) -> None:
    path = routing_root / f"{_safe_filename(product)}.csv"
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _safe_filename(product: str) -> str:
    result = product.lower().replace("\\", "-").replace("/", "-")
    result = "".join(c if c.isalnum() or c in "-_" else "_" for c in result)
    return result.strip("_") or "unknown"


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
