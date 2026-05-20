"""Entry point: regenerate every PDF in ``docs/`` from the pdf_builders package.

Usage:
    .venv/bin/python scripts/build_pdfs.py

This script is intentionally thin. All content and styling lives in
``scripts/pdf_builders/``:

  - styles.py                  — shared paragraph styles
  - helpers.py                 — p, bullets, code_block, section_table, toc_entry
  - document.py                — render a Platypus story to a PDF
  - system_guide.py            — System Guide content
  - onboarding.py              — Onboarding content
  - technical_reference.py     — Technical Reference content

Add a new PDF by writing a new builder module and registering it below.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"

# Make ``scripts`` importable so ``from scripts.pdf_builders import ...``
# works whether this file is run directly or via ``python -m``.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from scripts.pdf_builders import (  # noqa: E402  (sys.path tweak above)
    build_document,
    build_onboarding,
    build_system_guide,
    build_technical_reference,
    make_styles,
)


# Registry of PDFs to produce. To add another document:
#   1. Write a builder module in scripts/pdf_builders/.
#   2. Export build_<name>(styles) -> list (a Platypus story).
#   3. Add an entry below: (output filename, builder, footer text).
PDFS_TO_BUILD = [
    (
        "Local_AI_Orchestrator_System_Guide.pdf",
        build_system_guide,
        "Local AI Orchestrator — System Guide",
    ),
    (
        "Local_AI_Orchestrator_Onboarding.pdf",
        build_onboarding,
        "Local AI Orchestrator — Onboarding",
    ),
    (
        "Local_AI_Orchestrator_Technical_Reference.pdf",
        build_technical_reference,
        "Local AI Orchestrator — Technical Reference",
    ),
]


def main() -> None:
    styles = make_styles()
    for filename, builder, footer_text in PDFS_TO_BUILD:
        out_path = DOCS_DIR / filename
        build_document(out_path, builder(styles), footer_text)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
