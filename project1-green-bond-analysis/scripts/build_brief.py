"""
Markdown to PDF renderer
========================
Renders a Markdown document to PDF — the investment brief by default, and the
SLL structuring memo via ``--input``/``--output``.

The Markdown file is the single source of truth; the PDF is generated, so the
brief cannot drift from the figures the way a hand-maintained document would.

Usage:
    python scripts/build_brief.py

Requires ``reportlab`` (in requirements-dev.txt). Supports the Markdown subset
the brief actually uses: ATX headings, paragraphs, ``-`` bullets, ``1.``
numbered lists, pipe tables, ``---`` rules, inline ``**bold**`` / ``*italic*`` /
``` `code` ```, and backslash escapes such as ``\\*``.
"""

from __future__ import annotations

import argparse
import html
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

GREEN = colors.HexColor("#1A7A4A")
HEADER_BG = colors.HexColor("#2E7D32")
LIGHT = colors.HexColor("#E8F5E9")
GREY = colors.HexColor("#595959")


def styles() -> dict[str, ParagraphStyle]:
    """Paragraph styles for the brief."""
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=19, leading=23,
                             textColor=GREEN, spaceAfter=2, spaceBefore=0),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5, leading=15,
                             textColor=HEADER_BG, spaceBefore=11, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=10.5, leading=13,
                             textColor=HEADER_BG, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=8.9,
                               leading=12.2, alignment=TA_JUSTIFY, spaceAfter=5),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontSize=8.9,
                                 leading=12.0, spaceAfter=2.5),
        "cell": ParagraphStyle("cell", parent=base["BodyText"], fontSize=7.9,
                               leading=9.8, spaceAfter=0),
        "cellhead": ParagraphStyle("cellhead", parent=base["BodyText"], fontSize=7.9,
                                   leading=9.8, spaceAfter=0, textColor=colors.white),
        "note": ParagraphStyle("note", parent=base["BodyText"], fontSize=7.9,
                               leading=10.5, textColor=GREY, spaceAfter=6),
    }


def inline(text: str) -> str:
    """Convert inline Markdown to reportlab markup, escaping everything else."""
    # Backslash escapes (``\*``) are literal characters, not emphasis markers.
    # Park them in private-use code points so the emphasis rules cannot see them.
    escaped = {"*": "\ue000", "_": "\ue001", "`": "\ue002", "\\": "\ue003"}
    text = re.sub(r"\\([*_`\\])", lambda m: escaped[m.group(1)], text)
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", out)
    out = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', out)
    out = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", out)       # links: keep the label
    for char, mark in escaped.items():
        out = out.replace(mark, char)
    return out


def is_separator(cells: list[str]) -> bool:
    """True for a Markdown table's ``|---|---|`` separator row."""
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells)


