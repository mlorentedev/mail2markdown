# Verification - M5-003-shared-mailbox

## Evidence

- [x] Criterion 1 -> tests/core/test_outlook_mailbox.py::TestResolveStore::test_exact_match_case_insensitive
- [x] Criterion 2 -> tests/core/test_outlook_mailbox.py::TestOutlookMessageSourceMailbox::test_ensure_store_uses_default_when_no_mailbox
- [x] Criterion 3 -> tests/core/test_run_config_mailbox.py::test_load_run_config_with_mailbox (mailbox parsed) + test_load_run_config_mailbox_none_by_default
- [x] Criterion 4 -> tests/core/test_mailboxes_command.py::TestMailboxesCommand::test_list_stores
- [x] Criterion 5 -> tests/core/test_outlook_mailbox.py::TestResolveStore::test_not_found_raises_error + test_ambiguous_names_raises_error
- [x] Criterion 6 -> tests/core/test_outlook_mailbox.py::TestOutlookMessageSourceMailbox::test_get_store_hash + folders_config.checkpoint_name_for_folder(mailbox=...)

## Test status

- Test suite: `poetry run pytest --cov=mail2markdown --cov-report=term-missing` -> 61 passed, 0.95s
- Manual smoke test: TBD (requires Outlook with shared mailbox)
- No regressions in existing test suite: yes

## Test files

- `tests/core/test_outlook_mailbox.py` — store resolution, match/no-match/ambiguous/None
- `tests/core/test_mailboxes_command.py` — COM mock for discovery command
- `tests/core/test_run_config.py` — mailbox field parsing (existing file, append tests)
- `tests/core/test_folders_config.py` — checkpoint name with mailbox (existing file, append tests)

## Decisions made during implementation

- **Store resolution**: Uses `namespace.Stores` (not `namespace.Folders`) — each shared mailbox in Outlook profile appears as a Store with a `GetRootFolder()`.
- **Checkpoint isolation**: Uses SHA1 hash of mailbox name (first 8 hex chars) appended to checkpoint token. Stable across Outlook restarts.
- **Folder resolution**: Simplified from original `_resolve_folder` — removed special `Inbox` shortcut since shared mailboxes don't use `GetDefaultFolder(6)`. All paths resolved from store root.
- **`chr(92)` for backslash**: Used in `folder_path.split(chr(92))` to avoid escaping issues in the new unified path resolution.

## Promotion candidates

- [x] Lesson? yes — COM interop test pattern with sys.modules mocking for cross-platform CI
- [ ] ADR-worthy? no — straightforward extension of existing pattern
- [ ] Pattern candidate? no — mail2markdown specific

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/M5-003-shared-mailbox/` -> `specs/archive/M5-003-shared-mailbox/`
- [ ] Backlog entry in vault `11-tasks.md` ticked with PR link
- [ ] Promotions above executed (if any)
