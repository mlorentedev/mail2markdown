---
id: "M5-003-shared-mailbox"
type: spec
status: archived
created: "2026-06-04"
tags: [spec, proposal, mailbox, outlook, shared-mailbox]
template_version: "1.0"
---

# M5-003: Shared mailbox support

> **Naming**: file lives at `<repo>/specs/M5-003-shared-mailbox/proposal.md`.

## Why

`OutlookMessageSource._resolve_folder()` always resolves against `namespace.DefaultStore.GetRootFolder()`. Users with shared or secondary mailboxes added to their Outlook profile cannot extract emails from them. The operator has no way to specify which store/mailbox to use, blocking extraction of shared team inboxes like `Technical support\TOPAZ`.

<!-- from vault: 10_projects/mail2markdown/11-tasks.md: "Add shared mailbox support (select mailbox/store root before folder path resolution)" -->

## What

- **Config schema:** `run.json` folder entries gain an optional `"mailbox"` field. A top-level `"default_mailbox"` key provides a fallback for all folders.
- **Outlook extractor:** `OutlookMessageSource` iterates `namespace.Stores`, matches by display name (case-insensitive), and uses the matched store's `GetRootFolder()` instead of `DefaultStore`.
- **Discovery command:** `mail2markdown mailboxes` lists all Outlook stores with their display names, so the operator can pick the right one. This command does NOT require `run.json` — it connects to Outlook directly.
- **Backward compatible:** folders without `"mailbox"` resolve against `DefaultStore` (existing behavior).
- **Per-(mailbox, folder) checkpoint isolation:** checkpoint filename incorporates the mailbox token.

## Out of scope

- Mailbox CRUD operations (read-only extraction).
- Auto-discovery of shared mailboxes (manual selection only).
- Exchange Online / Graph API support.
- Permission error recovery beyond clear error messages.

## Risks / open questions

| # | Risk | Mitigation |
|---|------|------------|
| 1 | Store identity stability: display names can be renamed. | Display name is the only practical key for operator-facing config. Checkpoint uses a hash of the matched store's `StoreID` for stability. |
| 2 | Ambiguous store name: two stores with similar display names. | Exact case-insensitive match only. If multiple matches, error listing all candidates. |
| 3 | `namespace.Stores` vs `namespace.Folders` semantics. | Use `namespace.Stores` — each shared mailbox added to the profile appears as a Store. Verified against pywin32 docs. |

## Acceptance criteria

1. A folder entry with `"mailbox": "Shared Mailbox - Team"` resolves the folder path from that specific store's root.
2. A folder entry without `"mailbox"` still resolves against the default store (zero regression).
3. Top-level `"default_mailbox"` applies to all folders lacking an explicit `"mailbox"`.
4. `mail2markdown mailboxes` prints a table of available stores (display name, store type).
5. Extracting from a non-existent mailbox produces a clear error message (`ValueError: Mailbox 'X' not found. Available: Y, Z`), not a COM traceback.
6. Checkpoint files are named with mailbox context: `{checkpoint_prefix}_{folder_token}_{store_hash}.json`.

## References

- Vault: `10_projects/mail2markdown/11-tasks.md`
- Code: `src/mail2markdown/core/extractors/outlook.py:78-90` (`_resolve_folder` bottleneck)
- Code: `src/mail2markdown/core/run_config.py` (config schema)
- Code: `src/mail2markdown/core/folders_config.py` (folder path resolution)
- Code: `src/mail2markdown/core/extractors/__init__.py:18-27` (`create_source` factory)
