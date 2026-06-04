from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from mail2markdown.core.checkpoint import load_checkpoint, save_checkpoint
from mail2markdown.core.extractors import MessageSource, create_source
from mail2markdown.core.filenames import markdown_file_path, message_file_path
from mail2markdown.core.manifest import ManifestRow, ManifestWriter
from mail2markdown.core.markdown import MarkdownEmail, render_email_markdown
from mail2markdown.core.planning import (
    Cadence,
    Window,
    apply_window_limit,
    build_auto_windows,
    build_manual_window,
)


@dataclass
class ExtractionSummary:
    windows_processed: int = 0
    exported: int = 0
    markdown_written: int = 0
    skipped_existing: int = 0
    skipped_non_mail: int = 0
    failed: int = 0

    def merge(self, other: "ExtractionSummary") -> None:
        self.windows_processed += other.windows_processed
        self.exported += other.exported
        self.markdown_written += other.markdown_written
        self.skipped_existing += other.skipped_existing
        self.skipped_non_mail += other.skipped_non_mail
        self.failed += other.failed


def run_extraction(
    folder_path: str,
    output_root: Path,
    cadence: Cadence,
    start_date: date | None,
    end_date: date | None,
    manual: bool,
    checkpoint_path: Path | None,
    dry_run: bool,
    provider: str = "outlook",
    provider_config: dict[str, Any] | None = None,
    markdown_root: Path | None = None,
    verbose: bool = False,
    max_windows: int | None = None,
    manifest_writer: ManifestWriter | None = None,
) -> ExtractionSummary:
    if manual and end_date is None:
        raise ValueError("Manual mode requires --end-date.")

    destination = output_root.resolve()
    effective_end = end_date or datetime.now().date()
    checkpoint = checkpoint_path or destination / "checkpoint.json"

    windows = _build_windows(cadence, start_date, effective_end, manual, checkpoint)
    windows = apply_window_limit(windows, max_windows)
    summary = ExtractionSummary()
    if not windows:
        return summary

    source = _create_source(provider, provider_config or {})

    if verbose:
        mode = "manual" if manual else f"auto/{cadence}"
        console = _get_console()
        console.print(
            f"[mapi-msg-dumper] provider={provider} mode={mode} folder={folder_path} "
            f"windows={len(windows)} window_limit={max_windows if max_windows is not None else 'none'} "
            f"dry_run={str(dry_run).lower()}"
        )

    success_log = destination / "logs" / "success.csv"
    error_log = destination / "logs" / "errors.csv"

    for window in windows:
        if verbose:
            console = _get_console()
            console.print(f"[cyan]window[/cyan] {window.start.isoformat()} -> {window.end.isoformat()}")

        window_summary = _export_window(
            source,
            folder_path,
            destination,
            window,
            success_log,
            error_log,
            dry_run,
            verbose,
            folder_path,
            markdown_root.resolve() if markdown_root is not None else None,
            manifest_writer,
        )
        window_summary.windows_processed = 1
        summary.merge(window_summary)
        if not manual and not dry_run:
            save_checkpoint(checkpoint, window.end.date())
            if verbose:
                console = _get_console()
                console.print(f"[cyan]checkpoint updated to[/cyan] {window.end.date().isoformat()}")

    return summary


def _build_windows(
    cadence: Cadence,
    start_date: date | None,
    end_date: date,
    manual: bool,
    checkpoint_path: Path,
) -> list[Window]:
    if manual:
        if start_date is None:
            raise ValueError("Manual mode requires --start-date.")
        return [build_manual_window(start_date, end_date)]

    resume_from = load_checkpoint(checkpoint_path)
    first_start = resume_from or start_date
    if first_start is None:
        raise ValueError("Auto mode needs --start-date on first run when no checkpoint file exists.")
    return build_auto_windows(first_start, end_date, cadence)


def _create_source(provider: str, config: dict[str, Any]) -> MessageSource:
    kwargs: dict[str, object] = {}
    if "profile_path" in config:
        kwargs["profile_path"] = config["profile_path"]
    return create_source(provider, **kwargs)


