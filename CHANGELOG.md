# Changelog

All notable changes to this portfolio are documented here.

---

## [v0.3.0] — 2026-06-11 — Big update: bug fixes, new dashboard section, CI

### Fixed
- `project3/app.py`: Replaced fabricated Ember GitHub URL with bundled `data/eua_prices.csv`
  (the previous URL pointed to a non-existent repository and always fell through to synthetic data)
- `project3/app.py`: OWID region filtering now uses ISO code (`iso_code` must be 3 letters,
  not starting with `OWID`) — replaces the incomplete manual exclusion set that missed
  dozens of aggregate entries (e.g. "Central Africa", "Eastern Europe")
- `project3/app.py`: Added null-guard on EUA price load to prevent `KeyError` crash
  if data file is missing or malformed
- `project1/scripts/process_data.py`: Removed unused imports (`Path`, `Border`, `Side`)
  and unused `THEME_COLOURS` dict

### Added
- `project3/data/eua_prices.csv`: Bundled weekly EU ETS EUA price history (2018–2026)
  compiled from public sources — dashboard now works fully offline
- `project3/.streamlit/config.toml`: Green brand theme applied across the app
- **Country Climate Scorecard** (new dashboard section): Ranked table + scatter plot of
  CO₂ per capita vs renewable share + 5-year decarbonisation rate, all from OWID
- `.github/workflows/ci.yml`: GitHub Actions CI — runs syntax check and pyflakes lint
  on every push to main
- `CHANGELOG.md`: This file

---

## [v0.2.0] — 2026-06-11 — Open-source pivot

### Changed
- Removed all Bloomberg / proprietary data references throughout
- Project 2 reframed as a clearly hypothetical SLL framework (no real company data)
- Project 3 rewired to Our World in Data (CC BY) and Ember Climate (CC BY)

### Added
- `project1/scripts/process_data.py`: Python processing script for CBI data → Excel
- `project2-sll-structuring/README.md`: Full SLL structuring framework document
- `project3-climate-dashboard/`: Streamlit app scaffold
- `.gitignore`, root `requirements.txt`

---

## [v0.1.0] — 2026-03 — Initial commit

- Project 1: Green Bond Market Analysis (Excel model, README)
- Root README with portfolio overview
