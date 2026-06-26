import tempfile
from datetime import date
from pathlib import Path

from orchestrator import load_config, run, select_rows
from state import State
from vault_table import Row


def test_select_rows_ignores_daily_limit():
    state = State()
    rows = [
        Row({"Priority": "A", "URL": "https://a1", "Company": "A1", "Role": "R"}),
        Row({"Priority": "A", "URL": "https://a2", "Company": "A2", "Role": "R"}),
        Row({"Priority": "B", "URL": "https://b1", "Company": "B1", "Role": "R"}),
    ]
    selected = select_rows(rows, ["A", "B", "C"], {"A": 0, "B": 0, "C": 0}, 1, state)
    assert len(selected) == 3
    assert selected[0].get("Company") == "A1"
    assert selected[1].get("Company") == "A2"
    assert selected[2].get("Company") == "B1"


def test_select_rows_skips_prepped():
    state = State()
    state.mark_prepped("https://a1")
    rows = [
        Row({"Priority": "A", "URL": "https://a1", "Company": "A1", "Role": "R"}),
        Row({"Priority": "A", "URL": "https://a2", "Company": "A2", "Role": "R"}),
    ]
    selected = select_rows(rows, ["A", "B", "C"], {"A": 0, "B": 0, "C": 0}, 10, state)
    assert len(selected) == 1
    assert selected[0].get("Company") == "A2"


def test_select_rows_respects_priority_caps():
    state = State()
    rows = [
        Row({"Priority": "A", "URL": "https://a1", "Company": "A1", "Role": "R"}),
        Row({"Priority": "A", "URL": "https://a2", "Company": "A2", "Role": "R"}),
        Row({"Priority": "B", "URL": "https://b1", "Company": "B1", "Role": "R"}),
        Row({"Priority": "B", "URL": "https://b2", "Company": "B2", "Role": "R"}),
        Row({"Priority": "C", "URL": "https://c1", "Company": "C1", "Role": "R"}),
    ]
    selected = select_rows(rows, ["A", "B", "C"], {"A": 1, "B": 1, "C": 0}, 10, state)
    assert len(selected) == 3
    assert selected[0].get("Priority") == "A"
    assert selected[1].get("Priority") == "B"
    assert selected[2].get("Priority") == "C"


def test_select_rows_priority_caps_trumps_daily_limit():
    state = State()
    rows = [
        Row({"Priority": "A", "URL": f"https://a{i}", "Company": f"A{i}", "Role": "R"})
        for i in range(1, 6)
    ]
    selected = select_rows(rows, ["A", "B", "C"], {"A": 10, "B": 0, "C": 0}, 3, state)
    assert len(selected) == 5


def test_load_config_reads_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("daily_limit: 5\npriority_order: [A, B]\n")
        path = Path(f.name)
    try:
        config = load_config(path)
        assert config["daily_limit"] == 5
        assert config["priority_order"] == ["A", "B"]
    finally:
        path.unlink()


def test_run_dry_run(capfd):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        vault_root = tmp_path / "vault"
        career_root = tmp_path / "career"
        scripts_root = tmp_path / "scripts"
        vault_root.mkdir()
        career_root.mkdir()
        scripts_root.mkdir()

        backlog_dir = vault_root / "03 - Areas" / "Career & Job Hunt"
        backlog_dir.mkdir(parents=True)
        backlog_path = backlog_dir / "Job Backlog.md"
        backlog_path.write_text(
            "| Priority | Status | Company | Role | URL | Resume | Cover | Notes |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| A | Ready | Acme | Engineer | https://acme.example | resume | cover | note |\n"
        )

        tracker_path = backlog_dir / "Application Tracker.md"
        tracker_path.write_text(
            "| Date Prepped | Date Applied | Company | Role | URL | Status | Follow-up Due | Response | Notes |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
        )

        daily_dir = vault_root / "06 - Daily"
        daily_dir.mkdir(parents=True)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(f"""
vault_root: "{vault_root}"
career_root: "{career_root}"
scripts_root: "{scripts_root}"
backlog_path: "03 - Areas/Career & Job Hunt/Job Backlog.md"
tracker_path: "03 - Areas/Career & Job Hunt/Application Tracker.md"
daily_note_path_template: "06 - Daily/{{date}} — Job Hunt.md"
applications_dir: "applications"
daily_limit: 10
priority_order:
  - "A"
  - "B"
  - "C"
priority_caps:
  A: 0
  B: 0
  C: 0
follow_up_business_days: 5
resume_extension: ".pdf"
cover_extension: ".pdf"
""")

        config = load_config(config_path)
        run(config, dry_run=True)

        captured = capfd.readouterr()
        assert "[dry-run] Would prep: Acme — Engineer" in captured.out
        assert "Dry run: would prep 1 role(s)." in captured.out

        # No state, backlog, or tracker mutations in dry-run mode.
        assert not (scripts_root / "state.json").exists()
        assert not backlog_path.with_suffix(".md.bak").exists()
        assert not tracker_path.with_suffix(".md.bak").exists()
        tracker_vt_text = tracker_path.read_text()
        assert "Acme" not in tracker_vt_text


