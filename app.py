import io
import json
import os
import re
import random
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

try:
    pd.options.future.infer_string = False
except Exception:
    pass

# Force Streamlit base theme to Dark Mode for native canvas tables
try:
    st._config.set_option("theme.base", "dark")
    st._config.set_option("theme.backgroundColor", "#090D16")
    st._config.set_option("theme.secondaryBackgroundColor", "#111827")
    st._config.set_option("theme.textColor", "#F8FAFC")
    st._config.set_option("theme.primaryColor", "#3B82F6")
except Exception:
    pass

# ==============================================================================
# PAGE CONFIGURATION & ENCRYPTED SECRETS HELPERS
# ==============================================================================
st.set_page_config(
    page_title="Financial & POS Reconciliation Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_BASE_URL = "https://pos-margin-app-5dqt2eh8rz5vkti89awhnn.streamlit.app"
CLIENTS_JSON_PATH = "clients_store.json"
COGS_STORAGE_DIR = "client_cogs_store"
os.makedirs(COGS_STORAGE_DIR, exist_ok=True)


def get_secret(key: str, default: str = "") -> str:
    """Safely reads a key from Streamlit Cloud Secrets without exposing it in code."""
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


def get_admin_username() -> str:
    return get_secret("admin_username", "admin").lower()


def get_admin_password() -> str | None:
    """Returns None if admin_password is not configured in Streamlit Secrets."""
    pw = get_secret("admin_password", "")
    return pw if pw else None


def get_owner_whatsapp() -> str:
    return re.sub(r"[^0-9]", "", get_secret("owner_whatsapp", ""))


# ==============================================================================
# OBSIDIAN DARK DESIGN SYSTEM
# ==============================================================================
def apply_obsidian_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: #090D16 !important;
            color: #F8FAFC !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        #MainMenu, footer {visibility: hidden;}
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 2.5rem !important;
        }

        .block-container {
            padding-top: 3.25rem !important;
            padding-bottom: 3rem !important;
            max-width: 1440px;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 2.75rem !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #0D131F !important;
            border-right: 1px solid #1E293B !important;
        }
        section[data-testid="stSidebar"] * {
            color: #E2E8F0;
        }

        .suite-header {
            border-bottom: 1px solid #1E293B;
            padding-bottom: 0.85rem;
            margin-bottom: 1.25rem;
        }
        .suite-kicker {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #38BDF8;
            margin-bottom: 0.25rem;
        }
        .suite-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.2;
        }
        .suite-subtitle {
            font-size: 0.85rem;
            color: #94A3B8;
            margin-top: 0.25rem;
        }

        div[data-testid="stRadio"] > div[role="radiogroup"] {
            background-color: #111827;
            border: 1px solid #1E293B;
            border-radius: 8px;
            padding: 6px 14px;
            gap: 18px;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #131C2E 0%, #0F172A 100%) !important;
            border: 1px solid #1E293B !important;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
            transition: border-color 0.15s ease;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #334155 !important;
        }
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.71rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8 !important;
        }
        div[data-testid="stMetricValue"] > div {
            font-family: 'JetBrains Mono', 'Inter', monospace !important;
            font-size: 1.38rem !important;
            font-weight: 600 !important;
            color: #F8FAFC !important;
            letter-spacing: -0.02em;
        }

        div[data-testid="stExpander"] {
            background-color: #111827 !important;
            border: 1px solid #1E293B !important;
            border-radius: 8px !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background-color: #111827 !important;
            border-color: #1E293B !important;
            color: #F8FAFC !important;
        }
        label, .stMarkdown p, .stCaption {
            color: #CBD5E1 !important;
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid #3B82F6 !important;
            font-weight: 600 !important;
            border-radius: 6px !important;
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background-color: #1D4ED8 !important;
            border-color: #60A5FA !important;
        }
        .stButton > button[kind="secondary"],
        .stLinkButton > a {
            background-color: #161F30 !important;
            color: #E2E8F0 !important;
            border: 1px solid #26334D !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            border-bottom: 1px solid #1E293B;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 42px;
            font-size: 0.84rem;
            font-weight: 500;
            color: #64748B !important;
            padding: 0 4px;
            background-color: transparent !important;
        }
        .stTabs [aria-selected="true"] {
            color: #38BDF8 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #38BDF8 !important;
        }

        .exec-banner {
            background-color: #111827;
            border: 1px solid #1E293B;
            border-left: 3px solid #38BDF8;
            border-radius: 6px;
            padding: 13px 16px;
            margin-bottom: 1rem;
            font-size: 0.86rem;
            color: #E2E8F0;
            line-height: 1.55;
        }
        .exec-banner-warn {
            background-color: #1C1217;
            border: 1px solid #3F1D28;
            border-left: 3px solid #EF4444;
            border-radius: 6px;
            padding: 13px 16px;
            margin-bottom: 1rem;
            font-size: 0.86rem;
            color: #FCA5A5;
            line-height: 1.55;
        }
        .paywall-card {
            background: linear-gradient(180deg, #161F33 0%, #0D131F 100%);
            border: 1px solid #2563EB;
            border-left: 4px solid #38BDF8;
            border-radius: 8px;
            padding: 18px 22px;
            margin-bottom: 1.25rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
        }
        .paywall-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #F8FAFC;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .paywall-sub {
            font-size: 0.86rem;
            color: #CBD5E1;
            line-height: 1.55;
        }

        .memo-card {
            background: linear-gradient(180deg, #111827 0%, #0D131F 100%);
            border: 1px solid #1E293B;
            border-top: 3px solid #38BDF8;
            border-radius: 8px;
            padding: 24px 28px;
            margin-top: 0.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        .memo-header {
            border-bottom: 1px solid #1E293B;
            padding-bottom: 14px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
        }
        .memo-title {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            color: #F8FAFC;
            margin: 0;
        }
        .memo-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            color: #38BDF8;
        }
        .memo-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .memo-stat {
            background-color: #090D16;
            border: 1px solid #1E293B;
            border-radius: 6px;
            padding: 10px 14px;
        }
        .memo-stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748B;
            margin-bottom: 4px;
        }
        .memo-stat-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.05rem;
            font-weight: 600;
            color: #F8FAFC;
        }
        .memo-section-title {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94A3B8;
            margin-top: 16px;
            margin-bottom: 10px;
        }
        .memo-list {
            margin: 0;
            padding-left: 18px;
            color: #CBD5E1;
            font-size: 0.9rem;
            line-height: 1.7;
        }
        .memo-list li {
            margin-bottom: 8px;
        }
        .memo-highlight {
            color: #F8FAFC;
            font-weight: 600;
        }
        .memo-code {
            font-family: 'JetBrains Mono', monospace;
            background-color: #1E293B;
            color: #38BDF8;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.84rem;
        }
    </style>
    """, unsafe_allow_html=True)


apply_obsidian_theme()

# ==============================================================================
# MULTI-TENANT CLIENT DATABASE & ADMIN PERSISTENCE ENGINE
# ==============================================================================
DEFAULT_CLIENTS = {
    "demo": {
        "password": "demo123",
        "company_name": "Beirut Hospitality Group (Demo Sandbox)",
        "market": "Beirut",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 25.0,
        "card_fee_pct": 2.0,
        "whish_fee_pct": 1.0,
        "packaging_cost_usd": 0.65,
        "waste_pct": 3.0,
        "monthly_rent_usd": 1800.0,
        "monthly_payroll_usd": 2400.0,
        "monthly_generator_utilities_usd": 750.0,
        "demo_upload_mode": "teaser",
    },
    "dubai_demo": {
        "password": "demo123",
        "company_name": "Dubai Hospitality Group (Demo Sandbox)",
        "market": "Dubai",
        "default_lbp_rate": 3.6725,
        "delivery_fee_pct": 25.0,
        "card_fee_pct": 1.8,
        "whish_fee_pct": 1.0,
        "packaging_cost_usd": 0.75,
        "waste_pct": 3.0,
        "monthly_rent_usd": 4500.0,
        "monthly_payroll_usd": 5200.0,
        "monthly_generator_utilities_usd": 850.0,
        "demo_upload_mode": "teaser",
    },
}


def get_client_db() -> dict:
    db = {k: dict(v) for k, v in DEFAULT_CLIENTS.items()}
    try:
        if "clients" in st.secrets:
            for k, v in st.secrets["clients"].items():
                db[str(k).strip().lower()] = dict(v)
    except Exception:
        pass
    if os.path.exists(CLIENTS_JSON_PATH):
        try:
            with open(CLIENTS_JSON_PATH, "r", encoding="utf-8") as f:
                local_clients = json.load(f)
                for k, v in local_clients.items():
                    db[str(k).strip().lower()] = dict(v)
        except Exception:
            pass
    return db


def save_client_to_store(username: str, profile_data: dict):
    clean_user = username.strip().lower()
    existing = {}
    if os.path.exists(CLIENTS_JSON_PATH):
        try:
            with open(CLIENTS_JSON_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    existing[clean_user] = profile_data
    with open(CLIENTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def delete_client_from_store(username: str):
    clean_user = username.strip().lower()
    if os.path.exists(CLIENTS_JSON_PATH):
        try:
            with open(CLIENTS_JSON_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if clean_user in existing:
                del existing[clean_user]
                with open(CLIENTS_JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2)
        except Exception:
            pass


def save_client_cogs_df(username: str, std_cogs_df: pd.DataFrame):
    path = os.path.join(COGS_STORAGE_DIR, f"cogs_{username.strip().lower()}.csv")
    std_cogs_df.to_csv(path, index=False, encoding="utf-8")


def load_client_cogs_df(username: str) -> pd.DataFrame | None:
    path = os.path.join(COGS_STORAGE_DIR, f"cogs_{username.strip().lower()}.csv")
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return None
    return None


def format_secrets_toml(clients_dict: dict) -> str:
    lines = [
        f'admin_username = "{get_admin_username()}"',
        'admin_password = "KEEP_YOUR_SECRET_ADMIN_PASSWORD"',
        f'owner_whatsapp = "{get_owner_whatsapp()}"',
        ""
    ]
    for uname, p in clients_dict.items():
        lines.append(f"[clients.{uname}]")
        lines.append(f'password = "{p.get("password", "client123")}"')
        lines.append(f'company_name = "{p.get("company_name", uname)}"')
        lines.append(f'default_lbp_rate = {float(p.get("default_lbp_rate", 89500.0))}')
        lines.append(f'delivery_fee_pct = {float(p.get("delivery_fee_pct", 25.0))}')
        lines.append(f'card_fee_pct = {float(p.get("card_fee_pct", 2.0))}')
        lines.append(f'whish_fee_pct = {float(p.get("whish_fee_pct", 1.0))}')
        lines.append(f'packaging_cost_usd = {float(p.get("packaging_cost_usd", 0.65))}')
        lines.append(f'waste_pct = {float(p.get("waste_pct", 3.0))}')
        lines.append(f'monthly_rent_usd = {float(p.get("monthly_rent_usd", 1800.0))}')
        lines.append(f'monthly_payroll_usd = {float(p.get("monthly_payroll_usd", 2400.0))}')
        lines.append(f'monthly_generator_utilities_usd = {float(p.get("monthly_generator_utilities_usd", 750.0))}')
        if uname == "demo":
            lines.append(f'demo_upload_mode = "{p.get("demo_upload_mode", "teaser")}"')
        lines.append("")
    return "\n".join(lines)


# ==============================================================================
# ZERO-FRICTION URL AUTO-LOGIN (?demo=true or ?client=...) & SESSION STATE
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.client_profile = None
    st.session_state.is_admin = False

query_params = st.query_params
if not st.session_state.authenticated:
    demo_param = str(query_params.get("demo", "")).strip().lower()
    market_param = str(query_params.get("market", query_params.get("city", ""))).strip().title()
    company_param = str(query_params.get("company", "")).strip()

    if demo_param in ["1", "true", "yes"] or market_param in ["Beirut", "Dubai"] or company_param:
        clients = get_client_db()
        base_key = "dubai_demo" if market_param == "Dubai" else "demo"
        profile = dict(clients.get(base_key, clients["demo"]))
        if company_param:
            profile["company_name"] = f"{company_param} (Live Demo Audit)"
        st.session_state.authenticated = True
        st.session_state.username = "demo"
        st.session_state.client_profile = profile
        st.session_state.is_admin = False
    elif "client" in query_params and "key" in query_params:
        c_user = str(query_params.get("client", "")).strip().lower()
        c_key = str(query_params.get("key", ""))
        clients = get_client_db()
        if c_user in clients and clients[c_user]["password"] == c_key:
            st.session_state.authenticated = True
            st.session_state.username = c_user
            st.session_state.client_profile = dict(clients[c_user])
            st.session_state.is_admin = False


def login_screen():
    st.write("")
    col1, col2, col3 = st.columns([1.2, 1.4, 1.2])
    with col2:
        st.markdown("""
        <div class="suite-header">
            <div class="suite-kicker">FINANCIAL ANALYTICS & RECONCILIATION</div>
            <h1 class="suite-title">Executive POS & EBITDA Suite</h1>
            <div class="suite-subtitle">Multi-currency normalization, aggregator fee auditing, menu engineering, and shift reconciliation.</div>
        </div>
        """, unsafe_allow_html=True)

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("🇱🇧 Launch Beirut Demo", type="primary", use_container_width=True):
                clients = get_client_db()
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.client_profile = dict(clients["demo"])
                st.session_state.is_admin = False
                st.rerun()
        with d_col2:
            if st.button("🇦🇪 Launch Dubai Demo", type="primary", use_container_width=True):
                clients = get_client_db()
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.client_profile = dict(clients.get("dubai_demo", clients["demo"]))
                st.session_state.is_admin = False
                st.rerun()

        st.markdown(
            "<div style='text-align:center; color:#64748B; font-size:0.72rem; margin: 18px 0; "
            "text-transform:uppercase; letter-spacing:0.08em;'>Client & Administrator Sign In</div>",
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input("Account Identifier", placeholder="Enter client username").strip().lower()
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                admin_user = get_admin_username()
                admin_pw = get_admin_password()

                if username == admin_user and admin_pw is not None and password == admin_pw:
                    clients = get_client_db()
                    st.session_state.authenticated = True
                    st.session_state.username = admin_user
                    st.session_state.client_profile = dict(clients["demo"])
                    st.session_state.is_admin = True
                    st.rerun()

                clients = get_client_db()
                if username in clients and clients[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.client_profile = dict(clients[username])
                    st.session_state.is_admin = False
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use the buttons above to launch the demo environment.")


# ==============================================================================
# FILE PARSING & DATA NORMALIZATION
# ==============================================================================
def safe_read_file(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()
    raw_bytes = uploaded_file.getvalue()

    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw_bytes))
        return df.dropna(how="all")

    for encoding in ["utf-8-sig", "cp1256", "latin1", "utf-16"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, sep=sep)
                if len(df.columns) > 1:
                    return df.dropna(how="all")
            except Exception:
                continue
    uploaded_file.seek(0)
    return pd.read_csv(uploaded_file)


def guess_column_index(columns: list, keywords: list, allow_none: bool = False) -> int:
    offset = 1 if allow_none else 0
    for idx, col in enumerate(columns):
        clean_col = str(col).strip().lower()
        for kw in keywords:
            if kw in clean_col:
                return idx + offset
    return 0


def clean_numeric_series(series: pd.Series, default_val: float = 0.0) -> pd.Series:
    def parse_val(val):
        if pd.isna(val):
            return float(default_val)
        s = str(val).strip()
        if not s:
            return float(default_val)
        is_neg = s.startswith("(") and s.endswith(")")
        s = re.sub(r"[^0-9.,-]", "", s)
        if not s:
            return float(default_val)
        if "," in s and "." not in s:
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        else:
            s = s.replace(",", "")
        try:
            num = float(s)
            return float(-abs(num) if is_neg else num)
        except Exception:
            return float(default_val)

    return pd.to_numeric(series.apply(parse_val), errors="coerce").fillna(float(default_val)).astype("float64")


def classify_channel_and_fee(raw_channel: str, delivery_fee: float, card_fee: float, whish_fee: float):
    c = str(raw_channel).strip().lower()
    if any(k in c for k in ["toter", "talabat", "deliveroo", "careem", "noon", "zomato", "jahez", "hunger", "aggregat", "delivery"]):
        return "Delivery Aggregators", float(delivery_fee), True
    if any(k in c for k in ["whish", "wish", "omt", "bob", "wallet", "apple pay", "tap"]):
        return "Digital Wallet (Whish)", float(whish_fee), False
    if any(k in c for k in ["card", "visa", "master", "amex", "pos", "bank", "carte", "credit", "debit", "network"]):
        return "Card POS Terminal", float(card_fee), False
    return "In-Store Cash", 0.0, False


# ==============================================================================
# SAMPLE DATA GENERATOR
# ==============================================================================
@st.cache_data
def generate_sample_datasets(lbp_rate: float, market: str = "Beirut"):
    if market == "Dubai":
        cogs_data = [
            {"SKU": "SKU-101", "Item_Name": "Double Wagyu Smash Burger", "Category": "Mains", "Unit_Cost_USD": 4.40, "Menu_Price_USD": 13.50},
            {"SKU": "SKU-102", "Item_Name": "Nashville Hot Chicken Sliders", "Category": "Mains", "Unit_Cost_USD": 4.90, "Menu_Price_USD": 9.80},
            {"SKU": "SKU-103", "Item_Name": "Burrata & Heirloom Tomato Bowl", "Category": "Salads", "Unit_Cost_USD": 2.60, "Menu_Price_USD": 11.50},
            {"SKU": "SKU-104", "Item_Name": "Truffle Parmesan Crinkle Fries", "Category": "Sides", "Unit_Cost_USD": 1.15, "Menu_Price_USD": 5.50},
            {"SKU": "SKU-105", "Item_Name": "2-For-1 Aggregator Meal Box (Promo)", "Category": "Promos", "Unit_Cost_USD": 9.10, "Menu_Price_USD": 13.50},
            {"SKU": "SKU-106", "Item_Name": "Spanish Saffron Iced Latte", "Category": "Beverages", "Unit_Cost_USD": 1.35, "Menu_Price_USD": 6.00},
        ]
        branches = ["Downtown Dubai", "JLT Cluster D", "Dubai Marina Walk"]
        channels = ["In-Store Cash", "Apple Pay / Wallet", "Network Card POS", "Talabat Delivery", "Deliveroo / Careem"]
    else:
        cogs_data = [
            {"SKU": "SKU-101", "Item_Name": "Signature Truffle Burger", "Category": "Mains", "Unit_Cost_USD": 4.20, "Menu_Price_USD": 13.50},
            {"SKU": "SKU-102", "Item_Name": "Crispy Chicken Sliders", "Category": "Mains", "Unit_Cost_USD": 4.80, "Menu_Price_USD": 9.50},
            {"SKU": "SKU-103", "Item_Name": "Artisanal Kale & Quinoa Salad", "Category": "Salads", "Unit_Cost_USD": 2.40, "Menu_Price_USD": 11.00},
            {"SKU": "SKU-104", "Item_Name": "Loaded Parmesan Fries", "Category": "Sides", "Unit_Cost_USD": 1.10, "Menu_Price_USD": 5.50},
            {"SKU": "SKU-105", "Item_Name": "Combo Meal Box (Aggregator Promo)", "Category": "Promos", "Unit_Cost_USD": 8.90, "Menu_Price_USD": 13.00},
            {"SKU": "SKU-106", "Item_Name": "Specialty Iced Matcha Latte", "Category": "Beverages", "Unit_Cost_USD": 1.30, "Menu_Price_USD": 5.50},
        ]
        branches = ["Ashrafieh Flagship", "Mar Mikhael Branch", "Dbayeh Highway"]
        channels = ["In-Store Cash", "Whish Money", "Bank Card POS", "Toters Delivery", "Talabat / Deliveroo"]

    cogs_df = pd.DataFrame(cogs_data)
    sku_weights = [0.26, 0.20, 0.09, 0.19, 0.16, 0.10]
    cashiers = ["Nabil K.", "Maya S.", "Rami H.", "System_Aggregator"]
    channel_weights = [0.32, 0.18, 0.15, 0.23, 0.12]

    rng = random.Random(42)
    rows = []
    start_date = datetime(2026, 10, 1)

    for i in range(1, 621):
        sku_info = rng.choices(cogs_data, weights=sku_weights)[0]
        qty = rng.choices([1, 2, 3, 4], weights=[0.50, 0.32, 0.12, 0.06])[0]
        channel = rng.choices(channels, weights=channel_weights)[0]
        branch = rng.choice(branches)
        cashier = "System_Aggregator" if any(k in channel for k in ["Toters", "Talabat", "Deliveroo"]) else rng.choice(cashiers[:3])
        tx_date = start_date + timedelta(days=rng.randint(0, 14))
        date_str = tx_date.strftime("%Y-%m-%d")

        list_gross_usd = sku_info["Menu_Price_USD"] * qty

        discount_usd = 0.0
        if cashier == "Rami H." and channel == "In-Store Cash" and rng.random() < 0.25:
            discount_usd = round(list_gross_usd * rng.choice([0.20, 0.40, 0.50]), 2)
        elif rng.random() < 0.03:
            discount_usd = round(list_gross_usd * 0.10, 2)

        net_charged_usd = max(0.0, list_gross_usd - discount_usd)

        if market == "Dubai":
            is_local = rng.random() < 0.75
            currency = "AED" if is_local else "USD"
            fx = lbp_rate if lbp_rate < 100 else 3.6725
            raw_amount = round(net_charged_usd * fx, 2) if is_local else net_charged_usd
        else:
            is_lbp = (channel == "In-Store Cash") and (rng.random() < 0.35)
            currency = "LBP" if is_lbp else "USD"
            fx = lbp_rate if lbp_rate >= 100 else 89500.0
            raw_amount = round(net_charged_usd * fx, -3) if is_lbp else net_charged_usd

        rows.append({
            "Order_ID": f"ORD-{10000 + i}",
            "Date": date_str,
            "Branch": branch,
            "Cashier_Server": cashier,
            "Channel": channel,
            "SKU": sku_info["SKU"],
            "Item_Sold": sku_info["Item_Name"],
            "Quantity": qty,
            "Currency": currency,
            "Discount_USD": discount_usd,
            "Gross_Amount_Raw": raw_amount
        })

    return pd.DataFrame(rows), cogs_df


# ==============================================================================
# CORE FINANCIAL & BCG MATRIX ENGINE (PANDAS 3.0 / PYTHON 3.14 SAFE)
# ==============================================================================
def process_standardized_data(
    std_pos: pd.DataFrame,
    std_cogs: pd.DataFrame | None,
    lbp_rate: float,
    delivery_fee: float,
    card_fee: float,
    whish_fee: float,
    packaging_cost_usd: float,
    waste_pct: float,
    supplier_inflation_pct: float,
    fallback_cogs_pct: float
) -> pd.DataFrame:
    df = std_pos.copy()
    parsed_dates = pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce")
    df["Clean_Date"] = parsed_dates.dt.strftime("%Y-%m-%d").fillna(datetime.today().strftime("%Y-%m-%d"))
    df["Branch"] = df["Branch"].astype(str).str.strip()
    df["Cashier_Server"] = df.get("Cashier_Server", pd.Series(["Standard_POS"] * len(df), index=df.index)).astype(str).str.strip()

    qty_series = clean_numeric_series(df["Quantity"], default_val=1.0)
    df["Quantity"] = qty_series.where(qty_series > 0, 1.0).astype("float64")
    df["Gross_Amount_Raw"] = clean_numeric_series(df["Gross_Amount_Raw"], default_val=0.0)
    df["Discount_USD"] = clean_numeric_series(df.get("Discount_USD", pd.Series([0.0] * len(df), index=df.index)), default_val=0.0)

    safe_rate = float(lbp_rate) if lbp_rate and lbp_rate > 0 else 89500.0

    def calc_usd(row):
        curr = str(row["Currency"]).strip().upper()
        amt = float(row["Gross_Amount_Raw"])
        if any(k in curr for k in ["LBP", "LL", "L.L"]):
            return amt / (safe_rate if safe_rate >= 100 else 89500.0)
        if any(k in curr for k in ["AED", "DHS", "DH"]):
            return amt / (safe_rate if safe_rate < 100 else 3.6725)
        if curr == "AUTO":
            if amt >= 10000:
                return amt / (safe_rate if safe_rate >= 100 else 89500.0)
            if safe_rate < 100:
                return amt / safe_rate
        return amt

    df["Gross_Sales_USD"] = pd.to_numeric(df.apply(calc_usd, axis=1), errors="coerce").fillna(0.0).astype("float64")
    df = df[df["Gross_Sales_USD"] > 0].copy().reset_index(drop=True)

    # Pandas 3.0 / StringDtype safe COGS & Category mapping (avoids in-place .loc dtype clashes)
    cost_series = pd.Series(float("nan"), index=df.index, dtype="float64")
    cat_series = pd.Series("General", index=df.index, dtype="object")

    if std_cogs is not None and not std_cogs.empty:
        cogs_clean = std_cogs.copy()
        cogs_clean["Unit_Cost_USD"] = clean_numeric_series(cogs_clean["Unit_Cost_USD"], default_val=0.0)

        if "SKU" in cogs_clean.columns and (df["SKU"].astype(str) != "N/A").any():
            cogs_clean["_sku_key"] = cogs_clean["SKU"].astype(str).str.strip()
            sku_dedup = cogs_clean.drop_duplicates(subset=["_sku_key"])
            sku_cost_dict = dict(zip(sku_dedup["_sku_key"], sku_dedup["Unit_Cost_USD"]))
            df_sku_keys = df["SKU"].astype(str).str.strip()
            cost_series = pd.to_numeric(df_sku_keys.map(sku_cost_dict), errors="coerce").astype("float64")

            if "Category" in sku_dedup.columns:
                sku_cat_dict = dict(zip(sku_dedup["_sku_key"], sku_dedup["Category"].astype(str)))
                cat_series = df_sku_keys.map(sku_cat_dict).fillna("General").astype(str)

        if "Item_Name" in cogs_clean.columns:
            cogs_clean["_item_key"] = cogs_clean["Item_Name"].astype(str).str.strip().str.lower()
            name_dedup = cogs_clean.drop_duplicates(subset=["_item_key"])
            name_cost_dict = dict(zip(name_dedup["_item_key"], name_dedup["Unit_Cost_USD"]))
            df_item_keys = df["Item_Name"].astype(str).str.strip().str.lower()
            name_cost_series = pd.to_numeric(df_item_keys.map(name_cost_dict), errors="coerce").astype("float64")
            cost_series = cost_series.combine_first(name_cost_series).astype("float64")

            if "Category" in name_dedup.columns:
                name_cat_dict = dict(zip(name_dedup["_item_key"], name_dedup["Category"].astype(str)))
                name_cat_series = df_item_keys.map(name_cat_dict).fillna("General").astype(str)
                cat_series = cat_series.where(cat_series != "General", name_cat_series)

    df["Unit_Cost_USD"] = cost_series.astype("float64")
    df["Category"] = cat_series.fillna("General").astype(str)

    raw_cogs = (df["Quantity"] * df["Unit_Cost_USD"]).astype("float64")
    fallback_raw = (df["Gross_Sales_USD"] * float(fallback_cogs_pct)).astype("float64")
    unmatched = raw_cogs.isna() | (raw_cogs <= 0)

    df["Raw_COGS_USD"] = raw_cogs.where(~unmatched, fallback_raw).astype("float64")
    df["Unit_Cost_USD"] = (df["Raw_COGS_USD"] / df["Quantity"]).astype("float64")

    df["Raw_COGS_USD"] = (df["Raw_COGS_USD"] * (1.0 + float(supplier_inflation_pct))).astype("float64")
    df["Waste_Cost_USD"] = (df["Raw_COGS_USD"] * float(waste_pct)).astype("float64")
    df["Total_COGS_USD"] = (df["Raw_COGS_USD"] + df["Waste_Cost_USD"]).astype("float64")

    ch_results = [classify_channel_and_fee(c, delivery_fee, card_fee, whish_fee) for c in df["Channel"]]
    df["Channel"] = [r[0] for r in ch_results]
    df["Fee_Pct"] = pd.Series([r[1] for r in ch_results], index=df.index, dtype="float64")
    df["Is_Delivery"] = pd.Series([r[2] for r in ch_results], index=df.index, dtype="bool")

    df["Platform_Fee_USD"] = (df["Gross_Sales_USD"] * df["Fee_Pct"]).astype("float64")
    df["Packaging_Cost_USD"] = (
        df["Quantity"] * float(packaging_cost_usd) * df["Is_Delivery"].astype("float64")
    ).astype("float64")
    df["Net_Revenue_USD"] = (df["Gross_Sales_USD"] - df["Platform_Fee_USD"]).astype("float64")
    df["Net_Profit_USD"] = (df["Net_Revenue_USD"] - df["Total_COGS_USD"] - df["Packaging_Cost_USD"]).astype("float64")
    df["Net_Margin_Pct"] = (df["Net_Profit_USD"] / df["Gross_Sales_USD"]).astype("float64")

    return df


def build_bcg_menu_matrix(df: pd.DataFrame) -> pd.DataFrame:
    sku_df = df.groupby(["SKU", "Item_Name", "Category"], as_index=False).agg(
        Units_Sold=("Quantity", "sum"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Packaging_USD=("Packaging_Cost_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Net_Profit_USD=("Net_Profit_USD", "sum")
    )
    sku_df["Avg_Unit_Price_USD"] = sku_df["Gross_Sales_USD"] / sku_df["Units_Sold"]
    sku_df["Unit_Contribution_USD"] = sku_df["Net_Profit_USD"] / sku_df["Units_Sold"]
    sku_df["Margin_Pct"] = (sku_df["Net_Profit_USD"] / sku_df["Gross_Sales_USD"]) * 100.0

    avg_units = sku_df["Units_Sold"].mean() if not sku_df.empty else 0
    avg_contrib = sku_df["Unit_Contribution_USD"].mean() if not sku_df.empty else 0

    def classify_bcg(row):
        high_vol = row["Units_Sold"] >= avg_units
        high_prof = row["Unit_Contribution_USD"] >= avg_contrib and row["Margin_Pct"] >= 25.0
        if high_vol and high_prof:
            return "STAR — Protect & Feature"
        if high_vol and not high_prof:
            return "PLOWHORSE — Reprice (+USD)"
        if not high_vol and high_prof:
            return "PUZZLE — Increase Visibility"
        return "UNDERPERFORMER — Review / Cut"

    sku_df["Classification"] = sku_df.apply(classify_bcg, axis=1)
    return sku_df.sort_values("Net_Profit_USD", ascending=False)


# ==============================================================================
# ENTERPRISE ENGINE #1: AGGREGATOR CLAWBACK & OVERCHARGE FORENSIC MATCHER
# ==============================================================================
def generate_sample_aggregator_statement(cleaned_df: pd.DataFrame, contracted_fee: float) -> pd.DataFrame:
    """Generates a realistic weekly aggregator payout statement with intentional clawbacks & fee overcharges."""
    deliv_df = cleaned_df[cleaned_df["Is_Delivery"]].copy().reset_index(drop=True)
    if deliv_df.empty:
        return pd.DataFrame(columns=[
            "Order_ID", "Statement_Date", "Aggregator_Gross_USD",
            "Aggregator_Commission_USD", "Unverified_Refund_Clawback_USD",
            "Promo_CoPay_Deduction_USD", "Aggregator_Net_Paid_USD", "Aggregator_Note"
        ])

    rng = random.Random(101)
    stmt_rows = []
    for idx, row in deliv_df.iterrows():
        order_id = str(row["Order_ID"])
        gross = float(row["Gross_Sales_USD"])
        expected_fee = round(gross * float(contracted_fee), 2)
        roll = rng.random()

        # ~4% of orders are completely omitted from the weekly settlement ("Ghost Orders")
        if roll < 0.04:
            continue

        actual_fee = expected_fee
        refund_clawback = 0.0
        promo_deduction = 0.0
        note = "Standard Settlement"

        if 0.04 <= roll < 0.10:
            # Commission tier overcharge (charged 29-31% instead of contracted rate)
            over_rate = float(contracted_fee) + rng.choice([0.04, 0.05, 0.06])
            actual_fee = round(gross * over_rate, 2)
            note = f"Rate Applied: {over_rate*100:.1f}% (Tier Mismatch)"
        elif 0.10 <= roll < 0.15:
            # Unverified customer complaint / missing item 100% or 50% clawback
            refund_clawback = round(gross * rng.choice([0.50, 1.00]), 2)
            note = "Customer Dispute Clawback (No Photo Proof)"
        elif 0.15 <= roll < 0.19:
            # Co-funded promo where 100% of discount was charged to restaurant instead of 50/50
            promo_deduction = round(gross * rng.choice([0.15, 0.20]), 2)
            note = "Campaign Co-Pay Deduction (100% Charged)"

        net_paid = round(max(0.0, gross - actual_fee - refund_clawback - promo_deduction), 2)
        stmt_rows.append({
            "Order_ID": order_id,
            "Statement_Date": str(row["Clean_Date"]),
            "Aggregator_Gross_USD": round(gross, 2),
            "Aggregator_Commission_USD": actual_fee,
            "Unverified_Refund_Clawback_USD": refund_clawback,
            "Promo_CoPay_Deduction_USD": promo_deduction,
            "Aggregator_Net_Paid_USD": net_paid,
            "Aggregator_Note": note,
        })

    return pd.DataFrame(stmt_rows)


def audit_aggregator_settlement(
    cleaned_df: pd.DataFrame,
    settlement_df: pd.DataFrame,
    contracted_fee: float,
    demo_paywall_active: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Cross-matches POS delivery orders against the aggregator settlement statement order-by-order."""
    pos_deliv = cleaned_df[cleaned_df["Is_Delivery"]].copy()
    if pos_deliv.empty:
        empty_df = pd.DataFrame()
        return empty_df, empty_df, empty_df, {
            "pos_orders": 0, "expected_net": 0.0, "actual_paid": 0.0,
            "total_recoverable": 0.0, "disputed_count": 0,
            "ghost_usd": 0.0, "overcharge_usd": 0.0, "clawback_usd": 0.0, "promo_err_usd": 0.0
        }

    pos_deliv["Order_ID_Key"] = pos_deliv["Order_ID"].astype(str).str.strip().str.upper()
    pos_grouped = pos_deliv.groupby("Order_ID_Key", as_index=False).agg(
        Order_ID=("Order_ID", "first"),
        Clean_Date=("Clean_Date", "first"),
        Branch=("Branch", "first"),
        Item_Name=("Item_Name", "first"),
        POS_Gross_USD=("Gross_Sales_USD", "sum"),
        POS_Expected_Fee_USD=("Platform_Fee_USD", "sum"),
        POS_Expected_Net_USD=("Net_Revenue_USD", "sum"),
    )

    stmt = settlement_df.copy()
    if not stmt.empty and "Order_ID" in stmt.columns:
        stmt["Order_ID_Key"] = stmt["Order_ID"].astype(str).str.strip().str.upper()
        for col in ["Aggregator_Gross_USD", "Aggregator_Commission_USD", "Unverified_Refund_Clawback_USD", "Promo_CoPay_Deduction_USD", "Aggregator_Net_Paid_USD"]:
            if col in stmt.columns:
                stmt[col] = clean_numeric_series(stmt[col], 0.0)
            else:
                stmt[col] = 0.0
        stmt_grouped = stmt.groupby("Order_ID_Key", as_index=False).agg(
            Aggregator_Gross_USD=("Aggregator_Gross_USD", "sum"),
            Aggregator_Commission_USD=("Aggregator_Commission_USD", "sum"),
            Unverified_Refund_Clawback_USD=("Unverified_Refund_Clawback_USD", "sum"),
            Promo_CoPay_Deduction_USD=("Promo_CoPay_Deduction_USD", "sum"),
            Aggregator_Net_Paid_USD=("Aggregator_Net_Paid_USD", "sum"),
        )
        merged = pd.merge(pos_grouped, stmt_grouped, on="Order_ID_Key", how="left")
    else:
        merged = pos_grouped.copy()
        for col in ["Aggregator_Gross_USD", "Aggregator_Commission_USD", "Unverified_Refund_Clawback_USD", "Promo_CoPay_Deduction_USD", "Aggregator_Net_Paid_USD"]:
            merged[col] = float("nan")

    is_missing = merged["Aggregator_Net_Paid_USD"].isna()
    for col in ["Aggregator_Gross_USD", "Aggregator_Commission_USD", "Unverified_Refund_Clawback_USD", "Promo_CoPay_Deduction_USD", "Aggregator_Net_Paid_USD"]:
        merged[col] = merged[col].fillna(0.0).astype("float64")

    merged["Fee_Overcharge_USD"] = (merged["Aggregator_Commission_USD"] - merged["POS_Expected_Fee_USD"]).clip(lower=0.0).round(2)
    merged["Recoverable_Claim_USD"] = (merged["POS_Expected_Net_USD"] - merged["Aggregator_Net_Paid_USD"]).clip(lower=0.0).round(2)
    merged["Effective_Fee_Pct"] = (
        merged["Aggregator_Commission_USD"] / merged["POS_Gross_USD"].replace(0, 1.0) * 100.0
    ).round(1)

    violations = []
    for idx, r in merged.iterrows():
        if is_missing.iloc[idx]:
            violations.append("GHOST ORDER — Missing from Payout")
        elif r["Unverified_Refund_Clawback_USD"] > 0.05:
            violations.append("UNVERIFIED CLAWBACK — Customer Refund Deducted")
        elif r["Promo_CoPay_Deduction_USD"] > 0.05:
            violations.append("PROMO SPLIT ERROR — 100% Discount Charged")
        elif r["Fee_Overcharge_USD"] > 0.15:
            violations.append(f"COMMISSION OVERCHARGE ({r['Effective_Fee_Pct']:.1f}% vs {contracted_fee*100:.1f}%)")
        elif r["Recoverable_Claim_USD"] > 0.25:
            violations.append("NET PAYOUT SHORTFALL")
        else:
            violations.append("SETTLED AS CONTRACTED")

    merged["Audit_Finding"] = violations

    if demo_paywall_active:
        merged["Item_Name"] = [f"[REDACTED SKU — License Required]" for _ in range(len(merged))]

    disputed_df = merged[merged["Audit_Finding"] != "SETTLED AS CONTRACTED"].copy().sort_values("Recoverable_Claim_USD", ascending=False)

    type_summary = (
        disputed_df.groupby("Audit_Finding", as_index=False)
        .agg(
            Disputed_Orders=("Order_ID", "count"),
            POS_Expected_Net_USD=("POS_Expected_Net_USD", "sum"),
            Aggregator_Net_Paid_USD=("Aggregator_Net_Paid_USD", "sum"),
            Recoverable_Claim_USD=("Recoverable_Claim_USD", "sum"),
        )
        .sort_values("Recoverable_Claim_USD", ascending=False)
    )

    ghost_usd = float(merged.loc[merged["Audit_Finding"].str.startswith("GHOST"), "Recoverable_Claim_USD"].sum())
    clawback_usd = float(merged["Unverified_Refund_Clawback_USD"].sum())
    overcharge_usd = float(merged["Fee_Overcharge_USD"].sum())
    promo_err_usd = float(merged["Promo_CoPay_Deduction_USD"].sum())

    stats = {
        "pos_orders": int(len(merged)),
        "expected_net": float(merged["POS_Expected_Net_USD"].sum()),
        "actual_paid": float(merged["Aggregator_Net_Paid_USD"].sum()),
        "total_recoverable": float(disputed_df["Recoverable_Claim_USD"].sum()),
        "disputed_count": int(len(disputed_df)),
        "ghost_usd": ghost_usd,
        "overcharge_usd": overcharge_usd,
        "clawback_usd": clawback_usd,
        "promo_err_usd": promo_err_usd,
    }
    return merged, disputed_df, type_summary, stats


