"""
Monthly Sales Dashboard with Debtor-wise Analysis
====================================================
Supports the native Tally export format (14 columns) as well as the
legacy column layout — auto-detected on upload.

Run:  streamlit run monthly_sales_dashboard.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monthly Sales Dashboard",
    page_icon="📊",
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

# ── Sample-data generator (Tally format) ─────────────────────────────────────

def generate_sample_data() -> pd.DataFrame:
    """Return a realistic Tally-style 14-column sales export as a DataFrame."""
    rng = np.random.default_rng(42)

    # Party name → state code
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
        "PGIM India AMC": "MH",
        "Invesco Mutual Fund": "GJ",
        "Tata Asset Management": "MH",
        "Quantum AMC": "MH",
        "Edelweiss AMC": "MH",
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
    inv_seq = 1

    for mon_name, mon_num, yr in months_25_26:
        n = rng.integers(20, 45)
        for _ in range(n):
            day = rng.integers(1, 29)
            party = rng.choice(party_names)
            state_code = party_state[party]
            taxable = round(float(rng.uniform(50, 5_000)), 2)
            gst_rate = rng.choice(gst_rates)
            total_gst = round(taxable * gst_rate / 100, 2)

            # Inter-state → IGST only; intra-state → CGST + SGST
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
    Map Tally export column names to the internal canonical names used
    throughout this dashboard.  Works for both old and new Tally formats.
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

    # Sales Amount / Taxable Value harmonisation
    if "Taxable Value" in df.columns and "Sales Amount" not in df.columns:
        df["Sales Amount"] = pd.to_numeric(df["Taxable Value"], errors="coerce").fillna(0)
    elif "Sales Amount" in df.columns:
        df["Sales Amount"] = pd.to_numeric(df["Sales Amount"], errors="coerce").fillna(0)

    # Invoice Value
    if "Invoice Value" not in df.columns:
        if "InvoiceValue" not in df.columns:
            df["Invoice Value"] = df["Sales Amount"] + df["Total GST"]
    else:
        df["Invoice Value"] = pd.to_numeric(df["Invoice Value"], errors="coerce").fillna(0)

    # Extract State from PartyName suffix (e.g. "ABC Ltd_MH" → "Maharashtra")
    if "State" not in df.columns and "Party Name" in df.columns:
        def _extract_state(name: str) -> str:
            if isinstance(name, str) and "_" in name:
                code = name.rsplit("_", 1)[-1].strip().upper()
                return STATE_CODE_MAP.get(code, "")
            return ""
        df["State"] = df["Party Name"].apply(_extract_state)

    # Clean up Party Name (strip state code suffix for display)
    if "Party Name" in df.columns:
        df["Party Name"] = df["Party Name"].apply(
            lambda n: n.rsplit("_", 1)[0].strip() if isinstance(n, str) and "_" in n
            and n.rsplit("_", 1)[-1].upper() in STATE_CODE_MAP
            else n
        )

    return df


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data(uploaded_file=None) -> pd.DataFrame:
    """Load data from an uploaded file or fall back to sample data."""
    if uploaded_file is not None:
        fname = uploaded_file.name.lower()
        if fname.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        df = generate_sample_data()

    # Normalise column names
    df.columns = df.columns.str.strip()

    # Apply Tally column mapping (new → canonical names)
    df = _apply_tally_column_mapping(df)

    # Parse dates robustly (dayfirst for DD-Mon-YY Tally format)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    # Derived time columns
    df["Month"] = df["Date"].dt.month
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year
    df["Month-Year"] = df["Date"].dt.to_period("M").astype(str)

    # Net Sales = Taxable Value (GST excluded)
    df["Net Sales"] = pd.to_numeric(df.get("Sales Amount", df.get("Taxable Value", 0)),
                                    errors="coerce").fillna(0)

    # Ensure Invoice Number column exists
    if "Invoice Number" not in df.columns:
        df["Invoice Number"] = "N/A"

    # GSTIN column
    if "GSTIN" not in df.columns:
        df["GSTIN"] = ""

    # Debtor Type column
    if "Debtor Type" not in df.columns:
        df["Debtor Type"] = "General"

    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame):
    """Render sidebar upload widget and filters; return filtered DataFrame."""
    st.sidebar.header("📁 Data Source")
    uploaded = st.sidebar.file_uploader(
        "Upload Tally CSV / Excel",
        type=["csv", "xlsx", "xls"],
        help="Leave blank to use built-in demo data",
    )

    df = load_data(uploaded)

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")

    # Year filter
    years = sorted(df["Year"].dropna().unique())
    selected_years = st.sidebar.multiselect("Year", years, default=years)

    # Month filter
    month_opts = (
        df[df["Year"].isin(selected_years)]
        .sort_values("Month")[["Month", "Month Name"]]
        .drop_duplicates()
    )
    month_labels = month_opts["Month Name"].tolist()
    selected_months = st.sidebar.multiselect("Month", month_labels, default=month_labels)
    selected_month_nums = month_opts[
        month_opts["Month Name"].isin(selected_months)
    ]["Month"].tolist()

    # Debtor filter
    debtors = sorted(df["Party Name"].dropna().unique())
    selected_debtors = st.sidebar.multiselect("Debtor (Party Name)", debtors, default=debtors)

    # State filter
    if "State" in df.columns and df["State"].str.strip().ne("").any():
        states = sorted(df["State"].dropna().loc[df["State"].str.strip() != ""].unique())
        selected_states = st.sidebar.multiselect("State", states, default=states)
    else:
        selected_states = []

    # Debtor Type filter
    if "Debtor Type" in df.columns:
        drs_types = sorted(df["Debtor Type"].dropna().unique())
        selected_drs = st.sidebar.multiselect("Debtor Type", drs_types, default=drs_types)
    else:
        selected_drs = []

    # Apply filters
    mask = (
        df["Year"].isin(selected_years)
        & df["Month"].isin(selected_month_nums)
        & df["Party Name"].isin(selected_debtors)
    )
    if selected_states:
        mask &= df["State"].isin(selected_states)
    if selected_drs:
        mask &= df["Debtor Type"].isin(selected_drs)

    return df[mask].copy()


# ── KPI cards ─────────────────────────────────────────────────────────────────

def render_kpis(df: pd.DataFrame):
    """Display top-level KPI metric cards."""
    total_taxable = df["Net Sales"].sum()
    total_invoice = df["Invoice Value"].sum() if "Invoice Value" in df.columns else total_taxable
    total_gst = df["Total GST"].sum() if "Total GST" in df.columns else 0
    active_debtors = df["Party Name"].nunique()
    total_invoices = df["Invoice Number"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Taxable Value", f"₹{total_taxable:,.0f}")
    c2.metric("🧾 Invoice Value", f"₹{total_invoice:,.0f}")
    c3.metric("📋 Total GST", f"₹{total_gst:,.0f}")
    c4.metric("👥 Active Debtors", f"{active_debtors:,}")
    c5.metric("📄 Invoices", f"{total_invoices:,}")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def chart_top10_debtors(df: pd.DataFrame):
    """Horizontal bar chart of the top 10 debtors by Net Sales."""
    top10 = (
        df.groupby("Party Name")["Net Sales"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("Net Sales")
    )
    fig = px.bar(
        top10,
        x="Net Sales",
        y="Party Name",
        orientation="h",
        title="🏆 Top 10 Debtors by Taxable Value",
        labels={"Net Sales": "Taxable Value (₹)", "Party Name": "Debtor"},
        color="Net Sales",
        color_continuous_scale="Blues",
        text="Net Sales",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return fig


def chart_monthly_trend(df: pd.DataFrame):
    """Line chart of monthly net sales and invoice value trend."""
    monthly = (
        df.groupby(["Year", "Month", "Month Name"])
        .agg(
            Taxable_Value=("Net Sales", "sum"),
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
        title="📅 Monthly Sales Trend (Taxable vs Invoice Value)",
        labels={"Amount": "Amount (₹)", "Period": "Month"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
    )
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_layout(xaxis_tickangle=-45, legend_title="Metric")
    return fig


def chart_debtor_month_heatmap(df: pd.DataFrame):
    """Heatmap of Debtor vs Month net sales matrix."""
    pivot = (
        df.pivot_table(
            index="Party Name",
            columns="Month Name",
            values="Net Sales",
            aggfunc="sum",
            fill_value=0,
        )
    )
    month_order = [
        m for m in
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if m in pivot.columns
    ]
    pivot = pivot[month_order]

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        title="🗓️ Debtor vs Month Sales Heatmap",
        labels={"color": "Taxable Value (₹)"},
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Debtor",
        coloraxis_colorbar_title="₹",
    )
    return fig


def chart_state_sales(df: pd.DataFrame):
    """Donut chart of sales contribution by state."""
    if "State" not in df.columns:
        return None
    state_df = (
        df[df["State"].str.strip() != ""]
        .groupby("State")["Net Sales"]
        .sum()
        .reset_index()
    )
    if state_df.empty:
        return None
    fig = px.pie(
        state_df,
        names="State",
        values="Net Sales",
        title="🗺️ Sales by State",
        hole=0.40,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def chart_debtor_type_distribution(df: pd.DataFrame):
    """Donut chart showing sales by Debtor Type."""
    if "Debtor Type" not in df.columns:
        return None
    drs_df = df.groupby("Debtor Type")["Net Sales"].sum().reset_index()
    fig = px.pie(
        drs_df,
        names="Debtor Type",
        values="Net Sales",
        title="📂 Sales by Debtor Type",
        hole=0.40,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def chart_gst_summary(df: pd.DataFrame):
    """Grouped bar chart: IGST vs CGST+SGST split by month."""
    monthly_raw = (
        df.groupby(["Year", "Month", "Month Name"])[
            ["IGST Amount", "CGST Amount", "SGST Amount"]
        ]
        .sum()
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly = monthly_raw.copy()
    monthly["IGST"] = monthly["IGST Amount"]
    monthly["CGST_SGST"] = monthly["CGST Amount"] + monthly["SGST Amount"]
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
        title="🧾 GST Summary — Inter-state (IGST) vs Intra-state (CGST+SGST)",
        labels={"Amount": "GST Amount (₹)", "Period": "Month"},
        color_discrete_map={
            "IGST (Inter-state)": "#2196F3",
            "CGST+SGST (Intra-state)": "#4CAF50",
        },
    )
    fig.update_layout(xaxis_tickangle=-45, legend_title="GST Type")
    return fig


# ── Debtor breakdown table ────────────────────────────────────────────────────

def debtor_monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a Debtor × Month pivot table with totals."""
    pivot = df.pivot_table(
        index="Party Name",
        columns="Month Name",
        values="Net Sales",
        aggfunc="sum",
        fill_value=0,
    )
    month_order = [
        m for m in
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if m in pivot.columns
    ]
    pivot = pivot[month_order]
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False)
    return pivot.reset_index()


