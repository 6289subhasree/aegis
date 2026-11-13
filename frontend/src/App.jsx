import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import MapView from "./MapView.jsx";

const TIERS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const FACTORS = [
  ["life", "L · Threat to life", 0.4],
  ["urgency", "U · Urgency", 0.2],
  ["people", "P · People affected", 0.15],
  ["verification", "V · Verification", 0.15],
  ["isolation", "A · Isolation", 0.1],
];

function TierBadge({ tier }) {
  return <span className={`badge tier-${tier}`}>{tier}</span>;
}

function Summary({ queue }) {
  const counts = Object.fromEntries(TIERS.map((t) => [t, 0]));
  let reports = 0;
  queue.forEach((i) => {
    counts[i.effective_tier] += 1;
    reports += i.report_count;
  });
  return (
    <div className="summary">
      {TIERS.map((t) => (
        <div key={t} className={`stat border-${t}`}>
          <div className="stat-n">{counts[t]}</div>
          <div className="stat-l">{t}</div>
        </div>
      ))}
      <div className="stat stat-wide">
        <div className="stat-n">
          {reports} <span className="arrow">→</span> {queue.length}
        </div>
        <div className="stat-l">reports → incidents</div>
      </div>
    </div>
  );
}

function FactorBars({ factors }) {
  return (
    <div className="factors">
      {FACTORS.map(([key, label, weight]) => (
        <div className="factor" key={key}>
          <div className="factor-label">
            <span>{label}</span>
            <span className="muted">
              weight {weight.toFixed(2)} · value {factors[key].toFixed(2)}
            </span>
          </div>
          <div className="track">
            <div className="fill" style={{ width: `${Math.round(factors[key] * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ReportForm({ onSubmitted }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    setError("");
    try {
      // Demo coordinates; real reports carry GPS / cell-tower location from the gateway.
      await api.submitReport({
        text,
        channel: "text",
        lat: 21.94 + (Math.random() - 0.5) * 0.08,
        lon: 88.85 + (Math.random() - 0.5) * 0.1,
      });
      setText("");
      onSubmitted();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3>Send a report</h3>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. Five people trapped on the rooftop, water rising fast"
        rows={2}
      />
      <button className="primary" disabled={busy || !text.trim()}>
        {busy ? "Processing…" : "Submit report"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function PacketForm({ onSubmitted }) {
  const [b64, setB64] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    if (e) e.preventDefault();
    if (!b64.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api.submitPacket(b64.trim());
      setB64("");
      onSubmitted();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3>LoRa / SMS 20B Packet Ingest</h3>
      <p className="muted small">
        Compact 20-byte packet (28 chars Base64) with CRC-16, geocell, and L/U/A flags.
      </p>
      <input
        type="text"
        value={b64}
        onChange={(e) => setB64(e.target.value)}
        placeholder="Paste 28-character Base64 packet..."
        maxLength={28}
        style={{ width: "100%", marginBottom: "8px", fontFamily: "monospace", padding: "6px" }}
      />
      <div className="row">
        <button className="primary" disabled={busy || b64.trim().length !== 28}>
          {busy ? "Verifying CRC & Ingesting…" : "Ingest Packet"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

const LANG_NAMES = { hi: "Hindi", en: "English", bn: "Bengali" };
const MAX_RECORD_SECONDS = 30;

function VoiceRecorder({ onSubmitted }) {
  const [state, setState] = useState("idle"); // idle | recording | processing
  const [lang, setLang] = useState("");
  const [secs, setSecs] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const recorder = useRef(null);
  const chunks = useRef([]);
  const timer = useRef(null);

  useEffect(() => () => clearInterval(timer.current), []);

  async function start() {
    setError("");
    setResult(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser cannot record audio. Open the dashboard at http://localhost:5173 in Chrome or Edge.");
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone access was blocked. Allow the microphone for this page and try again.");
      return;
    }
    chunks.current = [];
    const rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      clearInterval(timer.current);
      setState("processing");
      try {
        const blob = new Blob(chunks.current, { type: rec.mimeType || "audio/webm" });
        // Demo coordinates; real reports carry GPS / cell-tower location from the gateway.
        const out = await api.submitVoice(blob, {
          lat: 21.94 + (Math.random() - 0.5) * 0.08,
          lon: 88.85 + (Math.random() - 0.5) * 0.1,
          language: lang,
        });
        setResult(out);
        onSubmitted();
      } catch (e) {
        setError(e.message);
      } finally {
        setState("idle");
      }
    };
    recorder.current = rec;
    rec.start();
    setSecs(0);
    setState("recording");
    timer.current = setInterval(() => {
      setSecs((s) => {
        if (s + 1 >= MAX_RECORD_SECONDS) rec.state === "recording" && rec.stop();
        return s + 1;
      });
    }, 1000);
  }

  function stop() {
    if (recorder.current?.state === "recording") recorder.current.stop();
  }

  return (
    <div className="card">
      <h3>Send a voice report</h3>
      <p className="muted small">Speak in Hindi or English. The speech is transcribed on this computer, with no internet needed.</p>
      <div className="row wrap">
        {state !== "recording" ? (
          <button className="primary" disabled={state === "processing"} onClick={start}>
            {state === "processing" ? "Transcribing…" : "● Record"}
          </button>
        ) : (
          <button className="rec" onClick={stop}>
            ■ Stop ({secs}s)
          </button>
        )}
        <select value={lang} onChange={(e) => setLang(e.target.value)} disabled={state !== "idle"}>
          <option value="">Auto-detect language</option>
          <option value="hi">Hindi</option>
          <option value="en">English</option>
        </select>
      </div>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="heard">
          <div className="muted small">Heard ({LANG_NAMES[result.language] || result.language}):</div>
          <div className="heard-text">{result.transcript}</div>
          {result.language !== "en" && (
            <>
              <div className="muted small">Understood as (English):</div>
              <div className="heard-text">{result.english}</div>
            </>
          )}
          <div className="row">
            <TierBadge tier={result.incident.effective_tier} />
            <span className="muted small">
              {result.merged ? "merged into an existing incident" : "new incident"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ incidentId, onChanged }) {
  const [inc, setInc] = useState(null);
  const [note, setNote] = useState("");

  const load = useCallback(() => api.incident(incidentId).then(setInc), [incidentId]);
  useEffect(() => {
    setInc(null);
    load();
  }, [load]);

  if (!inc) return <div className="card muted">Loading…</div>;

  async function act(fn) {
    await fn();
    await load();
    onChanged();
  }

  return (
    <div className="card detail">
      <div className="row">
        <h3>Incident #{inc.id}</h3>
        <TierBadge tier={inc.effective_tier} />
        <span className="grow" />
        <span className="score" title="Base score from the weighted formula">
          {inc.score.toFixed(1)}
          <span className="muted small"> base score</span>
        </span>
      </div>
      <p className="lead">{inc.summary}</p>
      <p className="muted small">
        {inc.incident_type} · {inc.report_count} report(s) · ~{inc.people_estimate} people · {inc.status}
      </p>
      {inc.escalation && <p className="escalation">{inc.escalation}</p>}

      <h4>Why this ranking</h4>
      <FactorBars factors={inc.factors} />
      <p className="muted small">S = 100 · (0.40L + 0.20U + 0.15P + 0.15V + 0.10A), plus two escalation rules.</p>

      <h4>Responder decision</h4>
      <p className="muted small">AI tier: {inc.tier}. Overrides are logged to recalibrate the weights.</p>
      <div className="row wrap">
        {TIERS.map((t) => (
          <button
            key={t}
            className={`tier-btn tier-${t} ${inc.override_tier === t ? "active" : ""}`}
            onClick={() => act(() => api.override(inc.id, t, note))}
          >
            {t}
          </button>
        ))}
        {inc.override_tier && <button onClick={() => act(() => api.clearOverride(inc.id))}>Clear override</button>}
      </div>
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason for override (optional)" />

      <div className="row wrap">
        <button onClick={() => act(() => api.setStatus(inc.id, "dispatched"))}>Mark dispatched</button>
        <button onClick={() => act(() => api.setStatus(inc.id, "resolved"))}>Mark resolved</button>
      </div>

      <h4>Reports in this incident</h4>
      <ul className="reports">
        {inc.reports.map((r) => (
          <li key={r.id}>
            <span className="muted">[{r.channel}/{r.language}]</span> {r.translated_text}
            {r.needs_verification && <em className="muted"> · needs call-back</em>}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const [queue, setQueue] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    api
      .queue()
      .then((q) => {
        setQueue(q);
        setError("");
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [refresh]);

  async function run(fn) {
    setBusy(true);
    try {
      await fn();
      refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const select = useCallback((id) => setSelected(id), []);

  return (
    <div className="app">
      <header>
        <div>
          <h1>
            DisasterSignal<span className="dot">.</span>
          </h1>
          <p style={{ margin: "2px 0", color: "#e2e8f0", fontWeight: 500 }}>
            Every Voice Matters. Every Second Counts. Every Life Comes First.
          </p>
          <p className="muted small" style={{ margin: "2px 0" }}>
            RURALCONNECT 2026 · IEEE NATIONAL WORKSHOP · IIT KHARAGPUR · Offline-First Rural Emergency Prioritisation
          </p>
        </div>
        <div className="row" style={{ flexWrap: "wrap", gap: "8px" }}>
          <button className="primary" disabled={busy} onClick={() => run(api.loadPacketDemo)}>
            Load 6-Packet LoRa Demo
          </button>
          <button disabled={busy} onClick={() => run(api.loadDemo)}>
            Load flood scenario
          </button>
          <button
            disabled={busy}
            onClick={() =>
              run(async () => {
                await api.resetDemo();
                setSelected(null);
              })
            }
          >
            Reset
          </button>
        </div>
      </header>

      {error && <p className="error banner">Backend unreachable: {error}</p>}
      <Summary queue={queue} />

      <main>
        <section>
          <div className="card">
            <h3>Prioritised queue</h3>
            {queue.length === 0 && (
              <p className="muted">No open incidents. Press “Load flood scenario” or send a report.</p>
            )}
            <ol className="queue">
              {queue.map((i, idx) => (
                <li key={i.id} className={`${selected === i.id ? "selected" : ""} edge-${i.effective_tier}`} onClick={() => select(i.id)}>
                  <span className="rank">{idx + 1}</span>
                  <div className="grow">
                    <div className="row">
                      <TierBadge tier={i.effective_tier} />
                      <span className="score">{i.score.toFixed(1)}</span>
                      {i.override_tier && <span className="muted small">overridden</span>}
                      {i.escalation && <span className="muted small">rule-escalated</span>}
                      <span className="grow" />
                      <span className="muted small">
                        {i.report_count} report{i.report_count > 1 ? "s" : ""}
                      </span>
                    </div>
                    <div>{i.summary}</div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
          <PacketForm onSubmitted={refresh} />
          <VoiceRecorder onSubmitted={refresh} />
          <ReportForm onSubmitted={refresh} />
        </section>

        <section>
          <div className="card map-card">
            <MapView queue={queue} selected={selected} onSelect={select} />
            <p className="muted small">Pins are numbered by queue rank. Map tiles need internet; pins work offline.</p>
          </div>
          {selected ? (
            <Detail key={selected} incidentId={selected} onChanged={refresh} />
          ) : (
            <div className="card muted">Select an incident (or a map pin) to see why it ranked where it did.</div>
          )}
        </section>
      </main>
    </div>
  );
}
