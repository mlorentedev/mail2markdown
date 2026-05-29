---
id: "mapi-msg-dumper-runbook-extraction"
type: project
status: active
tags: [runbook, outlook, extraction]
created: 2026-02-24
updated: 2026-02-24
owner: manu
---
# Outlook MSG Extraction Runbook

## Preconditions

1. Outlook desktop client is open and authenticated.
2. Repository dependencies are installed via Poetry.
3. Output destination has available disk space.

## Automated Monthly Run

```powershell
poetry run mapi-msg-dumper --output-root .\exports --start-date 2024-01-01 --verbose
```

- Uses checkpoint resume (`exports\checkpoint.json`) after first run.
- Exports to `exports\YYYY\MM\`.

## Biweekly Run

```powershell
poetry run mapi-msg-dumper --output-root .\exports --cadence biweekly --start-date 2024-01-01 --verbose
```

## Manual Window Run

```powershell
poetry run mapi-msg-dumper --manual --start-date 2024-01-01 --end-date 2024-01-31 --output-root .\exports --verbose
```

## Controlled Batch Run (N windows per execution)

```powershell
poetry run mapi-msg-dumper --output-root .\exports --start-date 2024-01-01 --max-windows 2 --verbose
```

- Useful when you want staged execution without changing cadence.
- Checkpoint advances only through processed windows.

## Last Month to Markdown (AI-ready)

```powershell
$firstThisMonth = (Get-Date -Day 1).Date
$start = $firstThisMonth.AddMonths(-1).ToString("yyyy-MM-dd")
$end = $firstThisMonth.AddDays(-1).ToString("yyyy-MM-dd")
poetry run mapi-msg-dumper --manual --start-date $start --end-date $end --output-root .\exports --markdown-root .\exports\markdown --verbose
```

## Persistent Run Config (single command)

Recurring execution (single config file: `run.json`):

```powershell
poetry run mapi-msg-dumper --run-config .\run.json
```

- Put folders, date range, output paths, checkpoints, and runtime flags in one JSON file.
- Include all product folders directly under `folders` in `run.json` (for example `Technical support\TOPAZ`).
- Change only the JSON between runs (for example monthly window updates).
- Keep `output_root` and `markdown_root` under the same root (for example `./exports` and `./exports/markdown`).

## Troubleshooting

- Check `exports\logs\errors.csv` for per-item failures.
- Rerun the same command safely; existing files are skipped.
- If checkpoint is wrong, back up and edit/remove `exports\checkpoint.json`, then rerun with explicit `--start-date`.

## Prepublish Verification

```powershell
poetry install
poetry run ruff check .
poetry run mypy src
poetry run pytest
```

