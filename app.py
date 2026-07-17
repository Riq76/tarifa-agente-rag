#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplicación web (Flask) que expone el agente RAG de Voltia Energía.

Endpoints:
    GET  /        Interfaz de chat simple (HTML)
    POST /ask     {"question": "..."} -> {"answer": "...", "sources": [...]}
    GET  /health  Chequeo de salud para el balanceador/monitor de OCI
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from rag.retriever import Retriever  # noqa: E402
from rag.generator import answer  # noqa: E402

INDEX_PATH = ROOT / "tfidf_index.pkl"

app = Flask(__name__)

_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        if not INDEX_PATH.exists():
            raise RuntimeError(
                "Falta tfidf_index.pkl. Ejecuta: python scripts/build_index.py"
            )
        _retriever = Retriever.load(INDEX_PATH)
    return _retriever


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Falta el campo 'question'"}), 400

    try:
        retriever = get_retriever()
        chunks = retriever.search(question, top_k=4)
        resp = answer(question, chunks)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500

    return jsonify({
        "answer": resp,
        "sources": [c["source"] for c in chunks],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
