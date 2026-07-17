#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agente conversacional por línea de comandos.

Uso:
    python agent_cli.py "¿Por cuántos meses me pueden cobrar un CNR?"
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from rag.retriever import Retriever  # noqa: E402
from rag.generator import answer  # noqa: E402

INDEX_PATH = ROOT / "tfidf_index.pkl"


def main():
    if len(sys.argv) < 2:
        print('Uso: python agent_cli.py "tu pregunta"')
        sys.exit(1)

    if not INDEX_PATH.exists():
        print("No existe el índice. Ejecuta primero: python scripts/build_index.py")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    retriever = Retriever.load(INDEX_PATH)
    chunks = retriever.search(question, top_k=4)

    print(f"\n> Pregunta: {question}")
    print("\n[Fragmentos recuperados]")
    for c in chunks:
        print(f"  - {c['source']} (score={c['score']:.3f})")

    resp = answer(question, chunks)
    print("\n[Respuesta del agente]")
    print(resp)


if __name__ == "__main__":
    main()
