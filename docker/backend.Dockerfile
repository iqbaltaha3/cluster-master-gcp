FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

# Cloud Run injects PORT (always 8080 in practice) and expects the
# container to bind to it — don't hardcode 8000 here. $PORT also works
# fine for local `docker run -p 8080:8080 -e PORT=8080 ...` or plain
# docker-compose (which still maps 8000:8000 via the PORT env default below).
ENV PORT=8000
EXPOSE 8000

CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
