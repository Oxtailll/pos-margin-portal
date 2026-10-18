import io
import re
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Executive POS & Margin Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# MULTI-TENANT CLIENT ACCOUNTS
# ==============================================================================
DEFAULT_CLIENTS = {
    "demo": {
        "password": "demo123",
        "company_name": "Beirut Hospitality Group (Demo)",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 25.0,
        "card_fee_pct": 2.0,
        "whish_fee_pct": 1.0,
    },
    "bistro_client": {
        "password": "bistro2026",
        "company_name": "Mar Mikhael Resto-Cafe",
        "default_lbp_rate": 89500.0,
        "delivery_fee_pct": 24.0,
        "card_fee_pct": 1.8,
        "whish_fee_pct": 1.0,
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
# AUTHENTICATION & SESSION STATE
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.client_profile = None

def login_screen():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("## 📊 SME Financial & POS Reconciliation Portal")
        st.caption("Convert messy POS exports (Omega, Bim, Foodics, Square), LBP/USD splits, and delivery commissions into an Executive Excel Dashboard in seconds.")

        with st.form("login_form"):
            username = st.text_input("Client Username", placeholder="e.g., demo").strip().lower()
            password = st.text_input("Password", type="password", placeholder="e.g., demo123")
            submit = st.form_submit_button("Sign In to Dashboard", type="primary", use_container_width=True)

            if submit:
                clients = get_client_db()
                if username in clients and clients[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.client_profile = clients[username]
                    st.rerun()
                else:
                    st.error("Invalid username or password. Try `demo` / `demo123`.")

        st.info("💡 **Prospect Demo Access:** Username: `demo` | Password: `demo123`")

# ==============================================================================
# CRASH-PROOF CSV READER & SMART COLUMN AUTO-DETECTOR
# ==============================================================================
def safe_read_csv(uploaded_file) -> pd.DataFrame:
    """Reads CSVs exported from English, French, or Arabic POS systems safely."""
    raw_bytes = uploaded_file.getvalue()
    for encoding in ["utf-8-sig", "cp1256", "latin1", "utf-16"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, sep=sep)
                if len(df.columns) > 1:
                    df = df.dropna(how="all")
                    return df
            except Exception:
                continue
    uploaded_file.seek(0)
    return pd.read_csv(uploaded_file)

def guess_column_index(columns: list, keywords: list, allow_none: bool = False) -> int:
    """Finds the best-matching column index based on POS header keywords."""
    options = ["(None / Auto-Fill)"] + list(columns) if allow_none else list(columns)
    offset = 1 if allow_none else 0

    for idx, col in enumerate(columns):
        clean_col = str(col).strip().lower()
        for kw in keywords:
            if kw in clean_col:
                return idx + offset
    return 0

def clean_numeric_series(series: pd.Series, default_val: float = 0.0) -> pd.Series:
    """Strips currency symbols ($, LBP, AED, spaces, commas) and converts to float safely."""
    def parse_val(val):
        if pd.isna(val):
            return default_val
        s = str(val).strip()
        if not s:
            return default_val
        # Handle accounting negative parentheses e.g. (12.50)
        is_neg = s.startswith("(") and s.endswith(")")
        # Keep only digits, dots, minus, and commas
        s = re.sub(r"[^0-9.,-]", "", s)
        if not s:
            return default_val
        # Handle European/French decimal comma (e.g. 12,50) vs thousands comma (1,250,000)
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
    """Maps any POS payment/order source name to standardized channel and fee."""
    c = str(raw_channel).strip().lower()
    if any(k in c for k in ["toter", "talabat", "deliveroo", "careem", "noon", "zomato", "jahez", "hunger", "aggregat", "delivery app"]):
        return "Toters / Delivery Apps", delivery_fee
    if any(k in c for k in ["whish", "wish", "omt", "bob", "wallet"]):
        return "Whish / Mobile Wallet", whish_fee
    if any(k in c for k in ["card", "visa", "master", "amex", "pos", "bank", "carte", "credit", "debit", "stripe", "tap"]):
        return "Bank Card POS", card_fee
    if not c or c in ["nan", "none"]:
        return "In-Store Cash", 0.0
    return str(raw_channel).strip(), 0.0

# ==============================================================================
# SAMPLE DATA GENERATOR (FOR PROSPECTS TESTING WITHOUT FILES)
# ==============================================================================
@st.cache_data
def generate_sample_datasets(lbp_rate: float):
    cogs_data = [
        {"SKU": "SKU-101", "Item_Name": "Signature Truffle Burger", "Category": "Mains", "Unit_Cost_USD": 4.20, "Menu_Price_USD": 12.50},
        {"SKU": "SKU-102", "Item_Name": "Crispy Chicken Sliders", "Category": "Mains", "Unit_Cost_USD": 3.50, "Menu_Price_USD": 10.00},
        {"SKU": "SKU-103", "Item_Name": "Artisanal Kale & Quinoa Salad", "Category": "Salads", "Unit_Cost_USD": 2.80, "Menu_Price_USD": 9.50},
        {"SKU": "SKU-104", "Item_Name": "Loaded Parmesan Fries", "Category": "Sides", "Unit_Cost_USD": 1.10, "Menu_Price_USD": 5.00},
        {"SKU": "SKU-105", "Item_Name": "Combo Meal Box (Promo)", "Category": "Promos", "Unit_Cost_USD": 8.90, "Menu_Price_USD": 13.00},
        {"SKU": "SKU-106", "Item_Name": "Specialty Iced Matcha Latte", "Category": "Beverages", "Unit_Cost_USD": 1.40, "Menu_Price_USD": 5.50},
    ]
    cogs_df = pd.DataFrame(cogs_data)

    branches = ["Ashrafieh Branch", "Mar Mikhael Branch", "Dbayeh Branch"]
    channels = ["In-Store Cash", "Whish Money", "Bank Card POS", "Toters Delivery", "Talabat / Deliveroo"]
    channel_weights = [0.30, 0.20, 0.15, 0.25, 0.10]

    random.seed(42)
    rows = []
    start_date = datetime(2026, 10, 1)

    for i in range(1, 351):
        sku_info = random.choice(cogs_data)
        qty = random.choices([1, 2, 3, 4], weights=[0.55, 0.30, 0.10, 0.05])[0]
        channel = random.choices(channels, weights=channel_weights)[0]
        branch = random.choice(branches)
        tx_date = start_date + timedelta(days=random.randint(0, 14))
        date_str = tx_date.strftime(random.choice(["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]))

        is_lbp = (channel == "In-Store Cash") and (random.random() < 0.35)
        gross_usd = sku_info["Menu_Price_USD"] * qty
        currency = "LBP" if is_lbp else "USD"
        raw_amount = round(gross_usd * lbp_rate, -3) if is_lbp else gross_usd

        rows.append({
            "Order_ID": f"ORD-{10000 + i}",
            "Date": date_str,
            "Branch": f"  {branch} ",
            "Channel": channel,
            "SKU": sku_info["SKU"],
            "Item_Sold": sku_info["Item_Name"],
            "Quantity": qty,
            "Currency": currency,
            "Gross_Amount_Raw": raw_amount
        })

    pos_df = pd.DataFrame(rows)
    return pos_df, cogs_df

# ==============================================================================
# CORE DATA PROCESSING & IN-MEMORY EXCEL BUILDER
# ==============================================================================
def process_standardized_data(
    std_pos: pd.DataFrame,
    std_cogs: pd.DataFrame | None,
    lbp_rate: float,
    delivery_fee: float,
    card_fee: float,
    whish_fee: float,
    fallback_cogs_pct: float
) -> pd.DataFrame:
    df = std_pos.copy()

    # Clean dates safely
    parsed_dates = pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce")
    df["Clean_Date"] = parsed_dates.dt.strftime("%Y-%m-%d").fillna(datetime.today().strftime("%Y-%m-%d"))

    # Clean numeric Quantity and Gross Amount
    df["Quantity"] = clean_numeric_series(df["Quantity"], default_val=1.0)
    df.loc[df["Quantity"] <= 0, "Quantity"] = 1.0
    df["Gross_Amount_Raw"] = clean_numeric_series(df["Gross_Amount_Raw"], default_val=0.0)

    # Filter out zero-dollar summary/empty rows
    df = df[df["Gross_Amount_Raw"] > 0].copy()

    # Normalize LBP vs USD (supports explicit Currency column OR automatic threshold detection)
    def calc_usd(row):
        curr = str(row["Currency"]).strip().upper()
        amt = float(row["Gross_Amount_Raw"])
        if "LBP" in curr or "LL" in curr or "L.L" in curr:
            return amt / lbp_rate
        if curr == "AUTO" and amt >= 10000:
            return amt / lbp_rate
        return amt

    df["Gross_Sales_USD"] = df.apply(calc_usd, axis=1)

    # Match COGS either by SKU or by Item Name, with fallback percentage
    df["Unit_Cost_USD"] = None
    df["Category"] = "General"

    if std_cogs is not None and not std_cogs.empty:
        cogs_clean = std_cogs.copy()
        cogs_clean["Unit_Cost_USD"] = clean_numeric_series(cogs_clean["Unit_Cost_USD"], default_val=0.0)

        # 1. Try matching by SKU if available
        if "SKU" in cogs_clean.columns and (df["SKU"] != "N/A").any():
            sku_map = cogs_clean.drop_duplicates(subset=["SKU"]).set_index("SKU")
            df["Unit_Cost_USD"] = df["SKU"].map(sku_map["Unit_Cost_USD"])
            if "Category" in sku_map.columns:
                df["Category"] = df["SKU"].map(sku_map["Category"]).fillna("General")

        # 2. Match remaining items by lowercase Item Name
        if "Item_Name" in cogs_clean.columns:
            cogs_clean["_item_key"] = cogs_clean["Item_Name"].astype(str).str.strip().str.lower()
            name_map = cogs_clean.drop_duplicates(subset=["_item_key"]).set_index("_item_key")
            df["_item_key"] = df["Item_Name"].astype(str).str.strip().str.lower()

            missing_cost = df["Unit_Cost_USD"].isna()
            df.loc[missing_cost, "Unit_Cost_USD"] = df.loc[missing_cost, "_item_key"].map(name_map["Unit_Cost_USD"])
            if "Category" in name_map.columns:
                df.loc[df["Category"] == "General", "Category"] = df.loc[df["Category"] == "General", "_item_key"].map(name_map["Category"]).fillna("General")
            df.drop(columns=["_item_key"], inplace=True, errors="ignore")

    # Calculate Total COGS (use fallback COGS % for any unmatched items)
    df["Total_COGS_USD"] = df["Quantity"] * df["Unit_Cost_USD"]
    unmatched = df["Total_COGS_USD"].isna() | (df["Total_COGS_USD"] <= 0)
    df.loc[unmatched, "Total_COGS_USD"] = df.loc[unmatched, "Gross_Sales_USD"] * fallback_cogs_pct
    df.loc[unmatched, "Unit_Cost_USD"] = df.loc[unmatched, "Total_COGS_USD"] / df.loc[unmatched, "Quantity"]

    # Classify Channel & Platform Fee
    ch_results = df["Channel"].apply(lambda c: classify_channel_and_fee(c, delivery_fee, card_fee, whish_fee))
    df["Channel"] = [r[0] for r in ch_results]
    df["Fee_Pct"] = [r[1] for r in ch_results]

    df["Platform_Fee_USD"] = df["Gross_Sales_USD"] * df["Fee_Pct"]
    df["Net_Revenue_USD"] = df["Gross_Sales_USD"] - df["Platform_Fee_USD"]
    df["Net_Profit_USD"] = df["Net_Revenue_USD"] - df["Total_COGS_USD"]
    df["Net_Margin_Pct"] = df["Net_Profit_USD"] / df["Gross_Sales_USD"]

    return df

def build_excel_in_memory(df: pd.DataFrame, company_name: str, lbp_rate: float) -> bytes:
    channel_summary = df.groupby("Channel", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Units_Sold=("Quantity", "sum"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Net_Revenue_USD=("Net_Revenue_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Net_Profit_USD=("Net_Profit_USD", "sum")
    )
    channel_summary["Net_Margin_Pct"] = channel_summary["Net_Profit_USD"] / channel_summary["Gross_Sales_USD"]
    channel_summary = channel_summary.sort_values(by="Net_Profit_USD", ascending=False)

    branch_summary = df.groupby("Branch", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Net_Profit_USD=("Net_Profit_USD", "sum")
    )
    branch_summary["Net_Margin_Pct"] = branch_summary["Net_Profit_USD"] / branch_summary["Gross_Sales_USD"]

    sku_summary = df.groupby(["SKU", "Item_Name", "Category"], as_index=False).agg(
        Units_Sold=("Quantity", "sum"),
        Gross_Sales_USD=("Gross_Sales_USD", "sum"),
        Platform_Fees_USD=("Platform_Fee_USD", "sum"),
        Total_COGS_USD=("Total_COGS_USD", "sum"),
        Net_Profit_USD=("Net_Profit_USD", "sum")
    )
    sku_summary["Realized_Margin_Pct"] = sku_summary["Net_Profit_USD"] / sku_summary["Gross_Sales_USD"]
    sku_summary["Status"] = sku_summary["Realized_Margin_Pct"].apply(
        lambda m: "HIGH MARGIN STAR" if m >= 0.50 else ("MARGIN BLEEDER (REPRICE)" if m < 0.25 else "HEALTHY")
    )
    sku_summary = sku_summary.sort_values(by="Net_Profit_USD", ascending=False)

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
        kpi_val_fmt = wb.add_format({"bold": True, "font_size": 13, "bg_color": "#FFFFFF", "font_color": "#0F172A", "num_format": "$#,##0.00", "border": 1, "align": "center"})
        kpi_pct_fmt = wb.add_format({"bold": True, "font_size": 13, "bg_color": "#FFFFFF", "font_color": "#16A34A", "num_format": "0.0%", "border": 1, "align": "center"})
        usd_fmt = wb.add_format({"num_format": "$#,##0.00", "border": 1})
        pct_fmt = wb.add_format({"num_format": "0.0%", "border": 1})
        int_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
        text_fmt = wb.add_format({"border": 1})
        alert_red_fmt = wb.add_format({"bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1})
        alert_green_fmt = wb.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True, "border": 1})

        # TAB 1: EXECUTIVE SUMMARY
        ws_exec = wb.add_worksheet("01_Executive_Summary")
        ws_exec.hide_gridlines(2)
        ws_exec.write("B2", f"{company_name.upper()} — EXECUTIVE FINANCIAL DASHBOARD", title_fmt)
        ws_exec.write("B3", f"Normalized to Fresh USD (Exchange Rate: {lbp_rate:,.0f} LBP/USD)", subtitle_fmt)

        total_gross = df["Gross_Sales_USD"].sum()
        total_fees = df["Platform_Fee_USD"].sum()
        total_cogs = df["Total_COGS_USD"].sum()
        total_net_profit = df["Net_Profit_USD"].sum()
        blended_margin = total_net_profit / total_gross if total_gross else 0

        kpis = [
            ("GROSS REVENUE (USD)", total_gross, kpi_val_fmt),
            ("DELIVERY & POS FEES", total_fees, kpi_val_fmt),
            ("TOTAL COGS", total_cogs, kpi_val_fmt),
            ("TRUE NET PROFIT", total_net_profit, kpi_val_fmt),
            ("NET PROFIT MARGIN", blended_margin, kpi_pct_fmt),
        ]
        for idx, (label, val, fmt) in enumerate(kpis):
            col = 1 + idx * 2
            ws_exec.merge_range(4, col, 4, col + 1, label, kpi_label_fmt)
            ws_exec.merge_range(5, col, 5, col + 1, val, fmt)

        start_row = 8
        ws_exec.write(start_row - 1, 1, "1. Profitability by Payment / Delivery Channel", title_fmt)
        for col_idx, col_name in enumerate(channel_summary.columns):
            ws_exec.write(start_row, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(channel_summary.itertuples(index=False), start=start_row + 1):
            ws_exec.write(r_idx, 1, row.Channel, text_fmt)
            ws_exec.write(r_idx, 2, row.Orders, int_fmt)
            ws_exec.write(r_idx, 3, row.Units_Sold, int_fmt)
            ws_exec.write(r_idx, 4, row.Gross_Sales_USD, usd_fmt)
            ws_exec.write(r_idx, 5, row.Platform_Fees_USD, usd_fmt)
            ws_exec.write(r_idx, 6, row.Net_Revenue_USD, usd_fmt)
            ws_exec.write(r_idx, 7, row.Total_COGS_USD, usd_fmt)
            ws_exec.write(r_idx, 8, row.Net_Profit_USD, usd_fmt)
            ws_exec.write(r_idx, 9, row.Net_Margin_Pct, pct_fmt)

        b_row = start_row + len(channel_summary) + 3
        ws_exec.write(b_row - 1, 1, "2. Branch Performance Breakdown", title_fmt)
        for col_idx, col_name in enumerate(branch_summary.columns):
            ws_exec.write(b_row, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(branch_summary.itertuples(index=False), start=b_row + 1):
            ws_exec.write(r_idx, 1, row.Branch, text_fmt)
            ws_exec.write(r_idx, 2, row.Orders, int_fmt)
            ws_exec.write(r_idx, 3, row.Gross_Sales_USD, usd_fmt)
            ws_exec.write(r_idx, 4, row.Platform_Fees_USD, usd_fmt)
            ws_exec.write(r_idx, 5, row.Total_COGS_USD, usd_fmt)
            ws_exec.write(r_idx, 6, row.Net_Profit_USD, usd_fmt)
            ws_exec.write(r_idx, 7, row.Net_Margin_Pct, pct_fmt)

        chart = wb.add_chart({"type": "column"})
        num_channels = len(channel_summary)
        chart.add_series({
            "name": "Gross Sales (USD)",
            "categories": ["01_Executive_Summary", start_row + 1, 1, start_row + num_channels, 1],
            "values": ["01_Executive_Summary", start_row + 1, 4, start_row + num_channels, 4],
            "fill": {"color": "#3B82F6"}
        })
        chart.add_series({
            "name": "True Net Profit (USD)",
            "categories": ["01_Executive_Summary", start_row + 1, 1, start_row + num_channels, 1],
            "values": ["01_Executive_Summary", start_row + 1, 8, start_row + num_channels, 8],
            "fill": {"color": "#10B981"}
        })
        chart.set_title({"name": "Gross Sales vs. True Net Profit by Channel"})
        chart.set_size({"width": 680, "height": 340})
        ws_exec.insert_chart(b_row + len(branch_summary) + 3, 1, chart)
        ws_exec.set_column("B:J", 20)

        # TAB 2: SKU PROFITABILITY
        ws_sku = wb.add_worksheet("02_SKU_Profitability")
        ws_sku.hide_gridlines(2)
        ws_sku.write("B2", "PRODUCT / MENU ENGINEERING & MARGIN BLEED AUDIT", title_fmt)
        for col_idx, col_name in enumerate(sku_summary.columns):
            ws_sku.write(4, 1 + col_idx, col_name.replace("_", " "), header_fmt)

        for r_idx, row in enumerate(sku_summary.itertuples(index=False), start=5):
            ws_sku.write(r_idx, 1, row.SKU, text_fmt)
            ws_sku.write(r_idx, 2, row.Item_Name, text_fmt)
            ws_sku.write(r_idx, 3, row.Category, text_fmt)
            ws_sku.write(r_idx, 4, row.Units_Sold, int_fmt)
            ws_sku.write(r_idx, 5, row.Gross_Sales_USD, usd_fmt)
            ws_sku.write(r_idx, 6, row.Platform_Fees_USD, usd_fmt)
            ws_sku.write(r_idx, 7, row.Total_COGS_USD, usd_fmt)
            ws_sku.write(r_idx, 8, row.Net_Profit_USD, usd_fmt)
            ws_sku.write(r_idx, 9, row.Realized_Margin_Pct, pct_fmt)
            status_style = alert_red_fmt if "BLEEDER" in row.Status else (alert_green_fmt if "STAR" in row.Status else text_fmt)
            ws_sku.write(r_idx, 10, row.Status, status_style)
        ws_sku.set_column("B:K", 22)

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
        ws_raw.set_column("A:O", 18)

    return output.getvalue()

# ==============================================================================
# MAIN AUTHENTICATED DASHBOARD VIEW
# ==============================================================================
def main_portal():
    profile = st.session_state.client_profile
    company_name = profile["company_name"]

    with st.sidebar:
        st.markdown(f"### 🏢 {company_name}")
        st.caption(f"Logged in as: `{st.session_state.username}`")
        st.divider()

        st.markdown("#### ⚙️ Financial Assumptions")
        lbp_rate = st.number_input(
            "LBP to 1 Fresh USD Rate",
            min_value=1000.0,
            max_value=500000.0,
            value=float(profile["default_lbp_rate"]),
            step=500.0
        )
        delivery_fee = st.slider(
            "Toters / Talabat Commission (%)",
            min_value=0.0, max_value=40.0,
            value=float(profile["delivery_fee_pct"]), step=0.5
        ) / 100.0
        card_fee = st.slider(
            "Bank Card POS Fee (%)",
            min_value=0.0, max_value=10.0,
            value=float(profile["card_fee_pct"]), step=0.1
        ) / 100.0
        whish_fee = st.slider(
            "Whish Money Fee (%)",
            min_value=0.0, max_value=10.0,
            value=float(profile["whish_fee_pct"]), step=0.1
        ) / 100.0
        fallback_cogs_pct = st.slider(
            "Default COGS % (If No COGS Sheet)",
            min_value=5.0, max_value=80.0,
            value=32.0, step=1.0,
            help="Used automatically if you only upload a POS sales file without a COGS sheet."
        ) / 100.0

        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    st.title(f"📊 {company_name} — Executive Financial Engine")
    st.write("Upload any raw POS export (Omega, Bim, Foodics, Square) below, or toggle **Demo Mode** to test with sample multi-branch data.")

    mode = st.radio(
        "Select Data Source:",
        ["Use Built-in Demo Dataset (Instant Preview)", "Upload Custom CSV Files (Smart Column Mapper)"],
        horizontal=True
    )

    std_pos, std_cogs = None, None

    if mode == "Upload Custom CSV Files (Smart Column Mapper)":
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            pos_file = st.file_uploader("1. Upload Raw POS Export (.csv) [Required]", type=["csv"])
        with u_col2:
            cogs_file = st.file_uploader("2. Upload SKU Master COGS (.csv) [Optional]", type=["csv"])

        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate)
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.download_button(
                "📥 Download Sample POS CSV",
                data=sample_pos.to_csv(index=False).encode("utf-8"),
                file_name="template_pos_export.csv",
                mime="text/csv"
            )
        with t_col2:
            st.download_button(
                "📥 Download Sample COGS CSV",
                data=sample_cogs.to_csv(index=False).encode("utf-8"),
                file_name="template_sku_cogs.csv",
                mime="text/csv"
            )

        if not pos_file:
            st.info("👆 Upload any POS CSV file above to open the **Smart Column Mapper** (works with Omega POS, Bim, Foodics, Toters, or custom spreadsheets).")
            return

        raw_pos = safe_read_csv(pos_file)
        pos_cols = list(raw_pos.columns)
        opt_pos_cols = ["(None / Auto-Fill)"] + pos_cols

        with st.expander("🛠️ Smart POS Column Mapper (Auto-Detected — Verify or Change Dropdowns)", expanded=True):
            st.caption("Match your POS file's column headers below. Optional columns can be left on `(None / Auto-Fill)`.")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                col_amount = st.selectbox(
                    "💰 Gross Sales / Total Price *",
                    pos_cols,
                    index=guess_column_index(pos_cols, ["gross", "amount", "total", "sales", "price", "montant", "ttc", "nettotal", "value"])
                )
                col_item = st.selectbox(
                    "🍔 Item / Product Name *",
                    pos_cols,
                    index=guess_column_index(pos_cols, ["item", "product", "article", "description", "menu", "designation", "name"])
                )
            with m2:
                col_qty = st.selectbox(
                    "🔢 Quantity Sold",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["qty", "quantity", "quantite", "qte", "count", "units"], allow_none=True)
                )
                col_channel = st.selectbox(
                    "🛵 Payment / Delivery Channel",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["channel", "payment", "source", "type", "method", "mode", "aggregator"], allow_none=True)
                )
            with m3:
                col_date = st.selectbox(
                    "📅 Order Date",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["date", "time", "day", "created", "business_date"], allow_none=True)
                )
                col_branch = st.selectbox(
                    "🏢 Branch / Store Location",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["branch", "store", "location", "outlet", "shop", "point"], allow_none=True)
                )
            with m4:
                col_sku = st.selectbox(
                    "🏷️ SKU / Item Code",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["sku", "code", "barcode", "ref", "item_id"], allow_none=True)
                )
                col_curr = st.selectbox(
                    "💵 Currency (LBP/USD)",
                    opt_pos_cols,
                    index=guess_column_index(pos_cols, ["curr", "devise", "currency"], allow_none=True)
                )

        # Build Standardized POS DataFrame
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

        # Optional COGS File Mapper
        if cogs_file:
            raw_cogs = safe_read_csv(cogs_file)
            cogs_cols = list(raw_cogs.columns)
            opt_cogs_cols = ["(None / Auto-Fill)"] + cogs_cols

            with st.expander("🛠️ Smart COGS Column Mapper", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    cogs_cost_col = st.selectbox(
                        "💵 Unit Cost (USD) *",
                        cogs_cols,
                        index=guess_column_index(cogs_cols, ["cost", "cogs", "unit_cost", "achat", "cout"])
                    )
                with c2:
                    cogs_item_col = st.selectbox(
                        "🍔 Item / Product Name",
                        opt_cogs_cols,
                        index=guess_column_index(cogs_cols, ["item", "product", "article", "name", "description"], allow_none=True)
                    )
                with c3:
                    cogs_sku_col = st.selectbox(
                        "🏷️ SKU / Item Code",
                        opt_cogs_cols,
                        index=guess_column_index(cogs_cols, ["sku", "code", "barcode", "ref"], allow_none=True)
                    )
                with c4:
                    cogs_cat_col = st.selectbox(
                        "📂 Category",
                        opt_cogs_cols,
                        index=guess_column_index(cogs_cols, ["cat", "group", "family", "department", "famille"], allow_none=True)
                    )

            std_cogs = pd.DataFrame()
            std_cogs["Unit_Cost_USD"] = raw_cogs[cogs_cost_col]
            std_cogs["Item_Name"] = raw_cogs[cogs_item_col].astype(str).str.strip() if cogs_item_col != "(None / Auto-Fill)" else "N/A"
            std_cogs["SKU"] = raw_cogs[cogs_sku_col].astype(str).str.strip() if cogs_sku_col != "(None / Auto-Fill)" else std_cogs["Item_Name"]
            std_cogs["Category"] = raw_cogs[cogs_cat_col].astype(str).str.strip() if cogs_cat_col != "(None / Auto-Fill)" else "General"
    else:
        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate)
        std_pos = sample_pos.rename(columns={"Item_Sold": "Item_Name"})
        std_cogs = sample_cogs

    # Process Standardized Data
    cleaned_df = process_standardized_data(
        std_pos, std_cogs, lbp_rate, delivery_fee, card_fee, whish_fee, fallback_cogs_pct
    )

    if cleaned_df.empty:
        st.error("No valid positive sales rows were found using the selected Gross Sales column. Please pick the numeric price/total column in the Smart POS Column Mapper above.")
        return

    total_gross = cleaned_df["Gross_Sales_USD"].sum()
    total_fees = cleaned_df["Platform_Fee_USD"].sum()
    total_cogs = cleaned_df["Total_COGS_USD"].sum()
    total_net = cleaned_df["Net_Profit_USD"].sum()
    margin_pct = (total_net / total_gross * 100) if total_gross else 0.0

    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Gross Revenue (USD)", f"${total_gross:,.2f}")
    k2.metric("Delivery & POS Fees", f"-${total_fees:,.2f}")
    k3.metric("Total COGS", f"-${total_cogs:,.2f}")
    k4.metric("True Net Profit", f"${total_net:,.2f}")
    k5.metric("Realized Net Margin", f"{margin_pct:.1f}%")

    excel_bytes = build_excel_in_memory(cleaned_df, company_name, lbp_rate)
    st.download_button(
        label="⬇️ Download Full 4-Tab Executive Excel Dashboard (.xlsx)",
        data=excel_bytes,
        file_name=f"{company_name.replace(' ', '_')}_Executive_Dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

    tab1, tab2, tab3 = st.tabs(["📈 Channel & Branch Profitability", "🚨 Margin Bleeder SKU Audit", "🧾 Cleaned Ledger Preview"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Net Profit by Payment / Delivery Channel")
            ch_df = cleaned_df.groupby("Channel", as_index=False)[["Gross_Sales_USD", "Platform_Fee_USD", "Net_Profit_USD"]].sum()
            st.dataframe(ch_df.style.format({"Gross_Sales_USD": "${:,.2f}", "Platform_Fee_USD": "${:,.2f}", "Net_Profit_USD": "${:,.2f}"}), use_container_width=True)
        with c2:
            st.subheader("Net Profit by Branch")
            br_df = cleaned_df.groupby("Branch", as_index=False)[["Gross_Sales_USD", "Total_COGS_USD", "Net_Profit_USD"]].sum()
            st.dataframe(br_df.style.format({"Gross_Sales_USD": "${:,.2f}", "Total_COGS_USD": "${:,.2f}", "Net_Profit_USD": "${:,.2f}"}), use_container_width=True)

    with tab2:
        st.subheader("Menu / SKU Engineering Breakdown")
        sku_df = cleaned_df.groupby(["SKU", "Item_Name", "Category"], as_index=False).agg(
            Units_Sold=("Quantity", "sum"),
            Gross_Sales_USD=("Gross_Sales_USD", "sum"),
            Platform_Fees_USD=("Platform_Fee_USD", "sum"),
            Total_COGS_USD=("Total_COGS_USD", "sum"),
            Net_Profit_USD=("Net_Profit_USD", "sum")
        )
        sku_df["Margin_Pct"] = sku_df["Net_Profit_USD"] / sku_df["Gross_Sales_USD"] * 100
        sku_df["Audit_Status"] = sku_df["Margin_Pct"].apply(
            lambda m: "🟢 STAR (50%+)" if m >= 50 else ("🔴 BLEEDER (Under 25%)" if m < 25 else "🟡 HEALTHY")
        )
        st.dataframe(
            sku_df.sort_values("Margin_Pct").style.format({
                "Gross_Sales_USD": "${:,.2f}",
                "Platform_Fees_USD": "${:,.2f}",
                "Total_COGS_USD": "${:,.2f}",
                "Net_Profit_USD": "${:,.2f}",
                "Margin_Pct": "{:.1f}%"
            }),
            use_container_width=True
        )

    with tab3:
        st.subheader("Normalized Transaction Ledger (First 100 Rows)")
        st.dataframe(cleaned_df.head(100), use_container_width=True)

if not st.session_state.authenticated:
    login_screen()
else:
    main_portal()
