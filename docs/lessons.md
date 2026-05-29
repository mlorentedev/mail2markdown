---
id: "mapi-msg-dumper-lessons"
type: lesson
status: active
tags: [lessons, outlook, automation]
created: 2026-02-24
updated: 2026-02-24
owner: manu
---
# Lessons Learned

## 2026-02-24
- Graph API constraints in corporate tenants can be bypassed with local Outlook COM interop without admin-level tenant changes.
- Stable file naming must include an item-specific suffix (for example, EntryID hash) to keep reruns idempotent.
- Window-level batching (`--max-windows`) is safer than item-level truncation because checkpoint progress remains consistent.
- Verbose execution logs reduce operator uncertainty during long Outlook COM extraction loops.
- AI ingestion works better with per-email Markdown that preserves metadata + plain body (`--markdown-root`).
- Folder orchestration is safer in `run.json` (`folders`) with per-folder checkpoints to avoid mixed resume state.
- A single persistent run file (`--run-config`) reduces operator error and supports resilient, repeatable monthly execution.
- Supporting top-level folders outside Inbox (for example `Technical support\TOPAZ`) makes product pipelines much easier.
- In Windows PowerShell, JSON files may be written with UTF-8 BOM, so readers should use `utf-8-sig`.
- For public repositories, keep `run.json` local-only and provide a sanitized `run.example.json`.
- Python projects of this type are best released as wheel/sdist assets, not compiled binaries.


### [2026-03-07] Release-please Tag Formatting
**Context:** Fixing release-please tag format.
**Problem:** By default, release-please-action (v4) with multiple packages or default python setup might prefix tags with the package name (e.g., 'mapi-msg-dumper-v0.2.0').
**Solution:** Add '"include-component-in-tag": false' to the package configuration in 'release-please-config.json' to force a clean 'vX.X.X' tag format.
**Tags:** `#github-actions` `#release-please` `#devops`

### [2026-05-26] print() encoding crash with non-ASCII subjects
**Context:** Dry-run extraction with --verbose crashed on Inbox due to Chinese character in subject line
**Problem:** extractor.py uses raw print() for verbose logging instead of rich console. When a subject contains non-ASCII characters (e.g. Chinese ideographs), print() fails with charmap encoding error because the Windows console code page cannot represent them.
**Solution:** Replace all print() in extractor.py with console.print() from Rich, or wrap in try/except for encoding errors. The manifest writer already handles UTF-8 correctly — only the display path is broken.
**Tags:** `##encoding` `##bug` `##tech-debt`

### [2026-05-27] ThunderbirdExtractor — mailbox stdlib for .mbox parsing
**Context:** Adding Thunderbird support to mapi-msg-dumper via Strategy Pattern with MessageSource abstraction.
**Problem:** Thunderbird stores emails in .mbox format with raw MIME messages. Need to parse dates from RFC 2822 headers, handle multipart messages (plain text + HTML), decode MIME-encoded headers, and compute stable entry IDs without MAPI EntryID.
**Solution:** Created MessageSource ABC with iter_messages/save_message/resolve_folder_source. ThunderbirdMessageSource uses mailbox.mbox for parsing, email.utils parsedate_to_datetime for dates, email.header decode_header for MIME encoding, and SHA-256 hash of From+Subject+Date+Body for entry IDs. Body extraction prefers plain text over HTML with HTML stripping fallback.
**Tags:** `#thunderbird` `#mbox` `#strategy-pattern` `#email-parsing`

### [2026-05-27] Lazy-import a Windows-only dep without breaking the second call
**Context:** After renaming to `mail2markdown`, CI on Linux started failing because `import win32com.client` at module top of `outlook.py` aborts on Linux. Two rushed fixes (commits 59a9171, ac27d9e) moved the import inside the function but left the assignment outside the `if self._namespace is None:` guard, and also duplicated the dispatch chain on the same line, producing a ruff E501.
**Problem:** Two failure modes: (1) ruff E501 — the duplicated text pushed line 24 past 120 chars; (2) latent runtime NameError on the second call to `_ensure_namespace`, because `import win32com.client` inside the `if` branch only binds `win32com` for that call. CI surfaced (1); (2) would only bite on Windows at runtime.
**Solution:** Keep BOTH the import AND the assignment inside the `if self._namespace is None:` guard. The cached `self._namespace` means subsequent calls skip the whole block and just return the attribute — they never need `win32com` again. Cleaner long-term posture: declare pywin32 as conditional in `pyproject.toml` with `markers = "sys_platform == 'win32'"` so Poetry doesn't even try to install it on Linux runners. Fix landed in commit `1a90e39` on PR #7.
**Tags:** `#python` `#ci` `#win32com` `#lazy-import` `#cross-platform`
