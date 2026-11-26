"""Render the rulebooks to real PDFs with reportlab (small, deterministic, committed)."""

import pathlib

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from rulebook.config import PDF_DIR
from rulebook.corpus.games import RULEBOOKS, Rulebook


def render(book: Rulebook, out_dir: pathlib.Path) -> pathlib.Path:
    styles = getSampleStyleSheet()
    path = out_dir / f"{book.slug}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=book.title, author="Rulebook Press")
    story = [Paragraph(f"{book.title} Rulebook", styles["Title"]),
             Paragraph(book.tagline, styles["Italic"]), Spacer(1, 18)]
    for section in book.sections:
        story.append(Paragraph(f"Section {section.number}: {section.title}", styles["Heading2"]))
        story.append(Paragraph(section.text, styles["BodyText"]))
        story.append(Spacer(1, 10))
    doc.build(story)
    return path


def generate_all(out_dir: pathlib.Path = PDF_DIR) -> list[pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    return [render(book, out_dir) for book in RULEBOOKS]


def ensure_pdfs(out_dir: pathlib.Path = PDF_DIR) -> None:
    """Regenerate any missing rulebook so a clean clone always has its input."""
    if not all((out_dir / f"{b.slug}.pdf").exists() for b in RULEBOOKS):
        generate_all(out_dir)
