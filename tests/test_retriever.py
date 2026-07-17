# -*- coding: utf-8 -*-
"""Pruebas de humo del paso de recuperación (no requieren API key)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from rag.loader import load_all_chunks  # noqa: E402
from rag.retriever import Retriever  # noqa: E402

DATA_DIR = ROOT / "data"


def _build_retriever():
    chunks = load_all_chunks(DATA_DIR)
    assert len(chunks) > 10, "Se esperaban múltiples fragmentos del PDF y el CSV"
    return Retriever.build(chunks)


def test_retrieval_cnr():
    retriever = _build_retriever()
    results = retriever.search("¿Por cuántos meses me pueden cobrar un CNR?", top_k=3)
    assert results[0]["score"] > 0
    joined = " ".join(r["text"] for r in results).lower()
    assert "cnr" in joined or "consumo no registrado" in joined


def test_retrieval_cargo_fijo():
    retriever = _build_retriever()
    results = retriever.search("¿Qué es el cargo fijo de mi boleta?", top_k=3)
    assert results[0]["score"] > 0
    joined = " ".join(r["text"] for r in results).lower()
    assert "cargo fijo" in joined


if __name__ == "__main__":
    test_retrieval_cnr()
    test_retrieval_cargo_fijo()
    print("OK: pruebas de recuperación pasaron correctamente")
