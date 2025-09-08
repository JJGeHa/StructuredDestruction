# Multi-stage build: build React frontend, then serve with FastAPI

# --- Frontend build stage ---
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Backend runtime stage ---
FROM python:3.12-slim AS backend
WORKDIR /app

# Install runtime deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend into expected path for StaticFiles
COPY --from=frontend /app/frontend/build ./frontend/build

# Expose port and run uvicorn
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

