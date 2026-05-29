---
id: curation-rules
type: runbook
status: active
created: "2026-05-26"
---

---
id: "mapi-msg-dumper-curation-rules"
type: runbook
status: draft
tags: [curation, vault, extraction]
created: "2026-05-26"
owner: manu
---

# Curation Rules

**Purpose:** Consistent criteria for deciding which extracted emails go to the vault.
**Version:** 0.1 (draft).

## Vault-worthy (import)

Emails that contain durable information:

- Technical decisions with rationale
- Bug reports with root cause analysis
- Customer requirements, specifications
- Meeting notes with decisions or action items
- Architecture discussions
- Design review feedback

## Not vault-worthy (skip)

Automated or ephemeral content:

- OOO / auto-replies / delivery receipts
- CI/CD build notifications
- JIRA/GitHub automated updates
- Meeting invitations with no content
- Newsletters, marketing, announcements
- Lunch orders, social events

## Classification tags

| Tag | When to use |
|-----|-------------|
| `technical-decision` | A choice was made with rationale |
| `bug-report` | Bug with root cause |
| `customer-req` | External requirement or spec |
| `meeting-notes` | Meeting recap with decisions |
| `process` | Workflow, procedure, policy |
| `reference` | Useful info, no immediate action |

## Curation workflow

1. Agent loads manifest per product from `routing/<product>.csv`
2. Agent shows batches of ~10-20 emails (subject, date, sender, snippet)
3. Per email: approve (y), skip (n), or uncertain (?)
4. Agent logs all decisions, imports approved .md files to vault

## Improvement

When rubric misses something, capture a lesson in `90-lessons.md` with tag `#curation-update`. Periodically promote into a rubric version bump.