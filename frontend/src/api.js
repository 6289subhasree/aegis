const BASE = "/api";

async function request(path, options) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  queue: () => request("/incidents"),
  incident: (id) => request(`/incidents/${id}`),
  submitReport: (body) => request("/reports", { method: "POST", body: JSON.stringify(body) }),
  override: (id, tier, note) =>
    request(`/incidents/${id}/override`, { method: "POST", body: JSON.stringify({ tier, note }) }),
  clearOverride: (id) => request(`/incidents/${id}/override`, { method: "DELETE" }),
  submitVoice: async (blob, { lat, lon, language }) => {
    const form = new FormData();
    form.append("audio", blob, "report.webm");
    if (lat != null) form.append("lat", lat);
    if (lon != null) form.append("lon", lon);
    if (language) form.append("language", language);
    const res = await fetch(`${BASE}/reports/voice`, { method: "POST", body: form });
    if (!res.ok) {
      let detail = await res.text();
      try {
        detail = JSON.parse(detail).detail ?? detail;
      } catch {
        /* keep raw text */
      }
      throw new Error(detail);
    }
    return res.json();
  },
  loadDemo: () => request("/demo/load", { method: "POST" }),
  resetDemo: () => request("/demo/reset", { method: "POST" }),
  setStatus: (id, status) =>
    request(`/incidents/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }),
};
