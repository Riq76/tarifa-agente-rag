# Agente RAG — Voltia Energía (Challenge Alura)

> Voltia Energía SpA es una empresa **ficticia**, creada exclusivamente para este proyecto educativo. Cualquier parecido con datos reales de contacto, dirección o RUT es coincidencia; no representa a ninguna empresa existente.

Asistente virtual que responde preguntas de clientes sobre facturación eléctrica chilena
(tarifas BT/AT, consumo provisorio y Consumo No Registrado — CNR), usando como única
fuente de conocimiento un documento propio de la empresa (PDF + CSV) mediante la técnica
**RAG (Retrieval-Augmented Generation)**.

Proyecto desarrollado para el Challenge Alura "Agente Inteligente".

## 1. Descripción general

Voltia Energía SpA es una empresa chilena ficticia de asesoría en gestión energética. Sus clientes
preguntan con frecuencia por qué llegó un cargo de "consumo provisorio", si corresponde un
cobro retroactivo de energía (CNR) y por cuántos meses, o qué significa cada tarifa de su
boleta (BT1, BT3, AT3, etc.).

Este proyecto implementa un agente que:

1. Lee un documento fuente propio (`data/Base_Conocimiento_Voltia_Energia.pdf` y
   `data/FAQ_Voltia_Energia.csv`) con la política de facturación, la guía de tarifas y el
   marco normativo de la SEC sobre CNR.
2. Indexa ese contenido para poder recuperar los fragmentos más relevantes ante cada
   pregunta.
3. Usa la API de **Google Gemini** (tier gratuito) para redactar, en español, una
   respuesta basada únicamente en los fragmentos recuperados — citando la fuente usada.

## 2. Arquitectura de la solución

```
                 ┌─────────────────────────┐
                 │  data/                  │
                 │  - Base_Conocimiento.pdf│
                 │  - FAQ_Voltia.csv       │
                 └───────────┬─────────────┘
                             │ scripts/build_index.py
                             ▼
                 ┌─────────────────────────┐
        rag/loader.py   →  chunking (PDF por página, CSV por fila)
                 │
                 ▼
                 ┌─────────────────────────┐
        rag/retriever.py → índice TF-IDF (scikit-learn) + similitud coseno
                 │  se guarda en tfidf_index.pkl
                 ▼
   Pregunta del usuario ──► búsqueda de los k fragmentos más similares
                 │
                 ▼
        rag/generator.py → arma el prompt (contexto + pregunta) y llama
                            a la API de Google Gemini
                 │
                 ▼
        Respuesta en español + fuente citada
```

**Dos interfaces sobre el mismo núcleo (`rag/`):**

- `agent_cli.py` — uso por línea de comandos.
- `app.py` — aplicación web Flask (interfaz de chat + API `/ask`), la que se despliega en OCI.

### Por qué TF-IDF y no embeddings neuronales

Se eligió **TF-IDF + similitud coseno** (scikit-learn) para la recuperación en vez de
embeddings de un modelo neuronal. Es una decisión de diseño deliberada para este proyecto:
sin dependencias de modelos pesados (torch/GPU) ni de una segunda API key solo para
generar embeddings, lo que simplifica el despliegue en una instancia gratuita de OCI. Para
la base de conocimiento del challenge (decenas de fragmentos), TF-IDF recupera con buena
precisión los pasajes relevantes, como muestran las pruebas en `tests/test_retriever.py`.

## 3. Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Generación de respuestas | API de Google Gemini (`gemini-3.5-flash`, tier gratuito) |
| Recuperación (retrieval) | scikit-learn (TF-IDF + similitud coseno) |
| Lectura de PDF | pypdf |
| Servidor web | Flask + Gunicorn |
| Contenedor | Docker |
| Nube de despliegue | Oracle Cloud Infrastructure (OCI) — Compute Always Free / Container Instances |

## 4. Estructura del repositorio

```
voltia-agente-rag/
├── app.py                  # Aplicación web Flask (UI + endpoint /ask)
├── agent_cli.py             # Agente por línea de comandos
├── rag/
│   ├── loader.py            # Lectura y chunking del PDF/CSV
│   ├── retriever.py         # Índice TF-IDF y búsqueda por similitud
│   └── generator.py         # Prompt + llamada a la API de Gemini
├── scripts/build_index.py   # Construye tfidf_index.pkl desde data/
├── data/                    # Documento fuente (PDF y CSV)
├── templates/index.html     # Interfaz de chat
├── tests/test_retriever.py  # Pruebas de recuperación (no requieren API key)
├── deploy/OCI_DEPLOY.md      # Guía paso a paso de despliegue en OCI
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 5. Instrucciones para ejecutar el proyecto

### 5.1 Localmente

```bash
git clone https://github.com/<tu-usuario>/voltia-agente-rag.git
cd voltia-agente-rag
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edita .env y pega tu GEMINI_API_KEY (gratis en aistudio.google.com/apikey)

python scripts/build_index.py   # construye el índice de recuperación

# Opción A: agente por consola
python agent_cli.py "¿Por cuántos meses me pueden cobrar un CNR?"

