# 10. Deployment

## Local development (two terminals)

```bash
# 1. Set up secrets
cp .env.example .env
# edit .env and fill in GROQ_API_KEY, TAVILY_API_KEY

# 2. Backend
cd backend
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload --port 8000

# 3. Frontend (second terminal)
cd frontend
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000   # optional, this is the default
streamlit run app.py
```

Visit `http://localhost:8501`.

## Docker Compose (recommended for anything beyond local dev)

```bash
cp .env.example .env
# edit .env

docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

`docker-compose.yml` wires the frontend to reach the backend via the
internal Docker network hostname (`http://backend:8000`), not
`localhost`.

## Production notes
- **CORS**: `backend/main.py` currently allows `allow_origins=["*"]` for
  ease of local development. Set this to your actual frontend origin(s)
  before exposing the backend publicly.
- **Workers**: `uvicorn backend.main:app --workers N` only works safely
  with N=1 today, because `SessionStore` is in-process memory (see ADR
  07). Do not scale backend workers/replicas until that's addressed.
- **TLS**: put both services behind a reverse proxy (e.g. Caddy, Nginx,
  or a managed load balancer) that terminates HTTPS; neither Uvicorn nor
  Streamlit's dev server should be exposed to the internet directly.
- **Secrets**: inject `.env` values via your platform's secrets manager
  in production rather than shipping a `.env` file inside the image.
- **Resource sizing**: clustering and PCA run in-process on the uploaded
  dataframe; size backend memory to comfortably hold a few copies of your
  largest expected dataset (raw df + cleaned df + feature matrix).
