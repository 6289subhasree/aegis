"""Demo flood scenario.

Reports are listed in the order they "arrive". The order is deliberately bad: minor reports come
first and the most dangerous ones come last, so a chronological queue would bury them. Locations
are illustrative coordinates in a coastal river-delta area; no real villages are named.

Nothing here is real disaster data.
"""

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .models import Incident, OverrideLog, Report
from .services.packet_codec import PacketReport, encode_packet, packet_to_base64_sms
from .services.pipeline import process_packet_report, process_report

PACKET_SCENARIO: list[PacketReport] = [
    # Arrival #1: Routine farmland flooding (L=0, U=0, A=0) -> LOW
    PacketReport(
        version=1, channel="lora", language="en", incident_type="flood",
        people=0, lat=21.900, lon=88.800, timestamp=1762963320, node_id=101,
        flag_life=False, flag_urgency=False, flag_isolation=False, hop_count=1,
    ),
    # Arrival #2: Road waterlogged/muddy (L=0, U=0, A=0) -> LOW
    PacketReport(
        version=1, channel="sms", language="en", incident_type="other",
        people=0, lat=21.970, lon=88.900, timestamp=1762963440, node_id=102,
        flag_life=False, flag_urgency=False, flag_isolation=False, hop_count=0,
    ),
    # Arrival #3: Farmland flooding duplicate (L=0, U=0, A=0) -> Merges with #1
    PacketReport(
        version=1, channel="lora", language="bn", incident_type="flood",
        people=0, lat=21.905, lon=88.805, timestamp=1762963620, node_id=103,
        flag_life=False, flag_urgency=False, flag_isolation=False, hop_count=2,
    ),
    # Arrival #4: Bridge collapsed & village cut off (L=0, U=1, A=1) -> Escalates to HIGH (Score ~72)
    PacketReport(
        version=1, channel="sms", language="bn", incident_type="collapse",
        people=25, lat=21.930, lon=88.840, timestamp=1762963500, node_id=104,
        flag_life=False, flag_urgency=True, flag_isolation=True, hop_count=1,
    ),
    # Arrival #5: LIFE THREAT - Rooftop entrapment (L=1, U=1, A=1) -> CRITICAL
    PacketReport(
        version=1, channel="lora", language="hi", incident_type="rescue",
        people=3, lat=21.940, lon=88.860, timestamp=1762963740, node_id=105,
        flag_life=True, flag_urgency=True, flag_isolation=True, hop_count=1,
    ),
    # Arrival #6: LIFE THREAT - Corroborating rooftop rescue (L=1, U=1, A=1) -> Merges & reaches Score 91!
    PacketReport(
        version=1, channel="lora", language="bn", incident_type="rescue",
        people=5, lat=21.941, lon=88.861, timestamp=1762963745, node_id=106,
        flag_life=True, flag_urgency=True, flag_isolation=True, hop_count=2,
    ),
]


def load_packet_scenario(db: Session) -> dict:
    """Execute the 6-packet demo described on Poster Section 06.

    Six packets arrive in bad order; the two life-threat packets (5th and 6th to arrive)
    are verified, clustered, and immediately leapfrog to Rank #1 and #2.
    """
    created_incidents: set[int] = set()
    encoded_packets = []
    for pkt in PACKET_SCENARIO:
        raw = encode_packet(pkt)
        encoded_packets.append(packet_to_base64_sms(raw))
        _, incident = process_packet_report(db, pkt)
        created_incidents.add(incident.id)

    return {
        "packets": len(PACKET_SCENARIO),
        "incidents": len(created_incidents),
        "base64_packets": encoded_packets,
    }


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
