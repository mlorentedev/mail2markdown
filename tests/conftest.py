"""Root conftest — ensures win32com mock is in sys.modules before any test imports."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

_mock_win32 = MagicMock()
_mock_win32_client = MagicMock()
_mock_win32_client_constants = MagicMock()
sys.modules["win32com"] = _mock_win32
sys.modules["win32com.client"] = _mock_win32_client
sys.modules["win32com.client.constants"] = _mock_win32_client_constants
_mock_win32.client = _mock_win32_client
