"""
Natural Language Query Parser for Graph Trip Planner.
Rule-based NLP extractor without any external paid AI API.
"""

import re
from typing import Dict, Any


def parse_natural_language_query(text: str) -> Dict[str, Any]:
    """
    Zero-cost rule-based extractor to understand queries like:
    'I'm in Bengaluru with Rs 1500 and 10 hours. Where can I go for a beach + trek trip?'
    """
    res = {
        "start_city": "Bengaluru",
        "budget": 2000,
        "max_hours": 12.0,
        "interests": [],
        "max_legs": 2,
    }

    # Extract City
    cities_known = [
        "Bengaluru", "Mysuru", "Mangaluru", "Gokarna", "Chikmagalur",
        "Hampi", "Coorg", "Ooty", "Chennai", "Pondicherry",
        "Madurai", "Kodaikanal", "Wayanad", "Kochi", "Munnar"
    ]
    for c in cities_known:
        if re.search(rf"\b{c}\b", text, re.IGNORECASE):
            res["start_city"] = c
            break

    # Extract Budget: Rs 1500, ₹1500, 1500 rs, budget 1500, etc.
    budget_match = re.search(r"(?:rs\.?|₹|budget(?:\s*of)?)\s*(\d+)", text, re.IGNORECASE)
    if not budget_match:
        budget_match = re.search(r"(\d+)\s*(?:rs|rupees|inr)", text, re.IGNORECASE)
    if budget_match:
        res["budget"] = int(budget_match.group(1))

    # Extract Hours: 10 hours, 8 hrs, 10h
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h)\b", text, re.IGNORECASE)
    if hours_match:
        res["max_hours"] = float(hours_match.group(1))

    # Extract Interests / Tags
    all_tags = ["beach", "trek", "temple", "food", "nature", "heritage", "nightlife"]
    for tag in all_tags:
        if re.search(rf"\b{tag}s?\b", text, re.IGNORECASE):
            res["interests"].append(tag)

    # Extract Legs
    if re.search(r"\b1\s*leg\b", text, re.IGNORECASE):
        res["max_legs"] = 1
    elif re.search(r"\b2\s*legs?\b", text, re.IGNORECASE):
        res["max_legs"] = 2

    return res
