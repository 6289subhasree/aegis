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
  setStatus: (id, status) =>
    request(`/incidents/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }),
};
