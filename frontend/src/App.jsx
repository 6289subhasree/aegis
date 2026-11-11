import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";

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

function FactorBars({ factors }) {
  return (
    <div className="factors">
      {FACTORS.map(([key, label, weight]) => (
        <div className="factor" key={key}>
          <div className="factor-label">
            <span>{label}</span>
            <span className="muted">w {weight.toFixed(2)} · {factors[key].toFixed(2)}</span>
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
      await api.submitReport({ text, channel: "text", lat: 22.57, lon: 88.36 });
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
      <h3>Simulate an incoming report</h3>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. Five people trapped on the rooftop, water rising fast"
        rows={3}
      />
      <button disabled={busy || !text.trim()}>{busy ? "Processing…" : "Submit report"}</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function Detail({ incidentId, onChanged }) {
  const [inc, setInc] = useState(null);
  const [note, setNote] = useState("");

  const load = useCallback(() => api.incident(incidentId).then(setInc), [incidentId]);
  useEffect(() => {
    load();
  }, [load]);

  if (!inc) return <div className="card">Loading…</div>;

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
        <span className="score">{inc.score.toFixed(1)}</span>
      </div>
      <p>{inc.summary}</p>
      <p className="muted">
        {inc.incident_type} · {inc.report_count} report(s) · ~{inc.people_estimate} people · {inc.status}
      </p>

      <h4>Why this score</h4>
      <FactorBars factors={inc.factors} />
      <p className="muted small">
        S = 100 · (0.40L + 0.20U + 0.15P + 0.15V + 0.10A). L &gt; 0.8 escalates to CRITICAL.
      </p>

      <h4>Responder override</h4>
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
        {inc.override_tier && <button onClick={() => act(() => api.clearOverride(inc.id))}>Clear</button>}
      </div>
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason (optional)" />

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

  const refresh = useCallback(() => {
    api.queue().then(setQueue).then(() => setError("")).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <div className="app">
      <header>
        <h1>Aegis</h1>
        <p>Severity-first emergency queue. Not arrival order.</p>
      </header>
      {error && <p className="error">Backend unreachable: {error}</p>}
      <main>
        <section>
          <ReportForm onSubmitted={refresh} />
          <div className="card">
            <h3>Prioritised queue ({queue.length})</h3>
            {queue.length === 0 && <p className="muted">No open incidents.</p>}
            <ol className="queue">
              {queue.map((i, idx) => (
                <li
                  key={i.id}
                  className={selected === i.id ? "selected" : ""}
                  onClick={() => setSelected(i.id)}
                >
                  <span className="rank">{idx + 1}</span>
                  <div className="grow">
                    <div className="row">
                      <TierBadge tier={i.effective_tier} />
                      <span className="score">{i.score.toFixed(1)}</span>
                      {i.override_tier && <span className="muted small">overridden</span>}
                    </div>
                    <div>{i.summary}</div>
                    <div className="muted small">
                      {i.report_count} report(s) · {i.incident_type}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>
        <section>
          {selected ? (
            <Detail incidentId={selected} onChanged={refresh} />
          ) : (
            <div className="card muted">Select an incident to see its score breakdown.</div>
          )}
          <div className="card muted small">Map view (Leaflet + OpenStreetMap) is on the roadmap.</div>
        </section>
      </main>
    </div>
  );
}
