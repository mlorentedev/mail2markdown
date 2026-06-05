"""Tests for shared mailbox support in Outlook extractor."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Re-import win32com from sys.modules so tests can use it directly
_mock_win32 = sys.modules["win32com"]
_mock_win32_client = sys.modules["win32com.client"]

import pytest

from mail2markdown.core.extractors.outlook import (
    _resolve_store,
    OutlookMessageSource,
)


@pytest.fixture
def mock_namespace() -> MagicMock:
    ns = MagicMock()
    store1 = MagicMock()
    store1.Name = "John Doe"
    store2 = MagicMock()
    store2.Name = "Shared Mailbox - Team"
    store3 = MagicMock()
    store3.Name = "Archive"
    ns.Stores = [store1, store2, store3]
    default_root = MagicMock()
    default_root.Name = "John Doe"
    ns.DefaultStore.GetRootFolder.return_value = default_root
    return ns


class TestResolveStore:
    def test_exact_match_case_insensitive(self, mock_namespace: MagicMock) -> None:
        result = _resolve_store(mock_namespace, "shared mailbox - team")
        mock_namespace.Stores[1].GetRootFolder.assert_called_once()
        assert result == mock_namespace.Stores[1].GetRootFolder.return_value

    def test_exact_match_default_store(self, mock_namespace: MagicMock) -> None:
        result = _resolve_store(mock_namespace, "John Doe")
        mock_namespace.Stores[0].GetRootFolder.assert_called_once()
        assert result == mock_namespace.Stores[0].GetRootFolder.return_value

    def test_not_found_raises_error(self, mock_namespace: MagicMock) -> None:
        with pytest.raises(ValueError, match="not found"):
            _resolve_store(mock_namespace, "Nonexistent Store")

    def test_not_found_lists_available_stores(self, mock_namespace: MagicMock) -> None:
        with pytest.raises(ValueError, match="John Doe"):
            _resolve_store(mock_namespace, "Missing")

    def test_ambiguous_names_raises_error(self) -> None:
        ns = MagicMock()
        s1 = MagicMock()
        s1.Name = "Shared Team"
        s2 = MagicMock()
        s2.Name = "shared team"
        ns.Stores = [s1, s2]
        with pytest.raises(ValueError, match="Ambiguous"):
            _resolve_store(ns, "shared team")


class TestOutlookMessageSourceMailbox:
    def test_default_constructor_no_mailbox(self) -> None:
        _mock_win32_client.Dispatch.reset_mock()
        source = OutlookMessageSource()
        assert source._mailbox is None

    def test_constructor_with_mailbox(self) -> None:
        _mock_win32_client.Dispatch.reset_mock()
        source = OutlookMessageSource(mailbox="Shared Mailbox")
        assert source._mailbox == "Shared Mailbox"

    def test_ensure_store_uses_default_when_no_mailbox(self) -> None:
        mock_ns = MagicMock()
        mock_root = MagicMock()
        mock_ns.DefaultStore.GetRootFolder.return_value = mock_root
        _mock_win32_client.Dispatch.return_value.GetNamespace.return_value = mock_ns

        source = OutlookMessageSource()
        store = source._ensure_store()
        assert store == mock_root
        mock_ns.DefaultStore.GetRootFolder.assert_called_once()

    def test_ensure_store_uses_named_store(self) -> None:
        mock_ns = MagicMock()
        mock_root = MagicMock()
        mock_store = MagicMock()
        mock_store.Name = "Shared Mailbox"
        mock_store.GetRootFolder.return_value = mock_root
        mock_ns.Stores = [mock_store]
        _mock_win32_client.Dispatch.return_value.GetNamespace.return_value = mock_ns

        source = OutlookMessageSource(mailbox="Shared Mailbox")
        store = source._ensure_store()
        assert store == mock_root

    def test_get_store_hash(self) -> None:
        mock_ns = MagicMock()
        mock_root = MagicMock()
        mock_root.Name = "Test Store"
        mock_ns.DefaultStore.GetRootFolder.return_value = mock_root
        _mock_win32_client.Dispatch.return_value.GetNamespace.return_value = mock_ns

        source = OutlookMessageSource()
        h = source.get_store_hash()
        assert len(h) == 8
        assert all(c in "0123456789abcdef" for c in h)
