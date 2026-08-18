---
id: lesson-001-context
type: lesson
status: active
created: "2026-05-01"
owner: manu
tags: [mail2markdown, lesson]
---

# Context

`mail2markdown` uses `win32com.client` for Outlook COM interop. CI runs on Linux where `pywin32` is not installed, so all COM-dependent tests must mock the module before it's imported.