def _make_run_fixtures(tmp_path: Path):
    vault_root = tmp_path / "vault"
    career_root = tmp_path / "career"
    scripts_root = tmp_path / "scripts"
    vault_root.mkdir()
    career_root.mkdir()
    scripts_root.mkdir()

    backlog_dir = vault_root / "03 - Areas" / "Career & Job Hunt"
    backlog_dir.mkdir(parents=True)
    backlog_path = backlog_dir / "Job Backlog.md"
    tracker_path = backlog_dir / "Application Tracker.md"
    tracker_path.write_text(
        "| Date Prepped | Date Applied | Company | Role | URL | Status | Follow-up Due | Response | Notes |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )

    daily_dir = vault_root / "06 - Daily"
    daily_dir.mkdir(parents=True)

    config_path = tmp_path / "config.yaml"

    return {
        "vault_root": vault_root,
        "career_root": career_root,
        "scripts_root": scripts_root,
        "backlog_dir": backlog_dir,
        "backlog_path": backlog_path,
        "tracker_path": tracker_path,
        "config_path": config_path,
    }


def _write_config(config_path: Path, fixtures: dict, daily_limit: int) -> None:
    config_path.write_text(f"""
vault_root: "{fixtures['vault_root']}"
career_root: "{fixtures['career_root']}"
scripts_root: "{fixtures['scripts_root']}"
backlog_path: "03 - Areas/Career & Job Hunt/Job Backlog.md"
tracker_path: "03 - Areas/Career & Job Hunt/Application Tracker.md"
daily_note_path_template: "06 - Daily/{{date}} — Job Hunt.md"
applications_dir: "applications"
daily_limit: {daily_limit}
priority_order:
  - "A"
  - "B"
  - "C"
priority_caps:
  A: 0
  B: 0
  C: 0
follow_up_business_days: 5
resume_extension: ".pdf"
cover_extension: ".pdf"
""")


def test_blocked_rows_do_not_count_toward_daily_limit(tmp_path):
    fixtures = _make_run_fixtures(tmp_path)

    # Missing assets for BlockedCorp; Gamma has assets.
    fixtures["backlog_path"].write_text(
        "| Priority | Status | Company | Role | URL | Resume | Cover | Notes |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| A | Ready | BlockedCorp | Engineer | https://blocked.example | missing_resume | missing_cover | note |\n"
        "| A | Ready | Gamma | Designer | https://gamma.example | gamma_resume | gamma_cover | note |\n"
    )

    (fixtures["career_root"] / "gamma_resume.pdf").write_text("resume")
    (fixtures["career_root"] / "gamma_cover.pdf").write_text("cover")

    _write_config(fixtures["config_path"], fixtures, daily_limit=1)
    config = load_config(fixtures["config_path"])
    run(config, dry_run=False)

    tracker_text = fixtures["tracker_path"].read_text()
    backlog_text = fixtures["backlog_path"].read_text()

    assert "Gamma" in tracker_text
    assert "BlockedCorp" not in tracker_text
    assert "BlockedCorp" in backlog_text
    assert "| A | Ready | BlockedCorp" in backlog_text
    assert "| A | Prepped | Gamma" in backlog_text


def test_state_last_run_is_set(tmp_path):
    fixtures = _make_run_fixtures(tmp_path)

    fixtures["backlog_path"].write_text(
        "| Priority | Status | Company | Role | URL | Resume | Cover | Notes |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| A | Ready | Delta | Manager | https://delta.example | delta_resume | delta_cover | note |\n"
    )

    (fixtures["career_root"] / "delta_resume.pdf").write_text("resume")
    (fixtures["career_root"] / "delta_cover.pdf").write_text("cover")

    _write_config(fixtures["config_path"], fixtures, daily_limit=10)
    config = load_config(fixtures["config_path"])
    run(config, dry_run=False)

    state_path = fixtures["scripts_root"] / "state.json"
    assert state_path.exists()
    import json
    saved = json.loads(state_path.read_text())
    assert saved["last_run"] == date.today().isoformat()
