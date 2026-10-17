"""
Graph Trip Planner - Database Seeder (Person A)
Neo4j Graph Builder: Build Sprint Bengaluru

Loads:
- 15 South India Cities
- 37 Curated Attractions with Tags & Costs
- 28 Bidirectional Travel Routes (Bus & Train) with Hours and Cost
- 7 Category Tags: beach, trek, temple, food, nature, heritage, nightlife
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ==============================================================================
# 🔑 PERSON A: PASTE YOUR AURADB CREDENTIALS HERE (OR IN .env)
CONFIG_URI = os.getenv("NEO4J_URI", "")
CONFIG_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
CONFIG_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
CONFIG_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# --- 1. DATA DEFINITIONS ---

CITIES = [
    {"name": "Bengaluru", "state": "Karnataka"},
    {"name": "Mysuru", "state": "Karnataka"},
    {"name": "Mangaluru", "state": "Karnataka"},
    {"name": "Gokarna", "state": "Karnataka"},
    {"name": "Chikmagalur", "state": "Karnataka"},
    {"name": "Hampi", "state": "Karnataka"},
    {"name": "Coorg", "state": "Karnataka"},
    {"name": "Ooty", "state": "Tamil Nadu"},
    {"name": "Chennai", "state": "Tamil Nadu"},
    {"name": "Pondicherry", "state": "Puducherry"},
    {"name": "Madurai", "state": "Tamil Nadu"},
    {"name": "Kodaikanal", "state": "Tamil Nadu"},
    {"name": "Wayanad", "state": "Kerala"},
    {"name": "Kochi", "state": "Kerala"},
    {"name": "Munnar", "state": "Kerala"},
    {"name": "Udupi", "state": "Karnataka"},
    {"name": "Malpe", "state": "Karnataka"},
    {"name": "Kundapura", "state": "Karnataka"},
    {"name": "Maravanthe", "state": "Karnataka"},
]

TAGS = ["beach", "trek", "temple", "food", "nature", "heritage", "nightlife"]

ATTRACTIONS = [
    # Bengaluru
    {"name": "Cubbon Park", "city": "Bengaluru", "cost": 0, "tags": ["nature"]},
    {"name": "Bangalore Palace", "city": "Bengaluru", "cost": 250, "tags": ["heritage"]},
    {"name": "VV Puram Food Street", "city": "Bengaluru", "cost": 150, "tags": ["food"]},

    # Mysuru
    {"name": "Mysore Palace", "city": "Mysuru", "cost": 100, "tags": ["heritage"]},
    {"name": "Chamundeshwari Temple", "city": "Mysuru", "cost": 0, "tags": ["temple", "heritage"]},
    {"name": "Ranganathittu Bird Sanctuary", "city": "Mysuru", "cost": 100, "tags": ["nature"]},

    # Mangaluru
    {"name": "Panambur Beach", "city": "Mangaluru", "cost": 0, "tags": ["beach"]},
    {"name": "Mangaladevi Temple", "city": "Mangaluru", "cost": 20, "tags": ["temple"]},
    {"name": "Giri Manja's Seafood", "city": "Mangaluru", "cost": 300, "tags": ["food"]},

    # Gokarna
    {"name": "Gokarna Main Beach", "city": "Gokarna", "cost": 0, "tags": ["beach"]},
    {"name": "Mirjan Fort", "city": "Gokarna", "cost": 80, "tags": ["heritage", "nature"]},
    {"name": "Om Beach", "city": "Gokarna", "cost": 0, "tags": ["beach", "trek", "nature"]},

    # Coastal Karnataka: Udupi, Malpe, Kundapura, Maravanthe
    {"name": "Sri Krishna Temple", "city": "Udupi", "cost": 0, "tags": ["temple", "heritage"]},
    {"name": "Manipal Lake", "city": "Udupi", "cost": 0, "tags": ["nature"]},
    {"name": "Malpe Beach", "city": "Malpe", "cost": 0, "tags": ["beach"]},
    {"name": "Coastal Ecology Park", "city": "Malpe", "cost": 100, "tags": ["nature"]},
    {"name": "Kodi Estuary", "city": "Kundapura", "cost": 0, "tags": ["nature"]},
    {"name": "Maravanthe Beach", "city": "Maravanthe", "cost": 0, "tags": ["beach"]},

    # Chikmagalur (13-15)
    {"name": "Mullayanagiri Peak", "city": "Chikmagalur", "cost": 0, "tags": ["trek", "nature"]},
    {"name": "Baba Budangiri", "city": "Chikmagalur", "cost": 0, "tags": ["trek", "heritage", "nature"]},
    {"name": "Coffee Estate Walk", "city": "Chikmagalur", "cost": 150, "tags": ["nature", "food"]},

    # Hampi (16-18)
    {"name": "Virupaksha Temple", "city": "Hampi", "cost": 50, "tags": ["temple", "heritage"]},
    {"name": "Vijaya Vittala Stone Chariot", "city": "Hampi", "cost": 40, "tags": ["heritage"]},
    {"name": "Matanga Hill Sunrise", "city": "Hampi", "cost": 0, "tags": ["trek", "nature"]},

    # Coorg (19-21)
    {"name": "Abbey Falls", "city": "Coorg", "cost": 50, "tags": ["nature"]},
    {"name": "Tadiandamol Peak", "city": "Coorg", "cost": 100, "tags": ["trek", "nature"]},
    {"name": "Namdroling Golden Temple", "city": "Coorg", "cost": 0, "tags": ["temple", "heritage"]},

    # Ooty (22-23)
    {"name": "Doddabetta Peak Trek", "city": "Ooty", "cost": 30, "tags": ["trek", "nature"]},
    {"name": "Nilgiri Mountain Railway", "city": "Ooty", "cost": 200, "tags": ["heritage", "nature"]},

    # Chennai (24-26)
    {"name": "Marina Beach", "city": "Chennai", "cost": 0, "tags": ["beach", "food"]},
    {"name": "Kapaleeshwarar Temple", "city": "Chennai", "cost": 0, "tags": ["temple", "heritage"]},
    {"name": "Fort St. George", "city": "Chennai", "cost": 50, "tags": ["heritage"]},

    # Pondicherry (27-29)
    {"name": "Promenade Beach & French Quarter", "city": "Pondicherry", "cost": 0, "tags": ["beach", "heritage", "nightlife"]},
    {"name": "Paradise Beach", "city": "Pondicherry", "cost": 150, "tags": ["beach", "nature"]},
    {"name": "Auroville Matrimandir", "city": "Pondicherry", "cost": 0, "tags": ["heritage", "nature"]},

    # Madurai (30-31)
    {"name": "Meenakshi Amman Temple", "city": "Madurai", "cost": 50, "tags": ["temple", "heritage"]},
    {"name": "Thirumalai Nayakar Mahal", "city": "Madurai", "cost": 30, "tags": ["heritage"]},

    # Kodaikanal (32-33)
    {"name": "Dolphin's Nose Trek", "city": "Kodaikanal", "cost": 0, "tags": ["trek", "nature"]},
    {"name": "Kodaikanal Lake Walk", "city": "Kodaikanal", "cost": 50, "tags": ["nature"]},

    # Wayanad (34-35)
    {"name": "Chembra Peak Heart Lake Trek", "city": "Wayanad", "cost": 200, "tags": ["trek", "nature"]},
    {"name": "Edakkal Prehistoric Caves", "city": "Wayanad", "cost": 50, "tags": ["heritage", "trek"]},

    # Kochi (36)
    {"name": "Fort Kochi & Chinese Fishing Nets", "city": "Kochi", "cost": 0, "tags": ["heritage", "beach", "food"]},

    # Munnar (37)
    {"name": "Anamudi Peak & Eravikulam Nature", "city": "Munnar", "cost": 200, "tags": ["nature", "trek"]},
]

# 28 unique routes across South India (each is bidirectional = 56 total paths)
ROUTES = [
    # Hub: Bengaluru
    {"from": "Bengaluru", "to": "Mysuru", "mode": "Train", "hours": 2.5, "cost": 120},
    {"from": "Bengaluru", "to": "Chikmagalur", "mode": "Bus", "hours": 5.0, "cost": 380},
    {"from": "Bengaluru", "to": "Coorg", "mode": "Bus", "hours": 5.5, "cost": 420},
    {"from": "Bengaluru", "to": "Mangaluru", "mode": "Train", "hours": 7.5, "cost": 350},
    {"from": "Bengaluru", "to": "Gokarna", "mode": "Bus", "hours": 9.5, "cost": 850},
    {"from": "Bengaluru", "to": "Hampi", "mode": "Train", "hours": 7.5, "cost": 400},
    {"from": "Bengaluru", "to": "Chennai", "mode": "Train", "hours": 4.5, "cost": 250},
    {"from": "Bengaluru", "to": "Pondicherry", "mode": "Bus", "hours": 6.5, "cost": 500},
    {"from": "Bengaluru", "to": "Wayanad", "mode": "Bus", "hours": 6.5, "cost": 450},

    # Hub: Mysuru
    {"from": "Mysuru", "to": "Ooty", "mode": "Bus", "hours": 4.0, "cost": 200},
    {"from": "Mysuru", "to": "Wayanad", "mode": "Bus", "hours": 3.0, "cost": 180},
    {"from": "Mysuru", "to": "Coorg", "mode": "Bus", "hours": 3.0, "cost": 180},
    {"from": "Mysuru", "to": "Mangaluru", "mode": "Bus", "hours": 6.0, "cost": 360},

    # Hub: Mangaluru & Coastal Karnataka Circuit
    {"from": "Bengaluru", "to": "Mangaluru", "mode": "Bus", "hours": 7.0, "cost": 700},
    {"from": "Mangaluru", "to": "Gokarna", "mode": "Train", "hours": 4.0, "cost": 250},
    {"from": "Bengaluru", "to": "Udupi", "mode": "Bus", "hours": 8.0, "cost": 800},
    {"from": "Bengaluru", "to": "Udupi", "mode": "Train", "hours": 10.0, "cost": 550},
    {"from": "Udupi", "to": "Malpe", "mode": "Bus", "hours": 1.0, "cost": 100},
    {"from": "Bengaluru", "to": "Kundapura", "mode": "Bus", "hours": 9.0, "cost": 850},
    {"from": "Kundapura", "to": "Maravanthe", "mode": "Bus", "hours": 1.0, "cost": 80},
    {"from": "Mangaluru", "to": "Chikmagalur", "mode": "Bus", "hours": 4.0, "cost": 240},
    {"from": "Mangaluru", "to": "Kochi", "mode": "Train", "hours": 7.0, "cost": 320},

    # Hub: Tamil Nadu
    {"from": "Chennai", "to": "Pondicherry", "mode": "Bus", "hours": 3.0, "cost": 180},
    {"from": "Chennai", "to": "Madurai", "mode": "Train", "hours": 6.5, "cost": 350},
    {"from": "Madurai", "to": "Kodaikanal", "mode": "Bus", "hours": 3.5, "cost": 160},
    {"from": "Madurai", "to": "Kochi", "mode": "Bus", "hours": 6.0, "cost": 320},
    {"from": "Pondicherry", "to": "Madurai", "mode": "Bus", "hours": 5.5, "cost": 320},

    # Hills: Ooty & Kodaikanal
    {"from": "Ooty", "to": "Kodaikanal", "mode": "Bus", "hours": 6.5, "cost": 300},
    {"from": "Ooty", "to": "Munnar", "mode": "Bus", "hours": 6.0, "cost": 320},

    # Kerala
    {"from": "Wayanad", "to": "Kochi", "mode": "Bus", "hours": 5.5, "cost": 300},
    {"from": "Kochi", "to": "Munnar", "mode": "Bus", "hours": 4.0, "cost": 200},
    {"from": "Munnar", "to": "Madurai", "mode": "Bus", "hours": 4.5, "cost": 220},

    # Heritage & Northern links
    {"from": "Hampi", "to": "Gokarna", "mode": "Bus", "hours": 7.0, "cost": 450},
    {"from": "Chikmagalur", "to": "Coorg", "mode": "Bus", "hours": 4.0, "cost": 220},
]


def load_all_data(uri: str, user: str, password: str, database: str = "neo4j"):
    """Connects to Neo4j, initializes schema, and loads cities, attractions, tags, and routes."""
    print(f"🔌 Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        driver.verify_connectivity()
        print(" Connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    with driver.session(database=database) as session:
        print("🧹 Clearing previous graph data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("📋 Creating unique constraints and indexes...")
        session.run("CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT attraction_name IF NOT EXISTS FOR (a:Attraction) REQUIRE a.name IS UNIQUE")
        session.run("CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE")

        print(f"🏙️  Loading {len(CITIES)} Cities...")
        for city in CITIES:
            session.run(
                "MERGE (c:City {name: $name}) SET c.state = $state",
                city
            )

        print(f"🏷️  Loading {len(TAGS)} Tags...")
        for tag in TAGS:
            session.run(
                "MERGE (t:Tag {name: $name})",
                {"name": tag}
            )

        print(f"🏛️  Loading {len(ATTRACTIONS)} Attractions & Tag Links...")
        for att in ATTRACTIONS:
            session.run(
                """
                MERGE (a:Attraction {name: $name})
                SET a.cost = $cost
                WITH a
                MATCH (c:City {name: $city})
                MERGE (a)-[:LOCATED_IN]->(c)
                WITH a
                UNWIND $tags AS tag_name
                MATCH (t:Tag {name: tag_name})
                MERGE (a)-[:HAS_TAG]->(t)
                """,
                {
                    "name": att["name"],
                    "cost": att["cost"],
                    "city": att["city"],
                    "tags": att["tags"],
                }
            )

        print(f"🛣️  Loading {len(ROUTES)} Bidirectional Travel Routes...")
        for route in ROUTES:
            # Bidirectional: from -> to AND to -> from
            session.run(
                """
                MATCH (c1:City {name: $from_city})
                MATCH (c2:City {name: $to_city})
                MERGE (c1)-[:CONNECTED_BY {mode: $mode, hours: $hours, cost: $cost}]->(c2)
                MERGE (c2)-[:CONNECTED_BY {mode: $mode, hours: $hours, cost: $cost}]->(c1)
                """,
                {
                    "from_city": route["from"],
                    "to_city": route["to"],
                    "mode": route["mode"],
                    "hours": float(route["hours"]),
                    "cost": float(route["cost"]),
                }
            )

        summary = session.run(
            """
            MATCH (c:City) WITH count(c) AS cities
            MATCH (a:Attraction) WITH cities, count(a) AS attractions
            MATCH (t:Tag) WITH cities, attractions, count(t) AS tags
            MATCH ()-[r:CONNECTED_BY]->() WITH cities, attractions, tags, count(r) AS routes
            RETURN cities, attractions, tags, routes
            """
        ).single()

        print("\n" + "=" * 50)
        print("🎉 GRAPH DATABASE LOAD COMPLETE!")
        print(f"   • Cities: {summary['cities']}")
        print(f"   • Attractions: {summary['attractions']}")
        print(f"   • Tags: {summary['tags']}")
        print(f"   • Route Segments (bidirectional): {summary['routes']}")
        print("=" * 50 + "\n")

    driver.close()


if __name__ == "__main__":
    uri = CONFIG_URI
    user = CONFIG_USERNAME
    password = CONFIG_PASSWORD
    database = CONFIG_DATABASE

    if not uri or not password:
        print("\n⚠️  Missing NEO4J_URI or NEO4J_PASSWORD!")
        print("Please set them in load_data.py (CONFIG_URI & CONFIG_PASSWORD) or in .env")
        try:
            uri = input("Enter Neo4j URI (e.g. neo4j+s://xxx.databases.neo4j.io): ").strip()
            user = input("Enter Username [default: neo4j]: ").strip() or "neo4j"
            password = input("Enter Password: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCannot prompt interactively. Exiting.")
            sys.exit(1)

    load_all_data(uri, user, password, database)
