# ~/.hermes/scripts/job-hunt/orchestrator.py
import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

from daily_note import DailyNote
from prepper import Prepper
from state import StateStore
from vault_table import Row, VaultTable


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def select_rows(
    rows: list[Row],
    priority_order: list[str],
    priority_caps: dict[str, int],
    state,
) -> list[Row]:
    """Return ready rows sorted by priority and capped per priority.

    A cap of ``0`` or a missing priority key means "unlimited" for that
    priority. The overall daily limit is enforced during processing so that
    blocked rows do not consume a slot.
    """
    selected = []
    for priority in priority_order:
        cap = priority_caps.get(priority, 0)
        priority_rows = []
        for r in rows:
            if r.get("Priority") != priority:
                continue
            url = r.get("URL").strip()
            if not url:
                continue
            if state.is_prepped(url):
                continue
            priority_rows.append(r)
        if cap > 0:
            priority_rows = priority_rows[:cap]
        selected.extend(priority_rows)
    return selected


def build_tracker_row(row: Row, today: date, follow_up_date: date) -> Row:
    return Row({
        "Date Prepped": today.isoformat(),
        "Date Applied": "",
        "Company": row.get("Company"),
        "Role": row.get("Role"),
        "URL": row.get("URL"),
        "Status": "Prepped",
        "Follow-up Due": follow_up_date.isoformat(),
        "Response": "",
        "Notes": row.get("Notes"),
    })


def run(config: dict, dry_run: bool) -> None:
    today = date.today()
    scripts_root = Path(config["scripts_root"])
    vault_root = Path(config["vault_root"])
    career_root = Path(config["career_root"])

    state_store = StateStore(scripts_root / "state.json")
    state = state_store.load()

    backlog_path = vault_root / config["backlog_path"]
    tracker_path = vault_root / config["tracker_path"]
    daily_note_path = vault_root / config["daily_note_path_template"].format(date=today.isoformat())

    backlog_text = backlog_path.read_text(encoding="utf-8")
    backlog_vt = VaultTable(backlog_text)

    ready_rows = [
        r for r in backlog_vt.table.rows
        if r.get("Status").strip().lower() == "ready"
    ]

    capped_rows = select_rows(
        ready_rows,
        config["priority_order"],
        config.get("priority_caps", {}),
        state,
    )

    prepper = Prepper(
        career_root=career_root,
        applications_dir=config["applications_dir"],
        resume_extension=config["resume_extension"],
        cover_extension=config["cover_extension"],
        follow_up_business_days=config["follow_up_business_days"],
        follow_up_template=config.get("follow_up_template"),
    )
    daily = DailyNote(vault_root)

    tracker_text = tracker_path.read_text(encoding="utf-8")
    tracker_vt = VaultTable(tracker_text)

    prepped_items = []
    blocked_items = []

    if not dry_run:
        shutil.copy(backlog_path, backlog_path.with_suffix(".md.bak"))
        shutil.copy(tracker_path, tracker_path.with_suffix(".md.bak"))

    for row in capped_rows:
        url = row.get("URL").strip()
        company = row.get("Company")
        role = row.get("Role")

        if state.is_prepped(url):
            continue

        if len(prepped_items) >= config["daily_limit"]:
            break

        if dry_run:
            print(f"[dry-run] Would prep: {company} — {role}")
            prepped_items.append({
                "company": company,
                "role": role,
                "url": url,
                "folder": "(dry-run)",
                "follow_up_date": "(dry-run)",
            })
            continue

        folder = prepper.prep(row, today)
        if folder is None:
            blocked_items.append({
                "company": company,
                "role": role,
                "missing": prepper.missing_assets(row),
            })
            continue

        row.update("Status", "Prepped")
        state.mark_prepped(url)

        follow_up_date = prepper.follow_up_date(today)
        tracker_vt.table.rows.append(build_tracker_row(row, today, follow_up_date))

        prepped_items.append({
            "company": company,
            "role": role,
            "url": url,
            "folder": str(folder),
            "follow_up_date": follow_up_date.isoformat(),
        })

    if not dry_run:
        backlog_path.write_text(backlog_vt.replace_table(backlog_vt.table), encoding="utf-8")
        tracker_path.write_text(tracker_vt.replace_table(tracker_vt.table), encoding="utf-8")

        daily_note_path.parent.mkdir(parents=True, exist_ok=True)
        daily_note_path.write_text(
            daily.generate(today, prepped_items, blocked=blocked_items),
            encoding="utf-8",
        )

        state.last_run = today.isoformat()
        state_store.save(state)
        print(f"Prepped {len(prepped_items)} role(s).")
        if blocked_items:
            print(f"Blocked {len(blocked_items)} role(s) — see daily note.")
        print(f"Daily note: {daily_note_path}")
    else:
        print(f"\nDry run: would prep {len(prepped_items)} role(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes job-hunt daily driver")
    parser.add_argument("--config", default="~/.hermes/scripts/job-hunt/config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        config = load_config(Path(args.config).expanduser())
        run(config, args.dry_run)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"Error: invalid YAML in config - {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
