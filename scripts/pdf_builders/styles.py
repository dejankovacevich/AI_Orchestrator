"""Shared ParagraphStyle definitions used by every PDF.

To tweak typography globally, edit here once. New styles should be added in
this single file rather than created inline inside section builders.
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


def make_styles() -> dict[str, ParagraphStyle]:
    """Return the project-wide style sheet keyed by name.

    Available keys:
      TitleBig, SubtitleBig, CoverMeta,
      H1, H2, H3, Body, Bullet,
      Code, Caption, Warn, Hint,
      TocItem, RecipeTitle
    """
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["TitleBig"] = ParagraphStyle(
        "TitleBig",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=38,
        textColor=colors.HexColor("#111111"),
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    styles["SubtitleBig"] = ParagraphStyle(
        "SubtitleBig",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["H1"] = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0a3d62"),
        spaceBefore=18,
        spaceAfter=10,
    )
    styles["H2"] = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0a3d62"),
        spaceBefore=12,
        spaceAfter=6,
    )
    styles["H3"] = ParagraphStyle(
        "H3",
        parent=base["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["Body"] = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=8,
        alignment=TA_LEFT,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet",
        parent=styles["Body"],
        leftIndent=14,
        bulletIndent=2,
        spaceAfter=3,
    )
    styles["Code"] = ParagraphStyle(
        "Code",
        parent=base["Code"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1a1a1a"),
        backColor=colors.HexColor("#f4f4f4"),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=4,
        spaceAfter=8,
        borderColor=colors.HexColor("#dddddd"),
        borderWidth=0.5,
        borderPadding=6,
    )
    styles["Caption"] = ParagraphStyle(
        "Caption",
        parent=styles["Body"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#666666"),
        spaceAfter=10,
    )
    styles["Warn"] = ParagraphStyle(
        "Warn",
        parent=styles["Body"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#7c1a1a"),
        backColor=colors.HexColor("#fdecea"),
        borderColor=colors.HexColor("#f5b7b1"),
        borderWidth=0.5,
        borderPadding=8,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=10,
    )
    styles["Hint"] = ParagraphStyle(
        "Hint",
        parent=styles["Body"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1d4f72"),
        backColor=colors.HexColor("#eaf4fb"),
        borderColor=colors.HexColor("#aed6f1"),
        borderWidth=0.5,
        borderPadding=8,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=10,
    )
    styles["TocItem"] = ParagraphStyle(
        "TocItem",
        parent=styles["Body"],
        fontSize=10.5,
        leading=16,
        spaceAfter=2,
    )
    styles["RecipeTitle"] = ParagraphStyle(
        "RecipeTitle",
        parent=styles["H2"],
        fontSize=15,
        textColor=colors.HexColor("#7c2d12"),
        spaceBefore=14,
        spaceAfter=6,
    )
    return styles


__all__ = ["make_styles"]
