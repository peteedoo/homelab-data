import pytest

from vault_table import MarkdownTable, Row, VaultTable


def test_parse_simple_table():
    text = """| Status | Company | Role |
|--------|---------|------|
| Ready | Samsara | TPM |
| Prepped | OLIPOP | TPM |
"""
    table = MarkdownTable.parse(text)
    assert table.headers == ["Status", "Company", "Role"]
    assert len(table.rows) == 2
    assert table.rows[0].get("Company") == "Samsara"
    assert table.rows[1].get("Status") == "Prepped"


def test_row_update_and_render():
    text = """| Status | Company |
|--------|---------|
| Ready | Samsara |
"""
    table = MarkdownTable.parse(text)
    table.rows[0].update("Status", "Prepped")
    rendered = table.render()
    assert "| Prepped | Samsara |" in rendered


def test_vault_table_replace_preserves_surrounding_text():
    text = """# Backlog

| Status | Company |
|--------|---------|
| Ready | Samsara |

Some notes below.
"""
    vt = VaultTable(text)
    vt.table.rows[0].update("Status", "Prepped")
    new_text = vt.replace_table(vt.table)
    assert "# Backlog" in new_text
    assert "| Prepped | Samsara |" in new_text
    assert "Some notes below." in new_text


def test_vault_table_appends_if_no_table():
    text = "# Backlog\n\nNo roles yet.\n"
    vt = VaultTable(text)
    vt.table.headers = ["Status", "Company"]
    vt.table.rows = [Row({"Status": "Ready", "Company": "Samsara"})]
    new_text = vt.replace_table(vt.table)
    assert "| Status | Company |" in new_text
    assert "| Ready | Samsara |" in new_text


def test_parse_malformed_table_too_few_lines():
    text = "| Status | Company |\n"
    with pytest.raises(ValueError, match="Malformed markdown table"):
        MarkdownTable.parse(text)


def test_parse_row_wrong_number_of_cells():
    text = """| Status | Company |
|--------|---------|
| Ready |
"""
    with pytest.raises(ValueError, match="Row has wrong number of cells"):
        MarkdownTable.parse(text)
