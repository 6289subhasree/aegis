from datetime import datetime, timedelta, timezone

from app.models import Incident
from app.services.dedup import cosine, find_matching_incident, haversine_km, update_centroid
from app.services.embeddings import HashingEmbedder

emb = HashingEmbedder()
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def make_incident(text, lat=22.57, lon=88.36, age_h=0.5, status="open"):
    return Incident(
        id=1,
        centroid=emb.embed(text),
        lat=lat,
        lon=lon,
        status=status,
        updated_at=NOW - timedelta(hours=age_h),
    )


def test_haversine_known_distance():
    # Kolkata to Kharagpur is roughly 115 km
    d = haversine_km(22.5726, 88.3639, 22.3460, 87.2320)
    assert 110 < d < 125


def test_similar_nearby_recent_reports_merge():
    inc = make_incident("five people trapped on the roof, flood water rising")
    v = emb.embed("5 people stuck on rooftop, water rising fast")
    assert find_matching_incident([inc], v, 22.571, 88.361, now=NOW) is inc


def test_far_away_report_does_not_merge():
    inc = make_incident("five people trapped on the roof, flood water rising")
    v = emb.embed("5 people stuck on rooftop, water rising fast")
    assert find_matching_incident([inc], v, 22.9, 88.9, now=NOW) is None


def test_old_incident_does_not_merge():
    inc = make_incident("five people trapped on the roof, flood water rising", age_h=10)
    v = emb.embed("five people trapped on the roof, flood water rising")
    assert find_matching_incident([inc], v, 22.57, 88.36, now=NOW) is None


def test_unrelated_text_does_not_merge():
    inc = make_incident("five people trapped on the roof, flood water rising")
    v = emb.embed("bridge has collapsed, village road cut off")
    assert find_matching_incident([inc], v, 22.57, 88.36, now=NOW) is None


def test_resolved_incident_is_ignored():
    inc = make_incident("five people trapped on the roof", status="resolved")
    v = emb.embed("five people trapped on the roof")
    assert find_matching_incident([inc], v, 22.57, 88.36, now=NOW) is None


def test_missing_location_falls_back_to_semantic_only():
    inc = make_incident("five people trapped on the roof, flood water rising", lat=None, lon=None)
    v = emb.embed("five people trapped on the roof, flood water rising")
    assert find_matching_incident([inc], v, None, None, now=NOW) is inc


def test_centroid_running_mean():
    assert update_centroid(None, 0, [1.0, 0.0]) == [1.0, 0.0]
    assert update_centroid([1.0, 0.0], 1, [0.0, 1.0]) == [0.5, 0.5]
    assert cosine([1, 0], [0, 1]) == 0.0
