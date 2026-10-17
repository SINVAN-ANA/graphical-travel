"""
Unit tests for Graph Trip Planner
Verifies dataset integrity, route definitions, and the natural language rule-based parser.
"""

from query_parser import parse_natural_language_query
from load_data import CITIES, ATTRACTIONS, TAGS, ROUTES


def test_data_integrity():
    # 1. South India Cities
    assert len(CITIES) >= 15, f"Expected at least 15 cities, found {len(CITIES)}"
    city_names = {c["name"] for c in CITIES}

    # 2. Curated Attractions
    assert len(ATTRACTIONS) >= 37, f"Expected at least 37 attractions, found {len(ATTRACTIONS)}"
    valid_tags = set(TAGS)

    for att in ATTRACTIONS:
        assert att["city"] in city_names, f"Attraction {att['name']} has invalid city {att['city']}"
        assert att["cost"] >= 0, f"Attraction {att['name']} has negative cost"
        for t in att["tags"]:
            assert t in valid_tags, f"Attraction {att['name']} has unknown tag {t}"

    # 3. Routes
    assert len(ROUTES) >= 28, f"Expected at least 28 routes, found {len(ROUTES)}"
    for r in ROUTES:
        assert r["from"] in city_names, f"Route from {r['from']} invalid"
        assert r["to"] in city_names, f"Route to {r['to']} invalid"
        assert r["hours"] > 0, f"Route hours must be positive"
        assert r["cost"] > 0, f"Route cost must be positive"
        assert r["mode"] in ["Bus", "Train"], f"Unknown mode {r['mode']}"

    print("✅ Dataset integrity verified: 15 cities, 37 attractions, 28 routes.")


def test_natural_language_parser():
    # Query 1
    q1 = "I'm in Bengaluru with Rs 1500 and 10 hours. Where can I go for a beach + trek trip?"
    p1 = parse_natural_language_query(q1)
    assert p1["start_city"] == "Bengaluru"
    assert p1["budget"] == 1500
    assert p1["max_hours"] == 10.0
    assert "beach" in p1["interests"]
    assert "trek" in p1["interests"]

    # Query 2
    q2 = "Bengaluru + trek + nature, budget Rs 1000, 8 hours"
    p2 = parse_natural_language_query(q2)
    assert p2["start_city"] == "Bengaluru"
    assert p2["budget"] == 1000
    assert p2["max_hours"] == 8.0
    assert "trek" in p2["interests"]
    assert "nature" in p2["interests"]

    # Query 3
    q3 = "Bengaluru + temple + heritage, 2 legs"
    p3 = parse_natural_language_query(q3)
    assert p3["start_city"] == "Bengaluru"
    assert p3["max_legs"] == 2
    assert "temple" in p3["interests"]
    assert "heritage" in p3["interests"]

    print("✅ All 3 canonical demo script queries successfully parsed!")


if __name__ == "__main__":
    test_data_integrity()
    test_natural_language_parser()
