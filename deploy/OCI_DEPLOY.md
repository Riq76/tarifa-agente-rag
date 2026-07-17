# Despliegue en Oracle Cloud Infrastructure (OCI)

Así es como lleve el agente a una instancia Compute **Always Free** de OCI, usando Docker. No es la única forma de hacerlo, pero es la que use para este proyecto y la dejo documentada paso a paso.

## 1. Crear la instancia Compute

En la consola de OCI, ve a **Compute → Instances → Create Instance**. Le pusimos de nombre `voltia-agente-rag`, pero puedes usar el que quieras.

Como imagen, elige **Canonical Ubuntu 22.04** (los comandos de esta guía asumen Ubuntu, con `apt`). Y en la forma (shape), busca alguna que esté marcada como *Always Free*: la `VM.Standard.A1.Flex` (Ampere, hasta 4 OCPU y 24 GB de RAM) suele rendir mucho mejor que la `VM.Standard.E2.1.Micro` (AMD, 1 GB), así que si tu región la tiene disponible, prefiérela.

En la sección de networking, asegúrate de que la instancia quede en una subred pública. Si es la primera instancia que creas en esa cuenta, probablemente no tengas todavía una VCN — puedes dejar que OCI te cree una nueva ahí mismo. Y en las llaves SSH, descarga la llave privada cuando te la ofrezcan: es tu única oportunidad, no se puede volver a descargar después.

Un par de cosas que me pasó al hacerlo y que te pueden ahorrar tiempo:

- A veces el checkbox para asignar IP pública automáticamente no se deja activar durante la creación (parece un bug de la consola cuando la subred recién se está armando). Si te pasa, simplemente crea la instancia igual y asigna la IP pública después, desde **Networking → tu VNIC → IP administration**.
- Si la subred no tiene todavía un Internet Gateway, en la pestaña de Networking de la instancia vas a ver un atajo que dice "Connect public subnet to internet" — con eso se soluciona en un clic.

## 2. Abrir los puertos que vas a necesitar

Necesitas dos puertos abiertos: el 22 para
SSH (para poder conectarte y configurar todo) y el 8080 para la app.

Ve al Network Security Group asociado a tu instancia (o a la Security List de la subred, si no usaste NSG) y agrega dos reglas de tipo Ingress, ambas con origen `0.0.0.0/0` y protocolo TCP: una para el puerto `22` y otra para el `8080`.

## 3. Conectarte por SSH e instalar Docker

```bash
ssh -i tu-llave.pem ubuntu@<IP_PUBLICA>
```

La primera vez que te conectes te va a preguntar si confías en el host — contesta `yes`.

Ya adentro, instala Docker y Git:

```bash
sudo apt update && sudo apt install -y docker.io git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Ese último comando agrega tu usuario al grupo `docker`, pero el cambio no se aplica hasta que abras una sesión nueva. Así que sal (`exit`) y vuelve a conectarte con el mismo comando SSH de antes.

## 4. Clonar el repositorio y poner tu API key

```bash
git clone https://github.com/<tu-usuario>/voltia-agente-rag.git
cd voltia-agente-rag
cp .env.example .env
nano .env
```

Dentro de nano, reemplaza el valor de ejemplo de `GEMINI_API_KEY` por tu key real. Para guardar: `Ctrl+O` y Enter; para salir: `Ctrl+X`.

## 5. Construir la imagen y levantar el contenedor

```bash
docker build -t voltia-agente-rag .
docker run -d --name voltia-agente \
  --env-file .env \
  -p 8080:8080 \
  --restart unless-stopped \
  voltia-agente-rag
```

El `--restart unless-stopped` hace que el contenedor vuelva a levantarse solo si la instancia se reinicia.

## 6. Comprobar que quedó andando

```bash
curl http://localhost:8080/health
```

Debería devolver `{"status":"ok"}`. Y desde tu computador, si abres `http://<IP_PUBLICA>:8080` en el navegador, ya deberías ver la interfaz de chat del agente funcionando.

## 7. Evidencia para la entrega del Challenge

Con la app corriendo, entra a esa URL, hazle un par de preguntas (puedes usar las de la sección "Ejemplos" del README) y toma una captura donde se vea la pregunta y la respuesta. Guárdala como `deploy/evidencia-oci.png` y anota la URL pública en el README — con eso ya tienes la evidencia de despliegue lista.

## Si prefieres no administrar una VM completa: OCI Container Instances

Es una alternativa más simple si no quieres estar pendiente de parches ni de la VM en sí.

Primero subes tu imagen a OCI Container Registry:

```bash
docker login <region>.ocir.io -u '<tenancy-namespace>/<tu-usuario>' -p '<auth-token>'
docker tag voltia-agente-rag <region>.ocir.io/<tenancy-namespace>/voltia-agente-rag:latest
docker push <region>.ocir.io/<tenancy-namespace>/voltia-agente-rag:latest
```

Y luego, en **Developer Services → Container Instances → Create Container Instance**, eliges esa imagen recién subida, defines el puerto `8080` y agregas `GEMINI_API_KEY` como variable de entorno. OCI le asigna una IP pública al contenedor, y esa es la que usas como enlace de evidencia.

## Notas de seguridad

Tu `.env` con la API key real nunca debería llegar a GitHub — ya está en el `.gitignore`, pero vale la pena revisarlo antes de cada commit. Y si piensas dejar el servicio corriendo por un tiempo largo, considera poner Nginx con un certificado TLS (Let's Encrypt) delante del puerto 8080, para que quede sirviendo por `https://` en vez de HTTP plano.
