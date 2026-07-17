# Agente RAG — Voltia Energía (Challenge Alura)

> Voltia Energía SpA es una empresa **ficticia**, creada exclusivamente para este proyecto educativo. Cualquier parecido con datos reales de contacto, dirección o RUT es coincidencia; no representa a ninguna empresa existente.

Asistente virtual que responde preguntas de clientes sobre facturación eléctrica chilena
(tarifas BT/AT, consumo provisorio y Consumo No Registrado — CNR), usando como única
fuente de conocimiento un documento propio de la empresa (PDF + CSV) mediante la técnica
**RAG (Retrieval-Augmented Generation)**.

Proyecto desarrollado para el Challenge Alura "Agente Inteligente".

## 1. Descripción general

Voltia Energía SpA es una empresa chilena ficticia de asesoría en gestión energética. A sus
clientes les pasa algo bien común en el rubro eléctrico: les llega un cargo de "consumo
provisorio" y no saben qué significa, o reciben un cobro retroactivo (CNR) y no tienen claro
si corresponde ni por cuántos meses, o simplemente no entienden qué tarifa tienen en su
boleta (BT1, BT3, AT3...). Este proyecto arma un agente que responde ese tipo de preguntas.

En términos generales, el agente hace tres cosas: lee un documento propio de la empresa
(`data/Base_Conocimiento_Voltia_Energia.pdf` y `data/FAQ_Voltia_Energia.csv`, con la política
de facturación, la guía de tarifas y el marco normativo de la SEC sobre CNR), indexa ese
contenido para poder encontrar rápido los fragmentos relevantes ante cada pregunta, y usa
**Google Gemini** (en su tier gratuito) para redactar la respuesta en español a partir de esos
fragmentos, citando siempre de dónde la sacó.

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

Para la recuperación usamos **TF-IDF + similitud coseno** (scikit-learn) en vez de embeddings
de un modelo neuronal, y fue una decisión a propósito: nos evita depender de librerías
pesadas (torch, GPU) o de una segunda API solo para generar embeddings, lo que hace más
liviano el despliegue en una instancia gratuita de OCI. Con la cantidad de fragmentos que
tiene la base de conocimiento de este proyecto (unas cuantas decenas), TF-IDF encuentra los
pasajes relevantes con buena precisión — puedes verlo en las pruebas de
`tests/test_retriever.py`.

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

Cloná el repo y armá el entorno:

```bash
git clone https://github.com/<tu-usuario>/voltia-agente-rag.git
cd voltia-agente-rag
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Después copiá el archivo de ejemplo de variables de entorno y completá tu propia key (es
gratis, se genera en aistudio.google.com/apikey):

```bash
cp .env.example .env
```

Con eso listo, construí el índice de recuperación una vez:

```bash
python scripts/build_index.py
```

Y ya podés usar el agente, ya sea por consola:

```bash
python agent_cli.py "¿Por cuántos meses me pueden cobrar un CNR?"
```

o levantando la app web y abriendo `http://localhost:8080` en el navegador:

```bash
python app.py
```

### 5.2 Con Docker

Si preferís no instalar nada en tu máquina más que Docker:

```bash
docker build -t voltia-agente-rag .
docker run -p 8080:8080 --env-file .env voltia-agente-rag
```

### 5.3 Pruebas

Hay pruebas de humo para el paso de recuperación que no necesitan API key:

```bash
python tests/test_retriever.py
```

### 5.4 Despliegue en OCI

La guía completa, con capturas y todo lo que nos fue pasando al hacerlo, está en
[`deploy/OCI_DEPLOY.md`](deploy/OCI_DEPLOY.md).

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

El agente está corriendo en una instancia Compute Always Free de OCI (`voltia-agent-rag`,
Ampere `VM.Standard.A1.Flex` con Ubuntu 20.04, región `sa-valparaiso-1`), dentro de un
contenedor Docker construido desde este mismo repo — el paso a paso está en
[`deploy/OCI_DEPLOY.md`](deploy/OCI_DEPLOY.md).

Podés probarlo vos mismo en: **http://148.116.109.139:8080**

Y en [`deploy/evidencia-oci.png`](deploy/evidencia-oci.png) queda una captura de una
conversación real con el agente ya desplegado, respondiendo sobre CNR y datos de contacto
con sus fuentes citadas.
