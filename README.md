# URL Shortener Service

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A small, production-minded URL shortening service built with **FastAPI** and **SQLAlchemy**. Create short links with auto-generated base62 codes or custom aliases, redirect visitors with click tracking, inspect per-link statistics, and expire or delete links — all through a clean, fully tested REST API.

## Features

- **Short link creation** — 6-character base62 codes generated with cryptographically secure randomness
- **Custom aliases** — choose your own code (e.g. `/my-link`), with conflict detection (`409`)
- **Optional expiration** — links can carry an `expires_at` date; expired links answer `410 Gone`
- **Click tracking** — every redirect increments the counter and records the last access time
- **Statistics endpoint** — clicks, creation date, last access and expiration state per link
- **Link management** — list and delete links through the API
- **Configurable persistence** — SQLite by default, PostgreSQL (or any SQLAlchemy URL) via `DATABASE_URL`
- **Healthcheck, Docker & CI** — ready to run locally, in containers, and in GitHub Actions

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Validation | Pydantic v2 |
| ORM / persistence | SQLAlchemy 2.0 (SQLite by default, PostgreSQL supported) |
| Server | Uvicorn |
| Tests | pytest + FastAPI TestClient |
| Packaging / runtime | Docker, docker compose |
| CI | GitHub Actions (Python 3.12) |

## Installation

### Local (Python 3.12)

```bash
git clone https://github.com/medreda091/url-shortener-service.git
cd url-shortener-service

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

The API is then available at http://localhost:8000 — interactive docs at http://localhost:8000/docs.

### Docker

```bash
docker compose up --build
```

This starts the API on http://localhost:8000 using SQLite.

To run with PostgreSQL instead, uncomment the `DATABASE_URL` line for the `api` service in `docker-compose.yml`, then:

```bash
docker compose --profile postgres up --build
```

Or build the image alone:

```bash
docker build -t url-shortener-service .
docker run -p 8000:8000 url-shortener-service
```

## Usage

### Healthcheck

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Create a short link

```bash
curl -X POST http://localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/a/very/long/url"}'
```

```json
{
  "code": "a3F9kQ",
  "original_url": "https://example.com/a/very/long/url",
  "is_custom_alias": false,
  "click_count": 0,
  "created_at": "2026-10-20T18:00:00Z",
  "last_accessed_at": null,
  "expires_at": null
}
```

With a custom alias and an expiration date:

```bash
curl -X POST http://localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/promo",
    "custom_alias": "promo",
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

If the alias is already taken, the API returns `409 Conflict`.

### Redirect to the original URL

```bash
curl -i http://localhost:8000/a3F9kQ
# HTTP/1.1 307 Temporary Redirect
# location: https://example.com/a/very/long/url
```

Unknown codes return `404`, expired links return `410 Gone`.

### Get link statistics

```bash
curl http://localhost:8000/api/links/a3F9kQ/stats
```

```json
{
  "code": "a3F9kQ",
  "original_url": "https://example.com/a/very/long/url",
  "is_custom_alias": false,
  "click_count": 3,
  "created_at": "2026-10-20T18:00:00Z",
  "last_accessed_at": "2026-10-20T18:05:12Z",
  "expires_at": null,
  "is_expired": false
}
```

### List links

```bash
curl "http://localhost:8000/api/links?limit=100&offset=0"
```

### Delete a link

```bash
curl -X DELETE http://localhost:8000/api/links/a3F9kQ
# HTTP/1.1 204 No Content
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/links` | Create a short link (`201`, `409` on alias conflict) |
| `GET` | `/{code}` | Redirect (`307`) to the original URL and count the click |
| `GET` | `/api/links/{code}/stats` | Statistics for one link |
| `GET` | `/api/links` | List links (most recent first) |
| `DELETE` | `/api/links/{code}` | Delete a link (`204`) |
| `GET` | `/health` | Healthcheck |

## Project Structure

```
url-shortener-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, lifespan, /health
│   ├── database.py      # Engine, session factory, get_db dependency
│   ├── models.py         # SQLAlchemy Link model
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── services.py       # Base62 encoding + unique code generation
│   └── routes.py         # Link creation, redirect, stats, list, delete
├── tests/
│   ├── conftest.py       # Isolated in-memory DB fixtures
│   ├── test_links.py     # End-to-end API lifecycle tests
│   └── test_services.py  # Base62 unit tests
├── .github/workflows/
│   └── ci.yml            # GitHub Actions: pytest on Python 3.12
├── Dockerfile
├── docker-compose.yml    # API + optional PostgreSQL profile
├── requirements.txt
└── README.md
```

## Tests

The test suite covers link creation, custom-alias conflicts, redirection and click counting, statistics, unknown codes (`404`), expiration (`410`), deletion, and the base62 codec.

```bash
pip install -r requirements.txt
pytest -v
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./url_shortener.db` | SQLAlchemy connection string. Example for PostgreSQL: `postgresql+psycopg2://user:password@host:5432/dbname` |

No secrets are stored in the repository — configuration is provided exclusively through environment variables.

## License

MIT — see [LICENSE](LICENSE).
