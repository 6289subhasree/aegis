# Aegis (DisasterSignal)

**An AI-powered rural disaster communication and emergency prioritisation network.**

> Aegis doesn't just collect emergency messages; it identifies which emergency needs attention first.

Citizens report emergencies by voice, SMS or text in their own language. Aegis translates and
understands each report, merges duplicate reports of the same incident, scores every incident by
threat to life, and shows authorities a severity-ranked queue instead of a chronological one.

## How it works

```
Report (voice / SMS / text / LoRa)
  -> Ingest -> Speech-to-text -> Language ID + translation
  -> Extraction (type, location, people, injuries)
  -> Duplicate detection (semantic + spatial + temporal)
  -> Severity score S(c) = 100 * (0.40 L + 0.20 U + 0.15 P + 0.15 V + 0.10 A)
  -> Authority dashboard (ranked queue + map) -> Responder confirm / override
```

| Factor | Meaning | Weight |
|---|---|---|
| L | Threat to life (trapped, injured, missing) | 0.40 |
| U | Urgency / rate of deterioration | 0.20 |
| P | People affected (log-scaled) | 0.15 |
| V | Verification: independent reports in the cluster | 0.15 |
| A | Isolation: access cut, no connectivity | 0.10 |

Tiers: **CRITICAL** >= 80, **HIGH** 60-79, **MEDIUM** 30-59, **LOW** < 30.
Any incident with `L > 0.8` is escalated to CRITICAL regardless of its total score.
Weights are initial proposals, to be calibrated with district disaster-management officers.
Rankings support human decisions and can always be overridden by authorised responders.

## Repository layout

```
backend/    FastAPI service: ingest pipeline, dedup, scoring, REST API, tests
frontend/   React (Vite) authority dashboard
docs/       Architecture notes
```

## Quick start

Backend (SQLite by default, no external services needed):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

Dashboard:

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Full stack with PostgreSQL:

```bash
cp .env.example .env
docker compose up --build
```

## Free and offline by design

No paid APIs are used anywhere in this project.

| Need | Tool | Cost |
|---|---|---|
| Backend / API | FastAPI, SQLAlchemy | free, open source |
| Database | SQLite (dev), PostgreSQL (prod) | free, open source |
| Embeddings | built-in hashing embedder; optional Sentence-BERT | free, runs locally |
| Speech-to-text | optional Whisper (faster-whisper) | free, runs locally |
| Translation | optional IndicTrans2 | free, runs locally |
| Entity extraction | rule-based; optional spaCy | free, runs locally |
| Maps | OpenStreetMap tiles via Leaflet | free |

The heavy models are optional extras (`backend/requirements-ml.txt`). Out of the box, every
pipeline stage has a lightweight offline fallback, so the project runs on a laptop.

## Status

Framework stage. See [docs/ROADMAP.md](docs/ROADMAP.md) for what is stubbed versus done.
