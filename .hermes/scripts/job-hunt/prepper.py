import re
import shutil
from datetime import date, timedelta
from pathlib import Path

from vault_table import Row


class Prepper:
    def __init__(
        self,
        career_root: Path,
        applications_dir: str,
        resume_extension: str,
        cover_extension: str,
        follow_up_business_days: int,
        follow_up_template: str | None = None,
    ):
        self.career_root = Path(career_root)
        self.applications_dir = applications_dir
        self.resume_extension = resume_extension
        self.cover_extension = cover_extension
        self.follow_up_business_days = follow_up_business_days
        self.follow_up_template = follow_up_template

    def _folder_name(self, row: Row) -> str:
        company = re.sub(r"[^\w\-]", "", row.get("Company").replace(" ", "-"))
        role = re.sub(r"[^\w\-]", "", row.get("Role").replace(" ", "-"))
        return f"{company}-{role}".lower()

    def _add_business_days(self, start: date, days: int) -> date:
        current = start
        added = 0
        while added < days:
            current += timedelta(days=1)
            if current.weekday() < 5:
                added += 1
        return current

    def missing_assets(self, row: Row) -> list[str]:
        missing = []
        resume_src = self.career_root / f"{row.get('Resume')}{self.resume_extension}"
        if not resume_src.exists():
            missing.append(str(resume_src))
        cover_src = self.career_root / f"{row.get('Cover')}{self.cover_extension}"
        if not cover_src.exists():
            missing.append(str(cover_src))
        return missing

    def prep(self, row: Row, today: date) -> Path | None:
        folder = (
            self.career_root
            / self.applications_dir
            / today.isoformat()
            / self._folder_name(row)
        )

        if self.missing_assets(row):
            return None

        folder.mkdir(parents=True, exist_ok=True)

        resume_src = self.career_root / f"{row.get('Resume')}{self.resume_extension}"
        shutil.copy(resume_src, folder / f"resume{self.resume_extension}")

        cover_src = self.career_root / f"{row.get('Cover')}{self.cover_extension}"
        shutil.copy(cover_src, folder / f"cover{self.cover_extension}")

        (folder / "job_url.txt").write_text(row.get("URL"), encoding="utf-8")

        follow_up_date = self._add_business_days(today, self.follow_up_business_days)
        if self.follow_up_template:
            follow_up_text = self.follow_up_template.format(
                role=row.get("Role"),
                company=row.get("Company"),
                follow_up_date=follow_up_date.isoformat(),
            )
        else:
            follow_up_text = f"""Follow up on {follow_up_date.isoformat()}

Hi [NAME],

I applied for the {row.get('Role')} role at {row.get('Company')} and wanted to follow up.

Best,
Petee
"""
        (folder / "follow_up.txt").write_text(follow_up_text, encoding="utf-8")

        return folder
