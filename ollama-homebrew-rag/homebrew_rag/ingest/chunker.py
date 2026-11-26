"""Split the guide into one chunk per '##' section."""

import pathlib


def chunk_markdown(path: pathlib.Path) -> list[dict]:
    """Return [{'source', 'heading', 'text'}], the title prepended to each section."""
    title, *sections = path.read_text().split("\n## ")
    title = title.removeprefix("# ").strip()
    chunks = []
    for section in sections:
        heading, _, body = section.partition("\n")
        chunks.append({
            "source": path.name,
            "heading": heading.strip(),
            "text": f"{title} / {heading.strip()}\n{body.strip()}",
        })
    return chunks