def _export_window(
    source: MessageSource,
    folder_path: str,
    output_root: Path,
    window: Window,
    success_log: Path,
    error_log: Path,
    dry_run: bool,
    verbose: bool,
    folder_path_label: str,
    markdown_root: Path | None,
    manifest_writer: ManifestWriter | None = None,
) -> ExtractionSummary:
    summary = ExtractionSummary()

    messages = list(source.iter_messages(folder_path, window.start, window.end))

    for raw_msg in messages:
        entry_id = raw_msg.entry_id
        subject = raw_msg.subject

        try:
            msg_path = message_file_path(output_root, raw_msg.received_at, subject, entry_id)

            if msg_path.exists():
                summary.skipped_existing += 1
                if verbose:
                    console = _get_console()
                    console.print(f"[dim]skip existing[/dim] {msg_path}")
            else:
                if not dry_run:
                    source.save_message(raw_msg, msg_path)

                summary.exported += 1
                if verbose:
                    console = _get_console()
                    action = "simulated save" if dry_run else "saved"
                    console.print(f"[green]{action}[/green] {msg_path}")
                _append_csv(
                    success_log,
                    ["window_start", "window_end", "entry_id", "saved_path", "dry_run"],
                    {
                        "window_start": window.start.isoformat(),
                        "window_end": window.end.isoformat(),
                        "entry_id": entry_id,
                        "saved_path": str(msg_path),
                        "dry_run": str(dry_run).lower(),
                    },
                )

            md_path_str = ""
            if markdown_root is not None:
                md_path = markdown_file_path(markdown_root, raw_msg.received_at, subject, entry_id)
                if md_path.exists():
                    if verbose:
                        console = _get_console()
                        console.print(f"[dim]skip existing markdown[/dim] {md_path}")
                elif dry_run:
                    if verbose:
                        console = _get_console()
                        console.print(f"[dim]simulated markdown[/dim] {md_path}")
                else:
                    markdown = render_email_markdown(
                        MarkdownEmail(
                            received_at=raw_msg.received_at,
                            subject=subject,
                            sender_name=raw_msg.sender_name,
                            sender_email=raw_msg.sender_email,
                            to=raw_msg.to,
                            cc=raw_msg.cc,
                            entry_id=entry_id,
                            source_msg_path=msg_path,
                            folder_path=folder_path_label,
                            provider=source.__class__.__name__.replace("MessageSource", "").lower(),
                        ),
                        body=raw_msg.body,
                    )
                    md_path.parent.mkdir(parents=True, exist_ok=True)
                    md_path.write_text(markdown, encoding="utf-8")
                    summary.markdown_written += 1
                    md_path_str = str(md_path)
                    if verbose:
                        console = _get_console()
                        console.print(f"[dim]saved markdown[/dim] {md_path}")

            if manifest_writer is not None and not manifest_writer.already_written(entry_id):
                manifest_writer.write(
                    ManifestRow(
                        entry_id=entry_id,
                        received_at=raw_msg.received_at,
                        subject=subject,
                        sender_name=raw_msg.sender_name,
                        sender_email=raw_msg.sender_email,
                        to=raw_msg.to,
                        cc=raw_msg.cc,
                        folder=folder_path_label,
                        msg_path=str(msg_path),
                        md_path=md_path_str,
                        window_start=window.start.isoformat(),
                        window_end=window.end.isoformat(),
                    )
                )
        except Exception as exc:
            summary.failed += 1
            if verbose:
                console = _get_console()
                console.print(f"[red]error[/red] entry_id={entry_id or 'unknown'} subject={subject!r}: {exc}")
            _append_csv(
                error_log,
                ["window_start", "window_end", "entry_id", "subject", "error"],
                {
                    "window_start": window.start.isoformat(),
                    "window_end": window.end.isoformat(),
                    "entry_id": entry_id,
                    "subject": subject,
                    "error": str(exc),
                },
            )

    return summary


def _get_console() -> Any:
    from rich.console import Console

    return Console()


def _safe_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).encode("utf-8", errors="replace").decode("utf-8")


def _append_csv(path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: _safe_str(v) for k, v in row.items()})
