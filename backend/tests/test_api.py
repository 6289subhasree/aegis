LOC = {"lat": 22.57, "lon": 88.36}


def post(client, text, **kw):
    return client.post("/reports", json={"text": text, **LOC, **kw})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_queue_is_severity_first_not_arrival_order(client):
    """The headline behaviour: the rooftop rescue arrives LAST but ranks FIRST."""
    post(client, "Floodwater is entering the farmland, minor so far", lat=22.50, lon=88.10)
    post(client, "The bridge has collapsed, our village is cut off", lat=22.60, lon=88.50)
    post(client, "Five people trapped on the rooftop, water rising fast, help now", lat=22.57, lon=88.36)

    queue = client.get("/incidents").json()
    assert len(queue) == 3
    assert queue[0]["tier"] == "CRITICAL"
    assert "rooftop" in queue[0]["summary"].lower()
    assert queue[0]["score"] >= queue[1]["score"] >= queue[2]["score"]


def test_duplicate_reports_merge_and_raise_verification(client):
    first = post(client, "Five people trapped on the rooftop, water rising fast").json()
    second = post(client, "5 people stuck on rooftop, water rising fast, please help").json()
    assert first["merged"] is False
    assert second["merged"] is True
    assert second["incident"]["id"] == first["incident"]["id"]
    assert second["incident"]["report_count"] == 2
    assert second["incident"]["factors"]["verification"] > 0
    assert len(client.get("/incidents").json()) == 1


def test_override_is_applied_and_logged(client):
    inc = post(client, "Floodwater is entering the farmland, minor so far").json()["incident"]
    assert inc["tier"] in ("LOW", "MEDIUM")
    r = client.post(f"/incidents/{inc['id']}/override", json={"tier": "CRITICAL", "note": "school nearby"})
    assert r.status_code == 200
    body = r.json()
    assert body["effective_tier"] == "CRITICAL"
    assert body["tier"] == inc["tier"]  # the AI score itself is preserved
    assert client.delete(f"/incidents/{inc['id']}/override").json()["effective_tier"] == inc["tier"]


def test_resolved_incidents_leave_the_queue(client):
    inc = post(client, "Five people trapped on the rooftop").json()["incident"]
    client.post(f"/incidents/{inc['id']}/status", json={"status": "resolved"})
    assert client.get("/incidents").json() == []
    assert len(client.get("/incidents?include_resolved=true").json()) == 1


def test_unknown_incident_404(client):
    assert client.get("/incidents/999").status_code == 404


def test_validation(client):
    assert client.post("/reports", json={"text": ""}).status_code == 422
    assert client.post("/reports", json={"text": "help", "lat": 123}).status_code == 422


def test_voice_without_stt_backend_is_501(client):
    r = client.post("/reports/voice", files={"audio": ("a.wav", b"RIFF", "audio/wav")})
    assert r.status_code == 501
