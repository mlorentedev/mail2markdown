from __future__ import annotations

import sys

_mock_win32 = __import__("unittest.mock").mock.MagicMock()
_mock_win32_client = __import__("unittest.mock").mock.MagicMock()
sys.modules["win32com"] = _mock_win32
sys.modules["win32com.client"] = _mock_win32_client
sys.modules["win32com.client.constants"] = __import__("unittest.mock").mock.MagicMock()
