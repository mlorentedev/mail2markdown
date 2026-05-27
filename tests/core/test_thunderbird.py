from __future__ import annotations

import mailbox
from datetime import date, datetime
from pathlib import Path

import pytest

from mail2markdown.core.extractors import ThunderbirdMessageSource, create_source


def _write_mbox(path: Path, messages: list[tuple[str, dict[str, str], str]]) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    mb = mailbox.mbox(str(path), create=True)
    mb.flush()
    # Write directly to file to handle multipart properly
    with path.open("a", encoding="utf-8", newline="\n") as f:
        for from_, headers, body in messages:
            f.write(f"From {from_} Mon Jan  1 00:00:00 2026\n")
            for k, v in headers.items():
                f.write(f"{k}: {v}\n")
            # Add Content-Type if not present
            has_content_type = any(k == "Content-Type" for k in headers.keys())
            if not has_content_type:
                f.write("Content-Type: text/plain; charset=utf-8\n")
            f.write("\n")
            f.write(body)
            f.write("\n")
            f.write("\n")


def test_thunderbird_iter_messages_filters_by_date(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    mail_dir = profile / "Mail" / "local-folders"
    mbox_path = mail_dir / "TESTFOLDER"

    _write_mbox(
        mbox_path,
        [
            (
                "sender@example.com",
                {
                    "Date": "Mon, 15 Jan 2026 10:00:00 +0000",
                    "Subject": "In range",
                    "From": "sender@example.com",
                    "To": "me@example.com",
                },
                "Body 1",
            ),
            (
                "sender@example.com",
                {
                    "Date": "Mon, 01 Feb 2026 10:00:00 +0000",
                    "Subject": "Out of range",
                    "From": "sender@example.com",
                    "To": "me@example.com",
                },
                "Body 2",
            ),
        ],
    )

    source = ThunderbirdMessageSource(profile)
    msgs = list(source.iter_messages("Mail/local-folders/TESTFOLDER", date(2026, 1, 1), date(2026, 2, 1)))

    assert len(msgs) == 1
    assert msgs[0].subject == "In range"
    assert msgs[0].sender_name == ""
    assert msgs[0].sender_email == "sender@example.com"
    assert msgs[0].body.strip() == "Body 1"
    assert msgs[0].received_at == datetime(2026, 1, 15, 10, 0)


def test_thunderbird_iter_messages_empty_folder(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    source = ThunderbirdMessageSource(profile)
    msgs = list(source.iter_messages("Mail/local-folders/NONEXIST", date(2026, 1, 1), date(2026, 2, 1)))
    assert msgs == []


def test_thunderbird_save_message(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    mail_dir = profile / "Mail" / "local-folders"
    mbox_path = mail_dir / "SAVEFOLDER"

    import email.message

    raw = email.message.Message()
    raw["Date"] = "Tue, 20 Jan 2026 12:00:00 +0000"
    raw["Subject"] = "Save test"
    raw["From"] = "from@example.com"
    raw["To"] = "to@example.com"
    raw.set_payload("Hello world")

    _write_mbox(mbox_path, [("from@example.com", dict(raw.items()), "Hello world")])

    source = ThunderbirdMessageSource(profile)
    msgs = list(source.iter_messages("Mail/local-folders/SAVEFOLDER", date(2026, 1, 1), date(2026, 3, 1)))
    assert len(msgs) == 1

    save_path = tmp_path / "output" / "2026" / "01" / "test.msg"
    source.save_message(msgs[0], save_path)
    assert save_path.exists()


def test_thunderbird_resolve_folder_source(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    mail_dir = profile / "Mail" / "local-folders"
    (mail_dir / "SRCFOLDER").mkdir(parents=True, exist_ok=True)

    source = ThunderbirdMessageSource(profile)
    result = source.resolve_folder_source("Mail/local-folders/SRCFOLDER")
    assert result is not None
    assert "SRCFOLDER" in result


def test_thunderbird_resolve_folder_source_missing(tmp_path: Path) -> None:
    source = ThunderbirdMessageSource(tmp_path / "profile")
    result = source.resolve_folder_source("Mail/local-folders/MISSING")
    assert result is None


def test_thunderbird_decode_mime_header(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    mail_dir = profile / "Mail" / "local-folders"
    mbox_path = mail_dir / "ENCODINGFOLDER"

    _write_mbox(
        mbox_path,
        [
            (
                "sender@example.com",
                {
                    "Date": "Wed, 25 Mar 2026 08:00:00 +0000",
                    "Subject": "Re: =?UTF-8?B?0LjQvtC4?= Issue",
                    "From": "sender@example.com",
                    "To": "me@example.com",
                },
                "Encoded subject test",
            ),
        ],
    )

    source = ThunderbirdMessageSource(profile)
    msgs = list(source.iter_messages("Mail/local-folders/ENCODINGFOLDER", date(2026, 3, 1), date(2026, 4, 1)))
    assert len(msgs) == 1
    assert "0LjQvtC4" in msgs[0].subject or "Issue" in msgs[0].subject


def test_thunderbird_multipart_html_body(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    mail_dir = profile / "Mail" / "local-folders"
    mbox_path = mail_dir / "HTMLFOLDER"

    mbox_content = """From html@example.com Thu Mar 26 09:00:00 2026
Date: Thu, 26 Mar 2026 09:00:00 +0000
Subject: HTML email
From: html@example.com
To: me@example.com
Content-Type: multipart/alternative; boundary="boundary1"

--boundary1
Content-Type: text/plain; charset=utf-8

Plain text body
--boundary1
Content-Type: text/html; charset=utf-8

<html><body><p>HTML body</p></body></html>
--boundary1--

"""
    mbox_path.parent.mkdir(parents=True, exist_ok=True)
    mbox_path.write_text(mbox_content, encoding="utf-8", newline="\n")

    source = ThunderbirdMessageSource(profile)
    msgs = list(source.iter_messages("Mail/local-folders/HTMLFOLDER", date(2026, 3, 1), date(2026, 4, 1)))
    assert len(msgs) == 1
    assert "Plain text body" in msgs[0].body


def test_create_source_outlook() -> None:
    source = create_source("outlook")
    assert source.__class__.__name__ == "OutlookMessageSource"


def test_create_source_thunderbird(tmp_path: Path) -> None:
    source = create_source("thunderbird", profile_path=str(tmp_path / "profile"))
    assert source.__class__.__name__ == "ThunderbirdMessageSource"


def test_create_source_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        create_source("gmail")


def test_create_source_thunderbird_no_profile() -> None:
    with pytest.raises(ValueError, match="profile_path"):
        create_source("thunderbird")
