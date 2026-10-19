import io
import json
import os
import re
import random
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

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
# PAGE CONFIGURATION & OBSIDIAN DARK DESIGN SYSTEM
# ==============================================================================
st.set_page_config(
    page_title="Financial & POS Reconciliation Suite",
    layout="wide",
    initial_sidebar_state="expanded"
)

OWNER_WHATSAPP = "96170000000"
OWNER_EMAIL = "ryankhreiss@gmail.com"
ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "ryanadmin2026"

CLIENTS_JSON_PATH = "clients_store.json"
COGS_STORAGE_DIR = "client_cogs_store"
os.makedirs(COGS_STORAGE_DIR, exist_ok=True)

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
        "company_name": "Beirut Hospitality Group",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 25.0,
        "card_fee_pct": 2.0,
        "whish_fee_pct": 1.0,
        "packaging_cost_usd": 0.65,
        "waste_pct": 3.0,
        "monthly_rent_usd": 1800.0,
        "monthly_payroll_usd": 2400.0,
        "monthly_generator_utilities_usd": 750.0,
    },
    "bistro_client": {
        "password": "bistro2026",
        "company_name": "Mar Mikhael Resto-Cafe",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 24.0,
        "card_fee_pct": 1.8,
        "whish_fee_pct": 1.0,
        "packaging_cost_usd": 0.50,
        "waste_pct": 2.5,
        "monthly_rent_usd": 1600.0,
        "monthly_payroll_usd": 2200.0,
        "monthly_generator_utilities_usd": 650.0,
    }
}

def get_admin_password() -> str:
    try:
        if "admin_password" in st.secrets:
            return str(st.secrets["admin_password"])
    except Exception:
        pass
    return DEFAULT_ADMIN_PASSWORD

