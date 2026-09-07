---
id: lesson-002-problem
type: lesson
status: active
created: "2026-05-01"
owner: manu
tags: [mail2markdown, lesson]
---

> Part of a three-lesson series on mocking `win32com` in CI: see [lesson-001-context.md](lesson-001-context.md) and [lesson-003-solution.md](lesson-003-solution.md).

# Problem

`patch("win32com.client.Dispatch")` fails with `ModuleNotFoundError: No module named 'win32com'` because the import happens at module load time, before `patch` can intercept it.
