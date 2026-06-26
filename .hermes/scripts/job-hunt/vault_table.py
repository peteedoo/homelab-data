from dataclasses import dataclass


@dataclass
class Row:
    cells: dict[str, str]

    def get(self, key: str) -> str:
        return self.cells.get(key, "")

    def update(self, key: str, value: str) -> None:
        self.cells[key] = value


class MarkdownTable:
    def __init__(self, headers: list[str], rows: list[Row]):
        self.headers = headers
        self.rows = rows

    @classmethod
    def parse(cls, text: str) -> "MarkdownTable":
        lines = text.splitlines()
        table_lines = []
        for line in lines:
            if line.strip().startswith("|"):
                table_lines.append(line)
            elif table_lines:
                break
        if len(table_lines) < 2:
            raise ValueError("Malformed markdown table")
        headers = [h.strip() for h in table_lines[0].split("|")[1:-1]]
        rows = []
        for line in table_lines[2:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) != len(headers):
                raise ValueError("Row has wrong number of cells")
            rows.append(Row(dict(zip(headers, cells))))
        return cls(headers, rows)

    def render(self) -> str:
        lines = ["| " + " | ".join(self.headers) + " |"]
        lines.append("|" + "|".join(["---" for _ in self.headers]) + "|")
        for row in self.rows:
            lines.append("| " + " | ".join(row.cells.get(h, "") for h in self.headers) + " |")
        return "\n".join(lines) + "\n"


class VaultTable:
    def __init__(self, text: str):
        self.text = text
        try:
            self.table = MarkdownTable.parse(text)
        except ValueError:
            self.table = MarkdownTable([], [])

    def replace_table(self, new_table: MarkdownTable) -> str:
        lines = self.text.splitlines()
        start = None
        end = None
        for i, line in enumerate(lines):
            if line.strip().startswith("|"):
                if start is None:
                    start = i
                end = i
            elif start is not None:
                break
        rendered = new_table.render().splitlines()
        if start is None:
            return self.text.rstrip() + "\n\n" + "\n".join(rendered) + "\n"
        new_lines = lines[:start] + rendered + lines[end + 1 :]
        return "\n".join(new_lines) + "\n"
