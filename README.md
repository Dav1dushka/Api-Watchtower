# API Watchtower

A local-first API and website monitoring dashboard built with Python, FastAPI, SQLite and vanilla JavaScript.

API Watchtower helps developers check endpoints they own or are explicitly authorised to monitor. It records HTTP availability, response latency and a basic baseline of common HTTP security headers.

> **Scope:** This is a learning and portfolio project, not a vulnerability scanner, penetration test or compliance assessment. It performs one ordinary HTTP GET request per manual check. Only monitor endpoints you own or have permission to test.

## Features

- Add and remove named HTTP/HTTPS endpoints.
- Run on-demand availability checks.
- Record response status, latency and check history in SQLite.
- Inspect six HTTP security headers: HSTS (HTTPS only), CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy.
- Display a lightweight, explainable security-header score.
- Responsive web dashboard and documented FastAPI endpoints.
- Automated tests with pytest and a GitHub Actions workflow.
- Optional Docker deployment.

## Tech stack

Python 3.12 · FastAPI · HTTPX · SQLite · JavaScript · HTML · CSS · pytest · Docker · GitHub Actions

## Quick start

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

Run tests:

```bash
pytest -q
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/api/targets` | List monitored endpoints |
| POST | `/api/targets` | Add an endpoint |
| DELETE | `/api/targets/{id}` | Remove endpoint and history |
| POST | `/api/targets/{id}/check` | Run one manual check |
| GET | `/api/checks` | Read recent check history |

Interactive OpenAPI documentation is available at `/docs`.

## Security and limitations

The dashboard is designed for local use. Bind the server to `127.0.0.1`, and do not expose it publicly without authentication, authorisation, CSRF protection, rate limiting and a strict outbound-network policy. URL validation rejects credentials and non-HTTP schemes; redirects are not followed. The score only checks header presence and does not prove that an endpoint is secure.

## Planned improvements

Scheduled checks, alert notifications, historical charts, configurable thresholds, exportable reports and authenticated multi-user access.
