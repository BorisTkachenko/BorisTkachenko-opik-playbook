"""A tiny on-disk vector index with cosine search."""

import json
import pathlib

import numpy as np


def cosine_top_k(query: list[float], matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    """Indices and cosine scores of the k rows of `matrix` closest to `query`."""
    q = np.asarray(query, dtype=float)
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
    scores = matrix @ q / np.where(norms == 0, 1, norms)
    top = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top]


class Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.matrix = np.array([c["vector"] for c in chunks], dtype=float)

    @classmethod
    def load(cls, path: pathlib.Path) -> "Index":
        if not path.is_file():
            raise SystemExit(f"No index at {path}. Run `uv run homebrew-rag ingest` first.")
        return cls(json.loads(path.read_text())["chunks"])

    def top_k(self, query_vector: list[float], k: int) -> list[dict]:
        return [
            {"source": self.chunks[i]["source"], "heading": self.chunks[i]["heading"],
             "text": self.chunks[i]["text"], "score": round(score, 4)}
            for i, score in cosine_top_k(query_vector, self.matrix, k)
        ]
