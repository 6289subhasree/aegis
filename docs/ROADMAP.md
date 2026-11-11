# Roadmap

## Done in the framework stage
- Project layout, config, SQLAlchemy models, REST API
- Severity scoring (`S = 100 * (0.40L + 0.20U + 0.15P + 0.15V + 0.10A)`, CRITICAL escalation rule)
- Duplicate detection (semantic similarity + radius + time window)
- Rule-based extraction of incident type, people count, life-threat and isolation signals
- Pluggable adapters for embeddings, speech-to-text and translation, each with an offline fallback
- Authority dashboard skeleton (ranked queue, factor breakdown, override)
- Tests, Docker Compose, CI

## Stubbed (next)
- Real Whisper speech-to-text adapter
- Real IndicTrans2 translation adapter and language ID
- Sentence-BERT embedder wiring and threshold tuning
- SMS gateway and IVR webhooks (Twilio-free options: Gammu / local GSM modem)
- LoRa relay ingestion
- Map view with Leaflet and OpenStreetMap tiles
- IVR call-back verification for low-confidence reports
- Authentication for responders

## Later
- Weight calibration from logged responder overrides
- Evaluation harness (Cohen's kappa, cluster precision/recall, WER/BLEU, time-to-critical)
- Simulated flood-drill pilot
