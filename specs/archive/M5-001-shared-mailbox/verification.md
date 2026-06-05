# Verification - M5-001-shared-mailbox

## Evidence

- [ ] Criterion 1 (mailbox-qualified folder resolves from specific store) -> commit / test
- [ ] Criterion 2 (no mailbox field -> default store, no regression) -> commit / test
- [ ] Criterion 3 (default_mailbox fallback) -> commit / test
- [ ] Criterion 4 (per-mailbox checkpoint isolation) -> commit / test
- [ ] Criterion 5 (non-existent mailbox -> clear error) -> commit / test

## Test status

- Test suite: `poetry run pytest --cov=mapi_msg_dumper --cov-report=term-missing`
- Manual smoke test: TBD (requires Outlook with shared mailbox)
- No regressions in existing test suite: yes / no

## Decisions made during implementation

-

-

## Promotion candidates

- [ ] Lesson? <yes / no>
- [ ] ADR-worthy? <yes / no>
- [ ] Pattern candidate? <yes / no>

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/M5-001-shared-mailbox/` -> `specs/archive/M5-001-shared-mailbox/`
- [ ] Backlog entry in vault `11-tasks.md` ticked with PR link
- [ ] Promotions above executed (if any)