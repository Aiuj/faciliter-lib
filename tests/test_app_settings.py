import os
from pathlib import Path

from core_lib.utils.app_settings import AppSettings


def test_app_settings_reads_version_from_pyproject(tmp_path: Path, monkeypatch):
    # Create a fake project with a pyproject.toml
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(
        """
[project]
name = "dummy"
version = "9.8.7"
""".strip()
    )

    # Even if APP_VERSION is set, pyproject should take precedence
    monkeypatch.setenv("APP_VERSION", "1.2.3-env")

    s = AppSettings(app_name="Dummy", project_root=project_dir)
    assert s.version == "9.8.7"


def test_app_settings_env_and_defaults(monkeypatch, tmp_path: Path):
    # Change CWD to a temp folder with no pyproject to avoid auto-detection
    monkeypatch.chdir(tmp_path)

    # No project_root pyproject.toml -> fallback to env, then default
    monkeypatch.delenv("APP_VERSION", raising=False)
    s_default = AppSettings(app_name="NoProj", project_root=None)
    assert s_default.version == "0.1.0"

    monkeypatch.setenv("APP_VERSION", "2.0.0")
    s_env = AppSettings(app_name="NoProj", project_root=None)
    assert s_env.version == "2.0.0"


def test_app_settings_log_level(monkeypatch, tmp_path: Path):
    # Prepare pyproject
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0.0.1'\n")

    # ENVIRONMENT=dev -> default DEBUG
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s_dev = AppSettings(app_name="x", project_root=tmp_path)
    assert s_dev.log_level == "DEBUG"

    # ENVIRONMENT=prod -> default INFO unless overridden
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s_prod = AppSettings(app_name="x", project_root=tmp_path)
    assert s_prod.log_level == "INFO"

    # Override
    monkeypatch.setenv("LOG_LEVEL", "warning")
    s_warn = AppSettings(app_name="x", project_root=tmp_path)
    assert s_warn.log_level == "WARNING"
