from datetime import date
from pathlib import Path

from mail2markdown.core.checkpoint import load_checkpoint, save_checkpoint


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    assert load_checkpoint(checkpoint) is None

    save_checkpoint(checkpoint, date(2024, 5, 1))
    assert load_checkpoint(checkpoint) == date(2024, 5, 1)