# ── Customer insight helpers ──────────────────────────────────────────────────

def customer_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each debtor as Repeat or New based on month count."""
    seg = (
        df.groupby("Party Name")["Month"]
        .nunique()
        .reset_index(name="Active Months")
    )
    seg["Customer Type"] = seg["Active Months"].apply(
        lambda x: "🔄 Repeat" if x > 1 else "🆕 New"
    )
    sales = df.groupby("Party Name")["Net Sales"].sum().reset_index(name="Total Net Sales")
    result = seg.merge(sales, on="Party Name").sort_values("Total Net Sales", ascending=False)
    result["Share %"] = (result["Total Net Sales"] / result["Total Net Sales"].sum() * 100).round(2)
    return result


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
            Taxable_Value=("Net Sales", "sum"),
            Total_GST=("Total GST", "sum"),
            Invoice_Value=("Invoice Value", "sum"),
        )
        .reset_index()
        .sort_values("Taxable_Value", ascending=False)
    )
    return gstin_df


# ── Main dashboard ────────────────────────────────────────────────────────────

def main():
    st.title("📊 Monthly Sales Dashboard — Debtor-wise Analysis")
    st.caption("Powered by Tally Sales Export  •  Built with Streamlit + Plotly")

    # Load & filter data
    df = render_sidebar(pd.DataFrame())
    if df.empty:
        st.warning("No data available for the selected filters. Please adjust your selections.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("### 📌 Key Performance Indicators")
    render_kpis(df)
    st.markdown("---")

    # ── Tabs for drill-down ───────────────────────────────────────────────────
    tab_overview, tab_debtor, tab_gst, tab_trends, tab_insights, tab_data = st.tabs(
        ["📋 Overview", "👤 Debtor Analysis", "🧾 GST Summary",
         "📅 Trends", "💡 Insights", "🗃️ Data Preview"]
    )

    # ── Tab 1: Overview ───────────────────────────────────────────────────────
    with tab_overview:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_top10_debtors(df), use_container_width=True)
        with col2:
            state_fig = chart_state_sales(df)
            drs_fig = chart_debtor_type_distribution(df)
            if state_fig:
                st.plotly_chart(state_fig, use_container_width=True)
            elif drs_fig:
                st.plotly_chart(drs_fig, use_container_width=True)

        if drs_fig and state_fig:
            st.plotly_chart(drs_fig, use_container_width=True)

        st.markdown("#### Debtor-wise Monthly Breakdown")
        pivot_df = debtor_monthly_table(df)
        st.dataframe(
            pivot_df.style.format(
                {c: "₹{:,.0f}" for c in pivot_df.columns if c != "Party Name"}
            ),
            use_container_width=True,
            height=350,
        )
        csv_bytes = pivot_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Debtor Breakdown (CSV)",
            data=csv_bytes,
            file_name="debtor_monthly_breakdown.csv",
            mime="text/csv",
        )

    # ── Tab 2: Debtor Analysis ────────────────────────────────────────────────
    with tab_debtor:
        st.markdown("#### Debtor vs Month Heatmap")
        st.plotly_chart(chart_debtor_month_heatmap(df), use_container_width=True)

        st.markdown("#### Per-Debtor Summary")
        debtor_sum = (
            df.groupby("Party Name")
            .agg(
                Total_Taxable=("Net Sales", "sum"),
                Total_Invoice=("Invoice Value", "sum"),
                Total_GST=("Total GST", "sum"),
                Invoices=("Invoice Number", "nunique"),
                Active_Months=("Month", "nunique"),
            )
            .sort_values("Total_Taxable", ascending=False)
            .reset_index()
        )
        debtor_sum["Avg per Month"] = (
            debtor_sum["Total_Taxable"] / debtor_sum["Active_Months"]
        ).round(2)
        st.dataframe(
            debtor_sum.style.format(
                {
                    "Total_Taxable": "₹{:,.0f}",
                    "Total_Invoice": "₹{:,.0f}",
                    "Total_GST": "₹{:,.0f}",
                    "Avg per Month": "₹{:,.0f}",
                }
            ),
            use_container_width=True,
            height=400,
        )

        # GSTIN-wise analysis
        gstin_df = gstin_analysis(df)
        if not gstin_df.empty:
            st.markdown("#### GSTIN-wise Sales Summary")
            missing_gstin = df["GSTIN"].str.strip().eq("").sum()
            if missing_gstin:
                st.warning(f"⚠️ {missing_gstin} row(s) have missing GSTIN.")
            st.dataframe(
                gstin_df.style.format(
                    {
                        "Taxable_Value": "₹{:,.0f}",
                        "Total_GST": "₹{:,.0f}",
                        "Invoice_Value": "₹{:,.0f}",
                    }
                ),
                use_container_width=True,
                height=350,
            )

    # ── Tab 3: GST Summary ────────────────────────────────────────────────────
    with tab_gst:
        igst_total = df["IGST Amount"].sum() if "IGST Amount" in df.columns else 0
        cgst_total = df["CGST Amount"].sum() if "CGST Amount" in df.columns else 0
        sgst_total = df["SGST Amount"].sum() if "SGST Amount" in df.columns else 0
        total_gst = df["Total GST"].sum() if "Total GST" in df.columns else 0

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("🔵 Total GST", f"₹{total_gst:,.0f}")
        g2.metric("🌐 IGST (Inter-state)", f"₹{igst_total:,.0f}")
        g3.metric("🏛️ CGST", f"₹{cgst_total:,.0f}")
        g4.metric("🏛️ SGST", f"₹{sgst_total:,.0f}")

        st.plotly_chart(chart_gst_summary(df), use_container_width=True)

        # GST Rate slab breakdown
        if "GST Rate (%)" in df.columns:
            st.markdown("#### GST Rate Slab Breakdown")
            slab = (
                df.groupby("GST Rate (%)")
                .agg(
                    Invoices=("Invoice Number", "nunique"),
                    Taxable_Value=("Net Sales", "sum"),
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
                        "Total_GST": "₹{:,.0f}",
                        "GST Liability %": "{:.2f}%",
                    }
                ),
                use_container_width=True,
            )

    # ── Tab 4: Trends ─────────────────────────────────────────────────────────
    with tab_trends:
        st.plotly_chart(chart_monthly_trend(df), use_container_width=True)

        with st.expander("🔍 Year → Month Drill-Down"):
            year_month = (
                df.groupby(["Year", "Month", "Month Name"])["Net Sales"]
                .sum()
                .reset_index()
                .sort_values(["Year", "Month"])
            )
            year_month["Period"] = (
                year_month["Month Name"] + " " + year_month["Year"].astype(str)
            )
            fig_ym = px.bar(
                year_month,
                x="Period",
                y="Net Sales",
                color="Year",
                barmode="group",
                title="Year-over-Year Monthly Comparison",
                labels={"Net Sales": "Taxable Value (₹)"},
            )
            fig_ym.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_ym, use_container_width=True)

        with st.expander("🔍 Month → Debtor Drill-Down"):
            selected_drill_month = st.selectbox(
                "Select Month for Debtor breakdown",
                df["Month Name"].unique(),
                key="drill_month",
            )
            drilled = df[df["Month Name"] == selected_drill_month]
            drilled_grp = (
                drilled.groupby("Party Name")["Net Sales"]
                .sum()
                .nlargest(15)
                .reset_index()
                .sort_values("Net Sales")
            )
            fig_drill = px.bar(
                drilled_grp,
                x="Net Sales",
                y="Party Name",
                orientation="h",
                title=f"Top Debtors — {selected_drill_month}",
                color="Net Sales",
                color_continuous_scale="Teal",
                text="Net Sales",
            )
            fig_drill.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
            fig_drill.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_drill, use_container_width=True)

    # ── Tab 5: Insights ───────────────────────────────────────────────────────
    with tab_insights:
        st.markdown("#### Customer Segmentation — Repeat vs New")
        seg_df = customer_segmentation(df)

        repeat_count = (seg_df["Customer Type"] == "🔄 Repeat").sum()
        new_count = (seg_df["Customer Type"] == "🆕 New").sum()
        rc1, rc2 = st.columns(2)
        rc1.metric("🔄 Repeat Customers", repeat_count)
        rc2.metric("🆕 New Customers", new_count)

        fig_seg = px.bar(
            seg_df,
            x="Party Name",
            y="Total Net Sales",
            color="Customer Type",
            title="Customer Segmentation by Net Sales",
            labels={"Total Net Sales": "Taxable Value (₹)"},
            color_discrete_map={"🔄 Repeat": "#2ecc71", "🆕 New": "#e74c3c"},
        )
        fig_seg.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_seg, use_container_width=True)

        top_row = seg_df.iloc[0]
        st.info(
            f"🏆 **{top_row['Party Name']}** is the highest contributing debtor "
            f"with ₹{top_row['Total Net Sales']:,.0f} "
            f"({top_row['Share %']}% of total sales) across "
            f"{top_row['Active Months']} active month(s)."
        )

        st.markdown("#### Full Segmentation Table")
        st.dataframe(
            seg_df.style.format({"Total Net Sales": "₹{:,.0f}", "Share %": "{:.2f}%"}),
            use_container_width=True,
        )

        st.markdown("---")
        csv_full = df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Filtered Data (CSV)",
            data=csv_full,
            file_name="filtered_sales_data.csv",
            mime="text/csv",
        )

    # ── Tab 6: Data Preview ───────────────────────────────────────────────────
    with tab_data:
        st.markdown("#### 🗃️ Raw Data Preview")
        missing_gstin = df["GSTIN"].str.strip().eq("").sum() if "GSTIN" in df.columns else 0
        total_rows = len(df)
        dq1, dq2, dq3 = st.columns(3)
        dq1.metric("Total Rows", f"{total_rows:,}")
        dq2.metric("Missing GSTIN", f"{missing_gstin:,}")
        dq3.metric("Missing Dates", f"{df['Date'].isna().sum():,}")

        preview_cols = [
            c for c in [
                "Date", "Party Name", "Invoice Number", "VoucherNo",
                "GSTIN", "Debtor Type", "Net Sales", "Total GST",
                "Invoice Value", "GST Rate (%)", "State",
            ] if c in df.columns
        ]
        st.dataframe(df[preview_cols].head(100), use_container_width=True)


if __name__ == "__main__":
    main()
