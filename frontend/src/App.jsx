import { useCallback, useEffect, useState } from "react";
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
            Aegis<span className="dot">.</span>
          </h1>
          <p>Severity-first emergency queue. The most dangerous incident is first, not the earliest.</p>
        </div>
        <div className="row">
          <button className="primary" disabled={busy} onClick={() => run(api.loadDemo)}>
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
