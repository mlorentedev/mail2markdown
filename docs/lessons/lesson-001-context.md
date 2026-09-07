---
id: lesson-001-context
type: lesson
status: active
created: "2026-05-01"
owner: manu
tags: [mail2markdown, lesson]
---

> Part of a three-lesson series on mocking `win32com` in CI: see [lesson-002-problem.md](lesson-002-problem.md) and [lesson-003-solution.md](lesson-003-solution.md).

# Context

`mail2markdown` uses `win32com.client` for Outlook COM interop. CI runs on Linux where `pywin32` is not installed, so all COM-dependent tests must mock the module before it's imported.
