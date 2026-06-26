from datetime import date
from pathlib import Path

from daily_note import DailyNote


def test_generates_note_with_links():
    dn = DailyNote(Path("/Users/peteedoo/Documents/Obsidian/Vault"))
    today = date(2026, 6, 25)
    items = [
        {
            "company": "Samsara",
            "role": "TPM",
            "url": "https://example.com/samsara",
            "folder": "/Users/peteedoo/ops/career/applications/2026-06-25/samsara-tpm",
            "follow_up_date": "2026-07-02",
        }
    ]
    text = dn.generate(today, items)
    assert "# 2026-06-25 — Job Hunt" in text
    assert "Samsara" in text
    assert "- [ ] Applied" in text
    assert "https://example.com/samsara" in text
    assert "2026-07-02" in text


def test_generates_note_with_blocked_section():
    dn = DailyNote(Path("/Users/peteedoo/Documents/Obsidian/Vault"))
    today = date(2026, 6, 25)
    items = [
        {
            "company": "Stripe",
            "role": "TPM",
            "url": "https://example.com/stripe",
            "folder": "/Users/peteedoo/ops/career/applications/2026-06-25/stripe-tpm",
            "follow_up_date": "2026-07-02",
        }
    ]
    blocked = [
        {
            "company": "Samsara",
            "role": "TPM",
            "missing": ["/Users/peteedoo/ops/career/resume-samsara-ats.pdf"],
        }
    ]
    text = dn.generate(today, items, blocked)
    assert "## Blocked" in text
    assert "**Samsara — TPM**: missing resume-samsara-ats.pdf" in text
