"""Tiny helpers used by every PDF section builder.

Kept stateless and free of formatting opinions beyond what the project
style sheet already encodes. Avoid expanding this module — if a helper
grows beyond ~15 lines or owns its own concept (e.g. tables of contents),
give it a dedicated file.
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle


def p(styles, name, text):
    """Shorthand: build a ``Paragraph`` using a named style."""
    return Paragraph(text, styles[name])


def bullets(styles, items):
    """Return a list of bullet Paragraphs from a list of HTML-safe strings."""
    return [Paragraph(f"&bull;&nbsp;&nbsp;{item}", styles["Bullet"]) for item in items]


def code_block(styles, text):
    """Return a Paragraph rendered with the Code style.

    Escapes HTML special chars and converts newlines to ``<br/>`` so
    Platypus respects the formatting.
    """
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(" ", "&nbsp;")
    )
    lines = escaped.split("\n")
    return Paragraph("<br/>".join(lines), styles["Code"])


def section_table(rows, col_widths=None, header=True):
    """Return a styled Table with optional bold header row + striped body."""
    style_commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        (
            "ROWBACKGROUNDS",
            (0, 1 if header else 0),
            (-1, -1),
            [colors.white, colors.HexColor("#f7f7f7")],
        ),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style_commands.append(
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3d62"))
        )
        style_commands.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.white))
        style_commands.append(("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"))
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    table.setStyle(TableStyle(style_commands))
    return table


def toc_entry(styles, num, title):
    """One row in a manual table-of-contents page."""
    return Paragraph(
        f'<font face="Helvetica-Bold">{num}.</font>&nbsp;&nbsp;{title}',
        styles["TocItem"],
    )


__all__ = ["p", "bullets", "code_block", "section_table", "toc_entry"]
