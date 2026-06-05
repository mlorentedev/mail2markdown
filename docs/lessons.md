# COM interop testing on non-Windows platforms

## Context

`mail2markdown` uses `win32com.client` for Outlook COM interop. CI runs on Linux where `pywin32` is not installed, so all COM-dependent tests must mock the module before it's imported.

## Problem

`patch("win32com.client.Dispatch")` fails with `ModuleNotFoundError: No module named 'win32com'` because the import happens at module load time, before `patch` can intercept it.

## Solution

Mock `win32com` in `sys.modules` at the top of the test file, **before** any imports that transitively import it:

```python
import sys
from unittest.mock import MagicMock

_mock_win32 = MagicMock()
_mock_win32_client = MagicMock()
sys.modules["win32com"] = _mock_win32
sys.modules["win32com.client"] = _mock_win32_client
sys.modules["win32com.client.constants"] = MagicMock()

from mail2markdown.core.extractors.outlook import OutlookMessageSource
```

Then use the mock directly instead of `patch()`:

```python
import win32com.client
mock_ns = MagicMock()
win32com.client.Dispatch.return_value.GetNamespace.return_value = mock_ns
```

Reset between tests with `win32com.client.Dispatch.reset_mock()` and `side_effect = None`.
