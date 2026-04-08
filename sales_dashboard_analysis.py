"""
Detailed Sales Dashboard — Item-wise, HSN-wise & GST-wise Analysis
====================================================================
Supports the native Tally export format (14 columns) as well as the
legacy item-level column layout — auto-detected on upload.

Run:  streamlit run sales_dashboard_analysis.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales & GST Analysis Dashboard",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Professional CSS ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a3a5c 0%, #16547a 100%);
        border: 1px solid #2b6cb0;
        border-radius: 12px;
        padding: 16px 20px;
        color: #ffffff !important;
    }
    [data-testid="metric-container"] label {
        color: #a0c4e0 !important;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.5rem;
        font-weight: 700;
    }
    div[data-testid="stSidebar"] {
        background-color: #0f2841;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── State code → State name lookup ───────────────────────────────────────────
STATE_CODE_MAP = {
    "AN": "Andaman & Nicobar Islands", "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "CH": "Chandigarh", "DD": "Dadra & Nagar Haveli",
    "DL": "Delhi", "GA": "Goa", "GJ": "Gujarat", "HP": "Himachal Pradesh",
    "HR": "Haryana", "JH": "Jharkhand", "JK": "Jammu & Kashmir",
    "KA": "Karnataka", "KL": "Kerala", "LA": "Ladakh",
    "LD": "Lakshadweep", "MH": "Maharashtra", "ML": "Meghalaya",
    "MN": "Manipur", "MP": "Madhya Pradesh", "MZ": "Mizoram",
    "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab",
    "PY": "Puducherry", "RJ": "Rajasthan", "SK": "Sikkim",
    "TN": "Tamil Nadu", "TR": "Tripura", "TS": "Telangana",
    "UK": "Uttarakhand", "UP": "Uttar Pradesh", "WB": "West Bengal",
}

# ── Sample-data generator (Tally 14-column format) ────────────────────────────

def generate_sample_data() -> pd.DataFrame:
    """Return realistic Tally 14-column sales export as a DataFrame."""
    rng = np.random.default_rng(42)

    party_state = {
        "Baroda Bnp Paribas Mutual Fund": "MH",
        "HDFC Asset Management": "MH",
        "SBI Mutual Fund": "MH",
        "Axis Capital Ltd": "MH",
        "ICICI Prudential AMC": "MH",
        "Kotak Mahindra AMC": "MH",
        "Nippon India Mutual Fund": "MH",
        "DSP Investment Managers": "MH",
        "Sundaram Mutual Fund": "TN",
        "Franklin Templeton India": "KA",
        "Mirae Asset Mutual Fund": "DL",
        "Motilal Oswal AMC": "MH",
        "UTI Asset Management": "MH",
        "Aditya Birla Sun Life AMC": "MH",
        "Canara Robeco AMC": "KA",
    }
    drs_types = ["MF Drs", "Equity Drs", "Debt Drs", "Hybrid Drs"]
    gst_rates = [5, 12, 18, 28]
    months_25_26 = [
        ("Apr", 4, 2025), ("May", 5, 2025), ("Jun", 6, 2025),
        ("Jul", 7, 2025), ("Aug", 8, 2025), ("Sep", 9, 2025),
        ("Oct", 10, 2025), ("Nov", 11, 2025), ("Dec", 12, 2025),
        ("Jan", 1, 2026), ("Feb", 2, 2026), ("Mar", 3, 2026),
    ]
    party_names = list(party_state.keys())

    rows = []
    inv_seq = 2001
    for mon_name, mon_num, yr in months_25_26:
        for _ in range(rng.integers(30, 60)):
            day = rng.integers(1, 29)
            party = rng.choice(party_names)
            state_code = party_state[party]
            taxable = round(float(rng.uniform(50, 5_000)), 2)
            gst_rate = rng.choice(gst_rates)
            total_gst = round(taxable * gst_rate / 100, 2)

            inter = bool(rng.integers(0, 2))
            if inter:
                igst = total_gst
                cgst = sgst = ""
            else:
                igst = ""
                cgst = sgst = round(total_gst / 2, 2)

            invoice_value = round(taxable + total_gst, 2)
            mon_label = f"{mon_name}{str(yr)[2:]}"
            date_str = f"{day:02d}-{mon_name}-{str(yr)[2:]}"
            voucher = f"FIM/MF/{inv_seq:03d}/{str(yr-1)[2:]}-{str(yr)[2:]}"
            gstin_prefix = rng.integers(10, 30)
            gstin = f"{gstin_prefix}AAAT{party[:1].upper()}0509R1ZL"

            rows.append({
                "Date": date_str,
                "Month": mon_label,
                "Year": yr,
                "PartyName": f"{party}_{state_code}",
                "VoucherNo": voucher,
                "GSTIN": gstin,
                "TaxableValue": taxable,
                "IGST": igst,
                "CGST": cgst,
                "SGST": sgst,
                "TotalGST": total_gst,
                "GST Rate": f"{gst_rate}%",
                "InvoiceValue": invoice_value,
                "DrsType": rng.choice(drs_types),
            })
            inv_seq += 1

    return pd.DataFrame(rows)


# ── Column mapping helpers ────────────────────────────────────────────────────

def _apply_tally_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Tally export column names to canonical internal names.
    Supports both the new 14-column Tally format and the legacy item-level format.
    """
    rename = {}
    cols = df.columns.tolist()

    col_map = {
        "PartyName": "Party Name",
        "VoucherNo": "Invoice Number",
        "TaxableValue": "Taxable Value",
        "IGST": "IGST Amount",
        "CGST": "CGST Amount",
        "SGST": "SGST Amount",
        "TotalGST": "Total GST",
        "InvoiceValue": "Invoice Value",
        "DrsType": "Debtor Type",
    }
    for src, dst in col_map.items():
        if src in cols and dst not in cols:
            rename[src] = dst

    if rename:
        df = df.rename(columns=rename)

    # Parse GST Rate string ("18%") → numeric
    gst_rate_col = next(
        (c for c in df.columns if c.lower().replace(" ", "") in ("gstrate", "gstrate(%)")),
        None,
    )
    if gst_rate_col:
        df["GST Rate (%)"] = (
            pd.to_numeric(
                df[gst_rate_col].astype(str).str.replace("%", "", regex=False).str.strip(),
                errors="coerce",
            ).fillna(0)
        )
        if gst_rate_col != "GST Rate (%)":
            df = df.drop(columns=[gst_rate_col])

    # Fill missing GST component columns
    for col in ("IGST Amount", "CGST Amount", "SGST Amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0.0

    # Total GST derived if missing
    if "Total GST" not in df.columns:
        df["Total GST"] = df["IGST Amount"] + df["CGST Amount"] + df["SGST Amount"]
    else:
        df["Total GST"] = pd.to_numeric(df["Total GST"], errors="coerce").fillna(0)

    # Taxable Value numeric coercion
    if "Taxable Value" in df.columns:
        df["Taxable Value"] = pd.to_numeric(df["Taxable Value"], errors="coerce").fillna(0)

    # Invoice Value
    if "Invoice Value" not in df.columns:
        df["Invoice Value"] = df.get("Taxable Value", pd.Series(0, index=df.index)) + df["Total GST"]
    else:
        df["Invoice Value"] = pd.to_numeric(df["Invoice Value"], errors="coerce").fillna(0)

    # Extract State from PartyName suffix
    if "State" not in df.columns and "Party Name" in df.columns:
        def _extract_state(name: str) -> str:
            if isinstance(name, str) and "_" in name:
                code = name.rsplit("_", 1)[-1].strip().upper()
                return STATE_CODE_MAP.get(code, "")
            return ""
        df["State"] = df["Party Name"].apply(_extract_state)

    # Clean up Party Name suffix
    if "Party Name" in df.columns:
        df["Party Name"] = df["Party Name"].apply(
            lambda n: n.rsplit("_", 1)[0].strip() if isinstance(n, str) and "_" in n
            and n.rsplit("_", 1)[-1].upper() in STATE_CODE_MAP
            else n
        )

    # Populate placeholder columns if absent (Tally format has no Item/HSN)
    if "Item Name" not in df.columns:
        df["Item Name"] = df.get("Debtor Type", pd.Series("General", index=df.index)).fillna("General")
    if "HSN Code" not in df.columns:
        df["HSN Code"] = "N/A"
    if "Quantity" not in df.columns:
        df["Quantity"] = 1

    # GSTIN and Debtor Type defaults
    if "GSTIN" not in df.columns:
        df["GSTIN"] = ""
    if "Debtor Type" not in df.columns:
        df["Debtor Type"] = "General"

    return df


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data(uploaded_file=None) -> pd.DataFrame:
    """Load data from uploaded file or fall back to demo data."""
    if uploaded_file is not None:
        fname = uploaded_file.name.lower()
        if fname.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        df = generate_sample_data()

    df.columns = df.columns.str.strip()

    # Apply Tally column mapping
    df = _apply_tally_column_mapping(df)

    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    # Time dimensions
    df["Month"] = df["Date"].dt.month
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year
    df["Month-Year"] = df["Date"].dt.to_period("M").astype(str)

    # Numeric coercion for legacy columns
    for col in ("Quantity", "Taxable Value", "GST Rate (%)"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculated fields
    df["Total GST"] = df["CGST Amount"] + df["SGST Amount"] + df["IGST Amount"]
    df["Effective Tax %"] = np.where(
        df["Taxable Value"] > 0,
        (df["Total GST"] / df["Taxable Value"] * 100).round(2),
        0,
    )
    df["HSN Code"] = df["HSN Code"].astype(str).str.strip()

    # Ensure Invoice Number exists
    if "Invoice Number" not in df.columns:
        df["Invoice Number"] = "N/A"

    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar file-upload and all filter controls; return filtered df."""
    st.sidebar.header("📁 Data Source")
    uploaded = st.sidebar.file_uploader(
        "Upload Tally CSV / Excel",
        type=["csv", "xlsx", "xls"],
        help="Leave blank to use built-in demo data",
    )
    df = load_data(uploaded)

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")

    # Year
    years = sorted(df["Year"].dropna().unique())
    sel_years = st.sidebar.multiselect("Year", years, default=years)

    # Month
    month_opts = (
        df[df["Year"].isin(sel_years)]
        .sort_values("Month")[["Month", "Month Name"]]
        .drop_duplicates()
    )
    month_labels = month_opts["Month Name"].tolist()
    sel_months = st.sidebar.multiselect("Month", month_labels, default=month_labels)
    sel_month_nums = month_opts[
        month_opts["Month Name"].isin(sel_months)
    ]["Month"].tolist()

    # GST Rate
    gst_rates = sorted(df["GST Rate (%)"].dropna().unique())
    sel_gst = st.sidebar.multiselect("GST Rate (%)", gst_rates, default=gst_rates)

    # Party / Debtor
    parties = sorted(df["Party Name"].dropna().unique())
    sel_parties = st.sidebar.multiselect("Party Name", parties, default=parties)

    # Debtor Type filter
    if "Debtor Type" in df.columns:
        drs_types = sorted(df["Debtor Type"].dropna().unique())
        sel_drs = st.sidebar.multiselect("Debtor Type", drs_types, default=drs_types)
    else:
        sel_drs = []

    # Item (only show if meaningful)
    unique_items = df["Item Name"].dropna().unique()
    show_item_filter = len(unique_items) > 1 and not (len(unique_items) <= 5 and "General" in unique_items)
    if show_item_filter:
        items = sorted(unique_items)
        sel_items = st.sidebar.multiselect("Item", items, default=items)
    else:
        sel_items = list(unique_items)

    # HSN Code (only show if meaningful)
    unique_hsn = df["HSN Code"].dropna().unique()
    show_hsn_filter = len(unique_hsn) > 1 and "N/A" not in unique_hsn
    if show_hsn_filter:
        hsn_codes = sorted(unique_hsn)
        sel_hsn = st.sidebar.multiselect("HSN Code", hsn_codes, default=hsn_codes)
    else:
        sel_hsn = list(unique_hsn)

    # Apply filters
    mask = (
        df["Year"].isin(sel_years)
        & df["Month"].isin(sel_month_nums)
        & df["GST Rate (%)"].isin(sel_gst)
        & df["Party Name"].isin(sel_parties)
        & df["Item Name"].isin(sel_items)
        & df["HSN Code"].isin(sel_hsn)
    )
    if sel_drs:
        mask &= df["Debtor Type"].isin(sel_drs)
    return df[mask].copy()


# ── KPI cards ─────────────────────────────────────────────────────────────────

def render_kpis(df: pd.DataFrame):
    """Render CA-style KPI metric cards."""
    total_sales = df["Taxable Value"].sum()
    total_invoice = df["Invoice Value"].sum() if "Invoice Value" in df.columns else total_sales
    total_gst = df["Total GST"].sum()
    avg_gst_rate = df["GST Rate (%)"].mean() if not df.empty else 0
    total_invoices = df["Invoice Number"].nunique()
    active_debtors = df["Party Name"].nunique()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💰 Taxable Value", f"₹{total_sales:,.0f}")
    c2.metric("🧾 Invoice Value", f"₹{total_invoice:,.0f}")
    c3.metric("📋 Total GST", f"₹{total_gst:,.0f}")
    c4.metric("📊 Avg GST Rate", f"{avg_gst_rate:.1f}%")
    c5.metric("📄 Total Invoices", f"{total_invoices:,}")
    c6.metric("👥 Active Debtors", f"{active_debtors:,}")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def chart_top_parties(df: pd.DataFrame):
    """Horizontal bar chart of top debtors/parties by taxable value."""
    top_parties = (
        df.groupby("Party Name")["Taxable Value"]
        .sum()
        .nlargest(15)
        .reset_index()
        .sort_values("Taxable Value")
    )
    fig = px.bar(
        top_parties,
        x="Taxable Value",
        y="Party Name",
        orientation="h",
        title="🏆 Top Debtors by Taxable Value",
        labels={"Taxable Value": "Taxable Value (₹)", "Party Name": "Debtor"},
        color="Taxable Value",
        color_continuous_scale="Blues",
        text="Taxable Value",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


def chart_top_items(df: pd.DataFrame):
    """Horizontal bar chart of top items/categories by taxable value."""
    top_items = (
        df.groupby("Item Name")["Taxable Value"]
        .sum()
        .nlargest(15)
        .reset_index()
        .sort_values("Taxable Value")
    )
    fig = px.bar(
        top_items,
        x="Taxable Value",
        y="Item Name",
        orientation="h",
        title="📦 Top Categories by Taxable Value",
        labels={"Taxable Value": "Taxable Value (₹)", "Item Name": "Category"},
        color="Taxable Value",
        color_continuous_scale="Viridis",
        text="Taxable Value",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


def chart_invoice_vs_taxable(df: pd.DataFrame):
    """Line chart comparing monthly Invoice Value vs Taxable Value."""
    monthly = (
        df.groupby(["Year", "Month", "Month Name"])
        .agg(
            Taxable_Value=("Taxable Value", "sum"),
            Invoice_Value=("Invoice Value", "sum"),
        )
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly["Period"] = monthly["Month Name"] + " " + monthly["Year"].astype(str)
    melted = monthly.melt(
        id_vars="Period",
        value_vars=["Taxable_Value", "Invoice_Value"],
        var_name="Metric",
        value_name="Amount",
    )
    melted["Metric"] = melted["Metric"].map(
        {"Taxable_Value": "Taxable Value", "Invoice_Value": "Invoice Value"}
    )
    fig = px.line(
        melted,
        x="Period",
        y="Amount",
        color="Metric",
        markers=True,
        title="📅 Invoice Value vs Taxable Value — Monthly Trend",
        labels={"Amount": "Amount (₹)", "Period": "Month"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
    )
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_layout(xaxis_tickangle=-45, legend_title="Metric")
    return fig


def chart_hsn_sales(df: pd.DataFrame):
    """Bar chart of HSN-wise taxable sales."""
    hsn_df = (
        df.groupby("HSN Code")["Taxable Value"]
        .sum()
        .reset_index()
        .sort_values("Taxable Value", ascending=False)
    )
    # Skip if only N/A
    if hsn_df["HSN Code"].eq("N/A").all():
        return None
    fig = px.bar(
        hsn_df,
        x="HSN Code",
        y="Taxable Value",
        title="🔢 HSN-wise Sales",
        labels={"Taxable Value": "Taxable Value (₹)", "HSN Code": "HSN Code"},
        color="Taxable Value",
        color_continuous_scale="Teal",
        text="Taxable Value",
    )
    fig.update_traces(texttemplate="₹%{y:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, xaxis_type="category")
    return fig


def chart_gst_distribution(df: pd.DataFrame):
    """Pie chart showing distribution of sales across GST rate slabs."""
    gst_slab = (
        df.groupby("GST Rate (%)")["Taxable Value"]
        .sum()
        .reset_index()
    )
    gst_slab["GST Slab"] = gst_slab["GST Rate (%)"].astype(str) + "%"
    fig = px.pie(
        gst_slab,
        names="GST Slab",
        values="Taxable Value",
        title="🥧 GST Rate Slab Distribution",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def chart_monthly_gst_trend(df: pd.DataFrame):
    """Stacked line chart of monthly CGST / SGST / IGST collection."""
    monthly = (
        df.groupby(["Year", "Month", "Month Name"])[
            ["CGST Amount", "SGST Amount", "IGST Amount", "Total GST"]
        ]
        .sum()
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly["Period"] = monthly["Month Name"] + " " + monthly["Year"].astype(str)
    melted = monthly.melt(
        id_vars="Period",
        value_vars=["CGST Amount", "SGST Amount", "IGST Amount"],
        var_name="GST Component",
        value_name="Amount",
    )
    fig = px.line(
        melted,
        x="Period",
        y="Amount",
        color="GST Component",
        markers=True,
        title="📅 Monthly GST Collection Trend",
        labels={"Amount": "GST Amount (₹)", "Period": "Month"},
    )
    fig.update_layout(xaxis_tickangle=-45, legend_title="GST Component")
    return fig


def chart_interstate_intrastate(df: pd.DataFrame):
    """Grouped bar chart: Inter-state (IGST) vs Intra-state (CGST+SGST) by month."""
    monthly = (
        df.groupby(["Year", "Month", "Month Name"])
        .agg(
            IGST=("IGST Amount", "sum"),
            CGST_SGST=pd.NamedAgg(
                column="CGST Amount",
                aggfunc=lambda x: x.sum() + df.loc[x.index, "SGST Amount"].sum(),
            ),
        )
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly["Period"] = monthly["Month Name"] + " " + monthly["Year"].astype(str)
    melted = monthly.melt(
        id_vars="Period",
        value_vars=["IGST", "CGST_SGST"],
        var_name="GST Type",
        value_name="Amount",
    )
    melted["GST Type"] = melted["GST Type"].map(
        {"IGST": "IGST (Inter-state)", "CGST_SGST": "CGST+SGST (Intra-state)"}
    )
    fig = px.bar(
        melted,
        x="Period",
        y="Amount",
        color="GST Type",
        barmode="group",
        title="🌐 Inter-state vs Intra-state GST — Monthly",
        labels={"Amount": "GST Amount (₹)", "Period": "Month"},
        color_discrete_map={
            "IGST (Inter-state)": "#2196F3",
            "CGST+SGST (Intra-state)": "#4CAF50",
        },
    )
    fig.update_layout(xaxis_tickangle=-45, legend_title="GST Type")
    return fig


def chart_item_gst(df: pd.DataFrame):
    """Horizontal bar chart of top GST-generating categories."""
    item_gst = (
        df.groupby("Item Name")["Total GST"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("Total GST")
    )
    fig = px.bar(
        item_gst,
        x="Total GST",
        y="Item Name",
        orientation="h",
        title="💸 Top GST-Generating Categories",
        labels={"Total GST": "Total GST (₹)", "Item Name": "Category"},
        color="Total GST",
        color_continuous_scale="Oranges",
        text="Total GST",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


# ── GSTIN analysis ────────────────────────────────────────────────────────────

def gstin_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Return GSTIN-wise sales summary."""
    if "GSTIN" not in df.columns or df["GSTIN"].str.strip().eq("").all():
        return pd.DataFrame()
    gstin_df = (
        df[df["GSTIN"].str.strip() != ""]
        .groupby(["GSTIN", "Party Name"])
        .agg(
            Invoices=("Invoice Number", "nunique"),
            Taxable_Value=("Taxable Value", "sum"),
            Total_GST=("Total GST", "sum"),
            Invoice_Value=("Invoice Value", "sum"),
        )
        .reset_index()
        .sort_values("Taxable_Value", ascending=False)
    )
    return gstin_df


# ── Anomaly detection ─────────────────────────────────────────────────────────

def detect_gst_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """
    Identify rows where effective tax % deviates significantly from the
    declared GST Rate by more than `threshold` percentage points.
    """
    anom_cols = ["Invoice Number", "Party Name", "Item Name",
                 "Taxable Value", "GST Rate (%)", "Total GST",
                 "Effective Tax %", "Date"]
    available = [c for c in anom_cols if c in df.columns]
    anom = df[
        (df["Taxable Value"] > 0)
        & (df["GST Rate (%)"] > 0)
        & (abs(df["Effective Tax %"] - df["GST Rate (%)"]) > threshold)
    ][available].copy()
    anom["Deviation (pp)"] = (
        anom["Effective Tax %"] - anom["GST Rate (%)"]
    ).round(2)
    return anom.sort_values("Deviation (pp)", key=abs, ascending=False)


# ── Item + HSN + GST breakdown table ─────────────────────────────────────────

def item_hsn_gst_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a summarised Item + HSN + GST breakdown table."""
    tbl = (
        df.groupby(["Item Name", "HSN Code", "GST Rate (%)"])
        .agg(
            Quantity=("Quantity", "sum"),
            Taxable_Value=("Taxable Value", "sum"),
            CGST=("CGST Amount", "sum"),
            SGST=("SGST Amount", "sum"),
            IGST=("IGST Amount", "sum"),
            Total_GST=("Total GST", "sum"),
        )
        .reset_index()
        .sort_values("Taxable_Value", ascending=False)
    )
    tbl["GST %"] = np.where(
        tbl["Taxable_Value"] > 0,
        (tbl["Total_GST"] / tbl["Taxable_Value"] * 100).round(2),
        0,
    )
    return tbl


# ── Main dashboard ────────────────────────────────────────────────────────────

def main():
    st.title("🧾 Sales & GST Analysis Dashboard")
    st.caption(
        "Party-wise • GST-wise • Tally Export  |  CA-style Reporting  |  "
        "Powered by Tally Sales Export  •  Built with Streamlit + Plotly"
    )

    # Load & filter data
    df = render_sidebar(pd.DataFrame())
    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("### 📌 Key Performance Indicators")
    render_kpis(df)
    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_sales, tab_gst, tab_gstin, tab_hsn, tab_anomaly, tab_export = st.tabs(
        ["📦 Sales Analysis", "🧾 GST Analysis", "🔑 GSTIN / Party",
         "🔢 HSN Analysis", "⚠️ Anomaly Detection", "📥 Export"]
    )

    # ── Tab 1: Sales Analysis ─────────────────────────────────────────────────
    with tab_sales:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_top_parties(df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_gst_distribution(df), use_container_width=True)

        st.plotly_chart(chart_invoice_vs_taxable(df), use_container_width=True)

        st.markdown("#### Party + GST Breakdown Table")
        tbl = item_hsn_gst_table(df)
        st.dataframe(
            tbl.style.format(
                {
                    "Taxable_Value": "₹{:,.0f}",
                    "CGST": "₹{:,.0f}",
                    "SGST": "₹{:,.0f}",
                    "IGST": "₹{:,.0f}",
                    "Total_GST": "₹{:,.0f}",
                    "GST %": "{:.2f}%",
                    "Quantity": "{:,.0f}",
                }
            ),
            use_container_width=True,
            height=400,
        )

    # ── Tab 2: GST Analysis ───────────────────────────────────────────────────
    with tab_gst:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_monthly_gst_trend(df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_item_gst(df), use_container_width=True)

        st.plotly_chart(chart_interstate_intrastate(df), use_container_width=True)

        # Inter-state vs Intra-state summary
        igst_total = df["IGST Amount"].sum()
        cgst_total = df["CGST Amount"].sum()
        sgst_total = df["SGST Amount"].sum()
        total_gst = df["Total GST"].sum()
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("🔵 Total GST", f"₹{total_gst:,.0f}")
        g2.metric("🌐 IGST (Inter-state)", f"₹{igst_total:,.0f}")
        g3.metric("🏛️ CGST", f"₹{cgst_total:,.0f}")
        g4.metric("🏛️ SGST", f"₹{sgst_total:,.0f}")

        # GST slab summary
        st.markdown("#### GST Slab-wise Summary")
        slab = (
            df.groupby("GST Rate (%)")
            .agg(
                Invoices=("Invoice Number", "nunique"),
                Taxable_Value=("Taxable Value", "sum"),
                CGST=("CGST Amount", "sum"),
                SGST=("SGST Amount", "sum"),
                IGST=("IGST Amount", "sum"),
                Total_GST=("Total GST", "sum"),
            )
            .reset_index()
            .sort_values("Total_GST", ascending=False)
        )
        slab["GST Liability %"] = (
            slab["Total_GST"] / slab["Total_GST"].sum() * 100
        ).round(2)
        st.dataframe(
            slab.style.format(
                {
                    "GST Rate (%)": "{:.0f}%",
                    "Taxable_Value": "₹{:,.0f}",
                    "CGST": "₹{:,.0f}",
                    "SGST": "₹{:,.0f}",
                    "IGST": "₹{:,.0f}",
                    "Total_GST": "₹{:,.0f}",
                    "GST Liability %": "{:.2f}%",
                }
            ),
            use_container_width=True,
        )

        # Monthly GST summary table
        with st.expander("📅 Monthly GST Summary Table"):
            monthly_gst = (
                df.groupby(["Year", "Month", "Month Name"])[
                    ["Taxable Value", "CGST Amount", "SGST Amount",
                     "IGST Amount", "Total GST"]
                ]
                .sum()
                .reset_index()
                .sort_values(["Year", "Month"])
            )
            monthly_gst["Period"] = (
                monthly_gst["Month Name"] + " " + monthly_gst["Year"].astype(str)
            )
            st.dataframe(
                monthly_gst[
                    ["Period", "Taxable Value", "CGST Amount",
                     "SGST Amount", "IGST Amount", "Total GST"]
                ].style.format(
                    {
                        "Taxable Value": "₹{:,.0f}",
                        "CGST Amount": "₹{:,.0f}",
                        "SGST Amount": "₹{:,.0f}",
                        "IGST Amount": "₹{:,.0f}",
                        "Total GST": "₹{:,.0f}",
                    }
                ),
                use_container_width=True,
            )

    # ── Tab 3: GSTIN / Party Analysis ─────────────────────────────────────────
    with tab_gstin:
        gstin_df = gstin_analysis(df)
        if gstin_df.empty:
            st.info("ℹ️ No GSTIN data available in the current dataset.")
        else:
            missing_gstin = df["GSTIN"].str.strip().eq("").sum()
            if missing_gstin:
                st.warning(f"⚠️ {missing_gstin} row(s) have missing GSTIN.")

            st.markdown("#### GSTIN-wise Sales Summary")
            st.dataframe(
                gstin_df.style.format(
                    {
                        "Taxable_Value": "₹{:,.0f}",
                        "Total_GST": "₹{:,.0f}",
                        "Invoice_Value": "₹{:,.0f}",
                    }
                ),
                use_container_width=True,
                height=400,
            )

        st.markdown("#### Party-wise Sales Summary")
        party_df = (
            df.groupby("Party Name")
            .agg(
                Invoices=("Invoice Number", "nunique"),
                Taxable_Value=("Taxable Value", "sum"),
                Total_GST=("Total GST", "sum"),
                Invoice_Value=("Invoice Value", "sum"),
                IGST=("IGST Amount", "sum"),
                CGST=("CGST Amount", "sum"),
                SGST=("SGST Amount", "sum"),
            )
            .reset_index()
            .sort_values("Taxable_Value", ascending=False)
        )
        party_df["Share %"] = (
            party_df["Taxable_Value"] / party_df["Taxable_Value"].sum() * 100
        ).round(2)
        st.dataframe(
            party_df.style.format(
                {
                    "Taxable_Value": "₹{:,.0f}",
                    "Total_GST": "₹{:,.0f}",
                    "Invoice_Value": "₹{:,.0f}",
                    "IGST": "₹{:,.0f}",
                    "CGST": "₹{:,.0f}",
                    "SGST": "₹{:,.0f}",
                    "Share %": "{:.2f}%",
                }
            ),
            use_container_width=True,
            height=400,
        )

    # ── Tab 4: HSN Analysis ───────────────────────────────────────────────────
    with tab_hsn:
        hsn_fig = chart_hsn_sales(df)
        if hsn_fig:
            st.plotly_chart(hsn_fig, use_container_width=True)
        else:
            st.info("ℹ️ No HSN Code data in this dataset. Upload an item-level file to see HSN analysis.")

        st.markdown("#### HSN-wise Detailed Summary")
        hsn_detail = (
            df.groupby(["HSN Code", "GST Rate (%)"])
            .agg(
                Items=("Item Name", "nunique"),
                Quantity=("Quantity", "sum"),
                Taxable_Value=("Taxable Value", "sum"),
                Total_GST=("Total GST", "sum"),
            )
            .reset_index()
            .sort_values("Taxable_Value", ascending=False)
        )
        hsn_detail["Contribution %"] = (
            hsn_detail["Taxable_Value"] / hsn_detail["Taxable_Value"].sum() * 100
        ).round(2)

        top_hsn = hsn_detail.iloc[0]
        if top_hsn["HSN Code"] != "N/A":
            st.success(
                f"🏆 Top HSN Code **{top_hsn['HSN Code']}** contributes "
                f"**{top_hsn['Contribution %']}%** of total taxable sales "
                f"(₹{top_hsn['Taxable_Value']:,.0f})"
            )
        st.dataframe(
            hsn_detail.style.format(
                {
                    "Taxable_Value": "₹{:,.0f}",
                    "Total_GST": "₹{:,.0f}",
                    "Quantity": "{:,.0f}",
                    "Contribution %": "{:.2f}%",
                }
            ),
            use_container_width=True,
        )

    # ── Tab 5: Anomaly Detection ──────────────────────────────────────────────
    with tab_anomaly:
        st.markdown("#### ⚠️ GST Rate Anomalies")
        st.caption(
            "Rows where **Effective Tax %** deviates by more than the threshold from "
            "the declared **GST Rate (%)** are flagged below."
        )
        threshold = st.slider(
            "Deviation threshold (percentage points)", 0.5, 10.0, 2.0, 0.5
        )
        anom_df = detect_gst_anomalies(df, threshold)

        if anom_df.empty:
            st.success("✅ No GST rate anomalies detected within the selected threshold.")
        else:
            st.warning(f"⚠️ {len(anom_df)} anomalous line item(s) detected.")
            fmt = {
                "Taxable Value": "₹{:,.0f}",
                "Total GST": "₹{:,.0f}",
                "Effective Tax %": "{:.2f}%",
                "GST Rate (%)": "{:.0f}%",
                "Deviation (pp)": "{:+.2f}",
            }
            st.dataframe(
                anom_df.style.format({k: v for k, v in fmt.items() if k in anom_df.columns}),
                use_container_width=True,
            )
            csv_anom = anom_df.to_csv(index=False).encode()
            st.download_button(
                "⬇️ Download Anomalies (CSV)",
                data=csv_anom,
                file_name="gst_anomalies.csv",
                mime="text/csv",
            )

    # ── Tab 6: Export ─────────────────────────────────────────────────────────
    with tab_export:
        st.markdown("#### 📥 Export Filtered Data for Return Filing")
        st.caption(
            "Download filtered data as CSV for use in GST return preparation "
            "or further analysis in Excel."
        )

        # Data quality summary
        dq1, dq2, dq3 = st.columns(3)
        dq1.metric("Total Rows", f"{len(df):,}")
        missing_gstin = df["GSTIN"].str.strip().eq("").sum() if "GSTIN" in df.columns else 0
        dq2.metric("Missing GSTIN", f"{missing_gstin:,}")
        dq3.metric("Missing Dates", f"{df['Date'].isna().sum():,}")

        # Summary export
        summary = item_hsn_gst_table(df)
        csv_summary = summary.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Summary Table (CSV)",
            data=csv_summary,
            file_name="gst_summary.csv",
            mime="text/csv",
        )

        # Full line-item export
        export_cols = [
            "Date", "Invoice Number", "Party Name", "GSTIN", "Debtor Type",
            "Item Name", "HSN Code", "Quantity", "Taxable Value",
            "GST Rate (%)", "CGST Amount", "SGST Amount", "IGST Amount",
            "Total GST", "Invoice Value", "Effective Tax %", "State",
            "Month Name", "Year",
        ]
        available_cols = [c for c in export_cols if c in df.columns]
        csv_full = df[available_cols].to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Full Line-item Data (CSV)",
            data=csv_full,
            file_name="full_sales_gst_data.csv",
            mime="text/csv",
        )

        # Preview
        st.markdown("##### Preview (first 50 rows)")
        st.dataframe(df[available_cols].head(50), use_container_width=True)


if __name__ == "__main__":
    main()
