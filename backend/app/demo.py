"""Demo flood scenario.

Reports are listed in the order they "arrive". The order is deliberately bad: minor reports come
first and the most dangerous ones come last, so a chronological queue would bury them. Locations
are illustrative coordinates in a coastal river-delta area; no real villages are named.

Nothing here is real disaster data.
"""

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .models import Incident, OverrideLog, Report
from .services.pipeline import process_report

SCENARIO: list[dict] = [
    {"text": "Water is entering our fields and the crops are going under.", "lat": 21.900, "lon": 88.800},
    {"text": "The road near the market is waterlogged, buses have stopped.", "lat": 21.970, "lon": 88.900},
    {"text": "Floodwater entering the fields, crops are under water.", "lat": 21.905, "lon": 88.805},
    {"text": "The bridge has collapsed. Our village is cut off, no road and no network.", "lat": 21.930, "lon": 88.840},
    {"text": "No drinking water in the relief camp since yesterday.", "lat": 21.915, "lon": 88.820},
    {"text": "Bridge collapsed, village cut off, we cannot leave.", "lat": 21.931, "lon": 88.842},
    {"text": "Pregnant woman needs an ambulance, cannot reach the hospital, road is cut off.", "lat": 21.920, "lon": 88.830},
    {"text": "Embankment has breached, water rising fast near the primary school, children inside.", "lat": 21.960, "lon": 88.870},
    {"text": "Elderly woman and two children trapped on the rooftop, water rising fast, help now.", "lat": 21.940, "lon": 88.860},
    {"text": "Five people stuck on our roof, water rising fast, please send a boat.", "lat": 21.941, "lon": 88.861},
]


def load_scenario(db: Session) -> dict:
    created_incidents: set[int] = set()
    for item in SCENARIO:
        _, incident = process_report(db, item["text"], "text", "en", item["lat"], item["lon"])
        created_incidents.add(incident.id)
    return {"reports": len(SCENARIO), "incidents": len(created_incidents)}


def reset_all(db: Session) -> None:
    db.execute(delete(OverrideLog))
    db.execute(delete(Report))
    db.execute(delete(Incident))
    db.commit()
