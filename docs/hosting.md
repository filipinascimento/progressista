# Hosting Progressista

You can keep Progressista on your laptop or deploy it to a free or low-cost
PaaS. Below are options and quickstart notes.

## Quick checklist

1. Containerize with the built-in `uvicorn` server (already bundled).
2. Configure a bearer token via `PROGRESSISTA_API_TOKEN`.
3. Expose ports for both HTTP (`/progress`, `/tasks`, `/health`) and WebSocket
   (`/ws`).
4. Serve the dashboard (`/static/index.html`) behind TLS if the service is public.

## Free-tier friendly platforms

| Platform | Notes | Steps |
| --- | --- | --- |
| **Render (Free Web Service)** | Always-on free tier with sleep after inactivity. | 1) Create a new Web Service from your repo. 2) `Build Command: pip install .` 3) `Start Command: progressista serve --host 0.0.0.0 --port 10000`. 4) Add environment variables (token, retention, etc.). |
| **Railway** | Simple deployment with CLI; free credits monthly. | 1) `railway up` with a Python service. 2) Set `PORT` env to provided value. 3) Run `progressista serve --host 0.0.0.0 --port $PORT`. |
| **Fly.io** | 3 shared-cpu-1x VMs free; global regions. | 1) `fly launch --no-deploy`. 2) Edit `fly.toml` to expose `internal_port = 8000`. 3) Deploy with `fly deploy`. 4) Add `PROGRESSISTA_API_TOKEN` via `fly secrets set`. |
| **Deta Space / Deploy** | Free micro services, sleeps after inactivity. | Wrap Progressista in a FastAPI project and push via `deta deploy`. Ensure `main:app = progressista.server:create_app`. |
| **Google Cloud Run (Free tier)** | Scales to zero, free 2M requests. | 1) Build container `gcloud builds submit`. 2) Deploy `gcloud run deploy progressista --image ... --allow-unauthenticated`. 3) Set env vars with `gcloud run services update`. |

Any host that supports ASGI/WSGI apps works. You can also run Progressista on a
VPS (e.g. Lightsail, Hetzner) with systemd.

## Sample Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

ENV PROGRESSISTA_HOST=0.0.0.0
ENV PROGRESSISTA_PORT=8000

CMD ["progressista", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy the image to your chosen platform and expose port 8000.

## Security tips

- Set `PROGRESSISTA_API_TOKEN` (or `PROGRESSISTA_API_TOKENS`) so only authorised
  clients can publish progress or load the dashboard.
- Use `PROGRESSISTA_STALE_SECONDS` to highlight idle jobs and
  `PROGRESSISTA_MAX_TASK_AGE` to purge abandoned entries automatically.
- Terminate TLS at the platform or use a CDN/Reverse proxy. All listed hosts
  provide HTTPS endpoints by default.
- If you run behind nginx/Traefik, forward `Authorization` headers and the
  WebSocket upgrade (`Connection: Upgrade`, `Upgrade: websocket`).

## Using third-party relay services

There are no public “progress relay” services compatible with Progressista yet.
However, because the protocol is simple JSON-over-HTTP, you can host Progressista
on any generic provider and point your clients at that URL. If you need stronger
durability or multi-tenant hosting, consider using a managed FastAPI hosting
service or extend the code to publish to Redis/pub-sub.
