# Roadmap

## Done in the framework stage
- Project layout, config, SQLAlchemy models, REST API
- Severity scoring (`S = 100 * (0.40L + 0.20U + 0.15P + 0.15V + 0.10A)`, CRITICAL escalation rule)
- Duplicate detection (semantic similarity + radius + time window)
- Rule-based extraction of incident type, people count, life-threat and isolation signals
- Pluggable adapters for embeddings, speech-to-text and translation, each with an offline fallback
- Authority dashboard: ranked queue, tier summary, live map (Leaflet + OpenStreetMap), factor breakdown, override
- Demo flood scenario (10 reports, deliberately bad arrival order) with load and reset buttons
- Escalation rules: life threat above 0.8 is CRITICAL; isolation plus urgency or life risk is at least HIGH
- Voice reports: in-browser recording, local Whisper transcription, Hindi/English, original transcript kept
- Tests, Docker Compose, CI

## Stubbed (next)
- Real IndicTrans2 translation adapter and language ID
- Sentence-BERT embedder wiring and threshold tuning
- SMS gateway and IVR webhooks (Twilio-free options: Gammu / local GSM modem)
- LoRa relay ingestion
- IVR call-back verification for low-confidence reports
- Authentication for responders

## Later
- Weight calibration from logged responder overrides
- Evaluation harness (Cohen's kappa, cluster precision/recall, WER/BLEU, time-to-critical)
- Simulated flood-drill pilot
