---
id: "M5-extraction-pipeline"
type: spec
status: archived
created: "2026-05-26"
tags: [spec, proposal, pipeline, automation, vault]
template_version: "1.0"
---

# M5: Extraction pipeline — manifest, routing, sync, vault export

> **Naming**: file lives at `<repo>/specs/M5-extraction-pipeline/proposal.md`.

## Why

The tool dumps .msg and Markdown files, but there is no structured catalog of *what* was extracted, no automated grouping by product folder for downstream distillation, and no way to import results into the Obsidian vault. Every run requires manual inspection of CSV logs. To make this a recurring automated pipeline, we need:
- A manifest (catalog) so you can query/search what exists
- A routing report so emails naturally group by product/client
- A sync mode so incremental runs only fetch new items
- A vault export mode so selected Markdown files land in the vault knowledge base

## What

### 1. Manifest output (`--manifest`)
When enabled, produces two sibling files alongside the Markdown tree:
- `exports/manifest.csv` — one row per extracted email
- `exports/manifest.jsonl` — same data as newline-delimited JSON

Each row includes: entry_id, received_at, subject, sender_name, sender_email, to, cc, folder, tags, msg_path, md_path, window_start, window_end, created_at.

Manifest is **append-only** — re-running skips existing entries (dedup by entry_id), so it's safe to run incrementally.

### 2. Routing report (`--routing-report`)
Groups extracted emails by the top-level folder structure. For example, `Technical support\TOPAZ` routes to product `TOPAZ`. Output is a summary table + optional per-product CSV:
- `exports/routing/summary.csv` — product, count, first_date, last_date
- `exports/routing/<product>.csv` — all emails for that product

### 3. Incremental sync mode (`--sync`)
Run from checkpoint to now — only processes items newer than the last checkpoint, then updates. Designed for Windows Task Scheduler weekly runs.

### 4. Vault export (`--vault-root`)
Copies selected Markdown files into `%USERPROFILE%\Projects\knowledge\` structured per product.

Curation is **agent-assisted** (not automated AI). The agent reads the curation rubric at `vault: mapi-msg-dumper/50-curation/curation-rules.md`, presents batches per product, and you approve/skip each. See `AGENTS.md § Curation Workflow`.

## Scope: extraction plan

| Dimension | Decision |
|-----------|----------|
| **Folders** | Inbox + all Technical support product subfolders |
| **Date range** | All history (oldest available ~2020 → today) |
| **Output** | .msg + Markdown + manifest (CSV+JSONL) |
| **Curation** | Extract all → auto-route by folder → review per-product → import to vault |
| **Sync** | CLI `--sync` flag. Scheduling TBD (Windows Task Scheduler). |

The 15 product folders under `Technical support\` will route automatically. Inbox items route to a catch-all `Inbox` group.

### How curation & vault fits

1. Run extraction (full history + weekly sync)
2. Open `routing/summary.csv` — see count per product
3. For each product, review `exports/routing/<product>.csv` — skim subjects, dates
4. Run `--vault-root` with product filter to import selected items to vault
5. Vault structure: `10_projects/mapi-msg-dumper/extractions/<product>/<year>-<month>-*.md`

## Out of scope

- Shared mailbox support (not needed — primary only)
- Thunderbird extractor (separate feature)
- Project rename to `mail2markdown` (pipeline rename after extraction completes)
- Web UI or dashboard

## Risks / open questions

- [ ] Dedup by entry_id in manifest: need to ensure entry_id is stable across Outlook sessions (it is — MAPI permanent ID).
- [ ] Vault import path convention: flat per-product or mirror the year/month tree? Let's decide during implementation.
- [ ] Performance: 57K items → manifest with all fields will be sizable. JSONL at ~300 bytes/row = ~17MB. Acceptable.

## Acceptance criteria

- [ ] `--manifest` flag produces `manifest.csv` + `manifest.jsonl` with one row per extracted email, deduped by entry_id on re-run
- [ ] `--routing-report` produces `routing/summary.csv` + per-product CSVs grouped by top-level folder
- [ ] `--sync` mode runs from last checkpoint to now, is idempotent
- [ ] `--vault-root <path>` copies Markdown files into vault-structured folders per product
- [ ] Full dry-run over all 13 product folders + Inbox succeeds without errors

## References

- Vault: `10_projects/mapi-msg-dumper/11-tasks.md`
- Code: `src/mapi_msg_dumper/core/extractor.py` (main loop)
- Code: `src/mapi_msg_dumper/cli.py` (CLI flags)
- Code: `src/mapi_msg_dumper/core/markdown.py` (MarkdownEmail)
- Running context: ~57K items in primary mailbox, oldest email 2020