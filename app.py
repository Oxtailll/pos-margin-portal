import io
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
    if "clients" in {}:
        return dict({}["clients"])
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
        st.caption("Convert messy POS exports, LBP/USD splits, and delivery commissions into an Executive Excel Dashboard in seconds.")

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
def process_financial_data(pos_df: pd.DataFrame, cogs_df: pd.DataFrame, lbp_rate: float, channel_fees: dict):
    df = pos_df.copy()
    df["Branch"] = df["Branch"].astype(str).str.strip()
    df["Channel"] = df["Channel"].astype(str).str.strip()
    df["Currency"] = df["Currency"].astype(str).str.strip().str.upper()

    df["Clean_Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True).dt.strftime("%Y-%m-%d")

    df["Gross_Sales_USD"] = df.apply(
        lambda r: r["Gross_Amount_Raw"] / lbp_rate if r["Currency"] == "LBP" else r["Gross_Amount_Raw"],
        axis=1
    )

    merged = pd.merge(df, cogs_df[["SKU", "Item_Name", "Category", "Unit_Cost_USD"]], on="SKU", how="left")
    merged["Unit_Cost_USD"] = merged["Unit_Cost_USD"].fillna(0.0)
    merged["Item_Name"] = merged["Item_Name"].fillna(merged.get("Item_Sold", "Unknown SKU"))
    merged["Category"] = merged["Category"].fillna("Uncategorized")

    merged["Fee_Pct"] = merged["Channel"].map(channel_fees).fillna(0.0)
    merged["Platform_Fee_USD"] = merged["Gross_Sales_USD"] * merged["Fee_Pct"]
    merged["Net_Revenue_USD"] = merged["Gross_Sales_USD"] - merged["Platform_Fee_USD"]
    merged["Total_COGS_USD"] = merged["Quantity"] * merged["Unit_Cost_USD"]
    merged["Net_Profit_USD"] = merged["Net_Revenue_USD"] - merged["Total_COGS_USD"]
    merged["Net_Margin_Pct"] = merged["Net_Profit_USD"] / merged["Gross_Sales_USD"]

    return merged

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

        channel_fees = {
            "In-Store Cash": 0.00,
            "Whish Money": whish_fee,
            "Bank Card POS": card_fee,
            "Toters Delivery": delivery_fee,
            "Talabat / Deliveroo": delivery_fee,
        }

        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    st.title(f"📊 {company_name} — Executive Financial Engine")
    st.write("Upload your raw POS export and SKU COGS sheet below, or toggle **Demo Mode** to test with sample multi-branch data.")

    mode = st.radio(
        "Select Data Source:",
        ["Use Built-in Demo Dataset (Instant Preview)", "Upload Custom CSV Files"],
        horizontal=True
    )

    pos_df, cogs_df = None, None

    if mode == "Upload Custom CSV Files":
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            pos_file = st.file_uploader("1. Upload Raw POS Export (.csv)", type=["csv"])
        with u_col2:
            cogs_file = st.file_uploader("2. Upload SKU Master COGS (.csv)", type=["csv"])

        sample_pos, sample_cogs = generate_sample_datasets(lbp_rate)
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.download_button(
                "📥 Download Sample POS CSV Template",
                data=sample_pos.to_csv(index=False).encode("utf-8"),
                file_name="template_pos_export.csv",
                mime="text/csv"
            )
        with t_col2:
            st.download_button(
                "📥 Download Sample COGS CSV Template",
                data=sample_cogs.to_csv(index=False).encode("utf-8"),
                file_name="template_sku_cogs.csv",
                mime="text/csv"
            )

        if pos_file and cogs_file:
            pos_df = pd.read_csv(pos_file)
            cogs_df = pd.read_csv(cogs_file)
        else:
            st.warning("Please upload both your Raw POS CSV and Master COGS CSV above (or switch to Demo Mode).")
            return
    else:
        pos_df, cogs_df = generate_sample_datasets(lbp_rate)

    cleaned_df = process_financial_data(pos_df, cogs_df, lbp_rate, channel_fees)

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