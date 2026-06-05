# Tasks - M5-003-shared-mailbox

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.

## Setup

- [x] Branch created from main: `feat/M5-003-shared-mailbox`
- [x] `proposal.md` is complete and acceptance criteria are testable
- [x] No open questions left in `proposal.md` "Risks / open questions"

## Implementation

### Task 1: Config schema — top-level `mailbox` field

- [ ] Add `mailbox: str | None` to `FileRunConfig` in `run_config.py`
- [ ] Parse `"mailbox"` key from run.json payload (optional string)
- [ ] Validate: if set, must be non-empty string
- [ ] Tests: `test_run_config.py` — parse with mailbox, parse without (None), parse invalid type

### Task 2: Outlook extractor — store resolution

- [ ] Add `mailbox: str | None` parameter to `OutlookMessageSource.__init__()`
- [ ] Add `_resolve_store(namespace, mailbox_name)` that iterates `namespace.Stores`, matches by `StoreName` (case-insensitive)
- [ ] If mailbox is None, fall back to `namespace.DefaultStore.GetRootFolder()` (existing behavior)
- [ ] If mailbox is specified and not found, raise `ValueError("Mailbox 'X' not found. Available: Y, Z")`
- [ ] If multiple stores match, raise `ValueError` listing candidates
- [ ] Refactor `_resolve_folder()` to accept optional `store` parameter and use `store.GetRootFolder()` instead of `DefaultStore`
- [ ] Tests: `test_outlook_mailbox.py` — mock `namespace.Stores`, test match, no-match, ambiguous, None fallback

### Task 3: Factory wiring — pass mailbox through

- [ ] Update `create_source()` in `extractors/__init__.py` to pass `mailbox` kwarg to `OutlookMessageSource`
- [ ] Update `ProviderConfig` in `run_config.py` to include `mailbox: str | None`
- [ ] Update `cli.py` to pass `config.provider.mailbox` to `run_extraction` as part of provider config
- [ ] Update `run_extraction()` / `_create_source()` to forward mailbox to `create_source()`

### Task 4: Checkpoint isolation per mailbox

- [ ] Update `checkpoint_name_for_folder()` in `folders_config.py` to accept optional mailbox token
- [ ] Update `_resolve_checkpoint_for_folder()` in `cli.py` to incorporate mailbox into checkpoint filename
- [ ] Checkpoint filename: `{prefix}_{folder_token}_{store_hash}.json` where store_hash is first 8 chars of SHA1 of store name
- [ ] Tests: checkpoint filename includes mailbox context

### Task 5: `mailboxes` discovery command

- [ ] Add `@app.command("mailboxes")` in `cli.py`
- [ ] Connects to Outlook via COM, iterates `namespace.Stores`
- [ ] Prints a Rich table: `# | Display Name | Store Type`
- [ ] No `run.json` required — direct Outlook connection
- [ ] Handles COM connection failure gracefully with clear error
- [ ] Tests: `test_mailboxes_command.py` — mock COM, verify table output

### Task 6: Update docs and examples

- [ ] Update `run.example.json` with `"mailbox"` field example (commented out)
- [ ] Update README with mailbox configuration section
- [ ] Update CLI help text for `extract` to mention mailbox config

## Closing

- [x] Every acceptance criterion from `proposal.md` is covered by at least one test
- [x] Type checks pass (`poetry run mypy`)
- [x] Lint passes (`poetry run ruff check .`)
- [x] No unrelated changes in the diff (no scope creep)
- [x] `verification.md` filled in
- [ ] PR opened referencing this spec folder

> All code tasks done 2026-06-04. PR pending.
