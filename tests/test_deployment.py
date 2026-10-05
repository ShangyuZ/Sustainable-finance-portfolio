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

import re
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


# ── claims about third-party rights ──────────────────────────────────────────

BLANKET_LICENCE_CLAIM = re.compile(
    r"all data[^.]{0,60}(openly licensed|freely licensed)"
    r"|no proprietary or restricted data is used anywhere", re.I)


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    """
    Character ranges the document is quoting rather than asserting.

    Two forms count. Double quotes, straight or curly — paired across the whole
    document rather than per line, because a quotation in prose is routinely
    wrapped across a line break and a per-line parser mis-pairs the quote
    characters when it is. And Markdown blockquote lines, because reproducing a
    retired sentence as a block quotation is the other natural way to cite it,
    and a guard that only understood inline quotes would stop the repository
    quoting its own withdrawn claims at length.
    """
    spans, open_at = [], None
    for i, ch in enumerate(text):
        if ch in '"\u201c\u201d':
            if open_at is None:
                open_at = i
            else:
                spans.append((open_at, i))
                open_at = None

    offset = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(">"):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return spans


def _blanket_licence_assertions(text: str) -> list[str]:
    """
    Every place the text *makes* the blanket claim, rather than quoting it.

    FINDINGS.md and the README both reproduce the retired sentence to explain why
    it was withdrawn; a guard that could not tell the difference would stop the
    repository describing its own corrections.
    """
    spans = _quoted_spans(text)
    lowered = text.lower()
    found = []
    for match in BLANKET_LICENCE_CLAIM.finditer(text):
        asserted = False
        for phrase in ("openly licensed", "freely licensed", "used anywhere"):
            start = match.start()
            i = lowered.find(phrase, start, match.end() + len(phrase))
            if i == -1:
                continue
            if not any(a < i and i + len(phrase) <= b + 1 for a, b in spans):
                asserted = True
        if asserted:
            found.append(" ".join(text[match.start():match.end() + 40].split()))
    return found


@pytest.mark.parametrize("rel", ["README.md", "project1-green-bond-analysis/README.md",
                                 "project3-climate-dashboard/README.md", "FINDINGS.md"])
def test_no_unverified_blanket_licensing_claim(rel):
    """
    No document may assert that *all* data here is openly licensed.

    Three datasets have unverified or unknown terms (DATA.md). A blanket claim
    about third-party rights that nobody checked is the same failure mode as the
    Bloomberg claim in FINDINGS.md section 1, with legal exposure attached.
    """
    path = ROOT / rel
    if not path.exists():
        pytest.skip(f"{rel} not present")
    hits = _blanket_licence_assertions(path.read_text(encoding="utf-8"))
    assert not hits, f"unverified blanket licensing claim in {rel}:\n  " + "\n  ".join(hits)


def test_the_guard_still_catches_a_real_assertion():
    """The guard must not be so permissive that it never fires."""
    assert _blanket_licence_assertions("All data is publicly available and openly licensed.")
    assert _blanket_licence_assertions("No proprietary or restricted data is used anywhere.")
    # A block-quoted mention is allowed too: FINDINGS.md section 1 reproduces both
    # retired sentences as block quotations before explaining what replaced them.
    assert not _blanket_licence_assertions(
        "The README said, and had said for months:\n\n"
        "> All data is publicly available and openly licensed. No proprietary or\n"
        "> restricted data is used anywhere.\n\n"
        "Both halves were wrong.")
    # But a blockquote must not launder an assertion on an adjacent line.
    assert _blanket_licence_assertions(
        "> quoting something else entirely\n"
        "All data here is openly licensed.")
    # A quoted, retrospective mention is allowed — including across a line break,
    # which is how it actually appears in the README and FINDINGS.md.
    assert not _blanket_licence_assertions(
        'It used to claim that all data here is "openly licensed" and that\n'
        '"no proprietary or restricted data is used anywhere". That was never verified.')


def test_data_provenance_file_exists_and_marks_the_unverified():
    """DATA.md must exist and must not quietly mark everything as fine."""
    data_md = ROOT / "DATA.md"
    assert data_md.exists(), "DATA.md is missing; the README defers to it"
    text = data_md.read_text(encoding="utf-8")
    assert "not verified" in text.lower()
    for dataset in ("Climate Bonds", "Finanzagentur", "eua_prices"):
        assert dataset in text, f"DATA.md does not cover {dataset}"


def test_licence_file_exists_and_scopes_itself_to_original_work():
    """
    A licence that implicitly covered the third-party data would be a claim we
    cannot make.
    """
    licence = ROOT / "LICENSE"
    assert licence.exists(), "no LICENSE: the repo defaults to all-rights-reserved"
    text = licence.read_text(encoding="utf-8")
    assert "does NOT cover the third-party datasets" in text


# ── the published links ──────────────────────────────────────────────────────

LIVE_URL = "https://shangyuz-sustainable-finance.streamlit.app"


def test_live_url_is_recorded_in_both_readmes():
    """
    The deployed URL is the single most-clicked thing in this repository.

    If it is changed on Streamlit's side, both READMEs have to change with it —
    so they are checked together rather than one being left stale.
    """
    for readme in (ROOT / "README.md", DASHBOARD / "README.md"):
        assert LIVE_URL in readme.read_text(encoding="utf-8"), f"live URL missing from {readme.name}"


def test_deployment_is_marked_done():
    text = (DASHBOARD / "README.md").read_text(encoding="utf-8")
    assert "- [x] Deployed to Streamlit Community Cloud" in text
    assert "Not yet deployed" not in text


def test_documents_linked_from_the_root_readme_exist():
    """A broken PDF link on the landing page is worse than no link."""
    import re
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\((\./[^)]+\.pdf)\)", text)
    assert targets, "no PDF links found in the root README"
    for target in targets:
        assert (ROOT / target.lstrip("./")).exists(), f"broken link: {target}"
