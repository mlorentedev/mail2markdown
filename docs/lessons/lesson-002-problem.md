---
id: lesson-002-problem
type: lesson
status: active
created: "2026-05-01"
owner: manu
tags: [mail2markdown, lesson]
---

# Problem

`patch("win32com.client.Dispatch")` fails with `ModuleNotFoundError: No module named 'win32com'` because the import happens at module load time, before `patch` can intercept it.
