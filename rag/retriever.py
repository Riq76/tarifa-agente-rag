# -*- coding: utf-8 -*-
"""Índice de recuperación (retrieval) basado en TF-IDF + similitud coseno.

Se eligió TF-IDF (scikit-learn) en vez de embeddings neuronales para mantener
el despliegue liviano en la capa gratuita de OCI (sin GPU, sin descargar
modelos de cientos de MB) y sin dependencias adicionales de API keys solo
para el paso de recuperación."""

import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    def __init__(self, chunks, vectorizer, matrix):
        self.chunks = chunks
        self.vectorizer = vectorizer
        self.matrix = matrix

    @classmethod
    def build(cls, chunks):
        texts = [c["text"] for c in chunks]
        vectorizer = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        return cls(chunks, vectorizer, matrix)

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump({"chunks": self.chunks, "vectorizer": self.vectorizer, "matrix": self.matrix}, f)

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(data["chunks"], data["vectorizer"], data["matrix"])

    def search(self, query, top_k=4):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        top_idx = sims.argsort()[::-1][:top_k]
        return [{"score": float(sims[i]), **self.chunks[i]} for i in top_idx]
