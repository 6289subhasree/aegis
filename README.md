# DisasterSignal (Aegis)

**An inclusive, offline-first rural emergency communication network with AI-powered prioritisation.**

> *“Every Voice Matters. Every Second Counts. Every Life Comes First.”*  
> **RURALCONNECT 2026 · IEEE NATIONAL WORKSHOP · IIT KHARAGPUR · IDEATHON**  
> **Authors:** Subhasree Paul · Anushka Mukherjee  
> **Tracks:** Track 1: Rural Communications · Track 2: AI/ML for Rural India

---

## Overview

Reliable connectivity comes before digital inclusion, and in a flood or cyclone it is the first thing to fail. Rural communities in India then face communication collapse: towers and power go down, reports arrive in many languages and literacy levels, and critical rescue requests are buried among duplicate, low-urgency messages processed in arrival order.

**DisasterSignal** is a communication network first and an intelligence layer second:
1. **Inclusive Access Layer:** Ingests reports across Voice, IVR, SMS, App, and solar-powered LoRa mesh relays.
2. **Compact 20-Byte Packet:** Fits a single LoRa SF9 frame and a single 28-character Base64 SMS, protected with CRC-16 error detection.
3. **Multilingual Understanding:** Transcribes speech locally via Whisper (Hindi/English implemented and tested offline); IndicTrans2 translation architecture defined for full 22-language pipeline.
4. **Duplicate Clustering:** Spatio-temporal and semantic centroid clustering merges redundant reports into corroborating evidence.
5. **Severity-First Triage:** Prioritises rescue requests mathematically rather than by arrival order, reducing critical queue wait times by 81% to 97% under disaster surges (Section 12).

---

## Same Inbox. Different Order.

*(Demonstrates 4-tier calibration benchmark from Poster Section 02; loadable via `POST /demo/load-poster-tiers`)*

| TODAY: BY ARRIVAL (FIFO) | DISASTERSIGNAL: RANKED BY THREAT TO LIFE |
| :--- | :--- |
| `10:02` Water in farmland | **#1 (Score 91 — CRITICAL):** 5 people on a rooftop ×4 |
| `10:04` Road muddy, slow | **#2 (Score 72 — HIGH):** Bridge has collapsed (isolated community) |
| `10:05` Bridge has collapsed | **#3 (Score 38 — MEDIUM):** Water in farmland ×2 |
| `10:07` Field flooded *(duplicate)* | **#4 (Score 15 — LOW):** Road muddy, slow |
| `10:09` 5 people on a rooftop ×4 | *(Duplicates merged: rooftop rescue jumps from 5th to 1st)* |

---

## Severity Scoring Methodology

Each incident cluster $c$ receives a transparent, explainable score in $[0, 100]$:

$$S(c) = 100 \times (0.40L + 0.20U + 0.15P + 0.15V + 0.10A)$$

| Factor | Description | Formula / Saturation | Weight |
| :---: | :--- | :--- | :---: |
| **L** | **Threat to Life** | Trapped, injured, missing, rising water | **0.40** |
| **U** | **Urgency** | Rate of deterioration, immediate danger | **0.20** |
| **P** | **People Affected** | Log-scaled: $\ln(1+n) / \ln(1+50)$ | **0.15** |
| **V** | **Verification** | Independent reports in cluster: $\min(1, \frac{n-1}{3})$ | **0.15** |
| **A** | **Isolation** | Road cut off, bridge collapsed, zero connectivity | **0.10** |

### Escalation Rules
* **Rule 1:** $L > 0.8 \implies \textbf{CRITICAL}$ (threat to life always takes highest precedence).
* **Rule 2:** An isolated community ($A \ge 0.8$) that is urgent ($U \ge 0.7$) or has life risk ($L \ge 0.5$) is escalated to at least $\textbf{HIGH}$.

---

## Compact 20-Byte Report Packet

Designed to operate in India's delicensed **865–868 MHz band (G.S.R. 853(E))**:

