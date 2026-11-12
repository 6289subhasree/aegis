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

Tiers: **CRITICAL** >= 80, **HIGH** 60-79, **MEDIUM** 30-59, **LOW** < 30, plus two escalation rules:

1. `L > 0.8` (threat to life) is always CRITICAL.
2. An isolated community (`A >= 0.8`) that is also urgent (`U >= 0.7`) or has a credible life risk (`L >= 0.5`) is at least HIGH. Isolation is worth only 10 points in the formula, so without this rule "bridge collapsed, village cut off" could never reach HIGH.

The API always returns the plain-language reason when a rule, not the score band, set the tier.
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

Press **Load flood scenario** in the dashboard to fill the queue with a realistic example.

## Voice reports (Hindi and English)

Voice is transcribed on your own computer with Whisper. It is free and needs no internet once the
model is downloaded.

```bash
cd backend
pip install -r requirements-voice.txt       # small install, no PyTorch
python -m app.tools.download_models        # one time, needs internet (about 0.5 GB for "small")
```

Then set `STT_BACKEND=whisper` in `backend/.env` and restart the backend. In the dashboard, press
**Record**, speak, and press **Stop**. For non-English speech the dashboard shows what was heard and
the English version that was scored.

Check recognition quality on a recording of your own voice before relying on it:

```bash
python -m app.tools.transcribe my_recording.wav hi
```

If Hindi accuracy on `small` is not good enough, set `WHISPER_MODEL=medium` (about 1.5 GB, slower).

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
