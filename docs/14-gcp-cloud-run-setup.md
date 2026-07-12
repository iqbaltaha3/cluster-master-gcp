# Deploying the backend to Cloud Run via a Cloud Build trigger (console-only)

This covers the backend service only (`docker/backend.Dockerfile` +
`cloudbuild.yaml` at the repo root). The frontend (Streamlit) isn't
covered here since it wasn't asked for, but the same pattern applies if
you want it later — a second Dockerfile, Artifact Registry repo, and
Cloud Run service, with `BACKEND_URL` pointed at the backend's Cloud Run
URL.

All steps below use the Google Cloud Console UI, no `gcloud` CLI needed.

## 1. Enable the required APIs

Console → **APIs & Services → Enabled APIs & services → + Enable APIs and services**, enable each of:
- Cloud Build API
- Cloud Run Admin API
- Artifact Registry API
- Secret Manager API

## 2. Create an Artifact Registry repository

Console → **Artifact Registry → Repositories → Create Repository**
- Name: `clustermaster` (matches `_REPO` in `cloudbuild.yaml` — change one or the other if you want a different name)
- Format: **Docker**
- Mode: **Standard**
- Region: pick one, e.g. `us-central1` (matches `_REGION` default in `cloudbuild.yaml`)
- Create.

## 3. Store your secrets in Secret Manager

Console → **Security → Secret Manager → Create Secret**. Create three separate secrets (exact names matter — `cloudbuild.yaml` references them):

| Secret name | Value |
|---|---|
| `GROQ_API_KEY` | your **new**, rotated Groq key — the old one from the zip is burned, don't reuse it |
| `TAVILY_API_KEY` | your **new**, rotated Tavily key |
| `API_KEY` | a long random string you generate yourself (this becomes the shared secret the frontend must send as `X-API-Key`) |

For each: **Create Secret** → paste the value → leave replication as "Automatic" → Create.

## 4. Create a Cloud Build trigger connected to your git repo

Console → **Cloud Build → Triggers → Create Trigger**
- **Name**: `clustermaster-backend-deploy`
- **Event**: Push to a branch
- **Source**: connect your GitHub (or Cloud Source Repositories / Bitbucket) repo the first time you're asked — follow the "Connect Repository" flow, authorize GCP's GitHub app, select the `clustermaster` repo.
- **Branch**: `^main$` (or whatever your default branch is)
- **Configuration**: **Cloud Build configuration file (yaml or json)**
- **Location**: `/cloudbuild.yaml` (repo root, matches the file I created)
- **Substitution variables** (optional — only if you want non-default values):
  - `_REGION` (default `us-central1`)
  - `_REPO` (default `clustermaster`)
  - `_SERVICE_NAME` (default `clustermaster-backend`)
  - `_ALLOWED_ORIGINS` (default `*` — set to your frontend's real URL once you have one, e.g. `https://your-frontend-url.a.run.app`)
- Create.

## 5. Grant the Cloud Build service account permission to deploy

By default the Cloud Build service account (`<PROJECT_NUMBER>@cloudbuild.gserviceaccount.com`) can't deploy to Cloud Run or read secrets. Console → **IAM & Admin → IAM** → find that service account (check "Include Google-provided role grants" if you don't see it) → **Edit principal** → **Add another role**, and add:
- **Cloud Run Admin**
- **Service Account User** (needed so Cloud Build can deploy *as* the Cloud Run runtime service account)
- **Artifact Registry Writer**
- **Secret Manager Secret Accessor**

## 6. Grant the Cloud Run runtime service account access to the secrets

This is separate from step 5 — step 5 lets *Cloud Build* deploy; this lets the *running container* actually read the secret values at startup.

By default Cloud Run services run as the special **Compute Engine default service account** (`<PROJECT_NUMBER>-compute@developer.gserviceaccount.com`) unless you've configured a custom one. Console → **IAM & Admin → IAM** → find that account → **Edit principal** → **Add another role** → **Secret Manager Secret Accessor**.

(If you'd rather use a dedicated service account for this service instead of the default one, create it under **IAM & Admin → Service Accounts**, grant it the same Secret Accessor role, then add `--service-account=your-sa@project.iam.gserviceaccount.com` to the `gcloud run deploy` step in `cloudbuild.yaml`.)

## 7. Push to trigger the first deploy

Push to your `main` branch. Console → **Cloud Build → History** to watch the build. On success, the service will appear under **Cloud Run → Services → clustermaster-backend** with a public HTTPS URL.

## 8. Point the frontend at it

Wherever you run `frontend/app.py` (locally, or its own Cloud Run service later), set:
- `BACKEND_URL` = the Cloud Run URL from step 7
- `API_KEY` = the same value you put in the `API_KEY` secret in step 3 (`api_client.py` now sends this as `X-API-Key` on every request — see the bug-fix pass)

## Notes on what `cloudbuild.yaml` sets for you

- `--allow-unauthenticated`: the service is reachable on the public internet by URL. This is why the `API_KEY` app-level gate from the bug-fix pass matters — without it, `allow-unauthenticated` + `ALLOWED_ORIGINS=*` means anyone with the URL can use it. If you'd rather lock this down at the infrastructure level instead of (or in addition to) the app-level key, remove `--allow-unauthenticated`, use Cloud Run's built-in IAM auth (`roles/run.invoker`), and have the frontend authenticate its requests with an identity token — more setup, stronger guarantee.
- `--memory=1Gi --cpu=1 --timeout=300`: clustering/PCA/Isolation Forest on larger uploads and multi-second LLM calls both benefit from headroom; bump `--memory` (e.g. `2Gi`) if you expect large uploads (`MAX_UPLOAD_MB` is 50 by default) or get OOM-killed instances.
- `--min-instances=0`: scales to zero when idle (cheapest), at the cost of cold-start latency on the first request after idle. Set to `1` if you want it always warm.
- In-memory session store: remember this is still a known limitation (see `docs/07-state-persistence-tradeoff.md`) — with `--max-instances=4` and Cloud Run's autoscaling, a user's session can land on a different instance than the one that created it, and sessions vanish on scale-to-zero or redeploy. Fine for a demo; for real multi-user use you'd want the Redis/DB-backed session store the ADR already flags as the upgrade path.