```
byte 0: ver (1 bit) · chan (2 bits) · lang (5 bits)
| ver·chan·lang | type | people | geo-cell | time | node | flags | CRC-16 |
| 1 Byte        | 1 B  | 1 B    | 6 Bytes  | 4 B  | 4 B  | 1 Byte| 2 Bytes|
```

* **Flags (Byte 17):** Bit 0 = $L$, Bit 1 = $U$, Bit 2 = $A$, Bits 5–7 = Hop Count (0–7).
* **CRC-16 (Bytes 18–19):** Validated to detect 100% of single-bit errors across all 160 bits.
* **SMS Compatibility:** 20 raw bytes encode into exactly **28 characters Base64**, fitting within a single standard SMS without data plan.

---

## Repository Structure

```
aegis/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (reports, packets, incidents, demo)
│   │   ├── services/
│   │   │   ├── packet_codec.py # 20-byte LoRa/SMS codec + CRC-16 CCITT
│   │   │   ├── scoring.py      # Severity scoring formula & escalation rules
│   │   │   ├── dedup.py        # Spatio-temporal and semantic clustering
│   │   │   ├── extraction.py   # Information and entity extraction
│   │   │   ├── pipeline.py     # End-to-end report and packet pipeline
│   │   │   └── stt.py          # Whisper speech-to-text integration
│   │   ├── demo.py          # 6-packet demo & flood scenarios
│   │   └── main.py          # FastAPI application entrypoint
│   └── tests/               # Automated unit and alignment tests
├── frontend/                # React (Vite) Authority Dashboard
├── simulations/
│   ├── network_resilience.py # LoRa mesh Monte Carlo simulation (Poster Section 07)
│   └── surge_queue.py        # Discrete-event surge queue simulation (Poster Section 12)
└── docs/                    # Architecture and regulatory documentation
```

---

## Quick Start

### 1. Backend Setup & Tests
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_packet_codec.py tests/test_poster_alignment.py tests/test_scoring.py
uvicorn app.main:app --reload
```

### 2. Frontend Authority Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).  
Click **"Load 6-Packet LoRa Demo"** to see out-of-order radio packets automatically clustered and prioritized by threat to life.

---

## Reproducing Poster Simulations

### Network Resilience & Duty-Cycle (Section 07)
```bash
python simulations/network_resilience.py
```
* Generates the **SF7–SF12 Airtime & Capacity Table**.
* Runs 30 Monte Carlo iterations across 60 villages on an 18×18 km mesh.
* Confirms:
  * Towers fail: Cellular-only 39% $\to$ DisasterSignal 99%.
  * Congestion under surge: FIFO 68.7% $\to$ Priority Forwarding 99.5% life-threat delivery.
  * Links fail: Plain mesh 73.8% $\to$ Store-and-Forward 95.5%.
  * Stacked outage drill: 99.4% overall delivery, 100% life-threat delivery.

### Surge Queue Wait-Time Reduction (Section 12)
```bash
python simulations/surge_queue.py
```
* Simulates 400 reports over 200 runs with 1 officer (mean service time 0.78 min):
  * Load 0.85: FIFO 4.1 min $\to$ Severity-First 0.8 min (**-81%**)
  * Load 1.00: FIFO 11.0 min $\to$ Severity-First 0.9 min (**-92%**)
  * Load 1.30: FIFO 37.8 min $\to$ Severity-First 1.0 min (**-97%**)

---

## References

1. UNDRR, *Sendai Framework for Disaster Risk Reduction 2015–2030*, United Nations, 2015.
2. NDMA, *National Disaster Management Plan*, Government of India, 2019.
3. M. Imran et al., *Processing Social Media Messages in Mass Emergency: A Survey*, ACM Computing Surveys, 2015.
4. N. Reimers, I. Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*, EMNLP, 2019.
5. A. Radford et al., *Robust Speech Recognition via Large-Scale Weak Supervision*, ICML, 2023.
6. Ministry of Communications, *G.S.R. 853(E)*, Gazette of India, 10 Dec 2021 (865–868 MHz Band).
