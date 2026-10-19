import io
import re
import random
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# PAGE CONFIGURATION & OWNER CONTACT
# ==============================================================================
st.set_page_config(
    page_title="Executive POS, EBITDA & Menu Engineering Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

OWNER_WHATSAPP = "96170000000"
OWNER_EMAIL = "ryankhreiss@gmail.com"

# ==============================================================================
# MULTI-TENANT CLIENT ACCOUNTS (WITH OPEX & PACKAGING DEFAULTS)
# ==============================================================================
DEFAULT_CLIENTS = {
    "demo": {
        "password": "demo123",
        "company_name": "Beirut Hospitality Group (Live Demo)",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 25.0,
        "card_fee_pct": 2.0,
        "whish_fee_pct": 1.0,
        "packaging_cost_usd": 0.65,
        "waste_pct": 3.0,
        "monthly_rent_usd": 3500.0,
        "monthly_payroll_usd": 6200.0,
        "monthly_generator_utilities_usd": 1400.0,
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
        "monthly_rent_usd": 2800.0,
        "monthly_payroll_usd": 4500.0,
        "monthly_generator_utilities_usd": 1100.0,
    }
}

def get_client_db():
    try:
        if "clients" in st.secrets:
            return dict(st.secrets["clients"])
    except Exception:
        pass
    return DEFAULT_CLIENTS

# ==============================================================================
# ZERO-FRICTION URL AUTO-LOGIN (?demo=true) & SESSION STATE
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.client_profile = None

query_params = st.query_params
if not st.session_state.authenticated and query_params.get("demo", "").lower() in ["1", "true", "yes"]:
    clients = get_client_db()
    st.session_state.authenticated = True
    st.session_state.username = "demo"
    st.session_state.client_profile = clients["demo"]

def login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("## 📊 Executive POS, Menu Engineering & EBITDA Portal")
        st.caption(
            "Convert raw POS exports (Omega, Bim, Foodics, Square) into a 5-tab Executive Excel Dashboard "
            "with BCG Menu Engineering, Packaging/Waste Leakage, Cash Drawer Audits, and True EBITDA."
        )

        if st.button("🚀 Launch Instant Interactive Demo (No Password Needed)", type="primary", use_container_width=True):
            clients = get_client_db()
            st.session_state.authenticated = True
            st.session_state.username = "demo"
            st.session_state.client_profile = clients["demo"]
            st.rerun()

        st.markdown("<div style='text-align:center; color:#64748b; margin: 10px 0;'>— OR SIGN IN TO PRIVATE CLIENT PORTAL —</div>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Client Username", placeholder="e.g., demo").strip().lower()
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Sign In to Private Portal", use_container_width=True)

            if submit:
                clients = get_client_db()
                if username in clients and clients[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.client_profile = clients[username]
                    st.rerun()
                else:
                    st.error("Invalid username or password. Click the blue Instant Demo button above to preview.")

# ==============================================================================
# CRASH-PROOF EXCEL (.XLSX) & CSV READER
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
        return "Toters / Delivery Apps", delivery_fee, True
    if any(k in c for k in ["whish", "wish", "omt", "bob", "wallet"]):
        return "Whish / Mobile Wallet", whish_fee, False
    if any(k in c for k in ["card", "visa", "master", "amex", "pos", "bank", "carte", "credit", "debit"]):
        return "Bank Card POS", card_fee, False
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
        {"SKU": "SKU-105", "Item_Name": "Combo Meal Box (Delivery Promo)", "Category": "Promos", "Unit_Cost_USD": 8.90, "Menu_Price_USD": 13.00},
        {"SKU": "SKU-106", "Item_Name": "Specialty Iced Matcha Latte", "Category": "Beverages", "Unit_Cost_USD": 1.30, "Menu_Price_USD": 5.50},
    ]
    cogs_df = pd.DataFrame(cogs_data)
    sku_weights = [0.24, 0.22, 0.07, 0.19, 0.18, 0.10]

    branches = ["Ashrafieh Branch", "Mar Mikhael Branch", "Dbayeh Branch"]
    channels = ["In-Store Cash", "Whish Money", "Bank Card POS", "Toters Delivery", "Talabat / Deliveroo"]
    channel_weights = [0.30, 0.18, 0.15, 0.25, 0.12]

    random.seed(42)
    rows = []
    start_date = datetime(2026, 10, 1)

    for i in range(1, 381):
        sku_info = random.choices(cogs_data, weights=sku_weights)[0]
        qty = random.choices([1, 2, 3, 4], weights=[0.55, 0.30, 0.10, 0.05])[0]
        channel = random.choices(channels, weights=channel_weights)[0]
        branch = random.choice(branches)
        tx_date = start_date + timedelta(days=random.randint(0, 14))
        date_str = tx_date.strftime(random.choice(["%Y-%m-%d", "%d/%m/%Y"]))

        is_lbp = (channel == "In-Store Cash") and (random.random() < 0.35)
        gross_usd = sku_info["Menu_Price_USD"] * qty
        currency = "LBP" if is_lbp else "USD"
        raw_amount = round(gross_usd * lbp_rate, -3) if is_lbp else gross_usd

        rows.append({
            "Order_ID": f"ORD-{10000 + i}",
            "Date": date_str,
            "Branch": branch,
            "Channel": channel,
            "SKU": sku_info["SKU"],
            "Item_Sold": sku_info["Item_Name"],
            "Quantity": qty,
            "Currency": currency,
            "Gross_Amount_Raw": raw_amount
        })

    return pd.DataFrame(rows), cogs_df

# ==============================================================================
# CORE FINANCIAL, PACKAGING, WASTE & BCG MATRIX ENGINE
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
    fallback_cogs_pct: float
) -> pd.DataFrame:
    df = std_pos.copy()
    parsed_dates = pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce")
    df["Clean_Date"] = parsed_dates.dt.strftime("%Y-%m-%d").fillna(datetime.today().strftime("%Y-%m-%d"))
    df["Branch"] = df["Branch"].astype(str).str.strip()

    df["Quantity"] = clean_numeric_series(df["Quantity"], default_val=1.0)
    df.loc[df["Quantity"] <= 0, "Quantity"] = 1.0
    df["Gross_Amount_Raw"] = clean_numeric_series(df["Gross_Amount_Raw"], default_val=0.0)
    df = df[df["Gross_Amount_Raw"] > 0].copy()

    def calc_usd(row):
        curr = str(row["Currency"]).strip().upper()
        amt = float(row["Gross_Amount_Raw"])
        if "LBP" in curr or "LL" in curr or "L.L" in curr:
            return amt / lbp_rate
        if curr == "AUTO" and amt >= 10000:
            return amt / lbp_rate
        return amt

    df["Gross_Sales_USD"] = df.apply(calc_usd, axis=1)
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

    # Add Kitchen Waste / Spoilage Allowance
    df["Waste_Cost_USD"] = df["Raw_COGS_USD"] * waste_pct
    df["Total_COGS_USD"] = df["Raw_COGS_USD"] + df["Waste_Cost_USD"]

    # Classify Channel, Fee %, and Delivery Packaging Leakage
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
    """Builds the Boston Matrix (Popularity vs. Contribution Margin) for Menu Engineering."""
    sku_df = df.groupby(["SKU", "Item_Name", "Category"], as_index=False).agg(
        Units_Sold=("Quantity", "sum"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Packaging_USD=("Packaging_Cost_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Net_Profit_USD=("Net_Profit_USD", "sum")
    )
    sku_df["Unit_Contribution_USD"] = sku_df["Net_Profit_USD"] / sku_df["Units_Sold"]
    sku_df["Margin_Pct"] = (sku_df["Net_Profit_USD"] / sku_df["Gross_Sales_USD"]) * 100.0

    avg_units = sku_df["Units_Sold"].mean() if not sku_df.empty else 0
    avg_contrib = sku_df["Unit_Contribution_USD"].mean() if not sku_df.empty else 0

    def classify_bcg(row):
        high_vol = row["Units_Sold"] >= avg_units
        high_prof = row["Unit_Contribution_USD"] >= avg_contrib and row["Margin_Pct"] >= 25.0
        if high_vol and high_prof:
            return "⭐ STAR (High Vol / High Margin)"
        if high_vol and not high_prof:
            return "🐴 PLOWHORSE (High Vol / Low Margin - Reprice!)"
        if not high_vol and high_prof:
            return "🧩 PUZZLE (Low Vol / High Margin - Promote!)"
        return "💀 DOG / BLEEDER (Low Vol / Low Margin - Cut/Fix)"

    sku_df["BCG_Matrix_Class"] = sku_df.apply(classify_bcg, axis=1)
    return sku_df.sort_values("Net_Profit_USD", ascending=False)

# ==============================================================================
# 5-TAB EXECUTIVE EXCEL WORKBOOK BUILDER (WITH EBITDA & BCG MATRIX)
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
        title_fmt = wb.add_format({"bold": True, "font_size": 15, "font_color": "#0F172A"})
        subtitle_fmt = wb.add_format({"italic": True, "font_size": 10, "font_color": "#475569"})
        header_fmt = wb.add_format({"bold": True, "bg_color": "#1E293B", "font_color": "#FFFFFF", "border": 1, "align": "center"})
        kpi_label_fmt = wb.add_format({"bold": True, "bg_color": "#F1F5F9", "font_color": "#334155", "border": 1, "align": "center"})
        kpi_val_fmt = wb.add_format({"bold": True, "font_size": 12, "bg_color": "#FFFFFF", "font_color": "#0F172A", "num_format": "$#,##0.00", "border": 1, "align": "center"})
        kpi_pct_fmt = wb.add_format({"bold": True, "font_size": 12, "bg_color": "#FFFFFF", "font_color": "#16A34A", "num_format": "0.0%", "border": 1, "align": "center"})
        usd_fmt = wb.add_format({"num_format": "$#,##0.00", "border": 1})
        pct_fmt = wb.add_format({"num_format": "0.0%", "border": 1})
        int_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
        text_fmt = wb.add_format({"border": 1})
        alert_red_fmt = wb.add_format({"bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1})
        alert_green_fmt = wb.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True, "border": 1})
        alert_warn_fmt = wb.add_format({"bg_color": "#FEF3C7", "font_color": "#92400E", "bold": True, "border": 1})

        # TAB 1: EXECUTIVE SUMMARY
        ws_exec = wb.add_worksheet("01_Executive_Summary")
        ws_exec.hide_gridlines(2)
        ws_exec.write("B2", f"{company_name.upper()} — EXECUTIVE FINANCIAL & EBITDA DASHBOARD", title_fmt)
        ws_exec.write("B3", f"Normalized to Fresh USD (Rate: {lbp_rate:,.0f} LBP/USD | Active Days: {prorated_opex['days']})", subtitle_fmt)

        total_gross = df["Gross_Sales_USD"].sum()
        total_fees_pkg = df["Platform_Fee_USD"].sum() + df["Packaging_Cost_USD"].sum()
        total_cogs = df["Total_COGS_USD"].sum()
        contrib_profit = df["Net_Profit_USD"].sum()
        ebitda_val = contrib_profit - prorated_opex["total_opex"]
        ebitda_margin = ebitda_val / total_gross if total_gross else 0

        kpis = [
            ("GROSS REVENUE", total_gross, kpi_val_fmt),
            ("FEES + PACKAGING", total_fees_pkg, kpi_val_fmt),
            ("COGS + WASTE", total_cogs, kpi_val_fmt),
            ("PRORATED OPEX", prorated_opex["total_opex"], kpi_val_fmt),
            ("TRUE EBITDA", ebitda_val, kpi_val_fmt),
            ("EBITDA MARGIN", ebitda_margin, kpi_pct_fmt),
        ]
        for idx, (label, val, fmt) in enumerate(kpis):
            col = 1 + idx * 2
            ws_exec.merge_range(4, col, 4, col + 1, label, kpi_label_fmt)
            ws_exec.merge_range(5, col, 5, col + 1, val, fmt)

        start_row = 8
        ws_exec.write(start_row - 1, 1, "1. Channel Contribution Breakdown (Net of Fees, Packaging & Waste)", title_fmt)
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

        # TAB 2: BCG MENU ENGINEERING MATRIX
        ws_sku = wb.add_worksheet("02_BCG_Menu_Matrix")
        ws_sku.hide_gridlines(2)
        ws_sku.write("B2", "BOSTON MATRIX MENU ENGINEERING (POPULARITY VS. CONTRIBUTION)", title_fmt)
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
            ws_sku.write(r_idx, 10, row.Unit_Contribution_USD, usd_fmt)
            ws_sku.write(r_idx, 11, row.Margin_Pct / 100.0, pct_fmt)
            style = alert_green_fmt if "STAR" in row.BCG_Matrix_Class else (
                alert_red_fmt if "DOG" in row.BCG_Matrix_Class else alert_warn_fmt
            )
            ws_sku.write(r_idx, 12, row.BCG_Matrix_Class, style)
        ws_sku.set_column("B:M", 22)

        # TAB 3: DAILY PAYOUT RECONCILIATION
        daily_recon.to_excel(writer, sheet_name="03_Daily_Payout_Recon", index=False, startrow=3, startcol=1)
        ws_recon = writer.sheets["03_Daily_Payout_Recon"]
        ws_recon.hide_gridlines(2)
        ws_recon.write("B2", "DAILY EXPECTED NET PAYOUT RECONCILIATION (NET OF FEES)", title_fmt)
        for col_idx, col_name in enumerate(daily_recon.columns):
            ws_recon.write(3, 1 + col_idx, col_name.replace("_", " "), header_fmt)
        ws_recon.set_column("B:I", 22)

        # TAB 4: CLEAN MASTER LEDGER
        df.to_excel(writer, sheet_name="04_Clean_Master_Ledger", index=False)
        ws_raw = writer.sheets["04_Clean_Master_Ledger"]
        ws_raw.set_column("A:R", 18)

    return output.getvalue()

# ==============================================================================
# MAIN AUTHENTICATED PORTAL VIEW
# ==============================================================================
def main_portal():
    profile = st.session_state.client_profile
    company_name = profile["company_name"]

    with st.sidebar:
        st.markdown(f"### 🏢 {company_name}")
        role = st.selectbox(
            "👤 Active User Role (RBAC):",
            ["CFO / Owner (Full Access)", "Branch Manager (Cash Recon Only)"]
        )
        st.divider()

        st.markdown("#### 1️⃣ Commissions & Packaging")
        lbp_rate = st.number_input("LBP to 1 Fresh USD Rate", min_value=1000.0, max_value=500000.0, value=float(profile.get("default_lbp_rate", 89500.0)), step=500.0)
        delivery_fee = st.slider("Toters / Talabat Fee (%)", 0.0, 40.0, float(profile.get("delivery_fee_pct", 25.0)), 0.5) / 100.0
        packaging_cost_usd = st.number_input("Delivery Packaging / Order ($)", min_value=0.0, max_value=5.0, value=float(profile.get("packaging_cost_usd", 0.65)), step=0.05)
        card_fee = st.slider("Bank Card POS Fee (%)", 0.0, 10.0, float(profile.get("card_fee_pct", 2.0)), 0.1) / 100.0
        whish_fee = st.slider("Whish Money Fee (%)", 0.0, 10.0, float(profile.get("whish_fee_pct", 1.0)), 0.1) / 100.0

        st.markdown("#### 2️⃣ Waste & Monthly OPEX")
        waste_pct = st.slider("Kitchen Waste & Spoilage (%)", 0.0, 15.0, float(profile.get("waste_pct", 3.0)), 0.5) / 100.0
        fallback_cogs_pct = st.slider("Fallback COGS % (If No COGS File)", 5.0, 80.0, 32.0, 1.0) / 100.0
        monthly_rent = st.number_input("Monthly Rent (USD)", min_value=0.0, value=float(profile.get("monthly_rent_usd", 3500.0)), step=100.0)
        monthly_payroll = st.number_input("Monthly Staff Payroll (USD)", min_value=0.0, value=float(profile.get("monthly_payroll_usd", 6200.0)), step=100.0)
        monthly_utilities = st.number_input("Monthly Generator / EDL / WiFi (USD)", min_value=0.0, value=float(profile.get("monthly_generator_utilities_usd", 1400.0)), step=50.0)

        st.divider()
        wa_msg = urllib.parse.quote("Hi Ryan, I just tested your Executive POS & EBITDA Portal and want to run a free 7-day margin audit on our POS export.")
        st.link_button("📲 Request Custom POS Audit on WhatsApp", url=f"https://wa.me/{OWNER_WHATSAPP}?text={wa_msg}", use_container_width=True)
        if st.button("Log Out", use_container_width=True):
            st.query_params.clear()
            st.session_state.authenticated = False
            st.rerun()

    st.title(f"📊 {company_name} — Financial & Menu Engineering Engine")

    mode = st.radio(
        "Select Data Source:",
        ["Use Built-in Demo Dataset (Instant Preview)", "Upload Custom Excel / CSV Files (Smart Column Mapper)"],
        horizontal=True
    )

    std_pos, std_cogs = None, None

    if mode == "Upload Custom Excel / CSV Files (Smart Column Mapper)":
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            pos_file = st.file_uploader("1. Upload Raw POS Export (.xlsx, .xls, .csv) [Required]", type=["csv", "xlsx", "xls"])
        with u_col2:
            cogs_file = st.file_uploader("2. Upload SKU Master COGS (.xlsx, .xls, .csv) [Optional]", type=["csv", "xlsx", "xls"])

        if not pos_file:
            st.info("👆 Drop any Excel or CSV file from Omega POS, Bim, Foodics, or Square above to launch the **Smart Column Mapper**.")
            return

        raw_pos = safe_read_file(pos_file)
        pos_cols = list(raw_pos.columns)
        opt_pos_cols = ["(None / Auto-Fill)"] + pos_cols

        with st.expander("🛠️ Smart POS Column Mapper (Auto-Detected — Verify or Change Dropdowns)", expanded=True):
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                col_amount = st.selectbox("💰 Gross Sales / Total Price *", pos_cols, index=guess_column_index(pos_cols, ["gross", "amount", "total", "sales", "price", "montant", "ttc", "nettotal", "value"]))
                col_item = st.selectbox("🍔 Item / Product Name *", pos_cols, index=guess_column_index(pos_cols, ["item", "product", "article", "description", "menu", "designation", "name"]))
            with m2:
                col_qty = st.selectbox("🔢 Quantity Sold", opt_pos_cols, index=guess_column_index(pos_cols, ["qty", "quantity", "quantite", "qte", "count", "units"], allow_none=True))
                col_channel = st.selectbox("🛵 Payment / Delivery Channel", opt_pos_cols, index=guess_column_index(pos_cols, ["channel", "payment", "source", "type", "method", "mode", "aggregator"], allow_none=True))
            with m3:
                col_date = st.selectbox("📅 Order Date", opt_pos_cols, index=guess_column_index(pos_cols, ["date", "time", "day", "created", "business_date"], allow_none=True))
                col_branch = st.selectbox("🏢 Branch / Store Location", opt_pos_cols, index=guess_column_index(pos_cols, ["branch", "store", "location", "outlet", "shop", "point"], allow_none=True))
            with m4:
                col_sku = st.selectbox("🏷️ SKU / Item Code", opt_pos_cols, index=guess_column_index(pos_cols, ["sku", "code", "barcode", "ref", "item_id"], allow_none=True))
                col_curr = st.selectbox("💵 Currency (LBP/USD)", opt_pos_cols, index=guess_column_index(pos_cols, ["curr", "devise", "currency"], allow_none=True))
                col_inline_cost = st.selectbox("🧾 Unit Cost (If Inside POS File)", opt_pos_cols, index=guess_column_index(pos_cols, ["cout", "cost", "cogs", "achat"], allow_none=True))

        std_pos = pd.DataFrame()
        std_pos["Order_ID"] = [f"ORD-{10000 + i}" for i in range(len(raw_pos))]
        std_pos["Gross_Amount_Raw"] = raw_pos[col_amount]
        std_pos["Item_Name"] = raw_pos[col_item].astype(str).str.strip()
        std_pos["Quantity"] = raw_pos[col_qty] if col_qty != "(None / Auto-Fill)" else 1
        std_pos["Channel"] = raw_pos[col_channel] if col_channel != "(None / Auto-Fill)" else "In-Store Cash"
        std_pos["Date"] = raw_pos[col_date] if col_date != "(None / Auto-Fill)" else datetime.today().strftime("%Y-%m-%d")
        std_pos["Branch"] = raw_pos[col_branch].astype(str).str.strip() if col_branch != "(None / Auto-Fill)" else "Main Branch"
        std_pos["SKU"] = raw_pos[col_sku].astype(str).str.strip() if col_sku != "(None / Auto-Fill)" else std_pos["Item_Name"]
        std_pos["Currency"] = raw_pos[col_curr] if col_curr != "(None / Auto-Fill)" else "AUTO"

        if cogs_file:
            raw_cogs = safe_read_file(cogs_file)
            cogs_cols = list(raw_cogs.columns)
            opt_cogs_cols = ["(None / Auto-Fill)"] + cogs_cols
            with st.expander("🛠️ Smart COGS Column Mapper", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    cogs_cost_col = st.selectbox("💵 Unit Cost (USD) *", cogs_cols, index=guess_column_index(cogs_cols, ["cost", "cogs", "unit_cost", "achat", "cout"]))
                with c2:
                    cogs_item_col = st.selectbox("🍔 Item Name", opt_cogs_cols, index=guess_column_index(cogs_cols, ["item", "product", "article", "name", "designation"], allow_none=True))
                with c3:
                    cogs_sku_col = st.selectbox("🏷️ SKU / Code", opt_cogs_cols, index=guess_column_index(cogs_cols, ["sku", "code", "barcode", "ref"], allow_none=True))
                with c4:
                    cogs_cat_col = st.selectbox("📂 Category", opt_cogs_cols, index=guess_column_index(cogs_cols, ["cat", "group", "family", "famille"], allow_none=True))

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
    else:
        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate)
        std_pos = sample_pos.rename(columns={"Item_Sold": "Item_Name"})
        std_cogs = sample_cogs

    cleaned_df = process_standardized_data(
        std_pos, std_cogs, lbp_rate, delivery_fee, card_fee, whish_fee,
        packaging_cost_usd, waste_pct, fallback_cogs_pct
    )

    if cleaned_df.empty:
        st.error("No valid positive sales rows were found. Please check your Gross Sales column selection.")
        return

    # Calculate Active Period & Prorated OPEX for True EBITDA
    active_days = max(1, cleaned_df["Clean_Date"].nunique())
    monthly_total_opex = monthly_rent + monthly_payroll + monthly_utilities
    prorated_total_opex = (monthly_total_opex / 30.0) * active_days
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
    true_ebitda = contrib_profit - prorated_total_opex
    ebitda_margin_pct = (true_ebitda / total_gross * 100.0) if total_gross else 0.0

    sku_matrix = build_bcg_menu_matrix(cleaned_df)

    # Branch Manager Restricted View
    if role == "Branch Manager (Cash Recon Only)":
        st.info("🔒 **Branch Manager Mode Active:** COGS, Supplier Costs, and Executive EBITDA are hidden. Showing Shift Cash Drawer Reconciliation only.")
        branches_list = ["All Branches"] + sorted(cleaned_df["Branch"].unique().tolist())
        sel_branch = st.selectbox("Select Your Branch:", branches_list)
        b_df = cleaned_df if sel_branch == "All Branches" else cleaned_df[cleaned_df["Branch"] == sel_branch]
        expected_cash = b_df[b_df["Channel"] == "In-Store Cash"]["Gross_Sales_USD"].sum()
        expected_whish = b_df[b_df["Channel"] == "Whish / Mobile Wallet"]["Net_Revenue_USD"].sum()

        c1, c2 = st.columns(2)
        c1.metric("POS Expected In-Store Cash (USD Equiv.)", f"${expected_cash:,.2f}")
        c2.metric("Expected Whish Wallet Settlement", f"${expected_whish:,.2f}")

        st.subheader("💵 Physical Cash Drawer Count (End-of-Shift Audit)")
        col_u, col_l = st.columns(2)
        with col_u:
            counted_usd = st.number_input("Physical Fresh USD Bills Counted in Drawer ($)", min_value=0.0, value=float(round(expected_cash * 0.70, 2)), step=10.0)
        with col_l:
            counted_lbp = st.number_input("Physical LBP Bills Counted in Drawer (LBP)", min_value=0.0, value=float(round(expected_cash * 0.30 * lbp_rate, -3)), step=100000.0)

        total_counted_usd = counted_usd + (counted_lbp / lbp_rate)
        variance_usd = total_counted_usd - expected_cash
        if abs(variance_usd) < 1.0:
            st.success(f"✅ Drawer Balanced! Total Counted: ${total_counted_usd:,.2f} (Variance: ${variance_usd:+.2f})")
        elif variance_usd < 0:
            st.error(f"🚨 CASH SHORTAGE DETECTED: Drawer is SHORT by ${abs(variance_usd):,.2f} ({abs(variance_usd)*lbp_rate:,.0f} LBP)")
        else:
            st.warning(f"⚠️ CASH OVERAGE: Drawer is OVER by +${variance_usd:,.2f} (Check unrecorded POS tickets)")
        return

    # Full CFO / Owner View
    st.divider()
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Gross Sales", f"${total_gross:,.2f}")
    k2.metric("Fees & Packaging", f"-${total_fees_pkg:,.2f}")
    k3.metric("COGS + Waste", f"-${total_cogs_waste:,.2f}")
    k4.metric("Contribution Profit", f"${contrib_profit:,.2f}")
    k5.metric(f"Prorated OPEX ({active_days}d)", f"-${prorated_total_opex:,.2f}")
    k6.metric("True EBITDA (Net)", f"${true_ebitda:,.2f}", f"{ebitda_margin_pct:.1f}% margin")

    excel_bytes = build_excel_in_memory(cleaned_df, sku_matrix, company_name, lbp_rate, prorated_opex_dict)
    st.download_button(
        label="⬇️ Download Full Executive Excel Workbook (BCG Matrix + EBITDA + Recon) (.xlsx)",
        data=excel_bytes,
        file_name=f"{company_name.replace(' ', '_')}_Executive_EBITDA_Audit.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "⭐ BCG Menu Engineering Matrix",
        "📈 Channel & Branch Profitability",
        "🏢 OPEX, EBITDA & Working Capital Hold",
        "💵 Cash Drawer Shift Reconciliation"
    ])

    with tab1:
        st.subheader("Boston Matrix: Popularity (Volume) vs. Net Contribution (After Fees, Packaging & Waste)")
        plowhorses_dogs = sku_matrix[sku_matrix["BCG_Matrix_Class"].str.contains("PLOWHORSE|DOG")]
        if not plowhorses_dogs.empty:
            leaking_units = plowhorses_dogs["Units_Sold"].sum()
            monthly_recovery = leaking_units * 1.25 * (30.0 / active_days)
            st.warning(
                f"💡 **Menu Engineering Action Plan:** You have **{len(plowhorses_dogs)} SKU(s)** classified as **Plowhorses or Dogs** "
                f"({int(leaking_units)} units sold). Increasing their delivery menu price by **+$1.25** or swapping high-cost sides "
                f"adds **+${monthly_recovery:,.2f}/month** straight to your bottom-line EBITDA."
            )

        st.dataframe(
            sku_matrix.style.format({
                "Units_Sold": "{:,.0f}",
                "Gross_Sales_USD": "${:,.2f}",
                "Platform_Fees_USD": "${:,.2f}",
                "Packaging_USD": "${:,.2f}",
                "Total_COGS_USD": "${:,.2f}",
                "Net_Profit_USD": "${:,.2f}",
                "Unit_Contribution_USD": "${:,.2f}",
                "Margin_Pct": "{:.1f}%"
            }),
            use_container_width=True
        )

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Contribution by Channel (Inc. Packaging)")
            ch_df = cleaned_df.groupby("Channel", as_index=False)[["Gross_Sales_USD", "Platform_Fee_USD", "Packaging_Cost_USD", "Net_Profit_USD"]].sum()
            st.dataframe(ch_df.style.format({
                "Gross_Sales_USD": "${:,.2f}",
                "Platform_Fee_USD": "${:,.2f}",
                "Packaging_Cost_USD": "${:,.2f}",
                "Net_Profit_USD": "${:,.2f}"
            }), use_container_width=True)
        with c2:
            st.subheader("Contribution by Branch")
            br_df = cleaned_df.groupby("Branch", as_index=False)[["Gross_Sales_USD", "Total_COGS_USD", "Net_Profit_USD"]].sum()
            st.dataframe(br_df.style.format({
                "Gross_Sales_USD": "${:,.2f}",
                "Total_COGS_USD": "${:,.2f}",
                "Net_Profit_USD": "${:,.2f}"
            }), use_container_width=True)

    with tab3:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.subheader(f"📊 True EBITDA P&LWaterfall ({active_days} Active Days)")
            pnl_df = pd.DataFrame([
                {"Line Item": "1. Gross POS Revenue", "Amount (USD)": total_gross, "% of Sales": 100.0},
                {"Line Item": "2. (-) Delivery & POS Commissions", "Amount (USD)": -cleaned_df["Platform_Fee_USD"].sum(), "% of Sales": -cleaned_df["Platform_Fee_USD"].sum() / total_gross * 100},
                {"Line Item": "3. (-) Delivery Packaging & Disposables", "Amount (USD)": -cleaned_df["Packaging_Cost_USD"].sum(), "% of Sales": -cleaned_df["Packaging_Cost_USD"].sum() / total_gross * 100},
                {"Line Item": "4. (-) Raw Food / Inventory COGS", "Amount (USD)": -cleaned_df["Raw_COGS_USD"].sum(), "% of Sales": -cleaned_df["Raw_COGS_USD"].sum() / total_gross * 100},
                {"Line Item": "5. (-) Kitchen Waste & Spoilage Allowance", "Amount (USD)": -cleaned_df["Waste_Cost_USD"].sum(), "% of Sales": -cleaned_df["Waste_Cost_USD"].sum() / total_gross * 100},
                {"Line Item": "= GROSS CONTRIBUTION PROFIT", "Amount (USD)": contrib_profit, "% of Sales": contrib_profit / total_gross * 100},
                {"Line Item": "6. (-) Prorated Rent", "Amount (USD)": -prorated_opex_dict["rent"], "% of Sales": -prorated_opex_dict["rent"] / total_gross * 100},
                {"Line Item": "7. (-) Prorated Staff Payroll", "Amount (USD)": -prorated_opex_dict["payroll"], "% of Sales": -prorated_opex_dict["payroll"] / total_gross * 100},
                {"Line Item": "8. (-) Prorated Generator & Utilities", "Amount (USD)": -prorated_opex_dict["utilities"], "% of Sales": -prorated_opex_dict["utilities"] / total_gross * 100},
                {"Line Item": "= TRUE OPERATING EBITDA (NET CASH FLOW)", "Amount (USD)": true_ebitda, "% of Sales": ebitda_margin_pct},
            ])
            st.dataframe(pnl_df.style.format({"Amount (USD)": "${:,.2f}", "% of Sales": "{:.1f}%"}), use_container_width=True)

        with col_p2:
            st.subheader("⏳ Working Capital & Settlement Lag (Cash Timing)")
            instant_cash = cleaned_df[cleaned_df["Channel"].isin(["In-Store Cash", "Whish / Mobile Wallet"])]["Net_Revenue_USD"].sum()
            card_hold = cleaned_df[cleaned_df["Channel"] == "Bank Card POS"]["Net_Revenue_USD"].sum()
            aggregator_hold = cleaned_df[cleaned_df["Channel"] == "Toters / Delivery Apps"]["Net_Revenue_USD"].sum()

            wc_df = pd.DataFrame([
                {"Settlement Bucket": "🟢 Immediate Cash & Whish (Same Day)", "Net Receivable (USD)": instant_cash, "Typical Payout Lag": "0 Days (In Drawer / Wallet)"},
                {"Settlement Bucket": "🟡 Bank Card POS Terminal Hold", "Net Receivable (USD)": card_hold, "Typical Payout Lag": "2–3 Business Days"},
                {"Settlement Bucket": "🔴 Toters / Talabat / Aggregator Hold", "Net Receivable (USD)": aggregator_hold, "Typical Payout Lag": "7–14 Days (Weekly Statement)"},
            ])
            st.dataframe(wc_df.style.format({"Net Receivable (USD)": "${:,.2f}"}), use_container_width=True)
            st.info(
                f"📌 **Working Capital Alert:** **${aggregator_hold + card_hold:,.2f}** of your net revenue from this period is currently "
                f"tied up in aggregator and bank settlement holds. Ensure supplier payments are scheduled around your Toters/Talabat payout day."
            )

    with tab4:
        st.subheader("💵 End-of-Shift Cash Drawer Over/Short Audit")
        branches_list = ["All Branches"] + sorted(cleaned_df["Branch"].unique().tolist())
        sel_branch = st.selectbox("Filter Audit by Branch:", branches_list)
        b_df = cleaned_df if sel_branch == "All Branches" else cleaned_df[cleaned_df["Branch"] == sel_branch]
        expected_cash = b_df[b_df["Channel"] == "In-Store Cash"]["Gross_Sales_USD"].sum()

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            counted_usd = st.number_input("Physical USD Bills in Drawer ($)", min_value=0.0, value=float(round(expected_cash * 0.70, 2)), step=10.0)
        with col_c2:
            counted_lbp = st.number_input("Physical LBP Bills in Drawer (LBP)", min_value=0.0, value=float(round(expected_cash * 0.30 * lbp_rate, -3)), step=100000.0)
        with col_c3:
            total_counted = counted_usd + (counted_lbp / lbp_rate)
            variance = total_counted - expected_cash
            st.metric("Expected POS Cash (USD)", f"${expected_cash:,.2f}")
            st.metric("Actual Counted Cash (USD Equiv.)", f"${total_counted:,.2f}", f"{variance:+.2f} USD Variance")

if not st.session_state.authenticated:
    login_screen()
else:
    main_portal()
