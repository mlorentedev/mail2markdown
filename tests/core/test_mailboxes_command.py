from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

# Mock win32com so tests run on Linux without pywin32
_mock_win32 = MagicMock()
_mock_win32_client = MagicMock()
sys.modules["win32com"] = _mock_win32
sys.modules["win32com.client"] = _mock_win32_client
sys.modules["win32com.client.constants"] = MagicMock()

import pytest
from typer.testing import CliRunner

from mail2markdown.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestMailboxesCommand:
    def test_list_stores(self, runner: CliRunner) -> None:
        import win32com.client
        store1 = MagicMock()
        store1.Name = "John Doe"
        store1.StoreType = "Exchange"
        store2 = MagicMock()
        store2.Name = "Shared Mailbox - Team"
        store2.StoreType = "Mailbox"
        store3 = MagicMock()
        store3.Name = "Archive"
        store3.StoreType = "Archive"
        ns = MagicMock()
        ns.Stores = [store1, store2, store3]
        win32com.client.Dispatch.return_value.GetNamespace.return_value = ns

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code == 0
        assert "John Doe" in result.stdout
        assert "Shared Mailbox - Team" in result.stdout
        assert "Archive" in result.stdout
        assert "3 store(s)" in result.stdout

    def test_outlook_connection_failure(self, runner: CliRunner) -> None:
        import win32com.client
        win32com.client.Dispatch.side_effect = Exception("Outlook not running")

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code != 0
        assert "Cannot connect to Outlook" in result.stdout

        # Reset for other tests
        win32com.client.Dispatch.side_effect = None
        win32com.client.Dispatch.reset_mock()

    def test_empty_stores(self, runner: CliRunner) -> None:
        import win32com.client
        win32com.client.Dispatch.reset_mock()
        ns = MagicMock()
        ns.Stores = []
        win32com.client.Dispatch.return_value.GetNamespace.return_value = ns

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code == 0
        assert "0 store(s)" in result.stdout
