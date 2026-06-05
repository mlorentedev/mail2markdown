from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mail2markdown.core.checkpoint import load_checkpoint
from mail2markdown.core.extractor import ExtractionSummary, run_extraction
from mail2markdown.core.folders_config import checkpoint_name_for_folder, normalize_folder_path
from mail2markdown.core.manifest import ManifestWriter
from mail2markdown.core.planning import normalize_cadence, parse_iso_date
from mail2markdown.core.routing import build_routing_report
from mail2markdown.core.run_config import load_run_config
from mail2markdown.core.vault_export import vault_import

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def extract(
    folder: str = typer.Option(
        "Inbox", help="Outlook folder path (examples: Inbox\\Subfolder, Shared Inbox\\Product-A)."
    ),
    run_config: Path | None = typer.Option(
        None, help="JSON run config. If set, values from this file drive execution."
    ),
    output_root: Path = typer.Option(Path("exports"), help="Root path for MSG output."),
    cadence: str = typer.Option("monthly", help="Auto batching cadence: monthly or biweekly."),
    start_date: str | None = typer.Option(None, help="Start date in YYYY-MM-DD."),
    end_date: str | None = typer.Option(None, help="End date in YYYY-MM-DD."),
    manual: bool = typer.Option(
        False, "--manual", help="Single-window mode. If not set, auto mode uses checkpoint resume."
    ),
    checkpoint_file: Path | None = typer.Option(
        None, help="Checkpoint file path. Defaults to <output-root>\\checkpoint.json."
    ),
    max_windows: int | None = typer.Option(
        None, min=1, help="Process at most N date windows per run (safe batching control)."
    ),
    markdown_root: Path | None = typer.Option(
        None, help="Optional root path to also write AI-friendly Markdown files."
    ),
    dry_run: bool = typer.Option(False, help="Evaluate and log without writing MSG files."),
    verbose: bool = typer.Option(False, "--verbose", help="Print detailed extraction progress."),
    manifest: bool = typer.Option(False, help="Write CSV + JSONL manifest of extracted emails."),
    routing_report: bool = typer.Option(False, help="Generate routing report from manifest."),
    sync: bool = typer.Option(False, "--sync", help="Run from last checkpoint to today (incremental)."),
    vault_root: Path | None = typer.Option(
        None, help="Vault root path. Copies Markdown files into vault-structured folders per product."
    ),
    provider: str = typer.Option(
        "outlook", "--provider", help="Email provider: outlook or thunderbird."
    ),
) -> None:
    try:
        if run_config is not None:
            config = load_run_config(run_config.resolve())
            parsed_start = _parse_optional_date(config.window.start_date)
            parsed_end = _parse_optional_date(config.window.end_date)
            normalized_cadence = normalize_cadence(config.window.cadence)
            folder_paths = config.folder_paths
            output_root = config.output_root
            manual = config.window.manual
            checkpoint_file = config.window.checkpoint_file
            max_windows = config.window.max_windows
            markdown_root = config.output.markdown_root
            dry_run = config.dry_run
            verbose = config.verbose
            manifest = config.output.manifest
            routing_report = config.output.routing_report
            vault_root = config.output.vault_root
            sync = config.output.sync
            provider = config.provider.provider_name or "outlook"
            thunderbird_config = config.provider.thunderbird_config
            mailbox = config.provider.mailbox
        else:
            parsed_start = _parse_optional_date(start_date)
            parsed_end = _parse_optional_date(end_date)
            normalized_cadence = normalize_cadence(cadence)
            folder_paths = [normalize_folder_path(folder)]

        if sync:
            if parsed_start is None:
                chk = _resolve_checkpoint_for_folder(
                    checkpoint_file, output_root, folder_paths[0], len(folder_paths) > 1, mailbox
                )
                if chk is None:
                    chk = output_root.resolve() / "checkpoint.json"
                checkpoint_date = load_checkpoint(chk)
                if checkpoint_date is None:
                    console.print("[red]No checkpoint found. Run a full extraction first (without --sync).[/red]")
                    raise typer.Exit(code=1)
                parsed_start = checkpoint_date
                if verbose:
                    console.print(f"[cyan]Sync mode: resuming from[/cyan] {checkpoint_date.isoformat()}")
            manual = False
            if parsed_end is None:
                parsed_end = datetime.now().date()

        folder_failures: list[tuple[str, str]] = []
        summary = ExtractionSummary()
        multi_folder = len(folder_paths) > 1
        manifest_writer = _create_manifest_writer(output_root.resolve()) if manifest else None

        for target_folder in folder_paths:
            if verbose and multi_folder:
                console.print(f"[cyan]Processing folder:[/cyan] {target_folder}")

            effective_checkpoint = _resolve_checkpoint_for_folder(
                checkpoint_file=checkpoint_file,
                output_root=output_root,
                folder_path=target_folder,
                multi_folder=multi_folder,
                mailbox=mailbox,
            )
            try:
                folder_summary = run_extraction(
                    folder_path=target_folder,
                    output_root=output_root,
                    cadence=normalized_cadence,
                    start_date=parsed_start,
                    end_date=parsed_end,
                    manual=manual,
                    checkpoint_path=effective_checkpoint,
                    dry_run=dry_run,
                    provider=provider,
                    provider_config={**(thunderbird_config or {}), "mailbox": mailbox},
                    markdown_root=markdown_root,
                    verbose=verbose,
                    max_windows=max_windows,
                    manifest_writer=manifest_writer,
                )
                summary.merge(folder_summary)
            except Exception as exc:
                folder_failures.append((target_folder, str(exc)))
                console.print(f"[red]Folder failed:[/red] {target_folder} -> {exc}")

    except Exception as exc:
        console.print(f"[red]Extraction failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    _print_summary(
        summary=summary,
        output_root=output_root.resolve(),
        dry_run=dry_run,
        folders_requested=len(folder_paths),
        folders_failed=len(folder_failures),
        manifest=manifest,
    )

    resolved_root = output_root.resolve()
    if routing_report:
        manifest_path = resolved_root / "manifest.csv"
        if manifest_path.exists():
            routing_root = resolved_root / "routing"
            console.print(f"[green]Generating routing report:[/green] {routing_root}")
            build_routing_report(manifest_path, routing_root)
        else:
            console.print("[yellow]Skipping routing report: no manifest.csv found at[/yellow] " + str(manifest_path))

    if vault_root is not None and markdown_root is not None:
        md_root = markdown_root.resolve()
        if md_root.exists():
            manifest_path = resolved_root / "manifest.csv"
            if manifest_path.exists():
                console.print(f"[green]Importing to vault:[/green] {vault_root}")
                count = vault_import(manifest_path, md_root, vault_root.resolve())
                console.print(f"[green]Imported {count} files to vault.[/green]")
            else:
                console.print("[yellow]Skipping vault import: no manifest.csv found[/yellow]")
        else:
            console.print(f"[yellow]Markdown root not found:[/yellow] {md_root}")

    if folder_failures:
        raise typer.Exit(code=1)



