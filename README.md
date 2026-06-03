# HEMT

HTTP mail server emulator — capture, inspect, and organize emails via a web UI or REST API.

## Quick Start

```bash
cp .env.example .env
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000, register, and start sending emails.

## Docker

```bash
docker build -t hemt .
docker run -d -p 5000:5000 -v hemt-data:/app/instance --name hemt hemt
```

### Docker Compose

```yaml
services:
  hemt:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - hemt-data:/app/instance
      - hemt-attachments:/app/attachments
    environment:
      - SECRET_KEY=change-this
      - API_BASE_URL=http://localhost:5000
      - STORAGE_BACKEND=local
      - STORAGE_PATH=/app/attachments

volumes:
  hemt-data:
  hemt-attachments:
```

### With Cloudflare R2 / S3

```yaml
services:
  hemt:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - hemt-data:/app/instance
    environment:
      - SECRET_KEY=change-this
      - API_BASE_URL=http://localhost:5000
      - STORAGE_BACKEND=s3
      - S3_BUCKET_NAME=hemt
      - S3_REGION=auto
      - S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
      - AWS_ACCESS_KEY_ID=your-access-key-id
      - AWS_SECRET_ACCESS_KEY=your-secret-access-key

volumes:
  hemt-data:
```

### With PostgreSQL

```yaml
services:
  hemt:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - hemt-attachments:/app/attachments
    environment:
      - SECRET_KEY=change-this
      - API_BASE_URL=http://localhost:5000
      - DATABASE_BACKEND=postgres
      - DATABASE_URL=postgresql://hemt:hemt@db:5432/hemt
      - STORAGE_BACKEND=local
      - STORAGE_PATH=/app/attachments

  db:
    image: postgres:17
    environment:
      - POSTGRES_USER=hemt
      - POSTGRES_PASSWORD=hemt
      - POSTGRES_DB=hemt
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hemt"]

volumes:
  pgdata:
  hemt-attachments:
```

## Railway

Deploy directly from your Git repo. No Dockerfile changes needed — the included `railway.json` handles build and health checks.

### Backend choice → Volume needs

| Database | Storage | Railway Volumes | Services needed |
|----------|---------|----------------|-----------------|
| SQLite (default) | Local (default) | `/app/instance`, `/app/attachments` | None |
| SQLite | S3 / R2 | `/app/instance` | R2 bucket |
| Postgres | Local | `/app/attachments` | Postgres plugin |
| Postgres | S3 / R2 | *(none)* | Postgres plugin + R2 bucket |

### Environment variables

Set these in the Railway dashboard. Only the ones relevant to your chosen backends are required.

| Variable | When required | Value |
|----------|---------------|-------|
| `SECRET_KEY` | Always | A random secret |
| `DATABASE_BACKEND` | Always | `sqlite` (default) or `postgres` |
| `STORAGE_BACKEND` | Always | `local` (default) or `s3` |
| `DATABASE_URL` | `postgres` backend | Railway Postgres connection string |
| `AWS_ACCESS_KEY_ID` | `s3` storage | R2 token ID |
| `AWS_SECRET_ACCESS_KEY` | `s3` storage | R2 token secret |
| `S3_BUCKET_NAME` | `s3` storage | `hemt` |
| `S3_ENDPOINT_URL` | `s3` storage with R2 | `https://<accountid>.r2.cloudflarestorage.com` |
| `API_BASE_URL` | Railway | `https://<your-app>.up.railway.app` |

### Example: Postgres + local storage

1. Add a **Postgres** plugin — Railway automatically sets `DATABASE_URL` in the environment.
2. Add a **Volume** at `/app/attachments` (or use S3/R2 and skip the volume).
3. Set env vars: `SECRET_KEY`, `DATABASE_BACKEND=postgres`, `STORAGE_BACKEND=local`, `API_BASE_URL`.

### Example: SQLite + S3/R2

1. Add a **Volume** at `/app/instance` (SQLite needs a writable directory).
2. Set env vars: `SECRET_KEY`, `DATABASE_BACKEND=sqlite`, `STORAGE_BACKEND=s3`, `S3_BUCKET_NAME`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `API_BASE_URL`.

> The `entrypoint.sh` only creates directories for the active backends, so unused volume mounts are harmless.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask secret key |
| `API_BASE_URL` | `http://localhost:5000` | Base URL shown in API docs |
| `DATABASE_BACKEND` | `sqlite` | `sqlite` or `postgres` |
| `DATABASE_URL` | `sqlite:///emailtrap.db` | SQLAlchemy connection string |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `STORAGE_PATH` | `attachments` | Local attachment directory |
| `S3_BUCKET_NAME` | `emailtrap` | S3/R2 bucket for attachments |
| `S3_REGION` | `us-east-1` | AWS region |
| `S3_PREFIX` | `attachments` | S3/R2 key prefix |
| `S3_ENDPOINT_URL` | *(empty)* | Custom S3-compatible endpoint (e.g. Cloudflare R2) |
| `AWS_ACCESS_KEY_ID` | *(empty)* | Access key for S3/R2 |
| `AWS_SECRET_ACCESS_KEY` | *(empty)* | Secret key for S3/R2 |

## API

All endpoints require a Bearer token (`Authorization: Bearer et_<prefix>_<secret>`). Create API keys from the web Settings page or via `POST /api/v1/api-keys`.

| Method | Endpoint | Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/api-keys` | `keys:manage` | List API keys |
| `POST` | `/api/v1/api-keys` | `keys:manage` | Create API key |
| `DELETE` | `/api/v1/api-keys/<id>` | `keys:manage` | Delete API key |
| `POST` | `/api/v1/incoming-mail` | `mail:send` | Receive an email |
| `GET` | `/api/v1/messages` | `mail:read` | List messages (`?tag=...`, `?q=...`) |
| `GET` | `/api/v1/messages/<id>` | `mail:read` | Get message with attachments |
| `GET` | `/api/v1/tags` | `mail:read` | List your tags |

### Scopes

API keys control access with comma-separated scopes: `mail:send`, `mail:read`, `keys:manage`.

### Tags

API keys can have an optional tag. Emails sent with a tagged key are automatically grouped under that tag. Override per-request with the `X-HEMT-Tag` header.

```bash
curl -X POST http://localhost:5000/api/v1/incoming-mail \
  -H "Authorization: Bearer et_abc123..." \
  -H "X-HEMT-Tag: support" \
  -F "to=inbox@myapp.com" \
  -F "from=user@external.com" \
  -F "subject=Hello" \
  -F "body_text=Body"
```
