# React + FastAPI Demo (Local + Azure-ready)

This repo contains a simple demo web app:
- Backend: FastAPI with a small SQLite-backed Ideas API
- Frontend: React (CRA) with Ant Design UI
  - Tools: Cover letter generator, PDF generator, Email preview/send

The app demonstrates a simple workflow: submit an idea (title + description), the backend computes a lightweight priority score based on keywords, and the UI lists ideas with delete actions.

## Local Development

Prereqs:
- Python 3.11+ (3.12 recommended)
- Node 18+

Backend:
1. Create a venv and install deps
   - macOS/Linux:
     - `python3 -m venv .venv && source .venv/bin/activate`
   - Windows (Powershell):
     - `py -m venv .venv; .\\.venv\\Scripts\\Activate.ps1`
2. `pip install -r backend/requirements.txt`
3. Run API: `uvicorn backend.main:app --reload --port 8000`

Frontend (separate terminal):
1. `cd frontend`
2. `npm install` (includes `react-router-dom` for navigation)
3. `npm start`

Open http://localhost:3000. The frontend calls the API at http://localhost:8000.

Notes:
- The backend stores data in `backend/data.db` (auto-created on first run).
- CORS is open for local dev.

## Docker (single container)

Build + run locally with Docker:

```bash
# Build image
docker build -t react-fastapi-demo:local .

# Run
docker run --rm -p 8000:8000 react-fastapi-demo:local
```

Open http://localhost:8000 to serve the built frontend and API from the same container.

Using docker-compose to build and run both frontend and backend in one container:

```bash
docker compose up --build
```

Open http://localhost:8000. The container serves the built React app and the FastAPI API under `/api`.

Notes:
- Frontend fetches use a relative base (`/api`), so no hardcoded hosts.
- In CRA dev mode, `package.json#proxy` forwards `/api` to `http://localhost:8000`.

## Azure Deployment (overview)

Two straightforward options:

1) Azure App Service for Containers (single container)
- Build and push the image to Azure Container Registry (ACR):
  - `az acr build --registry <acr-name> --image react-fastapi-demo:latest .`
- Create App Service (Linux) using the ACR image
  - Set port to `8000` (or rely on `WEBSITES_PORT=8000`)
- App serves both API and static frontend using the provided Dockerfile.

2) Azure Container Apps
- Build/push image to ACR as above
- Create a Container App referencing that image, expose port 8000
- Optionally enable internal ingress for private-only access

Optional enhancements for production:
- Configure Azure Front Door / App Gateway for TLS + WAF
- Add Azure AD auth (Easy Auth) on App Service
- Use Azure Database for PostgreSQL instead of SQLite if multi-instance

## SMTP and PDF tools

- Email sending uses environment variables (if not set, API returns a preview):
  - `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_TLS` (true/false), `SMTP_FROM`
- PDF generation uses `reportlab` (installed via `backend/requirements.txt`). If missing, `/api/tools/pdf-fill` returns 501.

Example Docker run with SMTP envs:

```bash
docker compose up --build -d
# or
docker run --rm -p 8000:8000 \
  -e SMTP_HOST=smtp.example.com -e SMTP_USER=user -e SMTP_PASS=pass \
  react-fastapi-demo:local
```

## Project Structure

```
backend/
  main.py            # FastAPI app + Ideas API
  requirements.txt   # FastAPI + uvicorn
frontend/
  src/
    App.js             # Layout + routes + topbar
    HelloFromFastAPI.js
    Ideas.js           # Demo UI for Ideas
    pages/HomePage.js  # Post-auth landing page with overview + search
    pages/ToolPage.js  # Tool page wrapper
  package.json
Dockerfile            # Multi-stage build (frontend -> backend)
docker-compose.yml    # Local container dev
```

## Troubleshooting
- CRA 5 + React 19 can be finicky. If dev server fails, pin React to 18.x (`npm i react@18 react-dom@18`) and restart.
- CORS issues in dev: ensure backend runs on 8000 and frontend on 3000; endpoints in code use explicit `http://localhost:8000`.
- Database resets: delete `backend/data.db` to start fresh.
## Docker Dev (hot reload)

Run separate dev containers for live reload on save:

```bash
docker compose -f docker-compose.dev.yml up
```

- Frontend dev server: http://localhost:3000
- Backend API: http://localhost:8000
- The frontend dev server proxies `/api` to the backend using `frontend/src/setupProxy.js` and the env var `API_PROXY_TARGET` (set to `http://backend:8000` in compose).
