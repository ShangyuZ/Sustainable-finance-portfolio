"""
Fetch German green "twin" Bund data from the Deutsche Finanzagentur
==================================================================
Builds the two inputs ``greenium.py`` needs, entirely from the issuer's own
published pages:

  data/green_twin_pairs.csv   green ISIN <-> conventional twin, with coupon and maturity
  data/bund_yields.csv        tidy daily yields: date, isin, yield_pct

Usage:
    python scripts/fetch_bund_yields.py
    python scripts/greenium.py --pairs data/green_twin_pairs.csv \
                               --yields data/bund_yields.csv --strict

How the twin is identified
--------------------------
Germany issues each green Federal security alongside a conventional one with the
**same coupon and the same maturity date**. The pairing is therefore *derived*,
not asserted: for each green security this script collects the conventional ISINs
the issuer's own factsheet links to, fetches each, and keeps the one whose coupon
and maturity match exactly. A green bond with no exact match is reported and
skipped rather than paired approximately — an approximate pair would reintroduce
precisely the matching error the twin structure exists to remove.

Where the yields come from
--------------------------
Each factsheet renders a price and yield chart whose full daily series is
embedded in the page as Highcharts JSON. That series is the data source: daily,
per-ISIN, back to issuance, published by the issuer, free. No terminal
subscription is involved at any point.

The fetched HTML is cached on disk, so re-runs cost nothing and the script is
polite to the publisher.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_mod
import json
import os
import re
import time
import urllib.request

import pandas as pd

BASE = "https://www.deutsche-finanzagentur.de"
GREEN_PAGE = f"{BASE}/en/federal-securities/types-of-federal-securities/green-federal-securities"
FACTSHEET = f"{BASE}/en/federal-securities/factsheet/isin/{{isin}}"

ISIN_RE = re.compile(r"DE[0-9A-Z]{10}")
COUPON_RE = re.compile(r"([0-9]+[.,][0-9]+)\s*%")
USER_AGENT = ("Mozilla/5.0 (compatible; sustainable-finance-portfolio/1.0; "
              "+https://github.com/ShangyuZ/Sustainable-finance-portfolio)")

# Be polite between uncached requests.
DELAY_SECONDS = 0.6


# ── fetching ─────────────────────────────────────────────────────────────────

def fetch(url: str, cache_dir: str, force: bool = False) -> str:
    """Fetch ``url``, caching the body on disk so re-runs make no requests."""
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    path = os.path.join(cache_dir, f"{key}.html")
    if os.path.exists(path) and not force:
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8", errors="replace")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    time.sleep(DELAY_SECONDS)
    return body


# ── parsing ──────────────────────────────────────────────────────────────────

def text_of(fragment: str) -> str:
    """Strip tags and collapse whitespace."""
    return re.sub(r"\s+", " ", html_mod.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def tables(page: str) -> list[list[list[str]]]:
    """Every HTML table on the page, as rows of cell text."""
    out = []
    for table in re.findall(r"<table.*?</table>", page, re.S):
        rows = []
        for row in re.findall(r"<tr.*?</tr>", table, re.S):
            cells = [text_of(c) for c in re.findall(r"<t[hd].*?</t[hd]>", row, re.S)]
            if any(cells):
                rows.append(cells)
        if rows:
            out.append(rows)
    return out


def parse_date(value: str) -> pd.Timestamp | None:
    """Parse the issuer's DD.MM.YYYY format."""
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", value or "")
    if not match:
        return None
    day, month, year = match.groups()
    return pd.Timestamp(int(year), int(month), int(day))


def parse_coupon(value: str) -> float | None:
    """Parse a coupon like ``2.60 %`` or ``0,00 %``."""
    match = COUPON_RE.search(value or "")
    return float(match.group(1).replace(",", ".")) if match else None


