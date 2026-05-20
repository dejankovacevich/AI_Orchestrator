"""Document scaffolding: build a single PDF from a Platypus story.

This is the only place that knows about page margins, footer text, and
page numbering. Each PDF passes its own ``footer_text``.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate


def _on_page(footer_text: str):
    """Return a Platypus onPage handler that draws the footer + page number."""

    def _handler(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#888888"))
        canvas_obj.drawString(0.75 * inch, 0.45 * inch, footer_text)
        canvas_obj.drawRightString(
            LETTER[0] - 0.75 * inch,
            0.45 * inch,
            f"Page {doc.page}",
        )
        canvas_obj.restoreState()

    return _handler


def build_document(out_path: Path, story: list, footer_text: str) -> None:
    """Render ``story`` to ``out_path`` with LETTER pages and the standard footer."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=footer_text,
        author="Local AI Orchestrator",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    template = PageTemplate(id="default", frames=[frame], onPage=_on_page(footer_text))
    doc.addPageTemplates([template])
    doc.build(story)


__all__ = ["build_document"]
