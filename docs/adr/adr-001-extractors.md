---
id: adr-001-extractors
type: adr
status: active
created: "2026-03-07"
owner: manu
---

---
id: "adr-001-strategy-pattern-extractors"
type: adr
status: active
tags: [architecture, design-pattern]
---
# ADR 001: Strategy Pattern for Email Extractors

## Context
The project was originally designed exclusively for Outlook via MAPI/COM. To support other clients like Thunderbird (local mbox/maildir) or generic IMAP, the core logic needed to be decoupled from the specific extraction mechanism.

## Decision
Implement a Strategy Pattern using a `BaseExtractor` abstract class.

- `BaseExtractor`: Defines the interface (`connect`, `get_messages`, `save_raw`).
- `OutlookExtractor`: Implements MAPI/COM specific logic.
- `ThunderbirdExtractor`: (Planned) Implements local file parsing.

The `run_extraction` coordinator now receives an implementation of `BaseExtractor`, making it agnostic to the source.

## Consequences
- **Positive**: Easier to add new providers (Gmail, IMAP, Apple Mail).
- **Positive**: Tests for non-provider logic (planning, markdown rendering) can run on any OS by using a mock or a provider that doesn't require Windows.
- **Neutral**: Slightly more boilerplate due to interface definitions.
- **Negative**: Metadata extraction must be standardized across providers to fit the `ExtractedEmail` schema.