def parse_green_list(page: str) -> pd.DataFrame:
    """
    Parse the green Federal securities table.

    Expects columns Bond | Maturity | Coupon | Outstanding | Last Issuance | ISIN.
    Total-volume rows and anything without an ISIN are dropped.
    """
    rows = []
    for table in tables(page):
        header = [c.lower() for c in table[0]]
        if not ("isin" in header and "maturity" in header):
            continue
        idx = {name: header.index(name) for name in ("bond", "maturity", "coupon", "isin")
               if name in header}
        if "isin" not in idx:
            continue
        for cells in table[1:]:
            if len(cells) <= idx["isin"]:
                continue
            isin_match = ISIN_RE.search(cells[idx["isin"]])
            if not isin_match:
                continue
            rows.append({
                "name": cells[idx["bond"]] if "bond" in idx else "",
                "green_isin": isin_match.group(0),
                "green_coupon_pct": parse_coupon(cells[idx["coupon"]]) if "coupon" in idx else None,
                "green_maturity": parse_date(cells[idx["maturity"]]),
            })
    df = pd.DataFrame(rows).drop_duplicates(subset="green_isin")
    return df.dropna(subset=["green_coupon_pct", "green_maturity"]).reset_index(drop=True)


def parse_factsheet(page: str) -> dict:
    """
    Pull terms and the daily yield series out of one security's factsheet.

    The coupon comes from the page heading ("0.00% Federal bond 2020 (2030)"),
    because the terms table renders a zero coupon as "-".
    """
    heading_match = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    heading = text_of(heading_match.group(1)) if heading_match else ""

    maturity = None
    for table in tables(page):
        for cells in table:
            if len(cells) >= 2 and cells[0].strip().lower() == "maturity":
                maturity = parse_date(cells[1])
                break
        if maturity is not None:
            break

    return {
        "heading": heading,
        "coupon_pct": parse_coupon(heading),
        "maturity": maturity,
        "isin_refs": sorted(set(ISIN_RE.findall(page))),
        "yields": parse_series(page, "Yield"),
    }


def parse_series(page: str, name: str) -> pd.DataFrame:
    """
    Extract a Highcharts series embedded in the page.

    Returns columns ``date`` and ``value``; empty if the series is absent.
    """
    match = re.search(r'"name":"%s","data":(\[.*?\])\}' % re.escape(name), page, re.S)
    if not match:
        return pd.DataFrame(columns=["date", "value"])
    points = json.loads(match.group(1))
    df = pd.DataFrame(points)
    if df.empty or "x" not in df or "y" not in df:
        return pd.DataFrame(columns=["date", "value"])
    df["date"] = pd.to_datetime(df["x"], unit="ms")
    return (df[["date", "y"]].rename(columns={"y": "value"})
            .dropna().sort_values("date").reset_index(drop=True))


# ── twin matching ────────────────────────────────────────────────────────────

def find_twin(green: pd.Series, cache_dir: str, force: bool = False) -> dict | None:
    """
    Find the conventional twin of one green security.

    Considers the conventional ISINs the green factsheet links to and returns the
    one whose coupon and maturity both match exactly. Returns ``None`` when no
    candidate matches, so the caller can skip rather than pair approximately.
    """
    green_page = fetch(FACTSHEET.format(isin=green["green_isin"]), cache_dir, force)
    green_sheet = parse_factsheet(green_page)

    candidates = [i for i in green_sheet["isin_refs"] if i != green["green_isin"]]
    for isin in candidates:
        sheet = parse_factsheet(fetch(FACTSHEET.format(isin=isin), cache_dir, force))
        if sheet["maturity"] is None or sheet["coupon_pct"] is None:
            continue
        same_coupon = abs(sheet["coupon_pct"] - float(green["green_coupon_pct"])) < 1e-9
        same_maturity = sheet["maturity"] == green["green_maturity"]
        if same_coupon and same_maturity:
            return {
                "conventional_isin": isin,
                "conventional_coupon_pct": sheet["coupon_pct"],
                "conventional_maturity": sheet["maturity"],
                "conventional_heading": sheet["heading"],
                "green_yields": green_sheet["yields"],
                "conventional_yields": sheet["yields"],
            }
    return None


