import runpy
import sys
from pathlib import Path


def test_control_panel_imports_when_project_root_is_not_current_directory(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if Path(entry or ".").resolve() != project_root])

    runpy.run_path(
        str(project_root / "app" / "control_panel.py"),
        run_name="streamlit_app",
    )