def build_dispute_claim_excel(
    disputed_df: pd.DataFrame,
    type_summary: pd.DataFrame,
    company_name: str,
    contracted_fee: float,
    stats: dict
) -> bytes:
    """Builds a formal 2-Tab Aggregator Dispute Claim Excel Packet ready to email to Toters/Talabat finance."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", engine_kwargs={"options": {"in_memory": True}}) as writer:
        wb = writer.book
        title_fmt = wb.add_format({"bold": True, "font_size": 14, "font_color": "#0F172A"})
        sub_fmt = wb.add_format({"italic": True, "font_size": 10, "font_color": "#475569"})
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#991B1B", "font_color": "#FFFFFF", "border": 1, "align": "center"})
        usd_fmt = wb.add_format({"num_format": "$#,##0.00", "border": 1})
        int_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
        txt_fmt = wb.add_format({"border": 1})
        tot_txt = wb.add_format({"bold": True, "bg_color": "#FEE2E2", "font_color": "#991B1B", "border": 1})
        tot_usd = wb.add_format({"bold": True, "bg_color": "#FEE2E2", "font_color": "#991B1B", "num_format": "$#,##0.00", "border": 1})

        ws1 = wb.add_worksheet("01_Official_Dispute_Claim")
        ws1.hide_gridlines(2)
        ws1.write("B2", f"OFFICIAL AGGREGATOR SETTLEMENT DISPUTE CLAIM — {company_name.upper()}", title_fmt)
        ws1.write("B3", f"Contracted Commission Rate: {contracted_fee*100:.1f}% | Disputed Orders: {stats['disputed_count']} | Total Claim Amount: ${stats['total_recoverable']:,.2f} USD", sub_fmt)

        cols_s = ["Discrepancy / Violation Category", "Affected Orders", "POS Expected Net (USD)", "Aggregator Settled (USD)", "Net Claim Owed (USD)"]
        for idx, c in enumerate(cols_s):
            ws1.write(5, 1 + idx, c, hdr_fmt)

        for r_i, r in enumerate(type_summary.itertuples(index=False), start=6):
            ws1.write(r_i, 1, r.Audit_Finding, txt_fmt)
            ws1.write(r_i, 2, int(r.Disputed_Orders), int_fmt)
            ws1.write(r_i, 3, float(r.POS_Expected_Net_USD), usd_fmt)
            ws1.write(r_i, 4, float(r.Aggregator_Net_Paid_USD), usd_fmt)
            ws1.write(r_i, 5, float(r.Recoverable_Claim_USD), usd_fmt)

        t_row = 6 + len(type_summary)
        ws1.write(t_row, 1, "TOTAL CREDIT MEMO / REIMBURSEMENT CLAIMED", tot_txt)
        ws1.write(t_row, 2, int(stats["disputed_count"]), tot_txt)
        ws1.write(t_row, 3, float(disputed_df["POS_Expected_Net_USD"].sum()) if not disputed_df.empty else 0.0, tot_usd)
        ws1.write(t_row, 4, float(disputed_df["Aggregator_Net_Paid_USD"].sum()) if not disputed_df.empty else 0.0, tot_usd)
        ws1.write(t_row, 5, float(stats["total_recoverable"]), tot_usd)
        ws1.set_column("B:B", 44)
        ws1.set_column("C:F", 24)

        ws2 = wb.add_worksheet("02_Order_Level_Evidence")
        ws2.freeze_panes(1, 0)
        ev_cols = [
            ("Order_ID", "Order ID", txt_fmt),
            ("Clean_Date", "Order Date", txt_fmt),
            ("Branch", "Branch", txt_fmt),
            ("Item_Name", "Primary Item", txt_fmt),
            ("POS_Gross_USD", "POS Gross ($)", usd_fmt),
            ("POS_Expected_Fee_USD", "Contracted Fee ($)", usd_fmt),
            ("Aggregator_Commission_USD", "Charged Fee ($)", usd_fmt),
            ("Unverified_Refund_Clawback_USD", "Refund Clawback ($)", usd_fmt),
            ("Promo_CoPay_Deduction_USD", "Promo Overcharge ($)", usd_fmt),
            ("POS_Expected_Net_USD", "Expected Net ($)", usd_fmt),
            ("Aggregator_Net_Paid_USD", "Actual Paid ($)", usd_fmt),
            ("Recoverable_Claim_USD", "Claim Variance ($)", tot_usd),
            ("Audit_Finding", "Violation Reason", txt_fmt),
        ]
        for c_i, (_, title, _) in enumerate(ev_cols):
            ws2.write(0, c_i, title, hdr_fmt)

        for r_i, (_, row_s) in enumerate(disputed_df.iterrows(), start=1):
            for c_i, (col_key, _, cell_fmt) in enumerate(ev_cols):
                val = row_s[col_key]
                ws2.write(r_i, c_i, float(val) if cell_fmt in (usd_fmt, tot_usd) else str(val), cell_fmt)

        if not disputed_df.empty:
            ws2.autofilter(0, 0, len(disputed_df), len(ev_cols) - 1)
        ws2.set_column(0, len(ev_cols) - 1, 20)

    return output.getvalue()


# ==============================================================================
# ENTERPRISE ENGINE #3: REGISTER FORENSICS (CASH-ONLY DISCOUNT BIAS & FRAUD)
# ==============================================================================
def build_register_forensics(
    cleaned_df: pd.DataFrame,
    demo_paywall_active: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Detects post-payment cash pocketing via Cash- vs. Card-Discount Bias & peer benchmarking."""
    in_store_df = cleaned_df[~cleaned_df["Is_Delivery"]].copy()
    if in_store_df.empty:
        in_store_df = cleaned_df.copy()

    in_store_df["Is_Cash_Ticket"] = in_store_df["Channel"] == "In-Store Cash"
    in_store_df["Pre_Discount_Gross_USD"] = in_store_df["Gross_Sales_USD"] + in_store_df["Discount_USD"]
    in_store_df["Ticket_Discount_Pct"] = (
        in_store_df["Discount_USD"] / in_store_df["Pre_Discount_Gross_USD"].replace(0, 1.0) * 100.0
    ).round(1)
    in_store_df["Is_Bev_Or_Side"] = in_store_df["Category"].astype(str).str.lower().str.contains("bev|drink|side|coffee|latte")

    records = []
    for (branch, operator), grp in in_store_df.groupby(["Branch", "Cashier_Server"]):
        if str(operator) == "System_Aggregator":
            continue
        cash_grp = grp[grp["Is_Cash_Ticket"]]
        noncash_grp = grp[~grp["Is_Cash_Ticket"]]

        cash_orders = len(cash_grp)
        noncash_orders = len(noncash_grp)
        total_orders = len(grp)

        cash_disc_orders = int((cash_grp["Discount_USD"] > 0).sum())
        noncash_disc_orders = int((noncash_grp["Discount_USD"] > 0).sum())

        cash_disc_usd = float(cash_grp["Discount_USD"].sum())
        noncash_disc_usd = float(noncash_grp["Discount_USD"].sum())
        total_disc_usd = cash_disc_usd + noncash_disc_usd

        cash_pre_gross = float(cash_grp["Pre_Discount_Gross_USD"].sum())
        noncash_pre_gross = float(noncash_grp["Pre_Discount_Gross_USD"].sum())
        total_pre_gross = cash_pre_gross + noncash_pre_gross

        cash_disc_rate_pct = (cash_disc_usd / cash_pre_gross * 100.0) if cash_pre_gross > 0 else 0.0
        noncash_disc_rate_pct = (noncash_disc_usd / noncash_pre_gross * 100.0) if noncash_pre_gross > 0 else 0.0
        overall_disc_rate_pct = (total_disc_usd / total_pre_gross * 100.0) if total_pre_gross > 0 else 0.0

        cash_ticket_freq_pct = (cash_disc_orders / cash_orders * 100.0) if cash_orders > 0 else 0.0
        noncash_ticket_freq_pct = (noncash_disc_orders / noncash_orders * 100.0) if noncash_orders > 0 else 0.0

        # Cash-Only Discount Bias Multiplier (compares Cash Discount % against Card/Wallet Discount %)
        baseline_noncash = max(noncash_disc_rate_pct, 0.6)
        cash_bias_ratio = round(cash_disc_rate_pct / baseline_noncash, 1) if cash_disc_rate_pct > 0 else 0.0

        bev_attach_pct = (grp["Is_Bev_Or_Side"].sum() / total_orders * 100.0) if total_orders > 0 else 0.0

        # Forensic Risk Score (0 - 100)
        score = min(100.0, (
            min(45.0, cash_disc_rate_pct * 5.0)
            + min(35.0, max(0.0, cash_bias_ratio - 1.5) * 6.0)
            + min(20.0, cash_ticket_freq_pct * 0.9)
        ))
        score = round(score, 0)

        if score >= 65 or (cash_bias_ratio >= 3.5 and cash_disc_rate_pct >= 4.0):
            verdict = "CRITICAL: CASH-POCKETING SIGNATURE"
        elif score >= 40 or overall_disc_rate_pct >= 4.0:
            verdict = "HIGH RISK: EXCESSIVE COMPING"
        elif score >= 22:
            verdict = "ELEVATED: MONITOR SHIFT"
        else:
            verdict = "CLEARED: WITHIN PEER NORM"

        records.append({
            "Branch": branch,
            "Cashier_Server": operator,
            "Total_Orders": total_orders,
            "Cash_Orders": cash_orders,
            "Cash_Disc_Tickets": cash_disc_orders,
            "Cash_Discounts_USD": round(cash_disc_usd, 2),
            "Cash_Disc_Rate_Pct": round(cash_disc_rate_pct, 1),
            "Card_Wallet_Disc_Rate_Pct": round(noncash_disc_rate_pct, 1),
            "Cash_Bias_Ratio": cash_bias_ratio,
            "Bev_Side_Attach_Pct": round(bev_attach_pct, 1),
            "Forensic_Risk_Score": score,
            "Forensic_Verdict": verdict,
        })

    forensic_df = pd.DataFrame(records).sort_values("Forensic_Risk_Score", ascending=False).reset_index(drop=True)

    suspicious_tickets = in_store_df[
        in_store_df["Is_Cash_Ticket"] & (in_store_df["Ticket_Discount_Pct"] >= 15.0)
    ][
        [
            "Order_ID", "Clean_Date", "Branch", "Cashier_Server", "Item_Name",
            "Pre_Discount_Gross_USD", "Discount_USD", "Gross_Sales_USD", "Ticket_Discount_Pct"
        ]
    ].copy().sort_values("Discount_USD", ascending=False)

    if demo_paywall_active:
        forensic_df["Cashier_Server"] = [f"[REDACTED OPERATOR #{i+1}]" for i in range(len(forensic_df))]
        suspicious_tickets["Cashier_Server"] = "[REDACTED OPERATOR]"
        suspicious_tickets["Item_Name"] = "[REDACTED MENU ITEM]"

    critical_ops = int((forensic_df["Forensic_Verdict"].str.startswith("CRITICAL")).sum()) if not forensic_df.empty else 0
    suspected_cash_leak_usd = float(suspicious_tickets["Discount_USD"].sum()) if not suspicious_tickets.empty else 0.0

    f_stats = {
        "critical_operators": critical_ops,
        "suspicious_cash_tickets": int(len(suspicious_tickets)),
        "suspected_cash_pocketed_usd": suspected_cash_leak_usd,
        "max_bias_ratio": float(forensic_df["Cash_Bias_Ratio"].max()) if not forensic_df.empty else 0.0,
    }
    return forensic_df, suspicious_tickets, f_stats


