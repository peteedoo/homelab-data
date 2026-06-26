from datetime import date
from pathlib import Path


class DailyNote:
    def __init__(self, vault_root: Path):
        self.vault_root = Path(vault_root)

    def generate(self, today: date, items: list[dict]) -> str:
        lines = [f"# {today.isoformat()} — Job Hunt", ""]
        lines.append(f"**Roles prepped today:** {len(items)}")
        lines.append("")
        if not items:
            lines.append("No roles prepped today.")
        for item in items:
            lines.append(f"## {item['company']} — {item['role']}")
            lines.append(f"- [ ] Applied")
            lines.append(f"- Apply URL: {item['url']}")
            lines.append(f"- Packet folder: {item['folder']}")
            lines.append(f"- Follow up: {item['follow_up_date']}")
            lines.append("")
        return "\n".join(lines) + "\n"