@app.command()
def mailboxes() -> None:
    """List available Outlook mailboxes/stores."""
    try:
        import win32com.client

        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        stores = outlook.Stores

        table = Table(title="Outlook Stores")
        table.add_column("#", justify="right")
        table.add_column("Display Name")
        table.add_column("Store Type")

        for idx, store in enumerate(stores, 1):
            name = str(getattr(store, "Name", "<unknown>")).strip()
            store_type = str(getattr(store, "StoreType", "<unknown>")).strip()
            table.add_row(str(idx), name, store_type)

        console.print(table)
        console.print(f"[dim]{len(stores)} store(s) found[/dim]")
    except Exception as exc:
        console.print(f"[red]Cannot connect to Outlook:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    return parse_iso_date(value)


def _resolve_checkpoint_for_folder(
    checkpoint_file: Path | None, output_root: Path, folder_path: str, multi_folder: bool,
    mailbox: str | None = None,
) -> Path | None:
    if not multi_folder:
        return checkpoint_file

    token = checkpoint_name_for_folder(folder_path, mailbox=mailbox)
    if checkpoint_file is None:
        return output_root / "checkpoints" / f"{token}.json"
    if checkpoint_file.suffix.lower() == ".json":
        return checkpoint_file.with_name(f"{checkpoint_file.stem}.{token}{checkpoint_file.suffix}")
    return checkpoint_file / f"{token}.json"


def _create_manifest_writer(output_root: Path) -> ManifestWriter:
    return ManifestWriter(
        csv_path=output_root / "manifest.csv",
        jsonl_path=output_root / "manifest.jsonl",
    )


def _print_summary(
    summary: ExtractionSummary,
    output_root: Path,
    dry_run: bool,
    folders_requested: int,
    folders_failed: int,
    manifest: bool = False,
) -> None:
    table = Table(title="Extraction Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Folders requested", str(folders_requested))
    table.add_row("Folders failed", str(folders_failed))
    table.add_row("Windows processed", str(summary.windows_processed))
    table.add_row("Exported", str(summary.exported))
    table.add_row("Markdown written", str(summary.markdown_written))
    table.add_row("Skipped (existing)", str(summary.skipped_existing))
    table.add_row("Skipped (non-mail)", str(summary.skipped_non_mail))
    table.add_row("Failed", str(summary.failed))
    table.add_row("Dry run", str(dry_run).lower())

    console.print(table)
    console.print(f"Output root: {output_root}")
    console.print(f"Success log: {output_root / 'logs' / 'success.csv'}")
    console.print(f"Error log:   {output_root / 'logs' / 'errors.csv'}")
    if manifest:
        console.print(f"Manifest:    {output_root / 'manifest.csv'} (+ JSONL)")