# ==============================================================================
# ENTERPRISE ENGINE #6: 1-CLICK BULK REPRICING PATCH GENERATOR
# ==============================================================================
def round_psychological_price(price_val: float, rule: str) -> float:
    if price_val <= 0:
        return 0.0
    if rule == "Nearest $0.50 (.00 / .50)":
        return round(price_val * 2.0) / 2.0
    if rule == "Psychological .90 Ending":
        base = float(int(price_val))
        cand = base + 0.90
        return cand if cand >= price_val else base + 1.90
    return round(price_val * 4.0) / 4.0


def build_bulk_repricing_schedule(
    sku_matrix: pd.DataFrame,
    delivery_fee: float,
    packaging_cost_usd: float,
    target_delivery_margin_pct: float,
    elasticity_dropoff_pct: float,
    rounding_rule: str,
    lbp_rate: float,
    active_market: str,
    active_days: int
) -> pd.DataFrame:
    """Computes an executable POS & Aggregator price patch for all SKUs to hit target delivery margin."""
    rows = []
    target_m = float(target_delivery_margin_pct) / 100.0
    denom = max(0.12, 1.0 - float(delivery_fee) - target_m)
    local_curr = "AED" if active_market == "Dubai" else "LBP"

    for r in sku_matrix.itertuples(index=False):
        units = float(r.Units_Sold)
        cur_price = float(r.Avg_Unit_Price_USD)
        unit_cogs = float(r.Total_COGS_USD) / max(units, 1.0)
        cur_margin_pct = float(r.Margin_Pct)

        # Delivery break-even + target margin formula:
        # Price * (1 - delivery_fee) - unit_cogs - packaging_cost_usd = Price * target_m
        raw_req_deliv_price = (unit_cogs + float(packaging_cost_usd)) / denom
        if "STAR" in r.Classification and cur_margin_pct >= target_delivery_margin_pct:
            new_deliv_price = cur_price
            action_tag = "KEEP CURRENT PRICE (STAR)"
        else:
            cand_price = max(cur_price + 0.50, raw_req_deliv_price)
            new_deliv_price = round_psychological_price(cand_price, rounding_rule)
            action_tag = f"REPRICE (+${new_deliv_price - cur_price:.2f} USD)"

        price_delta = round(new_deliv_price - cur_price, 2)
        new_deliv_net_unit = (new_deliv_price * (1.0 - float(delivery_fee))) - unit_cogs - float(packaging_cost_usd)
        new_deliv_margin_pct = (new_deliv_net_unit / new_deliv_price * 100.0) if new_deliv_price > 0 else 0.0

        monthly_units = units * (30.0 / max(active_days, 1))
        adj_monthly_units = monthly_units * (1.0 - float(elasticity_dropoff_pct)) if price_delta > 0 else monthly_units
        cur_monthly_contrib = monthly_units * float(r.Unit_Contribution_USD)

        # Assume ~45% of volume is on delivery apps where the repricing patch applies
        deliv_share = 0.45
        lifted_unit_contrib = float(r.Unit_Contribution_USD) + (price_delta * (1.0 - float(delivery_fee)) * deliv_share)
        new_monthly_contrib = adj_monthly_units * lifted_unit_contrib
        monthly_ebitda_lift = max(0.0, new_monthly_contrib - cur_monthly_contrib) if price_delta > 0 else 0.0

        if active_market == "Dubai":
            fx = lbp_rate if lbp_rate < 100 else 3.6725
            local_price = round(new_deliv_price * fx * 2.0) / 2.0
        else:
            fx = lbp_rate if lbp_rate >= 100 else 89500.0
            local_price = round(new_deliv_price * fx, -4)

        rows.append({
            "SKU": r.SKU,
            "Item_Name": r.Item_Name,
            "Category": r.Category,
            "BCG_Class": r.Classification,
            "Unit_COGS_USD": round(unit_cogs, 2),
            "Current_Price_USD": round(cur_price, 2),
            "New_Delivery_Price_USD": round(new_deliv_price, 2),
            "Price_Adjustment_USD": price_delta,
            f"New_Delivery_Price_{local_curr}": local_price,
            "Current_Margin_Pct": round(cur_margin_pct, 1),
            "New_Delivery_Margin_Pct": round(new_deliv_margin_pct, 1),
            "Est_Monthly_EBITDA_Lift_USD": round(monthly_ebitda_lift, 2),
            "Patch_Action": action_tag,
        })

    return pd.DataFrame(rows).sort_values("Est_Monthly_EBITDA_Lift_USD", ascending=False)


