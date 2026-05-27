# Tasks - M5-001-shared-mailbox

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.

## Setup

- [ ] Branch created from main: `feat/M5-001-shared-mailbox`
- [ ] `proposal.md` is complete and acceptance criteria are testable
- [ ] No open questions left in `proposal.md` "Risks / open questions"

## Implementation

- [ ] Extend `run_config.py` to parse `"mailbox"` per folder entry and `"default_mailbox"` at root level
- [ ] Add mailbox-aware checkpoint token in `folders_config.py` (incorporate mailbox into the checkpoint name)
- [ ] Refactor `_resolve_folder` in `extractor.py` to take an optional mailbox/store name and iterate `namespace.Stores` or `namespace.Folders`
- [ ] Write tests for mailbox-qualified folder resolution (mocked COM)
- [ ] Write tests for config parsing of `"mailbox"` and `"default_mailbox"`
- [ ] Write tests for per-mailbox checkpoint isolation
- [ ] Wire mailbox through the CLI and folder iteration loop in `cli.py`
- [ ] Update `run.example.json` with mailbox examples

## Closing

- [ ] Every acceptance criterion from `proposal.md` is covered by at least one test
- [ ] Type checks pass (`poetry run mypy`)
- [ ] Lint passes (`poetry run ruff check .`)
- [ ] No unrelated changes in the diff (no scope creep)
- [ ] `verification.md` filled in
- [ ] PR opened referencing this spec folder