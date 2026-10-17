# Graph Trip Planner 🧭
**Neo4j Graph Builder | Build Sprint Bengaluru | Track: Open Problem Statement**

A multi-stop, budget- and time-constrained travel planner for South India powered by **Neo4j** and **Streamlit**. Zero paid AI APIs required (100% deterministic rule-based query parser).

---

## 1. Problem Statement
Planning a multi-stop trip in India is a mess of tabs. A traveler has to check bus and train sites, maps, blogs, and budgets separately, then work out by hand whether a route fits their money, their time, and what they actually want to do.

> **Challenge Query**: *"I'm in Bengaluru with Rs 1500 and 10 hours. Where can I go for a beach + trek trip, and what is the route?"*

---

## 2. Our Solution
A graph-based trip planner:
- **15 South India Cities**, **37 Curated Attractions**, and **28 Bidirectional Route Segments** stored natively in Neo4j.
- The user inputs start city, budget, available hours, and interest tags (beach, trek, temple, food, nature, heritage, nightlife).
- The Cypher engine traverses 1-leg and 2-leg paths, accumulates transit costs and travel time, matches destination attraction tags, and explains why each trip matched.

---

## 3. Why a Graph? (Judges Pitch Script)
1. **Routes are literally paths**: City to City to City. A graph database natively finds, matches, and traverses multi-hop paths in milliseconds.
2. **Vector DBs fail at constraints**: A vector database can find similar places, but it **cannot chain connections, sum transit costs, or prune by travel hours** along path edges.
3. **Explainable and Transparent**: Every recommended trip provides the exact route legs, transit modes, time/cost breakdown, and matched tags.

---

## 4. The Graph Model

```
(City {name, state})
  ^                                 |
  | [LOCATED_IN]                    | [CONNECTED_BY {mode, hours, cost}]
(Attraction {name, cost})           v
  |                              (City {name, state})
  | [HAS_TAG]
  v
(Tag {name})
```

- **Nodes**:
  - `City`: 15 South India hubs (Bengaluru, Mysuru, Mangaluru, Gokarna, Chikmagalur, Hampi, Coorg, Ooty, Chennai, Pondicherry, Madurai, Kodaikanal, Wayanad, Kochi, Munnar)
  - `Attraction`: 37 popular destinations with costs and tags
  - `Tag`: beach, trek, temple, food, nature, heritage, nightlife
- **Relationships**:
  - `(City)-[:CONNECTED_BY {mode, hours, cost}]->(City)` (bidirectional)
  - `(Attraction)-[:LOCATED_IN]->(City)`
  - `(Attraction)-[:HAS_TAG]->(Tag)`

---

## 5. Team Roles & Steps

### Person A: Database Setup & Data Loading
1. Create a free AuraDB instance at [console.neo4j.io](https://console.neo4j.io/) and download the password file.
2. Copy `.env.example` to `.env` and fill in:
   ```env
   NEO4J_URI=neo4j+s://<your-aura-id>.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=<your-password>
   NEO4J_DATABASE=neo4j
   ```
3. Run the data loader:
   ```bash
   python load_data.py
   ```
4. Send your `NEO4J_URI` and password to Person B.
5. Screenshot the graph in the Neo4j Browser for the pitch deck.

### Person B: Web Application
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify `.env` has Person A's credentials.
3. Launch Streamlit:
   ```bash
   streamlit run app.py
   ```
4. Test the demo queries using the 1-click buttons.

### Person C: Data Expansion & Verification
1. Review `CITIES`, `ATTRACTIONS`, and `ROUTES` in `load_data.py`.
2. Add new attractions or verify timings against RedBus / IRCTC.
3. Have Person A reload: `python load_data.py`.

### Person D: Pitch & Presentation
1. 5 Slides:
   1. Problem: Multi-tab planning chaos in India
   2. Solution: Graph Trip Planner
   3. Graph Model: Cities, Connections, Attractions, Tags
   4. Live Demo: 3 script queries
   5. Why a Graph: Paths + Edge Constraint Accumulation
2. 2-minute pitch rehearsal.

---

## 6. Demo Script (Pick 3 in App)
1. **Bengaluru + Beach** (Budget: ₹1500, 10 hours)
   - Matches: Mangaluru (Train, 7.5h, ₹350) or Gokarna (Bus, 9.5h, ₹850)
   - Matched Tags: `#beach`, `#nature`
2. **Bengaluru + Trek + Nature** (Budget: ₹1000, 8 hours)
   - Matches: Chikmagalur (Bus, 5h, ₹380) or Coorg (Bus, 5.5h, ₹420)
   - Matched Tags: `#trek`, `#nature`
3. **Bengaluru + Temple + Heritage** (2 Legs Multi-Stop)
   - Matches: Bengaluru ➔ Mysuru ➔ Coorg or Wayanad
   - Matched Tags: `#temple`, `#heritage`

---

## 7. Live Deployment (Streamlit Cloud)
1. Push to GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: complete graph trip planner for neo4j sprint"
   git branch -M main
   git remote add origin https://github.com/<your-username>/graph-trip-planner.git
   git push -u origin main
   ```
2. In [share.streamlit.io](https://share.streamlit.io/), link the repository and specify `app.py`.
3. In **Settings -> Secrets**, paste:
   ```toml
   NEO4J_URI = "neo4j+s://<your-id>.databases.neo4j.io"
   NEO4J_USERNAME = "neo4j"
   NEO4J_PASSWORD = "<your-password>"
   NEO4J_DATABASE = "neo4j"
   ```