def split_row(line: str) -> list[str]:
    """Split a pipe-table row into trimmed cells."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def make_table(rows: list[list[str]], st: dict) -> Table:
    """Build a styled table; the first row is treated as the header."""
    head, body = rows[0], rows[1:]
    data = [[Paragraph(f"<b>{inline(c)}</b>", st["cellhead"]) for c in head]]
    data += [[Paragraph(inline(c), st["cell"]) for c in r] for r in body]

    n_cols = len(head)
    avail = A4[0] - 32 * mm
    # First column carries the labels, so give it more room.
    first = avail * (0.30 if n_cols > 2 else 0.5)
    rest = (avail - first) / max(n_cols - 1, 1)
    widths = [first] + [rest] * (n_cols - 1)

    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    table.setStyle(TableStyle(style))
    return table


LIST_MARKERS = {"bullet": r"^[-*] ", "numbered": r"^\d+\. "}


def list_marker(line: str) -> str | None:
    """``"bullet"`` or ``"numbered"`` if ``line`` opens a list item, else None."""
    for kind, pattern in LIST_MARKERS.items():
        if re.match(pattern, line.strip()):
            return kind
    return None


def parse(md: str, st: dict) -> list:
    """Convert the Markdown subset used by the brief into reportlab flowables."""
    flow: list = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        if line.startswith("<!--"):                      # control comments
            if "PAGEBREAK" in line:
                flow.append(PageBreak())
            i += 1
            continue

        if re.fullmatch(r"-{3,}", line.strip()):
            flow.append(Spacer(1, 3))
            flow.append(HRFlowable(width="100%", thickness=0.6,
                                   color=colors.HexColor("#BFBFBF")))
            flow.append(Spacer(1, 4))
            i += 1
            continue

        if line.startswith("### "):
            flow.append(Paragraph(inline(line[4:]), st["h3"]))
            i += 1
            continue
        if line.startswith("## "):
            flow.append(Paragraph(inline(line[3:]), st["h2"]))
            i += 1
            continue
        if line.startswith("# "):
            flow.append(Paragraph(inline(line[2:]), st["h1"]))
            i += 1
            continue

        if line.lstrip().startswith("|"):                 # table
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = split_row(lines[i])
                if not is_separator(cells):
                    rows.append(cells)
                i += 1
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                flow.append(Spacer(1, 2))
                flow.append(make_table(rows, st))
                flow.append(Spacer(1, 6))
            continue

        list_kind = list_marker(line)
        if list_kind:                                     # bullet or numbered list
            items = []
            while i < len(lines) and list_marker(lines[i]) == list_kind:
                text = re.sub(LIST_MARKERS[list_kind], "", lines[i].strip())
                i += 1
                # fold continuation lines into the same item
                while (i < len(lines) and lines[i].strip()
                       and not list_marker(lines[i])
                       and not lines[i].lstrip().startswith(("|", "#"))
                       and lines[i].startswith(("  ", "\t"))):
                    text += " " + lines[i].strip()
                    i += 1
                items.append(ListItem(Paragraph(inline(text), st["bullet"]),
                                      leftIndent=12))
            if list_kind == "bullet":
                flow.append(ListFlowable(items, bulletType="bullet", start="•",
                                         leftIndent=12, bulletFontSize=7))
            else:
                flow.append(ListFlowable(items, bulletType="1", leftIndent=14,
                                         bulletFontSize=8.9, bulletFormat="%s."))
            flow.append(Spacer(1, 5))
            continue

        # paragraph: gather until a blank line or a block element
        para = [line]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not lines[i].lstrip().startswith(("|", "#"))
               and not list_marker(lines[i])
               and not re.fullmatch(r"-{3,}", lines[i].strip())):
            para.append(lines[i].rstrip())
            i += 1
        text = " ".join(para)
        style = st["note"] if text.startswith("*") and text.endswith("*") else st["body"]
        flow.append(Paragraph(inline(text), style))

    return flow


def make_footer(label: str):
    """Build a page-footer callback carrying ``label``."""
    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(16 * mm, 10 * mm, label)
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return footer


def document_title(md: str) -> str:
    """The document's H1, used for the PDF title and footer."""
    for line in md.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "Document"


def build(md_path: str, pdf_path: str) -> str:
    """
    Render a Markdown document to ``pdf_path``. Returns the output path.

    Document-agnostic: the title and footer come from the file's own H1, so the
    same renderer serves the investment brief and the SLL structuring memo.
    """
    with open(md_path, encoding="utf-8") as fh:
        md = fh.read()

    title = document_title(md)
    st = styles()
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm,
        title=title,
        author="ShangyuZ",
    )
    page_footer = make_footer(f"{title} · ShangyuZ · UCL")
    doc.build(parse(md, st), onFirstPage=page_footer, onLaterPages=page_footer)
    return pdf_path


def main() -> None:
    """Parse arguments and render the brief."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description="Render a Markdown document (brief, memo) to PDF")
    parser.add_argument("--input",
                        default=os.path.join(here, "brief", "Green_Bond_Market_Brief.md"))
    parser.add_argument("--output",
                        default=os.path.join(here, "brief", "Green_Bond_Market_Brief.pdf"))
    args = parser.parse_args()
    out = build(args.input, args.output)
    size = os.path.getsize(out)
    print(f"Brief written → {out} ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
