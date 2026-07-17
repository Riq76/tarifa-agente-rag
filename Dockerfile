FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Construye el índice TF-IDF a partir de data/ durante el build de la imagen
RUN python scripts/build_index.py

EXPOSE 8080
ENV PORT=8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
