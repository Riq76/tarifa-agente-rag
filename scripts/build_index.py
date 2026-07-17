# -*- coding: utf-8 -*-
"""Construye el índice TF-IDF a partir de los documentos en data/ y lo guarda
en tfidf_index.pkl en la raíz del proyecto. Ejecutar una vez antes de usar
agent_cli.py o app.py (y automáticamente durante el build de Docker)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from rag.loader import load_all_chunks  # noqa: E402
from rag.retriever import Retriever  # noqa: E402

DATA_DIR = ROOT / "data"
INDEX_PATH = ROOT / "tfidf_index.pkl"


def main():
    chunks = load_all_chunks(DATA_DIR)
    print(f"Fragmentos indexados: {len(chunks)}")
    retriever = Retriever.build(chunks)
    retriever.save(INDEX_PATH)
    print(f"Índice guardado en: {INDEX_PATH}")


if __name__ == "__main__":
    main()
