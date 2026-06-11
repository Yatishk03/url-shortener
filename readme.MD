# Scalable URL Shortener

A production-grade URL shortener built with FastAPI, MySQL, and Redis.
Load tested at **436 RPS** sustaining **200 concurrent users** with **74ms median latency**.
Cache-hit redirect path benchmarked at **6ms median** via Locust load testing.

## Architecture

```
Client
  │
  ▼
FastAPI (Python)
  │
  ├── Redis LRU Cache ──→ Cache hit  → 6ms redirect (no DB query)
  │
  └── MySQL ────────────→ Cache miss → fetch, cache, redirect
  
Hit counters → Redis INCR (atomic, no MySQL write on redirect)
```

## Key Design Decisions

| Decision | Reason |
|---|---|
| Base62 encoding of auto-increment ID | Guaranteed unique short codes — no collision possible |
| Redis LRU cache | Cache-hit redirects serve in ~6ms — no DB query needed |
| Redis INCR for hit counters | Eliminates MySQL write contention on read-heavy traffic |
| Connection pooling (32 connections) | Sustains throughput under 200 concurrent users |
| Background tasks for hit counting | Hit counter never blocks the redirect response |

## Benchmark Results

Load tested using **Locust** with 200 concurrent users, 9:1 read/write ratio.

| Metric | Value |
|---|---|
| Peak RPS | 436 |
| Median latency | 74ms |
| p95 latency | 230ms |
| Cache-hit redirect | 6ms median |
| Concurrent users | 200 |
| Server errors | 0 |

## API Endpoints

```
POST /shorten          → { short_code, short_url, original }
GET  /{short_code}     → 307 redirect to original URL
GET  /stats/{code}     → { short_code, original, hit_count }
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Cache | Redis 7.2 (LRU eviction) |
| Database | MySQL 8.0 |
| Containers | Docker + Docker Compose |
| Load Testing | Locust |

## Run Locally

**Prerequisites:** Docker Desktop running

```bash
# Clone the repo
git clone https://github.com/Yatishk03/url-shortener.git
cd url-shortener

# Start all services
docker compose up --build

# API live at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Test it:**
```bash
# Shorten a URL
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# Response
# {"short_code":"b","short_url":"http://localhost:8000/b","original":"https://www.google.com"}

# Check stats
curl http://localhost:8000/stats/b
```

## Load Test

```bash
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089
# Set Users: 200, Spawn rate: 20
```