# ==============================================================================
# EXCEL WORKBOOK GENERATOR (UPGRADED 4-TAB WITH CHARTS, TOTALS & AUTOFILTERS)
# ==============================================================================
def build_excel_in_memory(
    df: pd.DataFrame,
    sku_matrix: pd.DataFrame,
    company_name: str,
    lbp_rate: float,
    prorated_opex: dict
) -> bytes:
    channel_summary = df.groupby("Channel", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Units_Sold=("Quantity", "sum"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Packaging_USD=("Packaging_Cost_USD", "sum"),
        Net_Revenue_USD=("Net_Revenue_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Contribution_Profit_USD=("Net_Profit_USD", "sum")
    )
    channel_summary["Margin_Pct"] = channel_summary["Contribution_Profit_USD"] / channel_summary["Gross_Sales_USD"].replace(0, 1)
    channel_summary = channel_summary.sort_values(by="Contribution_Profit_USD", ascending=False)

    branch_summary = df.groupby("Branch", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Packaging_USD=("Packaging_Cost_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Contribution_Profit_USD=("Net_Profit_USD", "sum")
    )
    branch_summary["Margin_Pct"] = branch_summary["Contribution_Profit_USD"] / branch_summary["Gross_Sales_USD"].replace(0, 1)
    branch_summary = branch_summary.sort_values(by="Contribution_Profit_USD", ascending=False)

    daily_recon = df.pivot_table(
        index="Clean_Date",
        columns="Channel",
        values="Net_Revenue_USD",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index().sort_values("Clean_Date")
    daily_recon["Total_Expected_Payout_USD"] = daily_recon.drop(columns=["Clean_Date"]).sum(axis=1)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", engine_kwargs={"options": {"in_memory": True}}) as writer:
        wb = writer.book
        title_fmt = wb.add_format({"bold": True, "font_size": 14, "font_color": "#0F172A"})
        subtitle_fmt = wb.add_format({"italic": True, "font_size": 10, "font_color": "#475569"})
        header_fmt = wb.add_format({"bold": True, "bg_color": "#0F172A", "font_color": "#FFFFFF", "border": 1, "align": "center"})
        kpi_label_fmt = wb.add_format({"bold": True, "bg_color": "#F8FAFC", "font_color": "#475569", "border": 1, "align": "center"})
        kpi_val_fmt = wb.add_format({"bold": True, "font_size": 12, "bg_color": "#FFFFFF", "font_color": "#0F172A", "num_format": "$#,##0.00", "border": 1, "align": "center"})
        kpi_pct_fmt = wb.add_format({"bold": True, "font_size": 12, "bg_color": "#FFFFFF", "font_color": "#0F172A", "num_format": "0.0%", "border": 1, "align": "center"})
        usd_fmt = wb.add_format({"num_format": "$#,##0.00", "border": 1})
        pct_fmt = wb.add_format({"num_format": "0.0%", "border": 1})
        int_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
        text_fmt = wb.add_format({"border": 1})

        total_text_fmt = wb.add_format({"bold": True, "bg_color": "#E2E8F0", "font_color": "#0F172A", "border": 1})
        total_int_fmt = wb.add_format({"bold": True, "bg_color": "#E2E8F0", "font_color": "#0F172A", "num_format": "#,##0", "border": 1})
        total_usd_fmt = wb.add_format({"bold": True, "bg_color": "#E2E8F0", "font_color": "#0F172A", "num_format": "$#,##0.00", "border": 1})
        total_pct_fmt = wb.add_format({"bold": True, "bg_color": "#E2E8F0", "font_color": "#0F172A", "num_format": "0.0%", "border": 1})

        alert_red_fmt = wb.add_format({"bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1})
        alert_green_fmt = wb.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True, "border": 1})
        alert_warn_fmt = wb.add_format({"bg_color": "#FEF3C7", "font_color": "#92400E", "bold": True, "border": 1})

        # TAB 1: 01_Executive_Summary
        ws_exec = wb.add_worksheet("01_Executive_Summary")
        ws_exec.hide_gridlines(2)
        ws_exec.write("B2", f"{company_name.upper()} — EXECUTIVE FINANCIAL SUMMARY", title_fmt)
        fx_label = f"{lbp_rate:,.4f} AED/USD" if lbp_rate < 100 else f"{lbp_rate:,.0f} LBP/USD"
        ws_exec.write("B3", f"Normalized to USD (Rate: {fx_label} | Active Days: {prorated_opex['days']})", subtitle_fmt)

        total_orders = len(df)
        total_units = df["Quantity"].sum()
        total_gross = df["Gross_Sales_USD"].sum()
        total_fees = df["Platform_Fee_USD"].sum()
        total_pkg = df["Packaging_Cost_USD"].sum()
        total_fees_pkg = total_fees + total_pkg
        total_net_rev = df["Net_Revenue_USD"].sum()
        total_cogs = df["Total_COGS_USD"].sum()
        contrib_profit = df["Net_Profit_USD"].sum()
        contrib_margin = contrib_profit / total_gross if total_gross else 0.0
        ebitda_val = contrib_profit - prorated_opex["total_opex"]
        ebitda_margin = ebitda_val / total_gross if total_gross else 0.0

        kpis = [
            ("GROSS REVENUE", total_gross, kpi_val_fmt),
            ("FEES & PACKAGING", total_fees_pkg, kpi_val_fmt),
            ("COGS & WASTE", total_cogs, kpi_val_fmt),
            ("PRORATED OPEX", prorated_opex["total_opex"], kpi_val_fmt),
            ("OPERATING EBITDA", ebitda_val, kpi_val_fmt),
            ("EBITDA MARGIN", ebitda_margin, kpi_pct_fmt),
        ]
        for idx, (label, val, fmt) in enumerate(kpis):
            col = 1 + idx * 2
            ws_exec.merge_range(4, col, 4, col + 1, label, kpi_label_fmt)
            ws_exec.merge_range(5, col, 5, col + 1, val, fmt)

        start_row = 8
        ws_exec.write(start_row - 1, 1, "1. Channel Performance Breakdown", title_fmt)
        for col_idx, col_name in enumerate(channel_summary.columns):
            ws_exec.write(start_row, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(channel_summary.itertuples(index=False), start=start_row + 1):
            ws_exec.write(r_idx, 1, row.Channel, text_fmt)
            ws_exec.write(r_idx, 2, row.Orders, int_fmt)
            ws_exec.write(r_idx, 3, row.Units_Sold, int_fmt)
            ws_exec.write(r_idx, 4, row.Gross_Sales_USD, usd_fmt)
            ws_exec.write(r_idx, 5, row.Platform_Fees_USD, usd_fmt)
            ws_exec.write(r_idx, 6, row.Packaging_USD, usd_fmt)
            ws_exec.write(r_idx, 7, row.Net_Revenue_USD, usd_fmt)
            ws_exec.write(r_idx, 8, row.Total_COGS_USD, usd_fmt)
            ws_exec.write(r_idx, 9, row.Contribution_Profit_USD, usd_fmt)
            ws_exec.write(r_idx, 10, row.Margin_Pct, pct_fmt)

        ch_tot_row = start_row + len(channel_summary) + 1
        ws_exec.write(ch_tot_row, 1, "TOTAL / BLENDED", total_text_fmt)
        ws_exec.write(ch_tot_row, 2, total_orders, total_int_fmt)
        ws_exec.write(ch_tot_row, 3, total_units, total_int_fmt)
        ws_exec.write(ch_tot_row, 4, total_gross, total_usd_fmt)
        ws_exec.write(ch_tot_row, 5, total_fees, total_usd_fmt)
        ws_exec.write(ch_tot_row, 6, total_pkg, total_usd_fmt)
        ws_exec.write(ch_tot_row, 7, total_net_rev, total_usd_fmt)
        ws_exec.write(ch_tot_row, 8, total_cogs, total_usd_fmt)
        ws_exec.write(ch_tot_row, 9, contrib_profit, total_usd_fmt)
        ws_exec.write(ch_tot_row, 10, contrib_margin, total_pct_fmt)

        b_row = ch_tot_row + 3
        ws_exec.write(b_row - 1, 1, "2. Branch Performance Breakdown", title_fmt)
        for col_idx, col_name in enumerate(branch_summary.columns):
            ws_exec.write(b_row, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(branch_summary.itertuples(index=False), start=b_row + 1):
            ws_exec.write(r_idx, 1, row.Branch, text_fmt)
            ws_exec.write(r_idx, 2, row.Orders, int_fmt)
            ws_exec.write(r_idx, 3, row.Gross_Sales_USD, usd_fmt)
            ws_exec.write(r_idx, 4, row.Platform_Fees_USD, usd_fmt)
            ws_exec.write(r_idx, 5, row.Packaging_USD, usd_fmt)
            ws_exec.write(r_idx, 6, row.Total_COGS_USD, usd_fmt)
            ws_exec.write(r_idx, 7, row.Contribution_Profit_USD, usd_fmt)
            ws_exec.write(r_idx, 8, row.Margin_Pct, pct_fmt)

        br_tot_row = b_row + len(branch_summary) + 1
        ws_exec.write(br_tot_row, 1, "TOTAL / BLENDED", total_text_fmt)
        ws_exec.write(br_tot_row, 2, total_orders, total_int_fmt)
        ws_exec.write(br_tot_row, 3, total_gross, total_usd_fmt)
        ws_exec.write(br_tot_row, 4, total_fees, total_usd_fmt)
        ws_exec.write(br_tot_row, 5, total_pkg, total_usd_fmt)
        ws_exec.write(br_tot_row, 6, total_cogs, total_usd_fmt)
        ws_exec.write(br_tot_row, 7, contrib_profit, total_usd_fmt)
        ws_exec.write(br_tot_row, 8, contrib_margin, total_pct_fmt)

        chart_ch = wb.add_chart({"type": "column"})
        num_ch = len(channel_summary)
        chart_ch.add_series({
            "name": "Gross Sales (USD)",
            "categories": ["01_Executive_Summary", start_row + 1, 1, start_row + num_ch, 1],
            "values": ["01_Executive_Summary", start_row + 1, 4, start_row + num_ch, 4],
            "fill": {"color": "#3B82F6"}
        })
        chart_ch.add_series({
            "name": "Contribution Profit (USD)",
            "categories": ["01_Executive_Summary", start_row + 1, 1, start_row + num_ch, 1],
            "values": ["01_Executive_Summary", start_row + 1, 9, start_row + num_ch, 9],
            "fill": {"color": "#10B981"}
        })
        chart_ch.set_title({"name": "Gross Sales vs. Net Contribution by Channel"})
        chart_ch.set_size({"width": 660, "height": 320})
        ws_exec.insert_chart(br_tot_row + 2, 1, chart_ch)
        ws_exec.set_column("B:M", 19)

        # TAB 2: 02_BCG_Menu_Matrix
        ws_sku = wb.add_worksheet("02_BCG_Menu_Matrix")
        ws_sku.hide_gridlines(2)
        ws_sku.freeze_panes(5, 0)
        ws_sku.write("B2", "MENU ENGINEERING MATRIX (VOLUME VS. CONTRIBUTION MARGIN)", title_fmt)
        for col_idx, col_name in enumerate(sku_matrix.columns):
            ws_sku.write(4, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(sku_matrix.itertuples(index=False), start=5):
            ws_sku.write(r_idx, 1, row.SKU, text_fmt)
            ws_sku.write(r_idx, 2, row.Item_Name, text_fmt)
            ws_sku.write(r_idx, 3, row.Category, text_fmt)
            ws_sku.write(r_idx, 4, row.Units_Sold, int_fmt)
            ws_sku.write(r_idx, 5, row.Gross_Sales_USD, usd_fmt)
            ws_sku.write(r_idx, 6, row.Platform_Fees_USD, usd_fmt)
            ws_sku.write(r_idx, 7, row.Packaging_USD, usd_fmt)
            ws_sku.write(r_idx, 8, row.Total_COGS_USD, usd_fmt)
            ws_sku.write(r_idx, 9, row.Net_Profit_USD, usd_fmt)
            ws_sku.write(r_idx, 10, row.Avg_Unit_Price_USD, usd_fmt)
            ws_sku.write(r_idx, 11, row.Unit_Contribution_USD, usd_fmt)
            ws_sku.write(r_idx, 12, row.Margin_Pct / 100.0, pct_fmt)
            style = alert_green_fmt if "STAR" in row.Classification else (
                alert_red_fmt if "UNDERPERFORMER" in row.Classification else alert_warn_fmt
            )
            ws_sku.write(r_idx, 13, row.Classification, style)

        ws_sku.autofilter(4, 1, 4 + len(sku_matrix), 13)
        ws_sku.set_column("B:N", 22)

        # TAB 3: 03_Daily_Payout_Recon
        ws_recon = wb.add_worksheet("03_Daily_Payout_Recon")
        ws_recon.hide_gridlines(2)
        ws_recon.freeze_panes(4, 0)
        ws_recon.write("B2", "DAILY EXPECTED NET PAYOUT SCHEDULE (NET OF FEES)", title_fmt)

        recon_cols = list(daily_recon.columns)
        for col_idx, col_name in enumerate(recon_cols):
            ws_recon.write(3, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, (_, r_series) in enumerate(daily_recon.iterrows(), start=4):
            ws_recon.write(r_idx, 1, str(r_series["Clean_Date"]), text_fmt)
            for c_idx, col_name in enumerate(recon_cols[1:], start=2):
                ws_recon.write(r_idx, c_idx, float(r_series[col_name]), usd_fmt)

        recon_tot_row = 4 + len(daily_recon)
        ws_recon.write(recon_tot_row, 1, "TOTAL EXPECTED PAYOUT", total_text_fmt)
        for c_idx, col_name in enumerate(recon_cols[1:], start=2):
            ws_recon.write(recon_tot_row, c_idx, float(daily_recon[col_name].sum()), total_usd_fmt)

        ws_recon.set_column("B:I", 22)

        # TAB 4: 04_Clean_Master_Ledger
        df.to_excel(writer, sheet_name="04_Clean_Master_Ledger", index=False)
        ws_raw = writer.sheets["04_Clean_Master_Ledger"]
        ws_raw.freeze_panes(1, 0)
        ws_raw.autofilter(0, 0, len(df), len(df.columns) - 1)
        ws_raw.set_column("A:S", 18)

    return output.getvalue()


# ==============================================================================
# MULTILINGUAL CFO EXECUTIVE MEMO GENERATOR
# ==============================================================================
def build_cfo_memo_content(
    lang: str,
    company_name: str,
    active_days: int,
    total_gross: float,
    total_fees_pkg: float,
    true_ebitda: float,
    ebitda_margin_pct: float,
    daily_breakeven_sales: float,
    sku_matrix: pd.DataFrame,
    aggregator_hold: float
) -> tuple[str, str]:
    bleeders = sku_matrix[sku_matrix["Classification"].str.contains("PLOWHORSE|UNDERPERFORMER")]
    worst_items = ", ".join(bleeders["Item_Name"].head(2).tolist()) if not bleeders.empty else "None"
    top_stars = ", ".join(sku_matrix[sku_matrix["Classification"].str.contains("STAR")]["Item_Name"].head(2).tolist()) or "Core Menu"
    est_monthly_recovery = (bleeders["Units_Sold"].sum() * 1.25 * (30.0 / active_days)) if not bleeders.empty else 0.0

    if lang == "Français":
        html_card = f"""
        <div class="memo-card">
            <div class="memo-header">
                <h3 class="memo-title">NOTE D'AUDIT EXÉCUTIF — {company_name.upper()}</h3>
                <span class="memo-meta">PÉRIODE ANALYSÉE : {active_days} JOURS</span>
            </div>
            <div class="memo-grid">
                <div class="memo-stat"><div class="memo-stat-label">Chiffre d'Affaires Brut</div><div class="memo-stat-val">${total_gross:,.2f}</div></div>
                <div class="memo-stat"><div class="memo-stat-label">EBITDA Opérationnel</div><div class="memo-stat-val">${true_ebitda:,.2f} ({ebitda_margin_pct:.1f}%)</div></div>
                <div class="memo-stat"><div class="memo-stat-label">Point Mort Quotidien</div><div class="memo-stat-val">${daily_breakeven_sales:,.2f} / j</div></div>
                <div class="memo-stat"><div class="memo-stat-label">Trésorerie Retenue</div><div class="memo-stat-val">${aggregator_hold:,.2f}</div></div>
            </div>
            <div class="memo-section-title">1. Synthèse des Flux & Fuites Opérationnelles</div>
            <ul class="memo-list">
                <li><span class="memo-highlight">Seuil de Rentabilité :</span> L'établissement doit générer au minimum <span class="memo-code">${daily_breakeven_sales:,.2f} USD / jour</span> pour couvrir les charges fixes (loyer, salaires, énergie).</li>
                <li><span class="memo-highlight">Commissions & Emballages :</span> <span class="memo-code">-${total_fees_pkg:,.2f} USD</span> absorbés par les plateformes de livraison, terminaux TPE et coûts d'emballage.</li>
                <li><span class="memo-highlight">Besoin en Fonds de Roulement :</span> <span class="memo-code">${aggregator_hold:,.2f} USD</span> de recettes nettes sont actuellement en attente de règlement par les agrégateurs (cycle de 7 à 14 jours).</li>
            </ul>
            <div class="memo-section-title">2. Plan d'Action Menu Engineering (Matrice BCG)</div>
            <ul class="memo-list">
                <li><span class="memo-highlight">Protéger les Produits Leaders (Stars) :</span> <em>{top_stars}</em> génèrent la plus forte contribution unitaire. Maintenir les prix pleins sans remise promotionnelle.</li>
                <li><span class="memo-highlight">Ajustement Tarifaire Ciblé :</span> <em>{worst_items}</em> présentent une marge insuffisante après commission. Une hausse de <span class="memo-code">+$1.25 USD</span> sur les applications de livraison générera <span class="memo-code">+${est_monthly_recovery:,.2f} USD / mois</span> d'EBITDA net additionnel.</li>
            </ul>
        </div>
        """
        wa_text = (
            f"*NOTE D'AUDIT EXÉCUTIF — {company_name.upper()} ({active_days} Jours)*\n\n"
            f"• *CA Brut Normalisé :* ${total_gross:,.2f} USD\n"
            f"• *EBITDA Opérationnel :* ${true_ebitda:,.2f} USD ({ebitda_margin_pct:.1f}%)\n"
            f"• *Point Mort Quotidien :* ${daily_breakeven_sales:,.2f} USD / jour\n"
            f"• *Commissions & Emballages :* -${total_fees_pkg:,.2f} USD\n"
            f"• *Trésorerie Retenue (Agrégateurs) :* ${aggregator_hold:,.2f} USD\n\n"
            f"*Plan d'Action Menu Engineering :*\n"
            f"1. *Stars à protéger :* {top_stars}\n"
            f"2. *Articles à revaloriser (+$1.25) :* {worst_items} -> Gain estimé : *+${est_monthly_recovery:,.2f} USD / mois*"
        )
        return html_card, wa_text

    if lang == "العربية":
        html_card = f"""
        <div class="memo-card" dir="rtl" style="text-align:right;">
            <div class="memo-header">
                <h3 class="memo-title">التقرير المالي التنفيذي وتدقيق الربحية — {company_name}</h3>
                <span class="memo-meta">فترة التدقيق: {active_days} يوم</span>
            </div>
            <div class="memo-grid">
                <div class="memo-stat"><div class="memo-stat-label">إجمالي المبيعات</div><div class="memo-stat-val">${total_gross:,.2f}</div></div>
                <div class="memo-stat"><div class="memo-stat-label">صافي الأرباح (EBITDA)</div><div class="memo-stat-val">${true_ebitda:,.2f} ({ebitda_margin_pct:.1f}%)</div></div>
                <div class="memo-stat"><div class="memo-stat-label">نقطة التعادل اليومية</div><div class="memo-stat-val">${daily_breakeven_sales:,.2f}</div></div>
                <div class="memo-stat"><div class="memo-stat-label">السيولة المحتجزة</div><div class="memo-stat-val">${aggregator_hold:,.2f}</div></div>
            </div>
            <div class="memo-section-title">1. تحليل التدفقات النقدية والاستقطاعات</div>
            <ul class="memo-list" style="padding-right:18px; padding-left:0;">
                <li><span class="memo-highlight">نقطة التعادل اليومية:</span> يحتاج الفرع إلى تحقيق مبيعات يومية لا تقل عن <span class="memo-code">${daily_breakeven_sales:,.2f}</span> لتغطية المصاريف الثابتة (الإيجار، الرواتب، الطاقة).</li>
                <li><span class="memo-highlight">عمولات التوصيل وتكلفة التغليف:</span> تم اقتطاع <span class="memo-code">-${total_fees_pkg:,.2f}</span> كعمولات لتطبيقات التوصيل وأدوات التغليف.</li>
                <li><span class="memo-highlight">السيولة قيد التحصيل:</span> يوجد حالياً <span class="memo-code">${aggregator_hold:,.2f}</span> من صافي المبيعات قيد التحويل من شركات التوصيل (دورة تحصيل 7 إلى 14 يوماً).</li>
            </ul>
            <div class="memo-section-title">2. التوصيات التنفيذية لهندسة القائمة (BCG Matrix)</div>
            <ul class="memo-list" style="padding-right:18px; padding-left:0;">
                <li><span class="memo-highlight">حماية الأصناف عالية الربحية (Stars):</span> الأصناف (<em>{top_stars}</em>) تمثل الركيزة الأساسية للربح التشغيلي.</li>
                <li><span class="memo-highlight">إعادة تسعير الأصناف منخفضة الهامش:</span> الأصناف (<em>{worst_items}</em>) تتآكل ربحيتها بسبب عمولة التوصيل. تعديل السعر بمقدار <span class="memo-code">+$1.25</span> سيضيف <span class="memo-code">+${est_monthly_recovery:,.2f} شهرياً</span> إلى صافي الأرباح.</li>
            </ul>
        </div>
        """
        wa_text = (
            f"*التقرير المالي التنفيذي — {company_name} ({active_days} يوم)*\n\n"
            f"• *إجمالي المبيعات:* ${total_gross:,.2f}\n"
            f"• *صافي الأرباح التشغيلية (EBITDA):* ${true_ebitda:,.2f} ({ebitda_margin_pct:.1f}%)\n"
            f"• *نقطة التعادل اليومية:* ${daily_breakeven_sales:,.2f}\n"
            f"• *عمولات التوصيل والتغليف:* -${total_fees_pkg:,.2f}\n"
            f"• *السيولة المحتجزة لدى تطبيقات التوصيل:* ${aggregator_hold:,.2f}\n\n"
            f"*خطة العمل الفورية:*\n"
            f"1. *حماية الأصناف الرئيسية:* {top_stars}\n"
            f"2. *تعديل أسعار الأصناف المستنزفة (+$1.25):* {worst_items} <- ربح إضافي متوقع: *+${est_monthly_recovery:,.2f} شهرياً*"
        )
        return html_card, wa_text

    html_card = f"""
    <div class="memo-card">
        <div class="memo-header">
            <h3 class="memo-title">EXECUTIVE CFO AUDIT MEMO — {company_name.upper()}</h3>
            <span class="memo-meta">AUDIT WINDOW: {active_days} ACTIVE DAYS</span>
        </div>
        <div class="memo-grid">
            <div class="memo-stat"><div class="memo-stat-label">Gross POS Revenue</div><div class="memo-stat-val">${total_gross:,.2f}</div></div>
            <div class="memo-stat"><div class="memo-stat-label">Operating EBITDA</div><div class="memo-stat-val">${true_ebitda:,.2f} ({ebitda_margin_pct:.1f}%)</div></div>
            <div class="memo-stat"><div class="memo-stat-label">Daily Break-Even</div><div class="memo-stat-val">${daily_breakeven_sales:,.2f} / day</div></div>
            <div class="memo-stat"><div class="memo-stat-label">Aggregator Hold</div><div class="memo-stat-val">${aggregator_hold:,.2f}</div></div>
        </div>
        <div class="memo-section-title">1. Cash Flow & Margin Leakage Findings</div>
        <ul class="memo-list">
            <li><span class="memo-highlight">Daily Break-Even Threshold:</span> Operations require a minimum of <span class="memo-code">${daily_breakeven_sales:,.2f} USD / day</span> in gross revenue to cover fixed Rent, Payroll, and Generator/Utilities.</li>
            <li><span class="memo-highlight">Platform Commission & Packaging Leakage:</span> <span class="memo-code">-${total_fees_pkg:,.2f} USD</span> was deducted by delivery aggregators, card terminals, and takeout packaging during this window.</li>
            <li><span class="memo-highlight">Working Capital in Settlement Holds:</span> <span class="memo-code">${aggregator_hold:,.2f} USD</span> of net receivables is currently queued in 7–14 day aggregator settlement cycles.</li>
        </ul>
        <div class="memo-section-title">2. Menu Engineering Action Plan (BCG Matrix)</div>
        <ul class="memo-list">
            <li><span class="memo-highlight">Protect Core Stars:</span> <em>{top_stars}</em> drive peak unit contribution. Maintain full pricing and primary menu placement without discounting.</li>
            <li><span class="memo-highlight">Reprice Underperforming SKUs:</span> <em>{worst_items}</em> fall below target contribution thresholds on delivery channels. A <span class="memo-code">+$1.25 USD</span> delivery price adjustment recovers <span class="memo-code">+${est_monthly_recovery:,.2f} USD / month</span> in net operating EBITDA.</li>
        </ul>
    </div>
    """
    wa_text = (
        f"*EXECUTIVE CFO AUDIT MEMO — {company_name.upper()} ({active_days}-Day Period)*\n\n"
        f"• *Normalized Gross POS Revenue:* ${total_gross:,.2f} USD\n"
        f"• *Operating EBITDA:* ${true_ebitda:,.2f} USD ({ebitda_margin_pct:.1f}%)\n"
        f"• *Daily Break-Even Target:* ${daily_breakeven_sales:,.2f} USD / day\n"
        f"• *Commissions & Packaging Leakage:* -${total_fees_pkg:,.2f} USD\n"
        f"• *Working Capital in Aggregator Hold:* ${aggregator_hold:,.2f} USD\n\n"
        f"*Menu Engineering Action Plan:*\n"
        f"1. *Protect Core Stars:* {top_stars}\n"
        f"2. *Reprice Underperformers (+$1.25):* {worst_items} -> Recovers *+${est_monthly_recovery:,.2f} USD / month* in net EBITDA."
    )
    return html_card, wa_text


# ==============================================================================
# MASTER ADMIN CLIENT PROVISIONING CONSOLE
# ==============================================================================
def render_admin_console():
    st.markdown("""
    <div class="suite-header">
        <div class="suite-kicker">MASTER ADMINISTRATOR CONSOLE</div>
        <h1 class="suite-title">Client Account Provisioning & Multi-Tenant Manager</h1>
        <div class="suite-subtitle">Create paid client accounts, pre-load client SKU COGS sheets, configure Demo Paywall behavior, and export permanent cloud secrets.</div>
    </div>
    """, unsafe_allow_html=True)

    clients_db = get_client_db()
    col_form, col_list = st.columns([1.35, 1.0])

    with col_form:
        st.markdown("#### 1. Create or Update Paid Client Account")
        with st.form("create_client_form"):
            f1, f2 = st.columns(2)
            with f1:
                new_username = st.text_input("Client Login Username *", placeholder="e.g., roadster_ashrafieh").strip().lower()
                new_company = st.text_input("Company / Brand Display Name *", placeholder="e.g., Roadster Diner (Ashrafieh)")
                new_lbp_rate = st.number_input("Default LBP / USD Rate", value=89500.0, step=500.0)
                new_deliv_fee = st.number_input("Toters / Aggregator Fee (%)", value=25.0, step=0.5)
                new_pkg_cost = st.number_input("Delivery Packaging / Unit ($)", value=0.65, step=0.05)
            with f2:
                new_password = st.text_input("Client Password *", placeholder="e.g., rd2026secure")
                new_card_fee = st.number_input("Card POS Fee (%)", value=2.0, step=0.1)
                new_whish_fee = st.number_input("Digital Wallet / Whish Fee (%)", value=1.0, step=0.1)
                new_waste_pct = st.number_input("Kitchen Waste Allowance (%)", value=3.0, step=0.5)

            st.markdown("**Client Monthly Fixed OPEX Defaults (USD)**")
            o1, o2, o3 = st.columns(3)
            with o1:
                new_rent = st.number_input("Monthly Rent ($)", value=2500.0, step=100.0)
            with o2:
                new_payroll = st.number_input("Monthly Payroll ($)", value=4500.0, step=100.0)
            with o3:
                new_utilities = st.number_input("Generator & Utilities ($)", value=900.0, step=50.0)

            st.markdown("**Optional: Pre-Load Client Master SKU COGS File (.xlsx / .csv)**")
            admin_cogs_file = st.file_uploader("Upload Client COGS Sheet", type=["csv", "xlsx", "xls"])

            save_btn = st.form_submit_button("Create / Update Paid Client Account", type="primary", use_container_width=True)

            if save_btn:
                clean_u = re.sub(r"[^a-z0-9_-]", "", new_username)
                if not clean_u or clean_u in ["demo", get_admin_username()] or not new_password or not new_company:
                    st.error("Please provide a valid non-reserved Username, Password, and Company Name.")
                else:
                    profile_payload = {
                        "password": new_password.strip(),
                        "company_name": new_company.strip(),
                        "default_lbp_rate": float(new_lbp_rate),
                        "delivery_fee_pct": float(new_deliv_fee),
                        "card_fee_pct": float(new_card_fee),
                        "whish_fee_pct": float(new_whish_fee),
                        "packaging_cost_usd": float(new_pkg_cost),
                        "waste_pct": float(new_waste_pct),
                        "monthly_rent_usd": float(new_rent),
                        "monthly_payroll_usd": float(new_payroll),
                        "monthly_generator_utilities_usd": float(new_utilities),
                    }
                    save_client_to_store(clean_u, profile_payload)

                    if admin_cogs_file is not None:
                        raw_c = safe_read_file(admin_cogs_file)
                        c_cols = list(raw_c.columns)
                        cost_idx = guess_column_index(c_cols, ["cost", "cogs", "unit_cost", "achat", "cout"])
                        item_idx = guess_column_index(c_cols, ["item", "product", "article", "name", "designation"])
                        sku_idx = guess_column_index(c_cols, ["sku", "code", "barcode", "ref"])
                        std_c = pd.DataFrame({
                            "SKU": raw_c[c_cols[sku_idx]].astype(str).str.strip(),
                            "Item_Name": raw_c[c_cols[item_idx]].astype(str).str.strip(),
                            "Unit_Cost_USD": clean_numeric_series(raw_c[c_cols[cost_idx]], 0.0),
                            "Category": "Client Master"
                        })
                        save_client_cogs_df(clean_u, std_c)

                    st.success(f"Paid Client Account `{clean_u}` ({new_company}) is now live with full unlocked access!")
                    st.rerun()

    with col_list:
        st.markdown("#### 2. Demo Paywall & Active Client Accounts")
        demo_prof = clients_db.get("demo", DEFAULT_CLIENTS["demo"])
        cur_demo_mode = demo_prof.get("demo_upload_mode", "teaser")
        new_demo_mode = st.radio(
            "When a public `demo` visitor clicks 'Upload Custom POS File':",
            ["teaser", "locked"],
            index=0 if cur_demo_mode == "teaser" else 1,
            format_func=lambda m: "Teaser Diagnostic Mode (Shows Total Leakage $, Redacts SKU Names & Locks Excel Export)" if m == "teaser" else "Strict Lock Mode (Blocks File Uploader Completely on Demo Accounts)"
        )
        if new_demo_mode != cur_demo_mode:
            demo_prof["demo_upload_mode"] = new_demo_mode
            save_client_to_store("demo", demo_prof)
            st.rerun()

        rows = []
        for u, p in clients_db.items():
            has_cogs = "Pre-Loaded" if load_client_cogs_df(u) is not None else "Standard"
            rows.append({
                "Username": u,
                "Tier": "Public Sandbox (Paywalled)" if u in ("demo", "dubai_demo") else "Paid License (Unlocked)",
                "Password": p.get("password", ""),
                "Company": p.get("company_name", ""),
                "Saved COGS": has_cogs
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        selected_client = st.selectbox("Select Account to Generate Onboarding Link or Preview", list(clients_db.keys()))
        sel_p = clients_db[selected_client]
        magic_client_url = f"{APP_BASE_URL}/?client={selected_client}&key={urllib.parse.quote(str(sel_p['password']))}"

        onboarding_text = (
            f"*{sel_p['company_name']} — Executive POS & EBITDA Portal Access*\n\n"
            f"Your private financial reconciliation portal is now configured and live:\n"
            f"• *Direct 1-Click Login Link:* {magic_client_url}\n"
            f"• *Username:* {selected_client}\n"
            f"• *Password:* {sel_p['password']}"
        )
        st.code(onboarding_text, language="text")

        b_act1, b_act2, b_act3 = st.columns(3)
        with b_act1:
            if st.button("Preview Account", use_container_width=True):
                st.session_state.client_profile = dict(sel_p)
                st.session_state.username = selected_client
                st.rerun()
        with b_act2:
            wa_onboard_url = f"https://wa.me/?text={urllib.parse.quote(onboarding_text)}"
            st.link_button("Send Login via WhatsApp", url=wa_onboard_url, use_container_width=True)
        with b_act3:
            if selected_client not in ("demo", "dubai_demo"):
                if st.button("Delete Account", use_container_width=True):
                    delete_client_from_store(selected_client)
                    st.rerun()

        with st.expander("Permanent Cloud Backup (Streamlit Secrets TOML)"):
            st.caption("Copy and paste this block into Streamlit Cloud -> Settings -> Secrets so all paid accounts persist permanently.")
            st.code(format_secrets_toml(clients_db), language="toml")


# ==============================================================================
# MAIN AUTHENTICATED WORKSPACE
# ==============================================================================
def main_portal():
    profile = st.session_state.client_profile
    company_name = profile["company_name"]
    is_admin = st.session_state.get("is_admin", False)
    is_demo_account = (st.session_state.username in ("demo", "dubai_demo")) and (not is_admin)
    owner_wa = get_owner_whatsapp()
    default_market = profile.get("market", "Beirut")

    with st.sidebar:
        st.markdown(f"<div style='font-size:1.05rem; font-weight:700; color:#F8FAFC; margin-bottom:2px;'>{company_name}</div>", unsafe_allow_html=True)
        tier_label = "MASTER ADMIN" if is_admin else ("DEMO SANDBOX" if is_demo_account else "VERIFIED CLIENT LICENSE")
        st.caption(f"Account: `{st.session_state.username}` ({tier_label})")

        role_options = ["CFO / Executive View", "Branch Manager (Cash Recon)"]
        if is_admin:
            role_options = ["Master Admin: Client Provisioning"] + role_options

        role = st.selectbox("Workspace Mode", role_options)

        active_market = st.selectbox(
            "Regional Market Preset",
            ["Beirut", "Dubai"],
            index=1 if default_market == "Dubai" else 0,
            format_func=lambda m: "🇱🇧 Beirut (LBP / USD)" if m == "Beirut" else "🇦🇪 Dubai (AED / USD)"
        )

        with st.expander("1. FX & Channel Fees", expanded=True):
            if active_market == "Dubai":
                default_fx_val = float(profile.get("default_lbp_rate", 3.6725))
                if default_fx_val > 100:
                    default_fx_val = 3.6725
                lbp_rate = st.number_input("AED / USD Exchange Rate", min_value=1.0, max_value=10.0, value=default_fx_val, step=0.0025, format="%.4f")
            else:
                default_fx_val = float(profile.get("default_lbp_rate", 89500.0))
                if default_fx_val < 100:
                    default_fx_val = 89500.0
                lbp_rate = st.number_input("LBP / USD Exchange Rate", min_value=1000.0, max_value=500000.0, value=default_fx_val, step=500.0)

            delivery_fee = st.slider("Aggregator Commission (%)", 0.0, 40.0, float(profile.get("delivery_fee_pct", 25.0)), 0.5) / 100.0
            packaging_cost_usd = st.number_input("Delivery Packaging / Unit ($)", min_value=0.0, max_value=5.0, value=float(profile.get("packaging_cost_usd", 0.65)), step=0.05)
            card_fee = st.slider("Card POS Fee (%)", 0.0, 10.0, float(profile.get("card_fee_pct", 2.0)), 0.1) / 100.0
            whish_fee = st.slider("Digital Wallet Fee (%)", 0.0, 10.0, float(profile.get("whish_fee_pct", 1.0)), 0.1) / 100.0

        with st.expander("2. COGS, Waste & Inflation", expanded=False):
            waste_pct = st.slider("Kitchen Waste Allowance (%)", 0.0, 15.0, float(profile.get("waste_pct", 3.0)), 0.5) / 100.0
            supplier_inflation_pct = st.slider("Supplier Cost Stress-Test (%)", -10.0, 35.0, 0.0, 1.0) / 100.0
            fallback_cogs_pct = st.slider("Default COGS % (If Unmapped)", 5.0, 80.0, 32.0, 1.0) / 100.0

        with st.expander("3. Fixed Monthly OPEX", expanded=False):
            monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, value=float(profile.get("monthly_rent_usd", 1800.0)), step=100.0)
            monthly_payroll = st.number_input("Monthly Payroll ($)", min_value=0.0, value=float(profile.get("monthly_payroll_usd", 2400.0)), step=100.0)
            monthly_utilities = st.number_input("Generator & Utilities ($)", min_value=0.0, value=float(profile.get("monthly_generator_utilities_usd", 750.0)), step=50.0)

        st.divider()
        wa_msg = urllib.parse.quote("Hi, I tested the Executive POS & EBITDA Suite and want to activate a private client license for our branches.")
        st.link_button("Activate Private Client License", url=f"https://wa.me/{owner_wa}?text={wa_msg}", use_container_width=True)
        if st.button("Sign Out", use_container_width=True):
            st.query_params.clear()
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.rerun()

    if role == "Master Admin: Client Provisioning":
        render_admin_console()
        return

    top_left, top_right = st.columns([2.0, 1.4], vertical_alignment="center")
    with top_left:
        st.markdown(f"""
        <div style="margin-bottom:0.5rem;">
            <div class="suite-kicker">FINANCIAL OPERATIONS & AUDIT</div>
            <h1 class="suite-title">{company_name}</h1>
        </div>
        """, unsafe_allow_html=True)
    with top_right:
        mode = st.radio(
            "Data Source",
            ["Built-in Demo Dataset", "Upload Custom POS File"],
            horizontal=True,
            label_visibility="collapsed"
        )

    is_custom_upload = (mode == "Upload Custom POS File")
    demo_paywall_active = is_demo_account and is_custom_upload
    demo_upload_mode = profile.get("demo_upload_mode", "teaser")

    if demo_paywall_active and demo_upload_mode == "locked":
        st.markdown("""
        <div class="paywall-card">
            <div class="paywall-title">Custom POS Ingestion Locked — Client License Required</div>
            <div class="paywall-sub">
                Direct POS file ingestion (.xlsx / .csv), automated COGS mapping, and custom Executive Workbook exports are restricted to verified client accounts.
                Send 1 anonymized week of your POS export via WhatsApp below to receive your complimentary 7-day audit and activate your private login.
            </div>
        </div>
        """, unsafe_allow_html=True)
        wa_unlock = urllib.parse.quote("Hi, I am on the POS Suite Demo and would like to send 1 week of our POS export for a complimentary audit and private login.")
        st.link_button("Request Complimentary Audit & Private Login via WhatsApp", url=f"https://wa.me/{owner_wa}?text={wa_unlock}", type="primary")
        return

    std_pos, std_cogs = None, None
    preloaded_client_cogs = load_client_cogs_df(st.session_state.username)

    if is_custom_upload:
        if demo_paywall_active:
            st.markdown("""
            <div class="paywall-card">
                <div class="paywall-title">Demo Diagnostic Preview Mode Active</div>
                <div class="paywall-sub">
                    You may upload a sample POS file below to calculate your top-line commission leakage and monthly EBITDA recovery potential.
                    <strong>Individual SKU names, operator audit logs, and Excel Workbook (.xlsx) downloads are redacted on Demo accounts.</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

        u_col1, u_col2 = st.columns(2)
        with u_col1:
            pos_file = st.file_uploader("1. Raw POS Export (.xlsx, .xls, .csv) [Required]", type=["csv", "xlsx", "xls"])
        with u_col2:
            cogs_label = "2. Master SKU COGS [Optional — Pre-Loaded Active]" if preloaded_client_cogs is not None else "2. Master SKU COGS (.xlsx, .xls, .csv) [Optional]"
            cogs_file = st.file_uploader(cogs_label, type=["csv", "xlsx", "xls"])

        if not pos_file:
            st.markdown('<div class="exec-banner">Upload a POS export file above to initialize automated column mapping.</div>', unsafe_allow_html=True)
            return

        raw_pos = safe_read_file(pos_file)
        pos_cols = list(raw_pos.columns)
        opt_pos_cols = ["(None / Auto-Fill)"] + pos_cols

        with st.expander("Column Mapping Configuration (Auto-Detected)", expanded=True):
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                col_amount = st.selectbox("Gross Sales / Total *", pos_cols, index=guess_column_index(pos_cols, ["gross", "amount", "total", "sales", "price", "montant", "ttc", "nettotal", "value"]))
                col_item = st.selectbox("Item / Product Name *", pos_cols, index=guess_column_index(pos_cols, ["item", "product", "article", "description", "menu", "designation", "name"]))
            with m2:
                col_qty = st.selectbox("Quantity Sold", opt_pos_cols, index=guess_column_index(pos_cols, ["qty", "quantity", "quantite", "qte", "count", "units"], allow_none=True))
                col_channel = st.selectbox("Payment / Order Channel", opt_pos_cols, index=guess_column_index(pos_cols, ["channel", "payment", "source", "type", "method", "mode", "aggregator"], allow_none=True))
                col_discount = st.selectbox("Discount / Void Amount", opt_pos_cols, index=guess_column_index(pos_cols, ["disc", "remise", "void", "comp", "promo"], allow_none=True))
            with m3:
                col_date = st.selectbox("Transaction Date", opt_pos_cols, index=guess_column_index(pos_cols, ["date", "time", "day", "created", "business_date"], allow_none=True))
                col_branch = st.selectbox("Branch / Location", opt_pos_cols, index=guess_column_index(pos_cols, ["branch", "store", "location", "outlet", "shop", "point"], allow_none=True))
                col_cashier = st.selectbox("Cashier / Operator", opt_pos_cols, index=guess_column_index(pos_cols, ["cashier", "user", "server", "waiter", "caissier", "emp"], allow_none=True))
            with m4:
                col_sku = st.selectbox("SKU / Article Code", opt_pos_cols, index=guess_column_index(pos_cols, ["sku", "code", "barcode", "ref", "item_id"], allow_none=True))
                col_curr = st.selectbox("Currency (LBP / AED / USD)", opt_pos_cols, index=guess_column_index(pos_cols, ["curr", "devise", "currency"], allow_none=True))
                col_inline_cost = st.selectbox("Unit Cost (If in POS File)", opt_pos_cols, index=guess_column_index(pos_cols, ["cout", "cost", "cogs", "achat"], allow_none=True))

        std_pos = pd.DataFrame()
        std_pos["Order_ID"] = [f"ORD-{10000 + i}" for i in range(len(raw_pos))]
        std_pos["Gross_Amount_Raw"] = raw_pos[col_amount]
        std_pos["Item_Name"] = raw_pos[col_item].astype(str).str.strip()
        std_pos["Quantity"] = raw_pos[col_qty] if col_qty != "(None / Auto-Fill)" else 1
        std_pos["Channel"] = raw_pos[col_channel] if col_channel != "(None / Auto-Fill)" else "In-Store Cash"
        std_pos["Discount_USD"] = raw_pos[col_discount] if col_discount != "(None / Auto-Fill)" else 0.0
        std_pos["Date"] = raw_pos[col_date] if col_date != "(None / Auto-Fill)" else datetime.today().strftime("%Y-%m-%d")
        std_pos["Branch"] = raw_pos[col_branch].astype(str).str.strip() if col_branch != "(None / Auto-Fill)" else "Main Branch"
        std_pos["Cashier_Server"] = raw_pos[col_cashier].astype(str).str.strip() if col_cashier != "(None / Auto-Fill)" else "POS_Terminal"
        std_pos["SKU"] = raw_pos[col_sku].astype(str).str.strip() if col_sku != "(None / Auto-Fill)" else std_pos["Item_Name"]
        std_pos["Currency"] = raw_pos[col_curr] if col_curr != "(None / Auto-Fill)" else "AUTO"

        if cogs_file:
            raw_cogs = safe_read_file(cogs_file)
            cogs_cols = list(raw_cogs.columns)
            opt_cogs_cols = ["(None / Auto-Fill)"] + cogs_cols
            with st.expander("COGS Column Mapping", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    cogs_cost_col = st.selectbox("Unit Cost (USD) *", cogs_cols, index=guess_column_index(cogs_cols, ["cost", "cogs", "unit_cost", "achat", "cout"]))
                with c2:
                    cogs_item_col = st.selectbox("Item Name", opt_cogs_cols, index=guess_column_index(cogs_cols, ["item", "product", "article", "name", "designation"], allow_none=True))
                with c3:
                    cogs_sku_col = st.selectbox("SKU / Code", opt_cogs_cols, index=guess_column_index(cogs_cols, ["sku", "code", "barcode", "ref"], allow_none=True))
                with c4:
                    cogs_cat_col = st.selectbox("Category", opt_cogs_cols, index=guess_column_index(cogs_cols, ["cat", "group", "family", "famille"], allow_none=True))

            std_cogs = pd.DataFrame()
            std_cogs["Unit_Cost_USD"] = raw_cogs[cogs_cost_col]
            std_cogs["Item_Name"] = raw_cogs[cogs_item_col].astype(str).str.strip() if cogs_item_col != "(None / Auto-Fill)" else "N/A"
            std_cogs["SKU"] = raw_cogs[cogs_sku_col].astype(str).str.strip() if cogs_sku_col != "(None / Auto-Fill)" else std_cogs["Item_Name"]
            std_cogs["Category"] = raw_cogs[cogs_cat_col].astype(str).str.strip() if cogs_cat_col != "(None / Auto-Fill)" else "General"
        elif col_inline_cost != "(None / Auto-Fill)":
            std_cogs = pd.DataFrame({
                "SKU": std_pos["SKU"],
                "Item_Name": std_pos["Item_Name"],
                "Unit_Cost_USD": raw_pos[col_inline_cost],
                "Category": "POS Mapped"
            })
        elif preloaded_client_cogs is not None:
            std_cogs = preloaded_client_cogs
    else:
        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate, active_market)
        std_pos = sample_pos.rename(columns={"Item_Sold": "Item_Name"})
        std_cogs = preloaded_client_cogs if preloaded_client_cogs is not None else sample_cogs

    cleaned_df = process_standardized_data(
        std_pos, std_cogs, lbp_rate, delivery_fee, card_fee, whish_fee,
        packaging_cost_usd, waste_pct, supplier_inflation_pct, fallback_cogs_pct
    )

    if cleaned_df.empty:
        st.error("No valid positive sales rows were found. Verify the Gross Sales column selection.")
        return

    active_days = max(1, cleaned_df["Clean_Date"].nunique())
    monthly_total_opex = monthly_rent + monthly_payroll + monthly_utilities
    daily_fixed_opex = monthly_total_opex / 30.0
    prorated_total_opex = daily_fixed_opex * active_days
    prorated_opex_dict = {
        "days": active_days,
        "rent": (monthly_rent / 30.0) * active_days,
        "payroll": (monthly_payroll / 30.0) * active_days,
        "utilities": (monthly_utilities / 30.0) * active_days,
        "total_opex": prorated_total_opex
    }

    total_gross = cleaned_df["Gross_Sales_USD"].sum()
    total_fees_pkg = cleaned_df["Platform_Fee_USD"].sum() + cleaned_df["Packaging_Cost_USD"].sum()
    total_cogs_waste = cleaned_df["Total_COGS_USD"].sum()
    contrib_profit = cleaned_df["Net_Profit_USD"].sum()
    contrib_margin_ratio = (contrib_profit / total_gross) if total_gross > 0 else 0.35
    daily_breakeven_sales = (daily_fixed_opex / contrib_margin_ratio) if contrib_margin_ratio > 0 else 0.0

    true_ebitda = contrib_profit - prorated_total_opex
    ebitda_margin_pct = (true_ebitda / total_gross * 100.0) if total_gross else 0.0

    sku_matrix = build_bcg_menu_matrix(cleaned_df)

    display_matrix = sku_matrix.copy()
    if demo_paywall_active:
        display_matrix["SKU"] = [f"LOCKED-{i+1:02d}" for i in range(len(display_matrix))]
        display_matrix["Item_Name"] = [f"[REDACTED SKU #{i+1} — Client License Required]" for i in range(len(display_matrix))]

    if role == "Branch Manager (Cash Recon)":
        st.markdown('<div class="exec-banner"><strong>Branch Manager View:</strong> Supplier COGS and Executive EBITDA are hidden. Displaying Shift Cash Drawer Reconciliation.</div>', unsafe_allow_html=True)
        branches_list = ["All Branches"] + sorted(cleaned_df["Branch"].unique().tolist())
        sel_branch = st.selectbox("Select Branch", branches_list)
        b_df = cleaned_df if sel_branch == "All Branches" else cleaned_df[cleaned_df["Branch"] == sel_branch]
        expected_cash = b_df[b_df["Channel"] == "In-Store Cash"]["Gross_Sales_USD"].sum()
        expected_whish = b_df[b_df["Channel"] == "Digital Wallet (Whish)"]["Net_Revenue_USD"].sum()

        c1, c2 = st.columns(2)
        c1.metric("POS Expected Cash (USD Equiv.)", f"${expected_cash:,.2f}")
        c2.metric("Expected Digital Wallet Settlement", f"${expected_whish:,.2f}")

        st.subheader("End-of-Shift Physical Drawer Count")
        col_u, col_l = st.columns(2)
        with col_u:
            counted_usd = st.number_input("Physical USD Bills Counted ($)", min_value=0.0, value=float(round(expected_cash * 0.70, 2)), step=10.0)
        with col_l:
            local_label = "Physical AED Bills Counted (AED)" if active_market == "Dubai" else "Physical LBP Bills Counted (LBP)"
            local_step = 50.0 if active_market == "Dubai" else 100000.0
            local_default = float(round(expected_cash * 0.30 * lbp_rate, 2 if active_market == "Dubai" else -3))
            counted_lbp = st.number_input(local_label, min_value=0.0, value=local_default, step=local_step)

        total_counted_usd = counted_usd + (counted_lbp / lbp_rate)
        variance_usd = total_counted_usd - expected_cash
        if abs(variance_usd) < 1.0:
            st.success(f"Drawer Balanced — Total Counted: ${total_counted_usd:,.2f} (Variance: ${variance_usd:+.2f})")
        elif variance_usd < 0:
            st.error(f"Cash Shortage Detected — Drawer is short by ${abs(variance_usd):,.2f}")
        else:
            st.warning(f"Cash Overage — Drawer is over by +${variance_usd:,.2f} (Verify unrecorded POS tickets)")
        return

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Gross POS Sales", f"${total_gross:,.2f}")
    k2.metric("Fees & Packaging", f"-${total_fees_pkg:,.2f}")
    k3.metric("COGS & Waste", f"-${total_cogs_waste:,.2f}")
    k4.metric("Contribution Profit", f"${contrib_profit:,.2f}")
    k5.metric(f"Prorated OPEX ({active_days}d)", f"-${prorated_total_opex:,.2f}")
    k6.metric("Operating EBITDA", f"${true_ebitda:,.2f}", f"{ebitda_margin_pct:+.1f}% margin")

    bar_left, bar_right = st.columns([3, 1.2], vertical_alignment="center")
    with bar_left:
        fx_cap = f"{lbp_rate:,.4f} AED/USD" if active_market == "Dubai" else f"{lbp_rate:,.0f} LBP/USD"
        st.caption(f"Normalized ledger across {active_days} active day(s) at {fx_cap}.")
    with bar_right:
        if demo_paywall_active:
            wa_unlock_xlsx = urllib.parse.quote(
                f"Hi, I just ran a diagnostic on our POS file (${total_gross:,.2f} gross sales) and want to unlock our full SKU names and Excel Workbook."
            )
            st.link_button(
                "Unlock Custom Excel Export (Client License)",
                url=f"https://wa.me/{owner_wa}?text={wa_unlock_xlsx}",
                type="primary",
                use_container_width=True
            )
        else:
            excel_bytes = build_excel_in_memory(cleaned_df, sku_matrix, company_name, lbp_rate, prorated_opex_dict)
            st.download_button(
                label="Export Executive Workbook (.xlsx)",
                data=excel_bytes,
                file_name=f"{company_name.replace(' ', '_')}_Financial_Audit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Menu Engineering (BCG)",
        "Price Elasticity & Bulk Patch",
        "Aggregator Clawback Audit",
        "EBITDA & Working Capital",
        "Cash Drawer Audit",
        "Register Fraud Forensics",
        "Executive Memo"
    ])

    with tab1:
        plowhorses_dogs = sku_matrix[sku_matrix["Classification"].str.contains("PLOWHORSE|UNDERPERFORMER")]
        if not plowhorses_dogs.empty:
            leaking_units = plowhorses_dogs["Units_Sold"].sum()
            monthly_recovery = leaking_units * 1.25 * (30.0 / active_days)
            st.markdown(
                f'<div class="exec-banner"><strong>Margin Optimization Opportunity:</strong> {len(plowhorses_dogs)} SKU(s) classify as '
                f'Plowhorses or Underperformers ({int(leaking_units):,} units sold). A +$1.25 delivery price adjustment yields an estimated '
                f'<strong>+${monthly_recovery:,.2f}/month</strong> in net operating EBITDA.</div>',
                unsafe_allow_html=True
            )

        st.dataframe(
            display_matrix,
            hide_index=True,
            use_container_width=True,
            column_config={
                "SKU": st.column_config.TextColumn("SKU", width="small"),
                "Item_Name": st.column_config.TextColumn("Menu Item", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Units_Sold": st.column_config.NumberColumn("Units Sold", format="%d"),
                "Gross_Sales_USD": st.column_config.NumberColumn("Gross Sales", format="$%.2f"),
                "Platform_Fees_USD": st.column_config.NumberColumn("Platform Fees", format="$%.2f"),
                "Packaging_USD": st.column_config.NumberColumn("Packaging", format="$%.2f"),
                "Total_COGS_USD": st.column_config.NumberColumn("COGS & Waste", format="$%.2f"),
                "Net_Profit_USD": st.column_config.NumberColumn("Net Contribution", format="$%.2f"),
                "Avg_Unit_Price_USD": st.column_config.NumberColumn("Unit Price", format="$%.2f"),
                "Unit_Contribution_USD": st.column_config.NumberColumn("Unit Margin ($)", format="$%.2f"),
                "Margin_Pct": st.column_config.ProgressColumn("Net Margin (%)", format="%.1f%%", min_value=0, max_value=100),
                "Classification": st.column_config.TextColumn("BCG Classification", width="medium"),
            }
        )

    with tab2:
        st.markdown("**1. Single-SKU Price & Volume Elasticity Simulator**")
        st.caption("Model the net monthly EBITDA impact of repricing an item while accounting for potential customer volume dropoff.")

        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            selected_item = st.selectbox("Select SKU to Model", display_matrix["Item_Name"].tolist())
        with sim_col2:
            price_increase = st.slider("Proposed Price Increase (+USD)", 0.25, 5.00, 1.25, 0.25)
        with sim_col3:
            volume_dropoff_pct = st.slider("Assumed Volume Dropoff (%)", 0.0, 30.0, 5.0, 1.0) / 100.0

        item_row = display_matrix[display_matrix["Item_Name"] == selected_item].iloc[0]
        cur_monthly_units = item_row["Units_Sold"] * (30.0 / active_days)
        cur_unit_price = item_row["Avg_Unit_Price_USD"]
        cur_unit_contrib = item_row["Unit_Contribution_USD"]
        cur_monthly_profit = cur_monthly_units * cur_unit_contrib

        avg_fee_ratio = item_row["Platform_Fees_USD"] / item_row["Gross_Sales_USD"] if item_row["Gross_Sales_USD"] else 0.10
        new_unit_contrib = cur_unit_contrib + (price_increase * (1.0 - avg_fee_ratio))
        new_monthly_units = cur_monthly_units * (1.0 - volume_dropoff_pct)
        new_monthly_profit = new_monthly_units * new_unit_contrib
        monthly_ebitda_lift = new_monthly_profit - cur_monthly_profit

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Current Unit Price", f"${cur_unit_price:,.2f}")
        r2.metric("Simulated Unit Price", f"${cur_unit_price + price_increase:,.2f}", f"+${price_increase:,.2f}")
        r3.metric("Baseline Monthly Contribution", f"${cur_monthly_profit:,.2f}")
        r4.metric("Projected Monthly Contribution", f"${new_monthly_profit:,.2f}", f"{monthly_ebitda_lift:+,.2f} / mo")

        if monthly_ebitda_lift > 0:
            st.markdown(
                f'<div class="exec-banner"><strong>Positive Net Elasticity:</strong> Even with a {volume_dropoff_pct*100:.0f}% reduction in unit volume, '
                f'repricing <strong>{selected_item}</strong> by +${price_increase:.2f} generates <strong>+${monthly_ebitda_lift:,.2f}/month</strong> '
                f'(+${monthly_ebitda_lift*12:,.2f} annualized) in incremental EBITDA.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="exec-banner-warn"><strong>Negative Net Elasticity:</strong> Projected volume loss outweighs the unit price increase. '
                'Consider a smaller price adjustment or portion cost engineering.</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("**2. Automated Portfolio Bulk Repricing & POS Patch Generator**")
        st.caption(
            "Automatically calculates the exact delivery menu price required for every SKU to absorb aggregator commissions "
            "and packaging while hitting your target net margin—rounded to clean psychological price tiers and ready for 1-click POS / Aggregator import."
        )

        patch_c1, patch_c2, patch_c3 = st.columns([1.1, 1.1, 1.0])
        with patch_c1:
            target_deliv_margin = st.slider("Target Net Delivery Margin (%)", 15.0, 45.0, 28.0, 1.0)
        with patch_c2:
            rounding_rule = st.selectbox(
                "Psychological Price Rounding Rule",
                ["Nearest $0.50 (.00 / .50)", "Psychological .90 Ending", "Nearest $0.25 Increment"]
            )
        with patch_c3:
            local_curr_code = "AED" if active_market == "Dubai" else "LBP"
            repricing_df = build_bulk_repricing_schedule(
                sku_matrix=display_matrix,
                delivery_fee=delivery_fee,
                packaging_cost_usd=packaging_cost_usd,
                target_delivery_margin_pct=target_deliv_margin,
                elasticity_dropoff_pct=volume_dropoff_pct,
                rounding_rule=rounding_rule,
                lbp_rate=lbp_rate,
                active_market=active_market,
                active_days=active_days
            )
            total_portfolio_lift = float(repricing_df["Est_Monthly_EBITDA_Lift_USD"].sum()) if not repricing_df.empty else 0.0
            repriced_sku_count = int((repricing_df["Price_Adjustment_USD"] > 0).sum()) if not repricing_df.empty else 0
            st.metric(
                "Portfolio Monthly EBITDA Lift",
                f"+${total_portfolio_lift:,.2f} / mo",
                f"+${total_portfolio_lift * 12:,.0f} annualized ({repriced_sku_count} SKUs)"
            )

        local_col_name = f"New_Delivery_Price_{local_curr_code}"
        st.dataframe(
            repricing_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "SKU": st.column_config.TextColumn("SKU", width="small"),
                "Item_Name": st.column_config.TextColumn("Menu Item", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "BCG_Class": st.column_config.TextColumn("BCG Class", width="medium"),
                "Unit_COGS_USD": st.column_config.NumberColumn("Unit COGS", format="$%.2f"),
                "Current_Price_USD": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                "New_Delivery_Price_USD": st.column_config.NumberColumn("New Delivery Price", format="$%.2f"),
                "Price_Adjustment_USD": st.column_config.NumberColumn("Delta ($)", format="+$%.2f"),
                local_col_name: st.column_config.NumberColumn(
                    f"New Price ({local_curr_code})",
                    format="%.2f AED" if local_curr_code == "AED" else "%d LBP"
                ),
                "Current_Margin_Pct": st.column_config.NumberColumn("Old Margin (%)", format="%.1f%%"),
                "New_Delivery_Margin_Pct": st.column_config.ProgressColumn("New Deliv. Margin (%)", format="%.1f%%", min_value=0, max_value=60),
                "Est_Monthly_EBITDA_Lift_USD": st.column_config.NumberColumn("Monthly EBITDA Lift", format="+$%.2f"),
                "Patch_Action": st.column_config.TextColumn("Recommended Action", width="medium"),
            }
        )

        patch_csv_bytes = repricing_df.to_csv(index=False).encode("utf-8-sig")
        dl_p1, dl_p2 = st.columns([1.2, 1.8])
        with dl_p1:
            st.download_button(
                label=f"⬇️ Download Bulk POS & Aggregator Price Patch (.csv)",
                data=patch_csv_bytes,
                file_name=f"{company_name.replace(' ', '_')}_POS_Aggregator_Price_Patch.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        with dl_p2:
            st.caption(
                f"Formatted for direct bulk import into Foodics, Omega POS, Simphony, and Toters / Talabat / Deliveroo partner portals "
                f"(includes USD and normalized {local_curr_code} pricing)."
            )

    with tab3:
        st.markdown("**Aggregator Payout & Clawback Forensic Matcher (POS vs. Weekly Settlement)**")
        st.caption(
            "Cross-examines every POS delivery ticket against your weekly Toters, Talabat, Deliveroo, or Careem payout statement "
            "to isolate omitted 'Ghost Orders', commission tier overcharges, and unverified customer refund clawbacks."
        )

        stmt_mode = st.radio(
            "Aggregator Settlement Statement Source",
            ["Built-in Weekly Aggregator Statement (Demo Audit)", "Upload Custom Settlement Statement (.xlsx / .csv)"],
            horizontal=True
        )

        settlement_df = None
        if stmt_mode.startswith("Built-in"):
            settlement_df = generate_sample_aggregator_statement(cleaned_df, delivery_fee)
        else:
            up_stmt = st.file_uploader(
                "Upload Weekly Toters / Talabat / Deliveroo Payout Statement (.xlsx or .csv)",
                type=["xlsx", "xls", "csv"],
                key="agg_stmt_upload"
            )
            if up_stmt is not None:
                raw_stmt = safe_read_file(up_stmt)
                s_cols = list(raw_stmt.columns)
                st.markdown("**Map Settlement Statement Columns**")
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                with mc1:
                    c_oid = st.selectbox("Order ID Column", s_cols, index=guess_column_index(s_cols, ["order", "id", "ref", "ticket"]))
                with mc2:
                    c_gross = st.selectbox("Order Gross ($)", s_cols, index=guess_column_index(s_cols, ["gross", "amount", "sales", "subtotal"]))
                with mc3:
                    c_comm = st.selectbox("Commission Charged ($)", s_cols, index=guess_column_index(s_cols, ["comm", "fee", "charge"]))
                with mc4:
                    c_claw = st.selectbox("Refund / Clawback ($)", ["(None)"] + s_cols, index=guess_column_index(s_cols, ["refund", "clawback", "penalty", "dispute", "deduct"], allow_none=True))
                with mc5:
                    c_net = st.selectbox("Net Payout ($)", s_cols, index=guess_column_index(s_cols, ["net", "payout", "settled", "paid", "transfer"]))

                settlement_df = pd.DataFrame({
                    "Order_ID": raw_stmt[c_oid].astype(str),
                    "Aggregator_Gross_USD": clean_numeric_series(raw_stmt[c_gross], 0.0),
                    "Aggregator_Commission_USD": clean_numeric_series(raw_stmt[c_comm], 0.0),
                    "Unverified_Refund_Clawback_USD": clean_numeric_series(raw_stmt[c_claw], 0.0) if c_claw != "(None)" else 0.0,
                    "Promo_CoPay_Deduction_USD": 0.0,
                    "Aggregator_Net_Paid_USD": clean_numeric_series(raw_stmt[c_net], 0.0),
                })
            else:
                st.info("Upload your weekly aggregator payout file above, or switch to the Built-in Weekly Aggregator Statement to preview the forensic audit.")

        if settlement_df is not None:
            merged_recon, disputed_df, type_summary, agg_stats = audit_aggregator_settlement(
                cleaned_df, settlement_df, delivery_fee, demo_paywall_active
            )

            ak1, ak2, ak3, ak4 = st.columns(4)
            ak1.metric(
                "POS Expected Net Payout",
                f"${agg_stats['expected_net']:,.2f}",
                f"{agg_stats['pos_orders']:,} Delivery Orders"
            )
            ak2.metric(
                "Aggregator Settled Net",
                f"${agg_stats['actual_paid']:,.2f}",
                f"-${agg_stats['total_recoverable']:,.2f} Shortfall",
                delta_color="inverse"
            )
            ak3.metric(
                "Total Recoverable Claim",
                f"${agg_stats['total_recoverable']:,.2f}",
                f"{agg_stats['disputed_count']} Disputed Tickets"
            )
            ak4.metric(
                "Ghost Orders + Clawbacks",
                f"${agg_stats['ghost_usd'] + agg_stats['clawback_usd']:,.2f}",
                f"Overcharges: ${agg_stats['overcharge_usd'] + agg_stats['promo_err_usd']:,.2f}"
            )

            if agg_stats["total_recoverable"] > 0:
                monthly_clawback_proj = agg_stats["total_recoverable"] * (30.0 / max(active_days, 1))
                st.markdown(
                    f'<div class="exec-banner-warn"><strong>Recoverable Aggregator Leakage Detected:</strong> '
                    f'Found <strong>{agg_stats["disputed_count"]} delivery orders</strong> where the aggregator payout deviated from your '
                    f'contracted <strong>{delivery_fee*100:.1f}%</strong> commission rate—totaling <strong>${agg_stats["total_recoverable"]:,.2f} USD</strong> '
                    f'in immediate credit claims (<strong>~${monthly_clawback_proj:,.2f}/month</strong> annualized run-rate).</div>',
                    unsafe_allow_html=True
                )

                claim_excel_bytes = build_dispute_claim_excel(
                    disputed_df=disputed_df,
                    type_summary=type_summary,
                    company_name=company_name,
                    contracted_fee=delivery_fee,
                    stats=agg_stats
                )
                dispute_msg = (
                    f"*OFFICIAL SETTLEMENT DISPUTE CLAIM — {company_name.upper()}*\n\n"
                    f"Our POS reconciliation audit flagged *{agg_stats['disputed_count']} orders* in the current settlement cycle "
                    f"with a net payout shortfall of *${agg_stats['total_recoverable']:,.2f} USD* vs. our contracted {delivery_fee*100:.1f}% rate:\n"
                    f"• *Omitted / Ghost Orders:* ${agg_stats['ghost_usd']:,.2f} USD\n"
                    f"• *Unverified Refund Clawbacks:* ${agg_stats['clawback_usd']:,.2f} USD\n"
                    f"• *Commission Tier & Promo Overcharges:* ${agg_stats['overcharge_usd'] + agg_stats['promo_err_usd']:,.2f} USD\n\n"
                    f"Please find the Order-Level Evidence Workbook attached and issue a credit memo of *${agg_stats['total_recoverable']:,.2f} USD* on the next payout cycle."
                )
                dispute_wa_url = f"https://wa.me/?text={urllib.parse.quote(dispute_msg)}"

                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    st.download_button(
                        label="⬇️ Download Official Dispute Claim Packet (.xlsx)",
                        data=claim_excel_bytes,
                        file_name=f"{company_name.replace(' ', '_')}_Aggregator_Dispute_Claim.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                with btn_c2:
                    st.link_button(
                        "📤 Send Formal Dispute Notice via WhatsApp / Account Manager",
                        url=dispute_wa_url,
                        use_container_width=True
                    )

            st.markdown("**Discrepancy Breakdown by Violation Category**")
            st.dataframe(
                type_summary,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Audit_Finding": st.column_config.TextColumn("Violation Category", width="large"),
                    "Disputed_Orders": st.column_config.NumberColumn("Affected Orders", format="%d"),
                    "POS_Expected_Net_USD": st.column_config.NumberColumn("POS Expected Net ($)", format="$%.2f"),
                    "Aggregator_Net_Paid_USD": st.column_config.NumberColumn("Aggregator Paid ($)", format="$%.2f"),
                    "Recoverable_Claim_USD": st.column_config.NumberColumn("Recoverable Claim ($)", format="$%.2f"),
                }
            )

            st.markdown("**Order-Level Disputed Settlement Evidence Ledger**")
            st.dataframe(
                disputed_df[[
                    "Order_ID", "Clean_Date", "Branch", "Item_Name", "POS_Gross_USD",
                    "POS_Expected_Fee_USD", "Aggregator_Commission_USD", "Unverified_Refund_Clawback_USD",
                    "Promo_CoPay_Deduction_USD", "POS_Expected_Net_USD", "Aggregator_Net_Paid_USD",
                    "Recoverable_Claim_USD", "Audit_Finding"
                ]],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Order_ID": st.column_config.TextColumn("Order ID"),
                    "Clean_Date": st.column_config.TextColumn("Date"),
                    "Branch": st.column_config.TextColumn("Branch"),
                    "Item_Name": st.column_config.TextColumn("Primary Item"),
                    "POS_Gross_USD": st.column_config.NumberColumn("POS Gross", format="$%.2f"),
                    "POS_Expected_Fee_USD": st.column_config.NumberColumn("Contracted Fee", format="$%.2f"),
                    "Aggregator_Commission_USD": st.column_config.NumberColumn("Charged Fee", format="$%.2f"),
                    "Unverified_Refund_Clawback_USD": st.column_config.NumberColumn("Refund Clawback", format="$%.2f"),
                    "Promo_CoPay_Deduction_USD": st.column_config.NumberColumn("Promo Deduction", format="$%.2f"),
                    "POS_Expected_Net_USD": st.column_config.NumberColumn("Expected Net", format="$%.2f"),
                    "Aggregator_Net_Paid_USD": st.column_config.NumberColumn("Settled Net", format="$%.2f"),
                    "Recoverable_Claim_USD": st.column_config.NumberColumn("Claim Owed ($)", format="$%.2f"),
                    "Audit_Finding": st.column_config.TextColumn("Forensic Finding", width="medium"),
                }
            )

    with tab4:
        col_p1, col_p2 = st.columns([1.3, 1])
        with col_p1:
            st.markdown(f"**Operating P&L Waterfall ({active_days} Active Days)**")
            pnl_df = pd.DataFrame([
                {"Line Item": "1. Gross POS Revenue", "USD Amount": total_gross, "Share of Revenue (%)": 100.0},
                {"Line Item": "2. (-) Aggregator & POS Commissions", "USD Amount": -cleaned_df["Platform_Fee_USD"].sum(), "Share of Revenue (%)": -cleaned_df["Platform_Fee_USD"].sum() / total_gross * 100},
                {"Line Item": "3. (-) Delivery Packaging & Disposables", "USD Amount": -cleaned_df["Packaging_Cost_USD"].sum(), "Share of Revenue (%)": -cleaned_df["Packaging_Cost_USD"].sum() / total_gross * 100},
                {"Line Item": "4. (-) Raw Inventory COGS", "USD Amount": -cleaned_df["Raw_COGS_USD"].sum(), "Share of Revenue (%)": -cleaned_df["Raw_COGS_USD"].sum() / total_gross * 100},
                {"Line Item": "5. (-) Kitchen Waste & Spoilage", "USD Amount": -cleaned_df["Waste_Cost_USD"].sum(), "Share of Revenue (%)": -cleaned_df["Waste_Cost_USD"].sum() / total_gross * 100},
                {"Line Item": "= GROSS CONTRIBUTION PROFIT", "USD Amount": contrib_profit, "Share of Revenue (%)": contrib_profit / total_gross * 100},
                {"Line Item": "6. (-) Prorated Rent", "USD Amount": -prorated_opex_dict["rent"], "Share of Revenue (%)": -prorated_opex_dict["rent"] / total_gross * 100},
                {"Line Item": "7. (-) Prorated Staff Payroll", "USD Amount": -prorated_opex_dict["payroll"], "Share of Revenue (%)": -prorated_opex_dict["payroll"] / total_gross * 100},
                {"Line Item": "8. (-) Prorated Generator & Utilities", "USD Amount": -prorated_opex_dict["utilities"], "Share of Revenue (%)": -prorated_opex_dict["utilities"] / total_gross * 100},
                {"Line Item": "= OPERATING EBITDA (NET CASH FLOW)", "USD Amount": true_ebitda, "Share of Revenue (%)": ebitda_margin_pct},
            ])
            st.dataframe(
                pnl_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Line Item": st.column_config.TextColumn("P&L Line Item", width="medium"),
                    "USD Amount": st.column_config.NumberColumn("Amount (USD)", format="$%.2f"),
                    "Share of Revenue (%)": st.column_config.NumberColumn("% of Gross Sales", format="%.1f%%"),
                }
            )

        with col_p2:
            st.markdown("**Break-Even & Working Capital Settlement Lag**")
            avg_daily_sales = total_gross / active_days
            safety_margin = ((avg_daily_sales - daily_breakeven_sales) / avg_daily_sales * 100) if avg_daily_sales else 0.0

            b1, b2 = st.columns(2)
            b1.metric("Daily Break-Even Target", f"${daily_breakeven_sales:,.2f}/day")
            b2.metric("Actual Daily Average", f"${avg_daily_sales:,.2f}/day", f"{safety_margin:+.1f}% cushion")

            instant_cash = cleaned_df[cleaned_df["Channel"].isin(["In-Store Cash", "Digital Wallet (Whish)"])]["Net_Revenue_USD"].sum()
            card_hold = cleaned_df[cleaned_df["Channel"] == "Card POS Terminal"]["Net_Revenue_USD"].sum()
            aggregator_hold = cleaned_df[cleaned_df["Channel"] == "Delivery Aggregators"]["Net_Revenue_USD"].sum()

            wc_df = pd.DataFrame([
                {"Settlement Bucket": "Immediate Cash & Digital Wallet", "Net Receivable": instant_cash, "Settlement Cycle": "Same Day (0 Days)"},
                {"Settlement Bucket": "Card POS Acquirer Hold", "Net Receivable": card_hold, "Settlement Cycle": "2–3 Business Days"},
                {"Settlement Bucket": "Delivery Aggregator Hold", "Net Receivable": aggregator_hold, "Settlement Cycle": "7–14 Days (Weekly)"},
            ])
            st.dataframe(
                wc_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Net Receivable": st.column_config.NumberColumn("Net Receivable (USD)", format="$%.2f")
                }
            )

    with tab5:
        st.markdown("**End-of-Shift Cash Drawer Reconciliation**")
        branches_list = ["All Branches"] + sorted(cleaned_df["Branch"].unique().tolist())
        sel_branch = st.selectbox("Select Branch to Reconcile", branches_list)
        b_df = cleaned_df if sel_branch == "All Branches" else cleaned_df[cleaned_df["Branch"] == sel_branch]
        expected_cash = b_df[b_df["Channel"] == "In-Store Cash"]["Gross_Sales_USD"].sum()

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            counted_usd = st.number_input("Counted USD Notes ($)", min_value=0.0, value=float(round(expected_cash * 0.70, 2)), step=10.0)
        with col_c2:
            local_notes_label = "Counted AED Notes (AED)" if active_market == "Dubai" else "Counted LBP Notes (LBP)"
            local_notes_step = 50.0 if active_market == "Dubai" else 100000.0
            local_notes_val = float(round(expected_cash * 0.30 * lbp_rate, 2 if active_market == "Dubai" else -3))
            counted_lbp = st.number_input(local_notes_label, min_value=0.0, value=local_notes_val, step=local_notes_step)
        with col_c3:
            total_counted = counted_usd + (counted_lbp / lbp_rate)
            variance = total_counted - expected_cash
            st.metric("Expected POS Cash", f"${expected_cash:,.2f}")
            st.metric("Total Physical Cash (USD Equiv.)", f"${total_counted:,.2f}", f"{variance:+.2f} USD Variance")

    with tab6:
        st.markdown("**Register Forensic Engine: 'Cash-Only Discount Bias' & Post-Payment Skimming Audit**")
        st.caption(
            "Detects the #1 hospitality register theft pattern: a customer pays full price in cash, and the operator subsequently applies "
            "a 20%–50% staff/promo discount on the open cash ticket to pocket the cash difference while keeping the physical drawer balanced."
        )

        forensic_df, suspicious_tickets, f_stats = build_register_forensics(cleaned_df, demo_paywall_active)

        fk1, fk2, fk3, fk4 = st.columns(4)
        fk1.metric(
            "Critical Operators Flagged",
            f"{f_stats['critical_operators']} Operator(s)",
            "Cash-Pocketing Signature" if f_stats["critical_operators"] > 0 else "Within Peer Norm",
            delta_color="inverse" if f_stats["critical_operators"] > 0 else "normal"
        )
        fk2.metric(
            "Suspected Cash Skimmed",
            f"${f_stats['suspected_cash_pocketed_usd']:,.2f}",
            f"Est. ${f_stats['suspected_cash_pocketed_usd'] * (30.0 / max(active_days, 1)):,.0f} / mo exposure",
            delta_color="inverse"
        )
        fk3.metric(
            "High-Risk Cash Discount Tickets",
            f"{f_stats['suspicious_cash_tickets']} Tickets",
            "In-Store Cash Discounts >= 15%"
        )
        fk4.metric(
            "Peak Cash-vs-Card Bias",
            f"{f_stats['max_bias_ratio']:.1f}x Multiplier",
            "Cash Disc % vs. Card Disc %"
        )

        if f_stats["critical_operators"] > 0:
            st.markdown(
                f'<div class="exec-banner-warn"><strong>Forensic Alert — Asymmetric Cash Discounting Detected:</strong> '
                f'<strong>{f_stats["critical_operators"]} operator/branch profile(s)</strong> exhibit a Cash-Ticket Discount Rate '
                f'up to <strong>{f_stats["max_bias_ratio"]:.1f}x higher</strong> than their Card/Wallet discount rate across '
                f'<strong>{f_stats["suspicious_cash_tickets"]} cash transactions</strong> (${f_stats["suspected_cash_pocketed_usd"]:,.2f} USD). '
                f'Require manager PIN overrides on all post-print cash discounts immediately.</div>',
                unsafe_allow_html=True
            )

        st.markdown("**Peer-Benchmarked Operator Forensic Matrix**")
        st.dataframe(
            forensic_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Branch": st.column_config.TextColumn("Branch"),
                "Cashier_Server": st.column_config.TextColumn("Operator"),
                "Total_Orders": st.column_config.NumberColumn("Total Orders", format="%d"),
                "Cash_Orders": st.column_config.NumberColumn("Cash Orders", format="%d"),
                "Cash_Disc_Tickets": st.column_config.NumberColumn("Discounted Cash Tickets", format="%d"),
                "Cash_Discounts_USD": st.column_config.NumberColumn("Cash Discounts ($)", format="$%.2f"),
                "Cash_Disc_Rate_Pct": st.column_config.NumberColumn("Cash Disc. Rate (%)", format="%.1f%%"),
                "Card_Wallet_Disc_Rate_Pct": st.column_config.NumberColumn("Card/Wallet Disc. (%)", format="%.1f%%"),
                "Cash_Bias_Ratio": st.column_config.NumberColumn("Cash Bias Ratio", format="%.1fx"),
                "Bev_Side_Attach_Pct": st.column_config.NumberColumn("Bev/Side Attach (%)", format="%.1f%%"),
                "Forensic_Risk_Score": st.column_config.ProgressColumn("Forensic Risk Score", format="%d / 100", min_value=0, max_value=100),
                "Forensic_Verdict": st.column_config.TextColumn("Forensic Verdict", width="medium"),
            }
        )

        st.markdown("**Flagged High-Risk In-Store Cash Discount Tickets (Audit Evidence)**")
        st.dataframe(
            suspicious_tickets,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Order_ID": st.column_config.TextColumn("Order ID"),
                "Clean_Date": st.column_config.TextColumn("Date"),
                "Branch": st.column_config.TextColumn("Branch"),
                "Cashier_Server": st.column_config.TextColumn("Operator"),
                "Item_Name": st.column_config.TextColumn("Menu Item"),
                "Pre_Discount_Gross_USD": st.column_config.NumberColumn("Original Ticket ($)", format="$%.2f"),
                "Discount_USD": st.column_config.NumberColumn("Cash Discount Applied ($)", format="$%.2f"),
                "Gross_Sales_USD": st.column_config.NumberColumn("Net Cash Logged ($)", format="$%.2f"),
                "Ticket_Discount_Pct": st.column_config.NumberColumn("Discount %", format="%.1f%%"),
            }
        )

    with tab7:
        memo_lang = st.radio("Memo Language", ["English", "Français", "العربية"], horizontal=True)
        aggregator_hold_val = cleaned_df[cleaned_df["Channel"] == "Delivery Aggregators"]["Net_Revenue_USD"].sum()

        memo_html, memo_wa_text = build_cfo_memo_content(
            memo_lang, company_name, active_days, total_gross, total_fees_pkg,
            true_ebitda, ebitda_margin_pct, daily_breakeven_sales,
            display_matrix, aggregator_hold_val
        )
        st.markdown(memo_html, unsafe_allow_html=True)

        wa_summary_url = f"https://wa.me/?text={urllib.parse.quote(memo_wa_text)}"
        st.link_button("Forward Executive Memo via WhatsApp", url=wa_summary_url, type="primary")


if not st.session_state.authenticated:
    login_screen()
else:
    main_portal()
