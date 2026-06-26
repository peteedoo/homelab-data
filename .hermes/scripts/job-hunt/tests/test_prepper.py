import tempfile
from datetime import date
from pathlib import Path

from prepper import Prepper
from vault_table import Row


def test_prep_creates_folder_and_files():
    with tempfile.TemporaryDirectory() as tmp:
        career = Path(tmp) / "career"
        career.mkdir()
        (career / "resume-samsara-ats.pdf").write_text("resume")
        (career / "cover-samsara.pdf").write_text("cover")

        prepper = Prepper(
            career_root=career,
            applications_dir="applications",
            resume_extension=".pdf",
            cover_extension=".pdf",
            follow_up_business_days=5,
        )
        row = Row({
            "Company": "Samsara",
            "Role": "TPM",
            "URL": "https://example.com/samsara",
            "Resume": "resume-samsara-ats",
            "Cover": "cover-samsara",
        })
        today = date(2026, 6, 25)
        folder = prepper.prep(row, today)

        assert folder.exists()
        assert (folder / "job_url.txt").read_text() == "https://example.com/samsara"
        assert (folder / "resume.pdf").exists()
        assert (folder / "cover.pdf").exists()
        assert (folder / "follow_up.txt").exists()
        content = (folder / "follow_up.txt").read_text()
        assert "Samsara" in content
        assert "TPM" in content


def test_prep_skips_missing_assets():
    with tempfile.TemporaryDirectory() as tmp:
        career = Path(tmp) / "career"
        career.mkdir()
        prepper = Prepper(career, "applications", ".pdf", ".pdf", 5)
        row = Row({
            "Company": "Ghost",
            "Role": "Dev",
            "URL": "https://example.com/ghost",
            "Resume": "missing",
            "Cover": "missing",
        })
        folder = prepper.prep(row, date(2026, 6, 25))
        assert not (folder / "resume.pdf").exists()
        assert not (folder / "cover.pdf").exists()
        assert (folder / "job_url.txt").exists()
