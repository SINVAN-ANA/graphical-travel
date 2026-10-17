"""
Graph Trip Planner - Web Application
Neo4j Graph Builder | Build Sprint Bengaluru | Open Problem Statement

Streamlit application that queries Neo4j to find 1-leg and 2-leg travel paths,
accumulates budget and travel time, matches attraction tags, and provides
explainable graph recommendations.
"""

import os
import re
from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

from query_parser import parse_natural_language_query
from load_data import CITIES, ATTRACTIONS, TAGS, ROUTES, load_all_data

# Ensure telemetry prompts do not interfere
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
load_dotenv()

st.set_page_config(
    page_title="Graph Trip Planner | Neo4j Knowledge Graph",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F766E 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(90deg, #FFFFFF, #99F6E4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #CBD5E1;
        margin-top: 0.5rem;
        max-width: 750px;
        line-height: 1.5;
    }

    .demo-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
    }
    .demo-card:hover {
        border-color: #0D9488;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -4px rgba(13, 148, 136, 0.15);
    }

    .trip-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        border-left: 6px solid #0D9488;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }
    .trip-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }

    .pill-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .pill-time { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }
    .pill-cost { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
    .pill-legs { background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }

    /* Tag Category Colors */
    .tag-beach { background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
    .tag-trek { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
    .tag-temple { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .tag-nature { background: #F0FDF4; color: #166534; border: 1px solid #DCFCE7; }
    .tag-heritage { background: #F3E8FF; color: #6B21A8; border: 1px solid #E9D5FF; }
    .tag-food { background: #FFE4E6; color: #BE123C; border: 1px solid #FECDD3; }
    .tag-nightlife { background: #EDE9FE; color: #5B21B6; border: 1px solid #DDD6FE; }
    
    .timeline-step {
        display: inline-flex;
        align-items: center;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 6px 12px;
        margin-right: 8px;
        font-size: 0.88rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# --- NEO4J CONNECTION HELPER ---
def get_driver(uri: str, user: str, password: str) -> Driver:
    """Connect to Neo4j, with graceful fallback to +ssc if host SSL cert store needs it."""
    clean_pw = password.strip()
    try:
        d = GraphDatabase.driver(uri, auth=(user, clean_pw))
        return d
    except Exception as e:
        if uri.startswith("neo4j+s://"):
            alt_uri = uri.replace("neo4j+s://", "neo4j+ssc://")
            return GraphDatabase.driver(alt_uri, auth=(user, clean_pw))
        raise


# --- GRAPH TRAVERSAL ENGINES ---
def search_trips(
    driver: Driver,
    start_city: str,
    budget: float,
    max_hours: float,
    interests: List[str],
    max_legs: int = 2,
    database: str = "neo4j"
) -> List[Dict[str, Any]]:
    """Executes real Cypher path traversal in Neo4j."""
    trips = []

    query_1leg = """
    MATCH (start:City {name: $start_city})-[r:CONNECTED_BY]->(dest:City)
    WHERE r.cost <= $budget AND r.hours <= $max_hours
    MATCH (att:Attraction)-[:LOCATED_IN]->(dest)
    MATCH (att)-[:HAS_TAG]->(t:Tag)
    WHERE (size($interests) = 0 OR t.name IN $interests)
    WITH start, dest, r,
         collect(DISTINCT {
             name: att.name,
             cost: att.cost,
             tag: t.name
         }) AS matched_attractions,
         collect(DISTINCT t.name) AS matched_tags
    WHERE size(matched_tags) >= (CASE WHEN size($interests) > 0 THEN 1 ELSE 0 END)
    RETURN
        start.name AS origin,
        dest.name AS destination,
        [start.name, dest.name] AS path_cities,
        [{from: start.name, to: dest.name, mode: r.mode, hours: r.hours, cost: r.cost}] AS legs,
        r.hours AS total_hours,
        r.cost AS total_cost,
        matched_attractions,
        matched_tags,
        1 AS leg_count
    ORDER BY size(matched_tags) DESC, total_cost ASC
    """

    query_2leg = """
    MATCH (start:City {name: $start_city})-[r1:CONNECTED_BY]->(mid:City)-[r2:CONNECTED_BY]->(dest:City)
    WHERE start <> dest AND mid <> start
      AND (r1.cost + r2.cost) <= $budget
      AND (r1.hours + r2.hours) <= $max_hours
    MATCH (att:Attraction)-[:LOCATED_IN]->(dest)
    MATCH (att)-[:HAS_TAG]->(t:Tag)
    WHERE (size($interests) = 0 OR t.name IN $interests)
    WITH start, mid, dest, r1, r2,
         collect(DISTINCT {
             name: att.name,
             cost: att.cost,
             tag: t.name
         }) AS matched_attractions,
         collect(DISTINCT t.name) AS matched_tags
    WHERE size(matched_tags) >= (CASE WHEN size($interests) > 0 THEN 1 ELSE 0 END)
    RETURN
        start.name AS origin,
        dest.name AS destination,
        [start.name, mid.name, dest.name] AS path_cities,
        [
            {from: start.name, to: mid.name, mode: r1.mode, hours: r1.hours, cost: r1.cost},
            {from: mid.name, to: dest.name, mode: r2.mode, hours: r2.hours, cost: r2.cost}
        ] AS legs,
        (r1.hours + r2.hours) AS total_hours,
        (r1.cost + r2.cost) AS total_cost,
        matched_attractions,
        matched_tags,
        2 AS leg_count
    ORDER BY size(matched_tags) DESC, total_cost ASC
    """

    params = {
        "start_city": start_city,
        "budget": float(budget),
        "max_hours": float(max_hours),
        "interests": interests,
    }

    with driver.session(database=database) as session:
        res1 = session.run(query_1leg, params)
        for rec in res1:
            trips.append(dict(rec))

        if max_legs >= 2:
            res2 = session.run(query_2leg, params)
            for rec in res2:
                trips.append(dict(rec))

    def score_trip(t):
        matched_count = len(set(t["matched_tags"]).intersection(set(interests))) if interests else 1
        return (-matched_count, t["total_cost"])

    trips.sort(key=score_trip)
    return trips


def search_trips_offline(
    start_city: str,
    budget: float,
    max_hours: float,
    interests: List[str],
    max_legs: int = 2
) -> List[Dict[str, Any]]:
    """In-memory graph walker fallback when Neo4j is initializing or offline."""
    routes_bidir = []
    for r in ROUTES:
        routes_bidir.append(r)
        routes_bidir.append({
            'from': r['to'], 'to': r['from'], 'mode': r['mode'], 'hours': r['hours'], 'cost': r['cost']
        })

    trips = []
    # 1-leg paths
    for r in routes_bidir:
        if r['from'] == start_city and r['cost'] <= budget and r['hours'] <= max_hours:
            dest = r['to']
            dest_atts = [a for a in ATTRACTIONS if a['city'] == dest]
            matched_tags = set()
            matched_atts = []
            for a in dest_atts:
                m = set(a['tags']).intersection(set(interests)) if interests else set(a['tags'])
                if m:
                    matched_tags.update(m)
                    matched_atts.append(a)
            if not interests or len(matched_tags) > 0:
                trips.append({
                    'origin': start_city,
                    'destination': dest,
                    'path_cities': [start_city, dest],
                    'legs': [r],
                    'total_hours': r['hours'],
                    'total_cost': r['cost'],
                    'matched_tags': list(matched_tags),
                    'matched_attractions': matched_atts,
                    'leg_count': 1
                })

    # 2-leg paths
    if max_legs >= 2:
        for r1 in routes_bidir:
            if r1['from'] == start_city:
                mid = r1['to']
                for r2 in routes_bidir:
                    if r2['from'] == mid and r2['to'] != start_city:
                        dest = r2['to']
                        tot_c = r1['cost'] + r2['cost']
                        tot_h = r1['hours'] + r2['hours']
                        if tot_c <= budget and tot_h <= max_hours:
                            dest_atts = [a for a in ATTRACTIONS if a['city'] == dest]
                            matched_tags = set()
                            matched_atts = []
                            for a in dest_atts:
                                m = set(a['tags']).intersection(set(interests)) if interests else set(a['tags'])
                                if m:
                                    matched_tags.update(m)
                                    matched_atts.append(a)
                            if not interests or len(matched_tags) > 0:
                                trips.append({
                                    'origin': start_city,
                                    'destination': dest,
                                    'path_cities': [start_city, mid, dest],
                                    'legs': [r1, r2],
                                    'total_hours': tot_h,
                                    'total_cost': tot_c,
                                    'matched_tags': list(matched_tags),
                                    'matched_attractions': matched_atts,
                                    'leg_count': 2
                                })

    def score_trip(t):
        matched_count = len(set(t["matched_tags"]).intersection(set(interests))) if interests else 1
        return (-matched_count, t["total_cost"])

    trips.sort(key=score_trip)
    return trips


def render_tag_badge(tag: str) -> str:
    css_class = f"tag-{tag.lower()}"
    return f'<span class="pill-badge {css_class}">#{tag}</span>'


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://neo4j.com/wp-content/themes/neo4jweb/assets/images/neo4j-logo-2020.svg", width=180)
    st.markdown("### 🔌 Database Connection (Person A)")

    env_uri = os.getenv("NEO4J_URI", "")
    env_user = os.getenv("NEO4J_USERNAME", "neo4j")
    env_pass = os.getenv("NEO4J_PASSWORD", "")
    env_db = os.getenv("NEO4J_DATABASE", "neo4j")

    cfg_uri = st.text_input("Neo4j AuraDB / Bolt URI", value=env_uri)
    cfg_user = st.text_input("Username", value=env_user)
    cfg_pass = st.text_input("Password", value=env_pass, type="password", help="Enter the password from your AuraDB download")
    cfg_db = st.text_input("Database", value=env_db)

    is_connected = False
    driver = None
    if cfg_pass:
        try:
            driver = get_driver(cfg_uri, cfg_user, cfg_pass)
            driver.verify_connectivity()
            is_connected = True
            st.success(" Connected to Live Neo4j!")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")
    else:
        st.warning("⚠️ Enter password to connect to AuraDB.")

    if is_connected and driver:
        if st.button("🌱 Load Data into Neo4j (Person A)", use_container_width=True):
            try:
                with st.spinner("Loading 15 cities, 37 attractions, and 28 routes into Neo4j..."):
                    load_all_data(cfg_uri, cfg_user, cfg_pass, cfg_db)
                    st.success("🎉 Data successfully loaded into Neo4j!")
                    st.rerun()
            except Exception as e:
                st.error(f"Load error: {e}")

    st.divider()
    st.markdown("### 📊 Database Statistics")
    if is_connected and driver:
        try:
            with driver.session(database=cfg_db) as s:
                cnt = s.run("""
                MATCH (c:City) WITH count(c) AS cities
                MATCH (a:Attraction) WITH cities, count(a) AS attractions
                MATCH ()-[r:CONNECTED_BY]->()
                RETURN cities, attractions, count(r) AS routes
                """).single()
                if cnt:
                    col_s1, col_s2 = st.columns(2)
                    col_s1.metric("Cities", cnt["cities"])
                    col_s2.metric("Attractions", cnt["attractions"])
                    st.caption(f"🛣️ {cnt['routes']} active route segments")
        except Exception:
            pass
    else:
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Cities", len(CITIES))
        col_s2.metric("Attractions", len(ATTRACTIONS))
        st.caption(f"🛣️ {len(ROUTES) * 2} routes (Offline Simulation)")


# --- HERO BANNER ---
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #5EEAD4; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
                Neo4j Graph Builder • Build Sprint Bengaluru
            </div>
            <h1 class="hero-title">Graph Trip Planner 🧭</h1>
            <div class="hero-subtitle">
                Multi-stop travel optimization for South India. Traverses cities, sums route costs & hours along edges, and matches activities through native Neo4j graph algorithms.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- MAIN NAVIGATION TABS ---
tab_search, tab_network, tab_pitch, tab_admin = st.tabs([
    "🎯 Route Discovery & Planner",
    "🕸️ Interactive Graph Network",
    "💡 Why a Graph? (Pitch Script)",
    "🛠️ Person A Database Admin"
])


# ==============================================================================
# TAB 1: ROUTE DISCOVERY & PLANNER
# ==============================================================================
with tab_search:
    st.markdown("### ⚡ 1-Click Hackathon Demo Scenarios")
    st.caption("Click any preset query to test the canonical routes from the hackathon problem brief:")

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    if "nl_query" not in st.session_state:
        st.session_state["nl_query"] = "I'm in Bengaluru with Rs 1500 and 10 hours. Where can I go for a beach trip?"

    with col_d1:
        st.markdown("""
        <div class="demo-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">🏖️</div>
            <strong>1. Beach Route</strong><br/>
            <span style="color: #64748B; font-size: 0.85rem;">₹1500 • 10h • Direct</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Load Demo 1", key="btn_demo1", use_container_width=True):
            st.session_state["nl_query"] = "I'm in Bengaluru with Rs 1500 and 10 hours. Where can I go for a beach trip?"
            st.rerun()

    with col_d2:
        st.markdown("""
        <div class="demo-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">⛰️</div>
            <strong>2. Trek + Nature</strong><br/>
            <span style="color: #64748B; font-size: 0.85rem;">₹1000 • 8h • Direct</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Load Demo 2", key="btn_demo2", use_container_width=True):
            st.session_state["nl_query"] = "I'm in Bengaluru with Rs 1000 and 8 hours. Where can I go for a trek and nature trip?"
            st.rerun()

    with col_d3:
        st.markdown("""
        <div class="demo-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">🛕</div>
            <strong>3. Temple Circuit</strong><br/>
            <span style="color: #64748B; font-size: 0.85rem;">₹2000 • 15h • 2 Legs</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Load Demo 3", key="btn_demo3", use_container_width=True):
            st.session_state["nl_query"] = "I'm in Bengaluru for a 2 legs trip with temple and heritage under Rs 2000 and 15 hours"
            st.rerun()

    with col_d4:
        st.markdown("""
        <div class="demo-card" style="border-color: #FCA5A5; background: #FFF5F5;">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">⚠️</div>
            <strong style="color: #991B1B;">4. Empty State Demo</strong><br/>
            <span style="color: #B91C1C; font-size: 0.85rem;">₹500 • 4h • Beach & Nature</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Test Empty State", key="btn_demo4", use_container_width=True):
            st.session_state["nl_query"] = "Bengaluru with Rs 500 budget and 4h travel for beach and nature"
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Search Bar with Rule-based extraction
    st.markdown("### 💬 Ask in Natural Language (Zero-Cost AI Parser)")
    user_query = st.text_input(
        "Enter your travel goal (e.g. 'I am in Bengaluru with Rs 1500 and 10 hours for beach'):",
        value=st.session_state["nl_query"],
        key="query_input"
    )

    parsed = parse_natural_language_query(user_query)

    # Interactive Filter Controls
    with st.expander("🎛️ Refine Constraints & Graph Traversal Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        all_city_names = [c["name"] for c in CITIES]
        city_idx = all_city_names.index(parsed["start_city"]) if parsed["start_city"] in all_city_names else 0
        
        start_city = c1.selectbox("📍 Origin City", all_city_names, index=city_idx)
        budget = c2.number_input("💰 Max Budget (₹)", min_value=100, max_value=10000, value=parsed["budget"], step=100)
        max_hours = c3.number_input("⏱️ Max Travel Time (hrs)", min_value=1.0, max_value=30.0, value=parsed["max_hours"], step=1.0)
        max_legs = c4.radio("📍 Route Legs", [1, 2], index=(parsed["max_legs"] - 1), horizontal=True, help="1 leg = direct, 2 legs = multi-stop circuit")

        selected_tags = st.multiselect(
            "🏷️ Desired Activities / Tags",
            TAGS,
            default=parsed["interests"],
            help="Filter destinations by matched experiences"
        )

    if not selected_tags and parsed["interests"]:
        selected_tags = parsed["interests"]

    st.markdown("<br/>", unsafe_allow_html=True)

    # Action Button
    if st.button("🚀 Find My Graph Routes", type="primary", use_container_width=True):
        with st.spinner("Walking the Neo4j graph for feasible multi-stop paths..."):
            try:
                if is_connected and driver:
                    results = search_trips(
                        driver=driver,
                        start_city=start_city,
                        budget=budget,
                        max_hours=max_hours,
                        interests=selected_tags,
                        max_legs=max_legs,
                        database=cfg_db
                    )
                    engine_name = "Live Neo4j AuraDB Cypher Engine"
                else:
                    st.info("💡 **Local Simulation Engine Active**: Neo4j credentials not yet verified in sidebar. Traversing 15 South India cities, 37 attractions, and 28 routes in-memory.")
                    results = search_trips_offline(
                        start_city=start_city,
                        budget=budget,
                        max_hours=max_hours,
                        interests=selected_tags,
                        max_legs=max_legs
                    )
                    engine_name = "Local Graph Traversal Engine"

                if not results:
                    st.markdown(f"""
                    <div style="background: #FFFBFB; border: 1.5px solid #FCA5A5; border-radius: 16px; padding: 1.75rem; margin-top: 1rem; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.05);">
                        <div style="font-size: 0.8rem; font-weight: 800; color: #DC2626; text-transform: uppercase; letter-spacing: 0.06em;">
                            RESULTS · EMPTY STATE ALTERNATIVE
                        </div>
                        <h2 style="color: #991B1B; font-size: 1.4rem; font-weight: 700; margin: 0.35rem 0 0.75rem 0;">
                            A few small tweaks could open new roads.
                        </h2>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 1rem;">
                            <span class="pill-badge pill-legs">{start_city}</span>
                            <span class="pill-badge pill-cost">Rs {int(budget)} budget</span>
                            <span class="pill-badge pill-time">{max_hours}h travel</span>
                            <span class="pill-badge pill-legs">Up to {max_legs} legs</span>
                            {''.join([render_tag_badge(t) for t in selected_tags])}
                        </div>
                        <div style="color: #7F1D1D; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.25rem;">
                            No trips found — yet.
                        </div>
                        <p style="color: #475569; font-size: 0.92rem; line-height: 1.5; margin-bottom: 1.25rem;">
                            We couldn’t connect <strong>{start_city}</strong> to both a <em>{' and '.join(selected_tags) if selected_tags else 'selected'}</em> stop within <strong>Rs {int(budget)}</strong> and <strong>{max_hours}h</strong> of travel. Your next getaway might just need a little more room.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.markdown("#### 💡 Quick Action Recommendations")
                    col_fix1, col_fix2, col_fix3 = st.columns(3)

                    with col_fix1:
                        st.markdown("""
                        <div class="demo-card" style="border-left: 4px solid #0D9488;">
                            <strong>1. Increase your budget</strong><br/>
                            <span style="color: #64748B; font-size: 0.85rem;">Try Rs 1,000–1,500 for more coastal connections.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Apply Budget: ₹1,500", key="fix_budget", use_container_width=True):
                            st.session_state["nl_query"] = f"{start_city} with Rs 1500 budget and {max_hours}h travel for {' and '.join(selected_tags)}"
                            st.rerun()

                    with col_fix2:
                        st.markdown("""
                        <div class="demo-card" style="border-left: 4px solid #3B82F6;">
                            <strong>2. Give yourself more hours</strong><br/>
                            <span style="color: #64748B; font-size: 0.85rem;">Try 10–14h of travel to reach the coast.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Apply Time: 14h Travel", key="fix_hours", use_container_width=True):
                            st.session_state["nl_query"] = f"{start_city} with Rs {int(budget)} budget and 14h travel for {' and '.join(selected_tags)}"
                            st.rerun()

                    with col_fix3:
                        st.markdown("""
                        <div class="demo-card" style="border-left: 4px solid #8B5CF6;">
                            <strong>3. Start with one interest</strong><br/>
                            <span style="color: #64748B; font-size: 0.85rem;">Pick beach or nature, then explore what fits.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        single_tag = selected_tags[0] if selected_tags else "beach"
                        if st.button(f"Filter Single Tag: #{single_tag}", key="fix_single_tag", use_container_width=True):
                            st.session_state["nl_query"] = f"{start_city} with Rs {int(budget)} budget and {max_hours}h travel for {single_tag}"
                            st.rerun()
                else:
                    st.success(f"🎉 **{engine_name}** found {len(results)} optimal graph route(s)!")

                    for idx, trip in enumerate(results, 1):
                        path_str = " ➔ ".join(trip["path_cities"])
                        tag_badges_html = "".join([render_tag_badge(t) for t in set(trip["matched_tags"])])

                        # Render transit legs
                        legs_steps_html = []
                        for leg in trip["legs"]:
                            icon = "🚆" if leg["mode"] == "Train" else "🚌"
                            legs_steps_html.append(
                                f'<span class="timeline-step">{icon} <strong>{leg["from"]}</strong> ➔ <strong>{leg["to"]}</strong> '
                                f'<span style="color: #64748B; margin-left: 6px;">({leg["hours"]}h • ₹{int(leg["cost"])})</span></span>'
                            )
                        legs_timeline = "".join(legs_steps_html)

                        attractions_list = [f"{a['name']} (₹{a['cost']})" for a in trip["matched_attractions"]]

                        st.markdown(f"""
                        <div class="trip-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                                <div>
                                    <span style="font-size: 0.85rem; color: #0D9488; font-weight: 700; text-transform: uppercase;">Option {idx}</span>
                                    <h3 style="margin: 0.1rem 0 0.5rem 0; color: #0F172A; font-size: 1.35rem;">{path_str}</h3>
                                </div>
                                <div>
                                    <span class="pill-badge pill-time">⏱️ {trip['total_hours']} Hours</span>
                                    <span class="pill-badge pill-cost">💰 ₹{int(trip['total_cost'])} Transit</span>
                                    <span class="pill-badge pill-legs">📍 {trip['leg_count']} Leg{'s' if trip['leg_count'] > 1 else ''}</span>
                                </div>
                            </div>
                            <div style="margin-top: 10px;">
                                <strong>Transit Connections:</strong><br/>
                                <div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px;">
                                    {legs_timeline}
                                </div>
                            </div>
                            <div style="margin-top: 12px;">
                                <strong>Destination Attractions:</strong> {', '.join(attractions_list[:5])}
                            </div>
                            <div style="margin-top: 10px;">
                                <strong>Matched Activity Tags:</strong><br/>
                                <div style="margin-top: 4px;">
                                    {tag_badges_html}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            with st.expander(f"🗺️ View Graph Path Visualization (Option {idx})"):
                                dot_lines = [
                                    'digraph G {',
                                    '  rankdir=LR;',
                                    '  node [shape=box, style="filled,rounded", fontname="Helvetica", fontcolor="#0F172A"];',
                                    '  edge [fontname="Helvetica", fontsize=10, color="#64748B"];'
                                ]
                                for c in trip["path_cities"]:
                                    dot_lines.append(f'  "{c}" [fillcolor="#CCFBF1", color="#0D9488", penwidth=2];')
                                for leg in trip["legs"]:
                                    dot_lines.append(f'  "{leg["from"]}" -> "{leg["to"]}" [label="{leg["mode"]}\\n{leg["hours"]}h, ₹{int(leg["cost"])}", color="#0D9488", penwidth=2];')
                                dest = trip["destination"]
                                for att in trip["matched_attractions"][:4]:
                                    dot_lines.append(f'  "{att["name"]}" [fillcolor="#FEF3C7", color="#D97706", fontsize=9];')
                                    dot_lines.append(f'  "{att["name"]}" -> "{dest}" [label="LOCATED_IN", style=dashed, color="#94A3B8"];')
                                dot_lines.append('}')
                                st.graphviz_chart("\n".join(dot_lines), use_container_width=True)

                        with col_exp2:
                            with st.expander(f"🔍 Inspect Neo4j Cypher Traversal Query"):
                                st.code(f"""
// Live Traversal for Option {idx}
MATCH path = (start:City {{name: '{trip["origin"]}'}})-[r:CONNECTED_BY*{trip["leg_count"]}]->(dest:City {{name: '{trip["destination"]}'}})
WHERE reduce(c = 0, rel in relationships(path) | c + rel.cost) <= {budget}
  AND reduce(h = 0, rel in relationships(path) | h + rel.hours) <= {max_hours}
MATCH (att:Attraction)-[:LOCATED_IN]->(dest)
MATCH (att)-[:HAS_TAG]->(t:Tag)
WHERE t.name IN {selected_tags}
RETURN path, collect(DISTINCT att.name) AS attractions;
                                """, language="cypher")

            except Exception as e:
                st.error(f"Search failed: {e}")


# ==============================================================================
# TAB 2: INTERACTIVE GRAPH NETWORK
# ==============================================================================
with tab_network:
    st.subheader("🕸️ South India Regional Graph Topology")
    st.write("Explore all 15 cities, 37 attractions, and 28 route segments forming the travel graph.")

    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        selected_city_explore = st.selectbox("Inspect Hub City Connections:", [c["name"] for c in CITIES], index=0)
        city_routes = [r for r in ROUTES if r["from"] == selected_city_explore or r["to"] == selected_city_explore]
        city_atts = [a for a in ATTRACTIONS if a["city"] == selected_city_explore]

        st.metric("Direct Connected Routes", len(city_routes))
        st.metric("Local Curated Attractions", len(city_atts))

        st.markdown("**Local Attractions:**")
        for a in city_atts:
            st.markdown(f"- **{a['name']}** (₹{a['cost']}): {' '.join([render_tag_badge(t) for t in a['tags']])}", unsafe_allow_html=True)

    with col_g2:
        st.markdown(f"**Direct Graph Connections for {selected_city_explore}:**")
        dot_city = [
            'digraph G {',
            '  rankdir=LR;',
            '  node [shape=box, style="filled,rounded", fontname="Helvetica"];',
            f'  "{selected_city_explore}" [fillcolor="#0D9488", fontcolor="white", style="filled,rounded", penwidth=2];'
        ]
        for r in city_routes:
            other = r["to"] if r["from"] == selected_city_explore else r["from"]
            dot_city.append(f'  "{other}" [fillcolor="#F1F5F9", color="#94A3B8"];')
            dot_city.append(f'  "{selected_city_explore}" -> "{other}" [label="{r["mode"]} ({r["hours"]}h, ₹{r["cost"]})", dir=both, color="#0D9488"];')
        for a in city_atts:
            dot_city.append(f'  "{a["name"]}" [fillcolor="#FEF3C7", color="#D97706", fontsize=9];')
            dot_city.append(f'  "{a["name"]}" -> "{selected_city_explore}" [label="LOCATED_IN", style=dashed, color="#94A3B8"];')
        dot_city.append('}')
        st.graphviz_chart("\n".join(dot_city), use_container_width=True)


# ==============================================================================
# TAB 3: WHY A GRAPH? (PITCH SCRIPT FOR PERSON D)
# ==============================================================================
with tab_pitch:
    st.subheader("💡 Why a Graph? (Judges Pitch Script)")
    st.write("Use this exact narrative during your 2-minute pitch to explain why a graph database is mandatory for this problem.")

    col_w1, col_w2, col_w3 = st.columns(3)

    with col_w1:
        st.markdown("""
        ### 1. Routes are Literal Paths
        **City ➔ City ➔ City**  
        Travel in the real world is inherently a directed network. A graph database natively traverses multi-hop paths in microseconds without costly SQL table joins.
        """)

    with col_w2:
        st.markdown("""
        ### 2. Vector DBs Fail at Constraints
        **Vector Search Lacks Topology**  
        A vector database can find "places similar to beach," but it **cannot chain connections, sum transit ticket costs, or prune multi-stop routes by travel hours** along path edges.
        """)

    with col_w3:
        st.markdown("""
        ### 3. 100% Explainable Recommendations
        **Zero Hallucinations**  
        Every single result shows the exact transit mode (train vs bus), hours, rupee cost breakdown, and why each attraction matched the user's tags.
        """)

    st.divider()
    st.subheader("📊 Architectural Comparison Matrix")
    comparison_data = {
        "Feature": [
            "Multi-Hop Route Finding (1-leg, 2-legs)",
            "Edge Constraint Accumulation (Sum cost & hours)",
            "Tag & Experience Matching",
            "Explainable Decision Path",
            "Zero Hallucination Guarantee"
        ],
        "Neo4j Knowledge Graph": ["✅ Native O(k) Path Traversal", "✅ Native reduce() on Edges", "✅ Direct Pattern Match", "✅ Full Edge/Node Path Inspection", "✅ 100% Grounded in Database"],
        "Vector Database (e.g. Pinecone)": ["❌ Cannot Chain Multi-Hop Routes", "❌ Cannot Sum Edge Weights", "⚠️ Semantic similarity only", "❌ Blackbox Embedding Distance", "❌ Requires LLM Synthesis"],
        "Traditional Relational (SQL)": ["⚠️ Expensive Recursive Self-Joins", "⚠️ Complex CTE Window Queries", "⚠️ Rigid Normalization Tables", "⚠️ High Query Latency on N-hops", "✅ Grounded in Database"]
    }
    st.table(pd.DataFrame(comparison_data))


# ==============================================================================
# TAB 4: PERSON A DATABASE ADMIN
# ==============================================================================
with tab_admin:
    st.subheader("🛠️ Database Administration & Verification (Person A)")
    st.markdown("""
    Use this tab to verify and manage your Neo4j database instance.
    """)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Cloud AuraDB Status")
        st.write(f"**Target URI:** `{cfg_uri}`")
        st.write(f"**Username:** `{cfg_user}`")
        st.write(f"**Status:** {' Connected' if is_connected else '❌ Disconnected / Password Required'}")

        if is_connected and driver:
            if st.button("🔄 Execute Fresh Database Re-seed", type="secondary"):
                with st.spinner("Seeding database..."):
                    load_all_data(cfg_uri, cfg_user, cfg_pass, cfg_db)
                    st.success("Successfully loaded fresh graph dataset!")
                    st.rerun()

    with col_a2:
        st.markdown("#### Verification Cypher Queries")
        st.code("""
// Run in Neo4j Browser for pitch screenshot:
MATCH (c:City)-[r:CONNECTED_BY]->(c2:City)
RETURN c, r, c2 LIMIT 30;

// Verify tag links:
MATCH (a:Attraction)-[:HAS_TAG]->(t:Tag)
RETURN a.name, t.name LIMIT 20;
        """, language="cypher")
