import tempfile
from datetime import date
from pathlib import Path

from daily_note import DailyNote


def test_generates_note_with_links():
    with tempfile.TemporaryDirectory() as tmp:
        vault_root = Path(tmp) / "vault"
        folder = Path(tmp) / "applications" / "2026-06-25" / "samsara-tpm"
        dn = DailyNote(vault_root)
        today = date(2026, 6, 25)
        items = [
            {
                "company": "Samsara",
                "role": "TPM",
                "url": "https://example.com/samsara",
                "folder": str(folder),
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
    with tempfile.TemporaryDirectory() as tmp:
        vault_root = Path(tmp) / "vault"
        folder = Path(tmp) / "applications" / "2026-06-25" / "stripe-tpm"
        dn = DailyNote(vault_root)
        today = date(2026, 6, 25)
        items = [
            {
                "company": "Stripe",
                "role": "TPM",
                "url": "https://example.com/stripe",
                "folder": str(folder),
                "follow_up_date": "2026-07-02",
            }
        ]
        blocked = [
            {
                "company": "Samsara",
                "role": "TPM",
                "missing": [str(Path(tmp) / "resume-samsara-ats.pdf")],
            }
        ]
        text = dn.generate(today, items, blocked)
        assert "## Blocked" in text
        assert "**Samsara — TPM**: missing resume-samsara-ats.pdf" in text
