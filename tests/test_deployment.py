"""
Deployment preconditions for the Streamlit dashboard.

Streamlit Community Cloud runs the app with the **repository root** as the
working directory, not the app's own folder. Two things follow, and both failed
silently before these tests existed:

- ``.streamlit/config.toml`` is resolved relative to the working directory, so a
  config that lives only beside the app is ignored on Cloud and the theme is
  dropped without any error.
- ``app.py`` does ``from transforms import ...``. That resolves because Streamlit
  puts the main script's directory on ``sys.path``, which is worth pinning down
  rather than assuming.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "project3-climate-dashboard"
APP = DASHBOARD / "app.py"
ROOT_CONFIG = ROOT / ".streamlit" / "config.toml"
APP_CONFIG = DASHBOARD / ".streamlit" / "config.toml"


def parsed(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


# ── theme config ─────────────────────────────────────────────────────────────

def test_root_streamlit_config_exists():
    """
    Without this, Streamlit Cloud drops the theme silently.

    Cloud's working directory is the repository root, so a config only inside
    project3-climate-dashboard/ is never read.
    """
    assert ROOT_CONFIG.exists(), (
        "missing .streamlit/config.toml at the repository root — Streamlit Cloud "
        "would run the app unthemed")


def test_both_configs_agree():
    """The duplicate exists for a reason; it must not drift."""
    if not (ROOT_CONFIG.exists() and APP_CONFIG.exists()):
        pytest.skip("one of the configs is absent")
    assert parsed(ROOT_CONFIG) == parsed(APP_CONFIG), (
        "the repository-root and app-level Streamlit configs have diverged; the "
        "deployed theme would differ from the local one")


def test_theme_is_set():
    cfg = parsed(ROOT_CONFIG)
    assert "theme" in cfg
    assert cfg["theme"].get("primaryColor")


# ── dependencies ─────────────────────────────────────────────────────────────

def test_requirements_cover_the_app_imports():
    """
    Every third-party module app.py imports must be declared.

    Cloud installs from a requirements file; a missing entry is a build failure
    at deploy time rather than a test failure here.
    """
    declared = set()
    for req in (ROOT / "requirements.txt", DASHBOARD / "requirements.txt"):
        if not req.exists():
            continue
        for line in req.read_text().splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-"):
                name = line.split(">=")[0].split("==")[0].split("[")[0].strip()
                declared.add(name.lower())

    needed = {"streamlit", "plotly", "pandas"}
    assert needed <= declared, f"undeclared dependencies: {needed - declared}"


def test_streamlit_floor_supports_the_width_argument():
    """
    The app uses ``width="stretch"``, which needs Streamlit >= 1.49.

    ``use_container_width`` is past its removal date, so pinning the floor is
    what keeps the app working rather than warning.
    """
    text = (ROOT / "requirements.txt").read_text()
    assert "streamlit>=1.49" in text or "streamlit>=1.5" in text, (
        "streamlit floor is too low for width='stretch'")


def test_app_does_not_use_the_removed_argument():
    assert "use_container_width" not in APP.read_text(), (
        "use_container_width is past its removal date; use width='stretch'")


# ── entrypoint ───────────────────────────────────────────────────────────────

def test_app_entrypoint_exists():
    assert APP.exists()


def test_local_module_sits_beside_the_app():
    """
    ``from transforms import ...`` relies on Streamlit putting the script's own
    directory on sys.path, so the module must be beside app.py — not at the root.
    """
    assert (DASHBOARD / "transforms.py").exists()
    assert "from transforms import" in APP.read_text()


def test_bundled_data_is_present():
    """The EUA chart falls back to synthetic data without this file."""
    assert (DASHBOARD / "data" / "eua_prices.csv").exists()
