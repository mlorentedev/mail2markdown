---
id: "M5-001-shared-mailbox"
type: spec
status: archived
created: "2026-05-26"
tags: [spec, proposal, mailbox, outlook]
template_version: "1.0"
---

# M5-001: Shared mailbox support

> **Naming**: file lives at `<repo>/specs/M5-001-shared-mailbox/proposal.md`.

## Why

The tool currently resolves all folder paths against the default Outlook store only. Users with shared or secondary mailboxes (common in corporate environments) cannot extract emails from them. This blocks the primary use case for the tool — corporate historical extraction from shared team inboxes like `Technical support\TOPAZ`.

<!-- from vault: 10_projects/mapi-msg-dumper/11-tasks.md: "Add shared mailbox support (select mailbox/store root before folder path resolution)" -->

## What

- `run.json` folder entries gain an optional `"mailbox"` field to select a specific Outlook store (mailbox) before resolving the folder hierarchy.
- `run.json` also supports a top-level `"default_mailbox"` fallback for all folders.
- The extraction engine resolves folders from the specified store instead of always using `namespace.DefaultStore`.
- Backward compatible: folders without a `mailbox` field resolve against the default store (existing behavior).
- Per-(mailbox, folder) checkpoint isolation so each mailbox tracks its own resume state.

## Out of scope

- Mailbox discovery command (separate spec: M5-002).
- Manifest output and routing reports (separate specs).
- Thunderbird extractor (separate spec).
- Project rename.
- CRUD operations on mailboxes (read-only extraction only).

## Risks / open questions

- [ ] COM store iteration: `namespace.Stores` vs `namespace.Folders` — need to verify which correctly enumerates shared mailboxes added to the Outlook profile. These have different semantics in MAPI.
- [ ] Store identity stability: what stable identifier (store ID, mailbox DN, display name) to use for per-store checkpoint tokens? Display names can be renamed.
- [ ] Permission errors: shared mailboxes may throw access-denied on folder traversal. Need graceful skip + error logging vs hard failure.

## Acceptance criteria

- [ ] A folder entry with `"mailbox": "Shared Mailbox - Team"` resolves the folder path from that specific store root.
- [ ] A folder entry without `"mailbox"` still resolves against the default store (no regression).
- [ ] `"default_mailbox"` at the top level applies to all folders that lack an explicit `"mailbox"`.
- [ ] Checkpoint files are isolated per (mailbox, folder) pair — same folder name in different mailboxes gets separate checkpoints.
- [ ] Extracting from a non-existent mailbox produces a clear error message, not a COM traceback.

## References

- Vault: `10_projects/mapi-msg-dumper/11-tasks.md`
- Code: `src/mapi_msg_dumper/core/extractor.py:132-144` (`_resolve_folder` bottleneck)
- Code: `src/mapi_msg_dumper/core/run_config.py` (config schema)
- Code: `src/mapi_msg_dumper/core/folders_config.py` (folder path resolution)