from app import demo


def test_load_scenario_ranks_severity_not_arrival(client):
    r = client.post("/demo/load")
    assert r.status_code == 200
    body = r.json()
    assert body["reports"] == len(demo.SCENARIO)
    assert body["incidents"] < body["reports"]  # duplicates were merged

    queue = client.get("/incidents").json()
    assert len(queue) == body["incidents"]

    tiers = [i["effective_tier"] for i in queue]
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert tiers == sorted(tiers, key=order.index), "queue must be tier-ordered"

    # the first-arriving reports were minor; the top of the queue must not be one of them
    first_report = demo.SCENARIO[0]["text"][:30].lower()
    assert first_report not in queue[0]["summary"].lower()
    assert queue[0]["effective_tier"] == "CRITICAL"

    summaries = " ".join(i["summary"].lower() for i in queue if i["effective_tier"] == "CRITICAL")
    assert "roof" in summaries


def test_bridge_collapse_is_high_and_explained(client):
    client.post("/demo/load")
    queue = client.get("/incidents").json()
    bridge = next(i for i in queue if "bridge" in i["summary"].lower())
    assert bridge["tier"] == "HIGH"
    assert bridge["escalation"] and "isolated" in bridge["escalation"]
    assert bridge["report_count"] == 2


def test_reset_clears_everything(client):
    client.post("/demo/load")
    assert client.post("/demo/reset").json() == {"status": "cleared"}
    assert client.get("/incidents").json() == []


def test_demo_endpoints_can_be_disabled(client, monkeypatch):
    from app.config import Settings
    from app.api import demo as demo_api

    monkeypatch.setattr(demo_api, "get_settings", lambda: Settings(demo_mode=False))
    assert client.post("/demo/load").status_code == 404
    assert client.post("/demo/reset").status_code == 404
