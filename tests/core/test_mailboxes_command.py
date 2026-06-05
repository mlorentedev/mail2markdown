"""Tests for mailboxes discovery CLI command."""

from __future__ import annotations

import sys

# Ensure win32com is mocked from conftest.py
_mock_win32 = sys.modules["win32com"]
_mock_win32_client = sys.modules["win32com.client"]

import pytest
from typer.testing import CliRunner

from mail2markdown.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestMailboxesCommand:
    def test_list_stores(self, runner: CliRunner) -> None:
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
        _mock_win32_client.Dispatch.return_value.GetNamespace.return_value = ns

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code == 0
        assert "John Doe" in result.stdout
        assert "Shared Mailbox - Team" in result.stdout
        assert "Archive" in result.stdout
        assert "3 store(s)" in result.stdout

    def test_outlook_connection_failure(self, runner: CliRunner) -> None:
        _mock_win32_client.Dispatch.side_effect = Exception("Outlook not running")

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code != 0
        assert "Cannot connect to Outlook" in result.stdout

        # Reset for other tests
        _mock_win32_client.Dispatch.side_effect = None
        _mock_win32_client.Dispatch.reset_mock()

    def test_empty_stores(self, runner: CliRunner) -> None:
        _mock_win32_client.Dispatch.reset_mock()
        ns = MagicMock()
        ns.Stores = []
        _mock_win32_client.Dispatch.return_value.GetNamespace.return_value = ns

        result = runner.invoke(app, ["mailboxes"])

        assert result.exit_code == 0
        assert "0 store(s)" in result.stdout
