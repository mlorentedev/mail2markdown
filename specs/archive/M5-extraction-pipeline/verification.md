# Verification — M5-extraction-pipeline

## Evidence

- [x] `--manifest` produces CSV + JSONL, dedup works -> test_manifest*.py (4 tests, 100% coverage)
- [x] `--routing-report` groups by folder -> test_routing.py (4 tests, 94% coverage)
- [x] `--sync` runs from checkpoint -> wired in cli.py, uses existing checkpoint module
- [x] `--vault-root` copies files to vault -> test_vault_export.py (4 tests, 97% coverage)
- [x] Full dry-run completes -> 13 folders processed, 44 items, manifest.csv + manifest.jsonl produced

## Test status

- Test suite: `pytest --cov=mapi_msg_dumper --cov-report=term-missing` -> **33 passed**
- Lint: `ruff check .` -> All checks passed
- Type check: `mypy src` -> Success: no issues found in 14 source files
- Full dry-run over 13 folders (Inbox + 12 product folders): processed 44 items, manifest generated

## Technical debt found

- **TE-001**: `print()` encoding crash on non-ASCII subjects (extractor.py:77/89/205/214/233/257/280)
- **TE-002**: `_export_window` is 113 lines, violates <40 rule
- **TE-003**: Manifest `tags` field always written as empty string
- **TE-004**: `FileRunConfig` dataclass has 13 growing fields
- **TE-005**: Dry-run manifest includes non-existent file paths (no files written in dry-run)

## Decisions made during implementation

- Routing/vault post-processing now runs BEFORE exit-on-failure so partial folder failures don't block reporting
- Manifest writer is shareable across folders (one CSV + JSONL per output_root)
- Vault import uses `_derive_product()` from routing module to avoid duplicating product detection logic

## Promotion candidates

- [x] Lesson? yes — `print()` encoding crash (TE-001) is a recurring pattern across COM interop projects
- [ ] ADR-worthy? no
- [ ] Pattern candidate? no

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved to `specs/archive/M5-extraction-pipeline/`
- [ ] Backlog entry ticked with PR link
- [ ] Promotions executed (if any)