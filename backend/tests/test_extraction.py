from app.services.extraction import extract, extract_people


def test_rooftop_rescue_is_high_life_threat():
    e = extract("Five people trapped on a rooftop, water rising fast, please help")
    assert e.incident_type == "rescue"
    assert e.people == 5
    assert e.life >= 0.9
    assert e.urgency > 0.5


def test_bridge_collapse_is_isolation_not_life():
    e = extract("The bridge has collapsed, our village is cut off")
    assert e.incident_type == "infrastructure"
    assert e.isolation == 1.0
    assert e.life < 0.5


def test_farmland_flooding_is_low_signal():
    e = extract("Floodwater is entering the farmland, minor so far")
    assert e.incident_type == "flood"
    assert e.life == 0.0
    assert e.urgency == 0.0


def test_people_counts():
    assert extract_people("12 people on the roof") == 12
    assert extract_people("three children are missing") == 3
    assert extract_people("2 families stranded") == 8
    assert extract_people("water everywhere") == 0