# Opción B: aplicación web
python app.py
# abre http://localhost:8080
```

### 5.2 Con Docker

```bash
docker build -t voltia-agente-rag .
docker run -p 8080:8080 --env-file .env voltia-agente-rag
```

### 5.3 Pruebas

```bash
python tests/test_retriever.py
```

### 5.4 Despliegue en OCI

Ver guía completa en [`deploy/OCI_DEPLOY.md`](deploy/OCI_DEPLOY.md).

## 6. Ejemplos de preguntas que el agente puede responder

- ¿Por cuántos meses me pueden cobrar un Consumo No Registrado (CNR)?
- ¿Qué es el consumo provisorio y por qué me llegó ese cargo?
- ¿Cuál es la diferencia entre la tarifa BT1 y la BT3?
- ¿Cuánto tiene la distribuidora para responder un reclamo de facturación?
- ¿Cómo protege Voltia los datos de consumo de mis medidores?
- Recién me mudé y me llegó un cobro de CNR de meses anteriores, ¿corresponde?

## 7. Ejemplos de respuestas generadas por el agente

> Transcripciones reales de `agent_cli.py`, generadas con el modelo `gemini-3.5-flash`.

**Pregunta:** ¿Por cuántos meses me pueden cobrar un Consumo No Registrado (CNR)?

Fragmentos recuperados: `FAQ #6 (CNR)` (score=0.428), `PDF página 2` (score=0.253), `FAQ #8 (CNR)` (score=0.089)

Respuesta del agente:
> El plazo máximo por el cual le pueden cobrar un Consumo No Registrado (CNR) depende de la causa:
> * **No imputable al cliente** (por ejemplo, falla del medidor o error del concesionario): Se limita a un máximo de **3 meses**.
> * **Imputable al cliente** (por ejemplo, manipulación, conexión clandestina o negativa de acceso acreditada): Se puede cobrar hasta por **12 meses**.
> (Fuente: FAQ #6 (CNR) y PDF página 2)

**Pregunta:** ¿Cuál es la diferencia entre la tarifa BT1 y la BT3?

Fragmentos recuperados: `FAQ #11 (Tarifas)` (score=0.367), `PDF página 3` (score=0.230), `FAQ #13 (Tarifas)` (score=0.116)

Respuesta del agente:
> La diferencia principal radica en la medición y el cobro de la demanda (potencia):
> * **Tarifa BT1:** Es la más simple y no tiene medición de demanda de potencia. Solo incluye Cargo Fijo y Energía (Base y Adicional si corresponde), y nunca debe tener cargos de Demanda ni Potencia Contratada. Es usada por clientes residenciales y pequeños comerciales. (Fuente: FAQ #11 y PDF página 3)
> * **Tarifa BT3:** Sí registra la potencia máxima real mediante el medidor. Esta potencia, llamada "Demanda Facturada", se utiliza para calcular el cargo de Demanda en esta tarifa. (Fuente: FAQ #13 y PDF página 3)

**Pregunta:** ¿Qué es el consumo provisorio y por qué me llegó ese cargo?

Fragmentos recuperados: `FAQ #2 (Consumo provisorio)` (score=0.215), `PDF página 6` (score=0.196), `PDF página 2` (score=0.193)

Respuesta del agente:
> El consumo provisorio es una estimación de consumo que realiza la distribuidora cuando no pudo tomar la lectura real de su medidor (debido a un medidor inaccesible, falla de comunicación o atraso del lector).
> Le llegó este cargo como un mecanismo regulado para no dejar de facturar mientras se resuelve el problema de lectura. No representa un error, una irregularidad ni una sanción, y se calcula basándose en el consumo de referencia de sus meses anteriores.
> (Fuente: FAQ #2 (Consumo provisorio), PDF página 2 y PDF página 6)

## 8. Fuente de conocimiento del agente

- [`data/Base_Conocimiento_Voltia_Energia.pdf`](data/Base_Conocimiento_Voltia_Energia.pdf):
  guía de tarifas eléctricas chilenas, consumo provisorio, política de CNR (con cita de
  D.S. N°327/1997 y R.Ex. N°1.952/2009 y N°2.520/2009 de la SEC), privacidad de datos y
  procedimiento de reclamos.
- [`data/FAQ_Voltia_Energia.csv`](data/FAQ_Voltia_Energia.csv): 20 preguntas frecuentes en
  formato tabular (categoría, pregunta, respuesta).

## 9. Evidencia de despliegue en OCI

- **Enlace público:** http://148.116.109.139:8080
- **Instancia:** `voltia-agent-rag` — Compute Always Free (Ampere `VM.Standard.A1.Flex`, Ubuntu 20.04), región `sa-valparaiso-1`.
- **Despliegue:** contenedor Docker construido desde este mismo repo (ver `deploy/OCI_DEPLOY.md`), corriendo con `gunicorn` en el puerto 8080.
- **Captura de pantalla:** `deploy/evidencia-oci.png` (conversación real con el agente desplegado, incluyendo pregunta sobre CNR y datos de contacto, con fuentes citadas).
