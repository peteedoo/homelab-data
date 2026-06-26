import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

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


def test_prep_with_empty_cover_skips_cover():
    with tempfile.TemporaryDirectory() as tmp:
        career = Path(tmp) / "career"
        career.mkdir()
        (career / "resume-samsara-ats.pdf").write_text("resume")

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
            "Cover": "",
        })
        today = date(2026, 6, 25)
        assert prepper.missing_assets(row) == []
        folder = prepper.prep(row, today)
        assert folder.exists()
        assert (folder / "resume.pdf").exists()
        assert not (folder / "cover.pdf").exists()


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
        result = prepper.prep(row, date(2026, 6, 25))
        assert result is None
        assert prepper.missing_assets(row) != []
        folder = (
            career
            / "applications"
            / date(2026, 6, 25).isoformat()
            / "Ghost-Dev"
        )
        assert not folder.exists()


def test_prep_raises_runtime_error_on_copy_failure():
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
        with patch("prepper.shutil.copy", side_effect=PermissionError("denied")):
            with pytest.raises(RuntimeError, match="I/O error for"):
                prepper.prep(row, date(2026, 6, 25))


def test_prep_raises_runtime_error_on_write_failure():
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
        with patch.object(Path, "write_text", side_effect=PermissionError("denied")):
            with pytest.raises(RuntimeError, match="I/O error for"):
                prepper.prep(row, date(2026, 6, 25))
