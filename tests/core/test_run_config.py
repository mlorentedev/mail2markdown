import json
from pathlib import Path

import pytest

from mail2markdown.core.run_config import load_run_config


def test_load_run_config_defaults(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text("{}", encoding="utf-8")

    parsed = load_run_config(config)

    assert parsed.folder_paths == ["Inbox"]
    assert parsed.output_root == tmp_path / "exports"
    assert parsed.window.cadence == "monthly"
    assert parsed.window.start_date is None
    assert parsed.window.end_date is None
    assert parsed.window.manual is False
    assert parsed.window.checkpoint_file is None
    assert parsed.window.max_windows is None
    assert parsed.output.markdown_root is None
    assert parsed.dry_run is False
    assert parsed.verbose is False
    assert parsed.output.manifest is False
    assert parsed.output.routing_report is False
    assert parsed.output.vault_root is None
    assert parsed.output.sync is False


def test_load_run_config_with_folders_and_all_options(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps(
            {
                "folders": [r"Inbox\Finance", r"Inbox\HR"],
                "cadence": "biweekly",
                "manual": True,
                "start_date": "2020-01-01",
                "end_date": "2020-01-31",
                "output_root": "./exports",
                "checkpoint_file": "./exports/checkpoints/folder.json",
                "max_windows": 2,
                "markdown_root": "./exports/markdown",
                "dry_run": True,
                "verbose": True,
            }
        ),
        encoding="utf-8",
    )

    parsed = load_run_config(config)

    assert parsed.folder_paths == [r"Inbox\Finance", r"Inbox\HR"]
    assert parsed.output_root == tmp_path / "exports"
    assert parsed.window.cadence == "biweekly"
    assert parsed.window.start_date == "2020-01-01"
    assert parsed.window.end_date == "2020-01-31"
    assert parsed.window.manual is True
    assert parsed.window.checkpoint_file == tmp_path / "exports" / "checkpoints" / "folder.json"
    assert parsed.window.max_windows == 2
    assert parsed.output.markdown_root == tmp_path / "exports" / "markdown"
    assert parsed.dry_run is True
    assert parsed.verbose is True
    assert parsed.output.manifest is False
    assert parsed.output.routing_report is False
    assert parsed.output.vault_root is None
    assert parsed.output.sync is False


def test_load_run_config_rejects_invalid_max_windows(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text(json.dumps({"max_windows": 0}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_run_config(config)


def test_load_run_config_accepts_utf8_bom(tmp_path: Path) -> None:
    run_config = tmp_path / "run.json"
    payload = json.dumps({"folder": r"Shared Inbox\Product-A", "manual": True, "start_date": "2025-01-15"})
    run_config.write_bytes(payload.encode("utf-8-sig"))

    parsed = load_run_config(run_config)

    assert parsed.folder_paths == [r"Shared Inbox\Product-A"]
    assert parsed.window.manual is True
    assert parsed.window.start_date == "2025-01-15"
