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
| Generación de respuestas | API de Google Gemini (`gemini-2.5-flash`, tier gratuito) |
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

> Estos son ejemplos reales del paso de **recuperación** (los fragmentos que el agente
> encuentra en `data/` antes de redactar la respuesta), verificados con
> `tests/test_retriever.py`. La redacción final la hace el modelo Gemini a partir de ese
> contexto; al ejecutar el proyecto con tu propia `GEMINI_API_KEY` obtendrás la
> respuesta completa generada, con este mismo formato.

**Pregunta:** ¿Por cuántos meses me pueden cobrar un Consumo No Registrado (CNR)?

Fragmentos recuperados: `FAQ #6 (CNR)`, `PDF página 2`, `FAQ #5 (CNR)`

Respuesta del agente:
> Depende de la causa. Si la falla del medidor **no es imputable a ti** (falla interna,
> error del concesionario), el cobro se limita a un máximo de **3 meses**. Si la causa
> **sí te es imputable** (manipulación del medidor, conexión clandestina, negativa de
> acceso acreditada), el cobro puede llegar hasta **12 meses**, calculado sobre el
> promedio de tu consumo en los períodos verificados como correctos. (Fuente: FAQ #6)

**Pregunta:** ¿Cuál es la diferencia entre la tarifa BT1 y la BT3?

Fragmentos recuperados: `FAQ #11 (Tarifas)`, `PDF página 3`, `FAQ #20 (Tarifas)`

Respuesta del agente:
> La tarifa **BT1** es la más simple: no mide demanda de potencia y la usan clientes
> residenciales y pequeños comerciales; solo debería tener Cargo Fijo y Energía. La
> tarifa **BT3** sí mide la **demanda máxima leída** por el medidor y se aplica a
> clientes medianos con consumo variable, agregando un cargo de Demanda ($) a la
> boleta. (Fuente: FAQ #11)

**Pregunta:** ¿Qué es el consumo provisorio y por qué me llegó ese cargo?

Fragmentos recuperados: `PDF página 2`, `FAQ #2 (Consumo provisorio)`, `PDF página 6`

Respuesta del agente:
> Es una estimación que la distribuidora factura cuando no pudo tomar la lectura real
> de tu medidor ese mes (por ejemplo, medidor inaccesible o falla de comunicación). No
> es un error ni una sanción: cuando vuelve la lectura real, se aplica un ajuste
> ("Devolución Provisorio") a tu favor o en tu contra según corresponda. (Fuente: PDF
> página 2)

## 8. Fuente de conocimiento del agente

- [`data/Base_Conocimiento_Voltia_Energia.pdf`](data/Base_Conocimiento_Voltia_Energia.pdf):
  guía de tarifas eléctricas chilenas, consumo provisorio, política de CNR (con cita de
  D.S. N°327/1997 y R.Ex. N°1.952/2009 y N°2.520/2009 de la SEC), privacidad de datos y
  procedimiento de reclamos.
- [`data/FAQ_Voltia_Energia.csv`](data/FAQ_Voltia_Energia.csv): 20 preguntas frecuentes en
  formato tabular (categoría, pregunta, respuesta).

## 9. Evidencia de despliegue en OCI

_(Completar tras seguir `deploy/OCI_DEPLOY.md`)_

- Enlace público: `http://<IP_PUBLICA_OCI>:8080`
- Captura de pantalla: `deploy/evidencia-oci.png`
