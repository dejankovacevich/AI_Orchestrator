"""PDF builder package. One module per document.

Public API:
  - ``make_styles()``           — shared paragraph/table styles
  - ``build_document(...)``     — render one PDF from a Platypus story
  - ``build_system_guide(styles)``        — System Guide PDF story
  - ``build_onboarding(styles)``          — Onboarding PDF story
  - ``build_technical_reference(styles)`` — Technical Reference PDF story

Use ``scripts/build_pdfs.py`` as the entry point; it wires these together.
"""

from __future__ import annotations

from scripts.pdf_builders.document import build_document
from scripts.pdf_builders.onboarding import build_onboarding
from scripts.pdf_builders.styles import make_styles
from scripts.pdf_builders.system_guide import build_system_guide
from scripts.pdf_builders.technical_reference import build_technical_reference


__all__ = [
    "make_styles",
    "build_document",
    "build_system_guide",
    "build_onboarding",
    "build_technical_reference",
]
