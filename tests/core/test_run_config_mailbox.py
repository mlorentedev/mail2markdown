import json
from pathlib import Path

from mail2markdown.core.run_config import load_run_config


def test_load_run_config_with_mailbox(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps({
            "folder": r"Shared Inbox\Product-A",
            "manual": True,
            "start_date": "2025-01-01",
            "mailbox": "Shared Mailbox - Team",
        }),
        encoding="utf-8",
    )

    parsed = load_run_config(config)

    assert parsed.provider.mailbox == "Shared Mailbox - Team"


def test_load_run_config_mailbox_none_by_default(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text("{}", encoding="utf-8")

    parsed = load_run_config(config)

    assert parsed.provider.mailbox is None


def test_load_run_config_with_empty_mailbox(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps({
            "folder": r"Inbox",
            "mailbox": "",
        }),
        encoding="utf-8",
    )

    parsed = load_run_config(config)

    assert parsed.provider.mailbox is None


def test_load_run_config_mailbox_with_other_provider_config(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps({
            "provider": "thunderbird",
            "folder": r"Inbox",
            "mailbox": "Personal Mailbox",
            "thunderbird": {"profile_path": "/tmp/profile"},
        }),
        encoding="utf-8",
    )

    parsed = load_run_config(config)

    assert parsed.provider.provider_name == "thunderbird"
    assert parsed.provider.mailbox == "Personal Mailbox"
    assert parsed.provider.thunderbird_config == {"profile_path": "/tmp/profile"}