# ── main ─────────────────────────────────────────────────────────────────────

def build(out_dir: str, cache_dir: str, force: bool = False) -> tuple[str, str]:
    """Fetch everything and write the pair registry and the yield file."""
    print("Fetching the green Federal securities list …")
    green = parse_green_list(fetch(GREEN_PAGE, cache_dir, force))
    print(f"  {len(green)} green securities listed")
    if green.empty:
        raise SystemExit("Could not parse the green securities table — the page layout "
                         "may have changed.")

    pairs, yield_frames, skipped = [], [], []
    for _, row in green.iterrows():
        twin = find_twin(row, cache_dir, force)
        if twin is None:
            skipped.append((row["green_isin"], row["name"]))
            print(f"  {row['green_isin']}  {row['name'][:28]:28s} -> no exact twin found, skipped")
            continue

        pair_id = f"{row['green_maturity']:%Y-%m}_{row['green_coupon_pct']:.2f}pct"
        pairs.append({
            "pair_id": pair_id,
            "green_isin": row["green_isin"],
            "conventional_isin": twin["conventional_isin"],
            "green_coupon_pct": row["green_coupon_pct"],
            "green_maturity": row["green_maturity"].date().isoformat(),
            "conventional_coupon_pct": twin["conventional_coupon_pct"],
            "conventional_maturity": twin["conventional_maturity"].date().isoformat(),
            "issuer": "Federal Republic of Germany",
        })
        for isin, frame in ((row["green_isin"], twin["green_yields"]),
                            (twin["conventional_isin"], twin["conventional_yields"])):
            if not frame.empty:
                yield_frames.append(frame.assign(isin=isin))
        print(f"  {row['green_isin']}  {row['name'][:28]:28s} -> twin {twin['conventional_isin']} "
              f"({len(twin['green_yields'])} / {len(twin['conventional_yields'])} obs)")

    if not pairs:
        raise SystemExit("No exact twins identified; nothing to write.")

    os.makedirs(out_dir, exist_ok=True)
    pairs_path = os.path.join(out_dir, "green_twin_pairs.csv")
    yields_path = os.path.join(out_dir, "bund_yields.csv")

    pd.DataFrame(pairs).to_csv(pairs_path, index=False)

    tidy = (pd.concat(yield_frames, ignore_index=True)
            .rename(columns={"value": "yield_pct"})
            .drop_duplicates(subset=["date", "isin"]))
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.strftime("%Y-%m-%d")
    tidy = tidy[["date", "isin", "yield_pct"]].sort_values(["isin", "date"])
    tidy.to_csv(yields_path, index=False)

    print(f"\n{len(pairs)} twin pairs -> {pairs_path}")
    print(f"{len(tidy):,} daily observations across {tidy['isin'].nunique()} securities "
          f"-> {yields_path}")
    if skipped:
        print(f"\nSkipped {len(skipped)} green securities with no exact twin on their "
              f"factsheet: {', '.join(i for i, _ in skipped)}")
        print("  (a non-exact pair would reintroduce the matching error the twin "
              "structure exists to remove)")
    return pairs_path, yields_path


def main() -> None:
    """Parse arguments and fetch."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description="Fetch German green twin Bund pairs and daily yields "
                    "from the Deutsche Finanzagentur")
    parser.add_argument("--out-dir", default=os.path.join(here, "data"))
    parser.add_argument("--cache-dir", default=os.path.join(here, "data", ".fetch_cache"),
                        help="Where fetched HTML is cached (re-runs make no requests)")
    parser.add_argument("--force", action="store_true", help="Ignore the cache and refetch")
    args = parser.parse_args()
    build(args.out_dir, args.cache_dir, args.force)


if __name__ == "__main__":
    main()
