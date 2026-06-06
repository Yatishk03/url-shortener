from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
import os

from app.database  import get_connection, init_db
from app.cache     import get_cached_url, set_cached_url, REDIS_CLIENT
from app.shortener import encode
from app.models    import ShortenRequest, ShortenResponse, StatsResponse

app = FastAPI(title="URL Shortener")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(request: ShortenRequest):
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO urls (original) VALUES (%s)",
            (request.url,)
        )
        url_id     = cursor.lastrowid
        short_code = encode(url_id)

        cursor.execute(
            "UPDATE urls SET short_code = %s WHERE id = %s",
            (short_code, url_id)
        )
        conn.commit()
        set_cached_url(short_code, request.url)

        return ShortenResponse(
            short_code=short_code,
            short_url=f"{BASE_URL}/{short_code}",
            original=request.url,
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/stats/{short_code}", response_model=StatsResponse)
def get_stats(short_code: str):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT original FROM urls WHERE short_code = %s",
        (short_code,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    hits = REDIS_CLIENT.get(f"hits:{short_code}") or 0

    return StatsResponse(
        short_code=short_code,
        original=row[0],
        hit_count=int(hits),
    )


@app.get("/{short_code}")
def redirect_url(short_code: str, background_tasks: BackgroundTasks):
    original = get_cached_url(short_code)
    if original:
        background_tasks.add_task(_increment_hits_redis, short_code)
        return RedirectResponse(url=original, status_code=307)

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT original FROM urls WHERE short_code = %s",
        (short_code,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")

    original = row[0]
    set_cached_url(short_code, original)
    background_tasks.add_task(_increment_hits_redis, short_code)

    return RedirectResponse(url=original, status_code=307)


def _increment_hits_redis(short_code: str):
    try:
        REDIS_CLIENT.incr(f"hits:{short_code}")
    except Exception:
        pass