# Despliegue en Oracle Cloud Infrastructure (OCI)

Guía paso a paso para desplegar el agente en una instancia Compute **Always Free** de OCI usando Docker.

## 1. Crear la instancia Compute

1. En la consola de OCI: **Compute → Instances → Create Instance**.
2. Nombre: `optium-agente-rag`.
3. Imagen: **Canonical Ubuntu 22.04**.
4. Forma (shape): Always Free — `VM.Standard.E2.1.Micro` (AMD, 1 GB RAM) o `VM.Standard.A1.Flex` (ARM, hasta 4 OCPU / 24 GB RAM, recomendada si está disponible en tu región).
5. En **Networking**, usa una VCN con subred pública y asigna una **IP pública**.
6. Descarga o usa un par de llaves SSH para conectarte.
7. Crea la instancia y anota la **IP pública**.

## 2. Abrir el puerto de la aplicación

1. Ve a **Networking → Virtual Cloud Networks → (tu VCN) → Security Lists → Default Security List**.
2. **Add Ingress Rules**:
   - Source CIDR: `0.0.0.0/0`
   - Protocolo: TCP
   - Puerto destino: `8080` (o `80` si prefieres exponerlo sin puerto en la URL).
3. Guarda los cambios.

## 3. Conectarse e instalar Docker

```bash
ssh -i tu-llave.pem ubuntu@<IP_PUBLICA>

sudo apt update && sudo apt install -y docker.io git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# cierra sesión y vuelve a entrar para que aplique el grupo docker
```

## 4. Clonar el repositorio y configurar la API key

```bash
git clone https://github.com/<tu-usuario>/optium-agente-rag.git
cd optium-agente-rag
cp .env.example .env
nano .env   # pega tu ANTHROPIC_API_KEY real
```

## 5. Construir y correr el contenedor

```bash
docker build -t optium-agente-rag .
docker run -d --name optium-agente \
  --env-file .env \
  -p 8080:8080 \
  --restart unless-stopped \
  optium-agente-rag
```

## 6. Verificar que quedó funcionando

```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

Desde tu navegador, abre `http://<IP_PUBLICA>:8080` — debería cargar la interfaz de chat del agente.

## 7. Evidencia para la entrega del Challenge

- **Enlace público:** `http://<IP_PUBLICA>:8080`
- **Captura de pantalla:** abre esa URL, haz una pregunta de ejemplo (ver README, sección "Ejemplos") y toma una captura mostrando la pregunta y la respuesta del agente.

## Alternativa: OCI Container Instances (sin administrar un servidor)

Si prefieres no administrar una VM completa:

1. Sube la imagen construida a **OCI Container Registry (OCIR)**:
   ```bash
   docker login <region>.ocir.io -u '<tenancy-namespace>/<tu-usuario>' -p '<auth-token>'
   docker tag optium-agente-rag <region>.ocir.io/<tenancy-namespace>/optium-agente-rag:latest
   docker push <region>.ocir.io/<tenancy-namespace>/optium-agente-rag:latest
   ```
2. En la consola: **Developer Services → Container Instances → Create Container Instance**.
3. Selecciona la imagen recién subida desde OCIR, define el puerto `8080` y agrega `ANTHROPIC_API_KEY` como variable de entorno.
3. OCI asigna una IP pública al Container Instance — úsala como enlace de evidencia.

## Notas de seguridad

- Nunca subas tu `.env` ni tu API key a GitHub (ya están en `.gitignore`).
- Si vas a dejar el servicio corriendo, considera poner Nginx + certificado TLS (Let's Encrypt) delante del puerto 8080 para servir en `https://`.
