from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import validate_target_url
from .database import connect, init_db
from .monitor import check_url

BASE_DIR = Path(__file__).resolve().parent.parent
init_db()

app = FastAPI(
    title="API Watchtower",
    version="1.0.0",
    description="Local endpoint monitoring and HTTP security-header baseline.",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class TargetInput(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    url: str = Field(min_length=8, max_length=2048)


@app.get("/", include_in_schema=False)
async def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-watchtower"}


@app.get("/api/targets")
async def list_targets():
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT t.id, t.name, t.url, t.created_at,
                   c.health AS last_health, c.status_code AS last_status_code,
                   c.latency_ms AS last_latency_ms,
                   c.security_score AS last_security_score,
                   c.checked_at AS last_checked_at
            FROM targets t
            LEFT JOIN checks c ON c.id = (
                SELECT id FROM checks
                WHERE target_id = t.id
                ORDER BY checked_at DESC, id DESC LIMIT 1
            )
            ORDER BY t.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/targets", status_code=201)
async def add_target(payload: TargetInput):
    try:
        url = validate_target_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    with connect() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO targets(name, url) VALUES (?, ?)",
                (payload.name.strip(), url),
            )
            target_id = cursor.lastrowid
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise HTTPException(
                    status_code=409, detail="This URL is already monitored."
                ) from exc
            raise
    return {"id": target_id, "name": payload.name.strip(), "url": url}


@app.delete("/api/targets/{target_id}", status_code=204)
async def delete_target(target_id: int):
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM targets WHERE id = ?", (target_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Target not found.")
    return None


@app.post("/api/targets/{target_id}/check")
async def run_check(target_id: int):
    with connect() as connection:
        target = connection.execute(
            "SELECT id, name, url FROM targets WHERE id = ?", (target_id,)
        ).fetchone()

    if target is None:
        raise HTTPException(status_code=404, detail="Target not found.")

    result = await check_url(target["url"])

    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO checks(
                target_id, status_code, latency_ms, health,
                security_score, missing_headers, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_id,
                result["status_code"],
                result["latency_ms"],
                result["health"],
                result["security_score"],
                ",".join(result["missing_headers"]),
                result["error"],
            ),
        )
        check_id = cursor.lastrowid

    return {"id": check_id, "target": dict(target), **result}


@app.get("/api/checks")
async def list_checks(limit: int = 30):
    limit = max(1, min(limit, 100))
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT c.id, c.checked_at, c.status_code, c.latency_ms,
                   c.health, c.security_score, c.missing_headers, c.error,
                   t.name AS target_name, t.url AS target_url
            FROM checks c
            JOIN targets t ON t.id = c.target_id
            ORDER BY c.checked_at DESC, c.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
