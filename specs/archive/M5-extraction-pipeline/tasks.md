# Tasks — M5-extraction-pipeline

> TDD order. One task = one focused commit.

## Setup

- [x] Branch: `feat/M5-extraction-pipeline`
- [x] Proposal reviewed and frozen
- [x] No open risks blocking implementation

## Implementation

- [x] **Manifest output**: Add `--manifest` flag. On each item export, append row to `manifest.csv` + `manifest.jsonl`. Dedup by entry_id on subsequent runs.
- [x] **Routing report**: Add `--routing-report` flag. After extraction, group by top-level folder. Write `routing/summary.csv` + per-product CSV.
- [x] **Sync mode**: Add `--sync` flag. Load checkpoint, run from there to now. One-liner that wraps existing logic.
- [x] **Vault export**: Add `--vault-root <path>`. Copy Markdown files per product into vault tree.
- [x] **Extract all dry-run**: Run full dry-run over Inbox + 13 product folders to validate no errors.

## Verification

- [x] Type checks pass (`mypy`)
- [x] Lint passes (`ruff check .`)
- [x] Tests pass (`pytest --cov`)
- [x] Full dry-run over all folders confirms expected output sizes
- [x] `verification.md` filled

## Closing

- [ ] `verification.md` complete
- [ ] PR opened with link to spec
- [ ] Once extracted: review routing/summary.csv, plan vault import