def get_client_db() -> dict:
    db = dict(DEFAULT_CLIENTS)
    # 1. Merge permanent accounts from Streamlit Cloud Secrets
    try:
        if "clients" in st.secrets:
            for k, v in st.secrets["clients"].items():
                db[str(k).strip().lower()] = dict(v)
    except Exception:
        pass
    # 2. Merge dynamically created accounts from local JSON store
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
    lines = [f'admin_password = "{get_admin_password()}"', ""]
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
    if query_params.get("demo", "").lower() in ["1", "true", "yes"]:
        clients = get_client_db()
        st.session_state.authenticated = True
        st.session_state.username = "demo"
        st.session_state.client_profile = clients["demo"]
        st.session_state.is_admin = False
    elif "client" in query_params and "key" in query_params:
        c_user = query_params.get("client", "").strip().lower()
        c_key = query_params.get("key", "")
        clients = get_client_db()
        if c_user in clients and clients[c_user]["password"] == c_key:
            st.session_state.authenticated = True
            st.session_state.username = c_user
            st.session_state.client_profile = clients[c_user]
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

        if st.button("Launch Interactive Demo Environment", type="primary", use_container_width=True):
            clients = get_client_db()
            st.session_state.authenticated = True
            st.session_state.username = "demo"
            st.session_state.client_profile = clients["demo"]
            st.session_state.is_admin = False
            st.rerun()

        st.markdown(
            "<div style='text-align:center; color:#64748B; font-size:0.72rem; margin: 18px 0; "
            "text-transform:uppercase; letter-spacing:0.08em;'>Client & Administrator Sign In</div>",
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input("Account Identifier", placeholder="demo or admin").strip().lower()
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if username == ADMIN_USERNAME and password == get_admin_password():
                    clients = get_client_db()
                    st.session_state.authenticated = True
                    st.session_state.username = ADMIN_USERNAME
                    st.session_state.client_profile = clients["demo"]
                    st.session_state.is_admin = True
                    st.rerun()

                clients = get_client_db()
                if username in clients and clients[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.client_profile = clients[username]
                    st.session_state.is_admin = False
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use the button above to launch the demo environment.")

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
            return default_val
        s = str(val).strip()
        if not s:
            return default_val
        is_neg = s.startswith("(") and s.endswith(")")
        s = re.sub(r"[^0-9.,-]", "", s)
        if not s:
            return default_val
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
            return -abs(num) if is_neg else num
        except Exception:
            return default_val

    return series.apply(parse_val)

def classify_channel_and_fee(raw_channel: str, delivery_fee: float, card_fee: float, whish_fee: float):
    c = str(raw_channel).strip().lower()
    if any(k in c for k in ["toter", "talabat", "deliveroo", "careem", "noon", "zomato", "jahez", "hunger", "aggregat", "delivery"]):
        return "Delivery Aggregators", delivery_fee, True
    if any(k in c for k in ["whish", "wish", "omt", "bob", "wallet"]):
        return "Digital Wallet (Whish)", whish_fee, False
    if any(k in c for k in ["card", "visa", "master", "amex", "pos", "bank", "carte", "credit", "debit"]):
        return "Card POS Terminal", card_fee, False
    return "In-Store Cash", 0.0, False

# ==============================================================================
# SAMPLE DATA GENERATOR
# ==============================================================================
@st.cache_data
def generate_sample_datasets(lbp_rate: float):
    cogs_data = [
        {"SKU": "SKU-101", "Item_Name": "Signature Truffle Burger", "Category": "Mains", "Unit_Cost_USD": 4.20, "Menu_Price_USD": 13.50},
        {"SKU": "SKU-102", "Item_Name": "Crispy Chicken Sliders", "Category": "Mains", "Unit_Cost_USD": 4.80, "Menu_Price_USD": 9.50},
        {"SKU": "SKU-103", "Item_Name": "Artisanal Kale & Quinoa Salad", "Category": "Salads", "Unit_Cost_USD": 2.40, "Menu_Price_USD": 11.00},
        {"SKU": "SKU-104", "Item_Name": "Loaded Parmesan Fries", "Category": "Sides", "Unit_Cost_USD": 1.10, "Menu_Price_USD": 5.50},
        {"SKU": "SKU-105", "Item_Name": "Combo Meal Box (Aggregator Promo)", "Category": "Promos", "Unit_Cost_USD": 8.90, "Menu_Price_USD": 13.00},
        {"SKU": "SKU-106", "Item_Name": "Specialty Iced Matcha Latte", "Category": "Beverages", "Unit_Cost_USD": 1.30, "Menu_Price_USD": 5.50},
    ]
    cogs_df = pd.DataFrame(cogs_data)
    sku_weights = [0.26, 0.20, 0.09, 0.19, 0.16, 0.10]

    branches = ["Ashrafieh Flagship", "Mar Mikhael Branch", "Dbayeh Highway"]
    cashiers = ["Nabil K.", "Maya S.", "Rami H.", "System_Aggregator"]
    channels = ["In-Store Cash", "Whish Money", "Bank Card POS", "Toters Delivery", "Talabat / Deliveroo"]
    channel_weights = [0.32, 0.18, 0.15, 0.23, 0.12]

    random.seed(42)
    rows = []
    start_date = datetime(2026, 10, 1)

    for i in range(1, 621):
        sku_info = random.choices(cogs_data, weights=sku_weights)[0]
        qty = random.choices([1, 2, 3, 4], weights=[0.50, 0.32, 0.12, 0.06])[0]
        channel = random.choices(channels, weights=channel_weights)[0]
        branch = random.choice(branches)
        cashier = "System_Aggregator" if "Toters" in channel or "Talabat" in channel else random.choice(cashiers[:3])
        tx_date = start_date + timedelta(days=random.randint(0, 14))
        date_str = tx_date.strftime("%Y-%m-%d")

        is_lbp = (channel == "In-Store Cash") and (random.random() < 0.35)
        list_gross_usd = sku_info["Menu_Price_USD"] * qty

        discount_usd = 0.0
        if cashier == "Rami H." and channel == "In-Store Cash" and random.random() < 0.25:
            discount_usd = round(list_gross_usd * random.choice([0.20, 0.40, 0.50]), 2)
        elif random.random() < 0.03:
            discount_usd = round(list_gross_usd * 0.10, 2)

        net_charged_usd = max(0.0, list_gross_usd - discount_usd)
        currency = "LBP" if is_lbp else "USD"
        raw_amount = round(net_charged_usd * lbp_rate, -3) if is_lbp else net_charged_usd

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
# CORE FINANCIAL & BCG MATRIX ENGINE
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
    df["Cashier_Server"] = df.get("Cashier_Server", pd.Series(["Standard_POS"] * len(df))).astype(str).str.strip()

    df["Quantity"] = clean_numeric_series(df["Quantity"], default_val=1.0)
    df.loc[df["Quantity"] <= 0, "Quantity"] = 1.0
    df["Gross_Amount_Raw"] = clean_numeric_series(df["Gross_Amount_Raw"], default_val=0.0)
    df["Discount_USD"] = clean_numeric_series(df.get("Discount_USD", pd.Series([0.0] * len(df))), default_val=0.0)

    def calc_usd(row):
        curr = str(row["Currency"]).strip().upper()
        amt = float(row["Gross_Amount_Raw"])
        if "LBP" in curr or "LL" in curr or "L.L" in curr:
            return amt / lbp_rate
        if curr == "AUTO" and amt >= 10000:
            return amt / lbp_rate
        return amt

    df["Gross_Sales_USD"] = df.apply(calc_usd, axis=1)
    df = df[df["Gross_Sales_USD"] > 0].copy()
    df["Unit_Cost_USD"] = None
    df["Category"] = "General"

    if std_cogs is not None and not std_cogs.empty:
        cogs_clean = std_cogs.copy()
        cogs_clean["Unit_Cost_USD"] = clean_numeric_series(cogs_clean["Unit_Cost_USD"], default_val=0.0)

        if "SKU" in cogs_clean.columns and (df["SKU"] != "N/A").any():
            sku_map = cogs_clean.drop_duplicates(subset=["SKU"]).set_index("SKU")
            df["Unit_Cost_USD"] = df["SKU"].map(sku_map["Unit_Cost_USD"])
            if "Category" in sku_map.columns:
                df["Category"] = df["SKU"].map(sku_map["Category"]).fillna("General")

        if "Item_Name" in cogs_clean.columns:
            cogs_clean["_item_key"] = cogs_clean["Item_Name"].astype(str).str.strip().str.lower()
            name_map = cogs_clean.drop_duplicates(subset=["_item_key"]).set_index("_item_key")
            df["_item_key"] = df["Item_Name"].astype(str).str.strip().str.lower()

            missing_cost = df["Unit_Cost_USD"].isna()
            df.loc[missing_cost, "Unit_Cost_USD"] = df.loc[missing_cost, "_item_key"].map(name_map["Unit_Cost_USD"])
            if "Category" in name_map.columns:
                df.loc[df["Category"] == "General", "Category"] = df.loc[df["Category"] == "General", "_item_key"].map(name_map["Category"]).fillna("General")
            df.drop(columns=["_item_key"], inplace=True, errors="ignore")

    df["Raw_COGS_USD"] = df["Quantity"] * df["Unit_Cost_USD"]
    unmatched = df["Raw_COGS_USD"].isna() | (df["Raw_COGS_USD"] <= 0)
    df.loc[unmatched, "Raw_COGS_USD"] = df.loc[unmatched, "Gross_Sales_USD"] * fallback_cogs_pct
    df.loc[unmatched, "Unit_Cost_USD"] = df.loc[unmatched, "Raw_COGS_USD"] / df.loc[unmatched, "Quantity"]

    df["Raw_COGS_USD"] = df["Raw_COGS_USD"] * (1.0 + supplier_inflation_pct)
    df["Waste_Cost_USD"] = df["Raw_COGS_USD"] * waste_pct
    df["Total_COGS_USD"] = df["Raw_COGS_USD"] + df["Waste_Cost_USD"]

    ch_results = df["Channel"].apply(lambda c: classify_channel_and_fee(c, delivery_fee, card_fee, whish_fee))
    df["Channel"] = [r[0] for r in ch_results]
    df["Fee_Pct"] = [r[1] for r in ch_results]
    df["Is_Delivery"] = [r[2] for r in ch_results]

    df["Platform_Fee_USD"] = df["Gross_Sales_USD"] * df["Fee_Pct"]
    df["Packaging_Cost_USD"] = df.apply(lambda r: r["Quantity"] * packaging_cost_usd if r["Is_Delivery"] else 0.0, axis=1)
    df["Net_Revenue_USD"] = df["Gross_Sales_USD"] - df["Platform_Fee_USD"]
    df["Net_Profit_USD"] = df["Net_Revenue_USD"] - df["Total_COGS_USD"] - df["Packaging_Cost_USD"]
    df["Net_Margin_Pct"] = df["Net_Profit_USD"] / df["Gross_Sales_USD"]

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
# EXCEL WORKBOOK GENERATOR
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
    channel_summary["Margin_Pct"] = channel_summary["Contribution_Profit_USD"] / channel_summary["Gross_Sales_USD"]
    channel_summary = channel_summary.sort_values(by="Contribution_Profit_USD", ascending=False)

    branch_summary = df.groupby("Branch", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Packaging_USD=("Packaging_Cost_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Contribution_Profit_USD=("Net_Profit_USD", "sum")
    )
    branch_summary["Margin_Pct"] = branch_summary["Contribution_Profit_USD"] / branch_summary["Gross_Sales_USD"]

    daily_recon = df.pivot_table(
        index="Clean_Date",
        columns="Channel",
        values="Net_Revenue_USD",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()
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
        alert_red_fmt = wb.add_format({"bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1})
        alert_green_fmt = wb.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True, "border": 1})
        alert_warn_fmt = wb.add_format({"bg_color": "#FEF3C7", "font_color": "#92400E", "bold": True, "border": 1})

        ws_exec = wb.add_worksheet("01_Executive_Summary")
        ws_exec.hide_gridlines(2)
        ws_exec.write("B2", f"{company_name.upper()} — EXECUTIVE FINANCIAL SUMMARY", title_fmt)
        ws_exec.write("B3", f"Normalized to USD (Rate: {lbp_rate:,.0f} LBP/USD | Active Days: {prorated_opex['days']})", subtitle_fmt)

        total_gross = df["Gross_Sales_USD"].sum()
        total_fees_pkg = df["Platform_Fee_USD"].sum() + df["Packaging_Cost_USD"].sum()
        total_cogs = df["Total_COGS_USD"].sum()
        contrib_profit = df["Net_Profit_USD"].sum()
        ebitda_val = contrib_profit - prorated_opex["total_opex"]
        ebitda_margin = ebitda_val / total_gross if total_gross else 0

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

        b_row = start_row + len(channel_summary) + 3
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
        ws_exec.set_column("B:M", 18)

        ws_sku = wb.add_worksheet("02_BCG_Menu_Matrix")
        ws_sku.hide_gridlines(2)
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
        ws_sku.set_column("B:N", 22)

        daily_recon.to_excel(writer, sheet_name="03_Daily_Payout_Recon", index=False, startrow=3, startcol=1)
        ws_recon = writer.sheets["03_Daily_Payout_Recon"]
        ws_recon.hide_gridlines(2)
        ws_recon.write("B2", "DAILY EXPECTED NET PAYOUT SCHEDULE", title_fmt)
        for col_idx, col_name in enumerate(daily_recon.columns):
            ws_recon.write(3, 1 + col_idx, col_name.replace("_", " "), header_fmt)
        ws_recon.set_column("B:I", 22)

        df.to_excel(writer, sheet_name="04_Clean_Master_Ledger", index=False)
        ws_raw = writer.sheets["04_Clean_Master_Ledger"]
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
        <div class="suite-subtitle">Create new client accounts, pre-load client SKU COGS sheets, generate 1-click client magic links, and export permanent cloud secrets.</div>
    </div>
    """, unsafe_allow_html=True)

    clients_db = get_client_db()

    col_form, col_list = st.columns([1.35, 1.0])

    with col_form:
        st.markdown("#### 1. Create or Update Client Account")
        with st.form("create_client_form"):
            f1, f2 = st.columns(2)
            with f1:
                new_username = st.text_input("Client Login Username *", placeholder="e.g., roadster_ashrafieh").strip().lower()
                new_company = st.text_input("Company / Brand Display Name *", placeholder="e.g., Roadster Diner (Ashrafieh)")
                new_lbp_rate = st.number_input("Default LBP / USD Rate", value=89500.0, step=500.0)
                new_deliv_fee = st.number_input("Toters / Aggregator Fee (%)", value=25.0, step=0.5)
                new_pkg_cost = st.number_input("Delivery Packaging / Unit ($)", value=0.65, step=0.05)
            with f2:
                new_password = st.text_input("Client Password *", placeholder="e.g., rd2026")
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
            st.caption("If you upload their COGS sheet here, it attaches to their account automatically so they only ever need to upload 1 file (their weekly POS sales export).")
            admin_cogs_file = st.file_uploader("Upload Client COGS Sheet", type=["csv", "xlsx", "xls"])

            save_btn = st.form_submit_button("Create / Update Client Account", type="primary", use_container_width=True)

            if save_btn:
                clean_u = re.sub(r"[^a-z0-9_-]", "", new_username)
                if not clean_u or not new_password or not new_company:
                    st.error("Please provide a valid Username, Password, and Company Name.")
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

                    st.success(f"Account `{clean_u}` ({new_company}) is now live!")
                    st.rerun()

    with col_list:
        st.markdown("#### 2. Active Client Accounts & Onboarding Links")
        rows = []
        for u, p in clients_db.items():
            has_cogs = "Yes (Pre-Loaded)" if load_client_cogs_df(u) is not None else "Standard"
            rows.append({
                "Username": u,
                "Password": p.get("password", ""),
                "Company": p.get("company_name", ""),
                "Delivery Fee": f"{p.get('delivery_fee_pct', 25.0):.1f}%",
                "Monthly OPEX": f"${p.get('monthly_rent_usd', 0) + p.get('monthly_payroll_usd', 0) + p.get('monthly_generator_utilities_usd', 0):,.0f}",
                "Saved COGS": has_cogs
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        selected_client = st.selectbox("Select Client to Generate Onboarding Package or Preview", list(clients_db.keys()))
        sel_p = clients_db[selected_client]
        magic_client_url = f"https://exec-pos-audit.streamlit.app/?client={selected_client}&key={urllib.parse.quote(str(sel_p['password']))}"

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
            if st.button("Impersonate / Preview Client", use_container_width=True):
                st.session_state.client_profile = sel_p
                st.session_state.username = selected_client
                st.session_state.impersonating = True
                st.rerun()
        with b_act2:
            wa_onboard_url = f"https://wa.me/?text={urllib.parse.quote(onboarding_text)}"
            st.link_button("Send Login via WhatsApp", url=wa_onboard_url, use_container_width=True)
        with b_act3:
            if selected_client not in ["demo", "bistro_client"]:
                if st.button("Delete Account", use_container_width=True):
                    delete_client_from_store(selected_client)
                    st.rerun()

        with st.expander("Permanent Cloud Backup (Streamlit Secrets TOML)"):
            st.caption("Copy and paste this block into Streamlit Cloud -> Settings -> Secrets so all accounts persist permanently across server redeployments.")
            st.code(format_secrets_toml(clients_db), language="toml")

# ==============================================================================
# MAIN AUTHENTICATED WORKSPACE
# ==============================================================================
def main_portal():
    profile = st.session_state.client_profile
    company_name = profile["company_name"]
    is_admin = st.session_state.get("is_admin", False)

    with st.sidebar:
        st.markdown(f"<div style='font-size:1.05rem; font-weight:700; color:#F8FAFC; margin-bottom:2px;'>{company_name}</div>", unsafe_allow_html=True)
        st.caption(f"Account: `{st.session_state.username}`" + (" (MASTER ADMIN)" if is_admin else ""))

        role_options = ["CFO / Executive View", "Branch Manager (Cash Recon)"]
        if is_admin:
            role_options = ["Master Admin: Client Provisioning"] + role_options

        role = st.selectbox("Workspace Mode", role_options)

        with st.expander("1. FX & Channel Fees", expanded=True):
            lbp_rate = st.number_input("LBP / USD Exchange Rate", min_value=1000.0, max_value=500000.0, value=float(profile.get("default_lbp_rate", 89500.0)), step=500.0)
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
        wa_msg = urllib.parse.quote("Hi Ryan, I reviewed the Executive POS & EBITDA Suite and would like to configure a custom audit for our branches.")
        st.link_button("Request Custom Deployment", url=f"https://wa.me/{OWNER_WHATSAPP}?text={wa_msg}", use_container_width=True)
        if st.button("Sign Out", use_container_width=True):
            st.query_params.clear()
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.rerun()

    # If Master Admin selected the Provisioning Console
    if role == "Master Admin: Client Provisioning":
        render_admin_console()
        return

    # Top Workspace Header & Aligned Data Source Selector
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

    std_pos, std_cogs = None, None
    preloaded_client_cogs = load_client_cogs_df(st.session_state.username)

    if mode == "Upload Custom POS File":
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
                col_curr = st.selectbox("Currency (LBP / USD)", opt_pos_cols, index=guess_column_index(pos_cols, ["curr", "devise", "currency"], allow_none=True))
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
        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate)
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
            counted_lbp = st.number_input("Physical LBP Bills Counted (LBP)", min_value=0.0, value=float(round(expected_cash * 0.30 * lbp_rate, -3)), step=100000.0)

        total_counted_usd = counted_usd + (counted_lbp / lbp_rate)
        variance_usd = total_counted_usd - expected_cash
        if abs(variance_usd) < 1.0:
            st.success(f"Drawer Balanced — Total Counted: ${total_counted_usd:,.2f} (Variance: ${variance_usd:+.2f})")
        elif variance_usd < 0:
            st.error(f"Cash Shortage Detected — Drawer is short by ${abs(variance_usd):,.2f} ({abs(variance_usd)*lbp_rate:,.0f} LBP)")
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
        st.caption(f"Normalized ledger across {active_days} active day(s) at {lbp_rate:,.0f} LBP/USD.")
    with bar_right:
        excel_bytes = build_excel_in_memory(cleaned_df, sku_matrix, company_name, lbp_rate, prorated_opex_dict)
        st.download_button(
            label="Export Executive Workbook (.xlsx)",
            data=excel_bytes,
            file_name=f"{company_name.replace(' ', '_')}_Financial_Audit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Menu Engineering (BCG)",
        "Price Elasticity Lab",
        "EBITDA & Working Capital",
        "Cash Drawer Audit",
        "Discount & Void Controls",
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
            sku_matrix,
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
        st.markdown("**Unit Price & Volume Elasticity Simulator**")
        st.caption("Model the net monthly EBITDA impact of repricing an item while accounting for potential customer volume dropoff.")

        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            selected_item = st.selectbox("Select SKU to Model", sku_matrix["Item_Name"].tolist())
        with sim_col2:
            price_increase = st.slider("Proposed Price Increase (+USD)", 0.25, 5.00, 1.25, 0.25)
        with sim_col3:
            volume_dropoff_pct = st.slider("Assumed Volume Dropoff (%)", 0.0, 30.0, 5.0, 1.0) / 100.0

        item_row = sku_matrix[sku_matrix["Item_Name"] == selected_item].iloc[0]
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

    with tab3:
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

    with tab4:
        st.markdown("**End-of-Shift Cash Drawer Reconciliation**")
        branches_list = ["All Branches"] + sorted(cleaned_df["Branch"].unique().tolist())
        sel_branch = st.selectbox("Select Branch to Reconcile", branches_list)
        b_df = cleaned_df if sel_branch == "All Branches" else cleaned_df[cleaned_df["Branch"] == sel_branch]
        expected_cash = b_df[b_df["Channel"] == "In-Store Cash"]["Gross_Sales_USD"].sum()

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            counted_usd = st.number_input("Counted USD Notes ($)", min_value=0.0, value=float(round(expected_cash * 0.70, 2)), step=10.0)
        with col_c2:
            counted_lbp = st.number_input("Counted LBP Notes (LBP)", min_value=0.0, value=float(round(expected_cash * 0.30 * lbp_rate, -3)), step=100000.0)
        with col_c3:
            total_counted = counted_usd + (counted_lbp / lbp_rate)
            variance = total_counted - expected_cash
            st.metric("Expected POS Cash", f"${expected_cash:,.2f}")
            st.metric("Total Physical Cash (USD Equiv.)", f"${total_counted:,.2f}", f"{variance:+.2f} USD Variance")

    with tab5:
        st.markdown("**Cashier Discount & Void Anomaly Audit**")
        st.caption("Monitors discount frequency across operators and branches to identify unauthorized comps or register leakage.")

        cashier_audit = cleaned_df.groupby(["Branch", "Cashier_Server"], as_index=False).agg(
            Total_Orders=("Order_ID", "count"),
            Gross_Sales_USD=("Gross_Sales_USD", "sum"),
            Total_Discounts_USD=("Discount_USD", "sum"),
            Discounted_Orders=("Discount_USD", lambda s: int((s > 0).sum()))
        )
        cashier_audit["Discount_Rate_Pct"] = (
            cashier_audit["Total_Discounts_USD"] / (cashier_audit["Gross_Sales_USD"] + cashier_audit["Total_Discounts_USD"])
        ) * 100.0
        cashier_audit["Control_Status"] = cashier_audit["Discount_Rate_Pct"].apply(
            lambda r: "AUDIT REQUIRED (>5%)" if r >= 5.0 else ("ELEVATED (2–5%)" if r >= 2.0 else "WITHIN POLICY")
        )
        st.dataframe(
            cashier_audit.sort_values("Total_Discounts_USD", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Branch": st.column_config.TextColumn("Branch"),
                "Cashier_Server": st.column_config.TextColumn("Operator"),
                "Total_Orders": st.column_config.NumberColumn("Orders", format="%d"),
                "Discounted_Orders": st.column_config.NumberColumn("Discounted Tickets", format="%d"),
                "Gross_Sales_USD": st.column_config.NumberColumn("Net Sales (USD)", format="$%.2f"),
                "Total_Discounts_USD": st.column_config.NumberColumn("Discounts Granted", format="$%.2f"),
                "Discount_Rate_Pct": st.column_config.ProgressColumn("Discount Rate (%)", format="%.1f%%", min_value=0, max_value=25),
                "Control_Status": st.column_config.TextColumn("Audit Status"),
            }
        )

    with tab6:
        memo_lang = st.radio("Memo Language", ["English", "Français", "العربية"], horizontal=True)
        aggregator_hold_val = cleaned_df[cleaned_df["Channel"] == "Delivery Aggregators"]["Net_Revenue_USD"].sum()

        memo_html, memo_wa_text = build_cfo_memo_content(
            memo_lang, company_name, active_days, total_gross, total_fees_pkg,
            true_ebitda, ebitda_margin_pct, daily_breakeven_sales,
            sku_matrix, aggregator_hold_val
        )
        st.markdown(memo_html, unsafe_allow_html=True)

        wa_summary_url = f"https://wa.me/?text={urllib.parse.quote(memo_wa_text)}"
        st.link_button("Forward Executive Memo via WhatsApp", url=wa_summary_url, type="primary")

if not st.session_state.authenticated:
    login_screen()
else:
    main_portal()
