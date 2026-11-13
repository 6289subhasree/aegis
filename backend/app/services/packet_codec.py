"""Compact 20-Byte Emergency Report Packet Codec (DisasterSignal).

As specified in Poster Section 05:
    byte 0: ver 1 bit · chan 2 bits · lang 5 bits
    | ver·chan·lang | type | people | geo-cell | time | node | flags | CRC |
    | 1 B           | 1 B  | 1 B    | 6 B      | 4 B  | 4 B  | 1 B   | 2 B |

Flags (Byte 17):
    bit 0 = L (threat to life) -> forwarded first
    bit 1 = U (urgency)
    bit 2 = A (isolation)
    bits 3-4 = reserved (0)
    bits 5-7 = hop count (0..7)

CRC-16 (Bytes 18-19):
    Detects every single-bit error across the 18 payload bytes.
    Fits in 20 bytes total (one LoRa SF9 frame) and 28 characters Base64 (single SMS).
"""

from __future__ import annotations

import base64
import struct
from dataclasses import dataclass

CHANNELS = ["voice", "sms", "app", "lora"]
CHANNEL_TO_ID = {c: i for i, c in enumerate(CHANNELS)}

# 22 Scheduled Indian Languages + English
LANGUAGES = [
    "en", "hi", "bn", "te", "mr", "ta", "ur", "gu",
    "kn", "ml", "or", "pa", "as", "mai", "sat", "ks",
    "ne", "kok", "sd", "doi", "mni", "brx", "sa"
]
LANG_TO_ID = {lang: idx for idx, lang in enumerate(LANGUAGES)}

INCIDENT_TYPES = ["other", "flood", "collapse", "rescue", "medical", "supplies"]
TYPE_TO_ID = {t: idx for idx, t in enumerate(INCIDENT_TYPES)}


def crc16_ccitt(data: bytes) -> int:
    """CRC-16-CCITT (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


@dataclass
class PacketReport:
    version: int = 1
    channel: str = "lora"  # 'voice', 'sms', 'app', 'lora'
    language: str = "bn"
    incident_type: str = "rescue"
    people: int = 5
    lat: float = 22.31
    lon: float = 87.92
    timestamp: int = 1762963200
    node_id: int = 101
    flag_life: bool = True
    flag_urgency: bool = True
    flag_isolation: bool = True
    hop_count: int = 0


def _encode_geocell(lat: float, lon: float) -> bytes:
    """Encode latitude and longitude into 6 bytes (3 bytes lat, 3 bytes lon).

    Yields sub-meter resolution globally:
    lat in [-90, +90] mapped to uint24 [0, 2^24 - 1]
    lon in [-180, +180] mapped to uint24 [0, 2^24 - 1]
    """
    clamped_lat = max(-90.0, min(90.0, lat))
    clamped_lon = max(-180.0, min(180.0, lon))
    lat_val = round(((clamped_lat + 90.0) / 180.0) * 0xFFFFFF)
    lon_val = round(((clamped_lon + 180.0) / 360.0) * 0xFFFFFF)
    return struct.pack(">I", lat_val)[1:] + struct.pack(">I", lon_val)[1:]


def _decode_geocell(b: bytes) -> tuple[float, float]:
    lat_raw = struct.unpack(">I", b"\x00" + b[0:3])[0]
    lon_raw = struct.unpack(">I", b"\x00" + b[3:6])[0]
    lat = round((lat_raw / 0xFFFFFF) * 180.0 - 90.0, 5)
    lon = round((lon_raw / 0xFFFFFF) * 360.0 - 180.0, 5)
    return lat, lon


def encode_packet(p: PacketReport) -> bytes:
    """Encode a PacketReport into exactly 20 bytes with CRC-16."""
    ver = p.version & 0x01
    chan_id = CHANNEL_TO_ID.get(p.channel, 3) & 0x03
    lang_id = LANG_TO_ID.get(p.language, 0) & 0x1F
    byte0 = (ver << 7) | (chan_id << 5) | lang_id

    type_id = TYPE_TO_ID.get(p.incident_type, 0) & 0xFF
    people_count = max(0, min(255, p.people)) & 0xFF

    geocell = _encode_geocell(p.lat, p.lon)  # 6 bytes

    ts = p.timestamp & 0xFFFFFFFF
    node = p.node_id & 0xFFFFFFFF

    flag_byte = 0
    if p.flag_life:
        flag_byte |= 0x01  # bit 0: L (threat to life)
    if p.flag_urgency:
        flag_byte |= 0x02  # bit 1: U (urgency)
    if p.flag_isolation:
        flag_byte |= 0x04  # bit 2: A (isolation)
    flag_byte |= (p.hop_count & 0x07) << 5  # bits 5-7: hop count

    payload = struct.pack(
        ">BBB6sIIB",
        byte0,
        type_id,
        people_count,
        geocell,
        ts,
        node,
        flag_byte,
    )
    assert len(payload) == 18, f"Payload must be 18 bytes, got {len(payload)}"

    crc = crc16_ccitt(payload)
    packet = payload + struct.pack(">H", crc)
    assert len(packet) == 20, f"Packet must be exactly 20 bytes, got {len(packet)}"
    return packet


def decode_packet(packet: bytes) -> PacketReport:
    """Decode 20-byte packet and verify CRC. Raises ValueError on corruption."""
    if len(packet) != 20:
        raise ValueError(f"Packet must be 20 bytes, got {len(packet)}")

    payload = packet[:18]
    expected_crc = struct.unpack(">H", packet[18:20])[0]
    actual_crc = crc16_ccitt(payload)

    if actual_crc != expected_crc:
        raise ValueError(f"CRC verification failed: expected {expected_crc:#04x}, got {actual_crc:#04x}")

    byte0, type_id, people_count, geocell, ts, node, flag_byte = struct.unpack(">BBB6sIIB", payload)

    ver = (byte0 >> 7) & 0x01
    chan_id = (byte0 >> 5) & 0x03
    lang_id = byte0 & 0x1F

    channel = CHANNELS[chan_id] if chan_id < len(CHANNELS) else "lora"
    language = LANGUAGES[lang_id] if lang_id < len(LANGUAGES) else "en"
    incident_type = INCIDENT_TYPES[type_id] if type_id < len(INCIDENT_TYPES) else "other"

    lat, lon = _decode_geocell(geocell)

    flag_life = bool(flag_byte & 0x01)
    flag_urgency = bool(flag_byte & 0x02)
    flag_isolation = bool(flag_byte & 0x04)
    hop_count = (flag_byte >> 5) & 0x07

    return PacketReport(
        version=ver,
        channel=channel,
        language=language,
        incident_type=incident_type,
        people=people_count,
        lat=lat,
        lon=lon,
        timestamp=ts,
        node_id=node,
        flag_life=flag_life,
        flag_urgency=flag_urgency,
        flag_isolation=flag_isolation,
        hop_count=hop_count,
    )


def packet_to_base64_sms(packet: bytes) -> str:
    """Convert 20-byte packet to 28-character Base64 string for SMS."""
    if len(packet) != 20:
        raise ValueError(f"Packet must be 20 bytes, got {len(packet)}")
    encoded = base64.b64encode(packet).decode("ascii")
    assert len(encoded) == 28, f"Expected 28 chars, got {len(encoded)}"
    return encoded


def packet_from_base64_sms(sms_text: str) -> PacketReport:
    """Decode a 28-character Base64 SMS into a PacketReport."""
    clean_text = sms_text.strip()
    raw = base64.b64decode(clean_text)
    return decode_packet(raw)
