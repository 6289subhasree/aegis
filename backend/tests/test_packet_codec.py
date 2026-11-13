import pytest
from app.services.packet_codec import (
    PacketReport,
    crc16_ccitt,
    decode_packet,
    encode_packet,
    packet_from_base64_sms,
    packet_to_base64_sms,
)


def test_packet_exact_length_20_bytes():
    report = PacketReport(
        version=1,
        channel="lora",
        language="bn",
        incident_type="rescue",
        people=5,
        lat=22.31,
        lon=87.92,
        timestamp=1762963200,
        node_id=101,
        flag_life=True,
        flag_urgency=True,
        flag_isolation=True,
        hop_count=2,
    )
    raw = encode_packet(report)
    assert len(raw) == 20


def test_packet_fits_in_28_character_base64_sms():
    report = PacketReport()
    raw = encode_packet(report)
    sms = packet_to_base64_sms(raw)
    assert len(sms) == 28
    decoded = packet_from_base64_sms(sms)
    assert decoded.version == report.version
    assert decoded.channel == report.channel
    assert decoded.people == report.people
    assert round(decoded.lat, 2) == round(report.lat, 2)
    assert round(decoded.lon, 2) == round(report.lon, 2)


def test_packet_encode_decode_roundtrip():
    original = PacketReport(
        version=1,
        channel="sms",
        language="hi",
        incident_type="flood",
        people=12,
        lat=21.94,
        lon=88.85,
        timestamp=1700000000,
        node_id=402,
        flag_life=True,
        flag_urgency=False,
        flag_isolation=True,
        hop_count=3,
    )
    raw = encode_packet(original)
    decoded = decode_packet(raw)

    assert decoded.version == original.version
    assert decoded.channel == original.channel
    assert decoded.language == original.language
    assert decoded.incident_type == original.incident_type
    assert decoded.people == original.people
    assert abs(decoded.lat - original.lat) < 0.001
    assert abs(decoded.lon - original.lon) < 0.001
    assert decoded.timestamp == original.timestamp
    assert decoded.node_id == original.node_id
    assert decoded.flag_life is True
    assert decoded.flag_urgency is False
    assert decoded.flag_isolation is True
    assert decoded.hop_count == 3


def test_crc_detects_every_single_bit_error():
    """Verify that flipping any single bit of the 160 bits raises a verification error."""
    original = PacketReport(
        version=1,
        channel="lora",
        language="bn",
        incident_type="rescue",
        people=5,
        lat=22.31,
        lon=87.92,
        timestamp=1762963200,
        node_id=101,
        flag_life=True,
        flag_urgency=True,
        flag_isolation=True,
        hop_count=1,
    )
    packet = bytearray(encode_packet(original))
    assert len(packet) == 20

    # Test all 160 bits (20 bytes * 8 bits)
    for byte_idx in range(20):
        for bit_idx in range(8):
            corrupted = bytearray(packet)
            corrupted[byte_idx] ^= (1 << bit_idx)

            # Must raise ValueError due to CRC mismatch
            with pytest.raises(ValueError):
                decode_packet(bytes(corrupted))
