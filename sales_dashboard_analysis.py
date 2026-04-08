"""
Detailed Sales Dashboard — Item-wise, HSN-wise & GST-wise Analysis
====================================================================
Uses Tally sales export data (or generated demo data) to provide
interactive item, HSN, and GST-level sales insights in a
CA-style professional presentation.

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

# ── Sample-data generator ─────────────────────────────────────────────────────

def generate_sample_data() -> pd.DataFrame:
    """Return realistic Tally item-level sales export as a DataFrame."""
    rng = np.random.default_rng(42)

    items = {
        "Steel Pipe 1-inch": ("7304", 18),
        "Steel Pipe 2-inch": ("7304", 18),
        "Copper Wire 1mm": ("7408", 18),
        "Copper Wire 2mm": ("7408", 18),
        "PVC Fittings": ("3917", 12),
        "Industrial Pump": ("8413", 18),
        "Electric Motor 5HP": ("8501", 18),
        "Circuit Breaker": ("8536", 18),
        "Safety Gloves": ("3926", 12),
        "Hard Hat": ("6506", 5),
        "Lubricating Oil": ("2710", 18),
        "Filter Element": ("8421", 18),
        "Gasket Set": ("8484", 18),
        "Valve 1/2 inch": ("8481", 18),
        "Bolt & Nut Kit": ("7318", 18),
    }
    parties = [
        "Alpha Constructions", "Beta Industries", "Gamma Pvt Ltd",
        "Delta Enterprises", "Epsilon Corp", "Zeta Traders",
        "Eta Manufacturing", "Theta Solutions",
    ]

    item_names = list(items.keys())

    rows = []
    invoice_no = 2001
    for month in range(1, 13):
        for _ in range(rng.integers(30, 60)):
            day = rng.integers(1, 29)
            item_name = item_names[rng.integers(len(item_names))]
            hsn, gst_rate = items[item_name]
            qty = int(rng.integers(1, 51))
            unit_price = float(rng.uniform(200, 15_000))
            taxable_value = round(qty * unit_price, 2)

            # Determine if inter-state (IGST) or intra-state (CGST + SGST)
            inter_state = bool(rng.integers(0, 2))
            gst_total = round(taxable_value * gst_rate / 100, 2)
            if inter_state:
                cgst = sgst = 0.0
                igst = gst_total
            else:
                cgst = sgst = round(gst_total / 2, 2)
                igst = 0.0

            rows.append({
                "Date": pd.Timestamp(f"2024-{month:02d}-{day:02d}"),
                "Invoice Number": f"TLY-{invoice_no:05d}",
                "Party Name": rng.choice(parties),
                "Item Name": item_name,
                "HSN Code": hsn,
                "Quantity": qty,
                "Taxable Value": taxable_value,
                "GST Rate (%)": gst_rate,
                "CGST Amount": cgst,
                "SGST Amount": sgst,
                "IGST Amount": igst,
            })
            invoice_no += 1

    return pd.DataFrame(rows)


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
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    # Time dimensions
    df["Month"] = df["Date"].dt.month
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year
    df["Month-Year"] = df["Date"].dt.to_period("M").astype(str)

    # Numeric coercion
    num_cols = [
        "Quantity", "Taxable Value", "GST Rate (%)",
        "CGST Amount", "SGST Amount", "IGST Amount",
    ]
    for col in num_cols:
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
    years = sorted(df["Year"].unique())
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
    gst_rates = sorted(df["GST Rate (%)"].unique())
    sel_gst = st.sidebar.multiselect(
        "GST Rate (%)", gst_rates, default=gst_rates
    )

    # Item
    items = sorted(df["Item Name"].unique())
    sel_items = st.sidebar.multiselect("Item", items, default=items)

    # HSN Code
    hsn_codes = sorted(df["HSN Code"].unique())
    sel_hsn = st.sidebar.multiselect("HSN Code", hsn_codes, default=hsn_codes)

    # Apply filters
    mask = (
        df["Year"].isin(sel_years)
        & df["Month"].isin(sel_month_nums)
        & df["GST Rate (%)"].isin(sel_gst)
        & df["Item Name"].isin(sel_items)
        & df["HSN Code"].isin(sel_hsn)
    )
    return df[mask].copy()


# ── KPI cards ─────────────────────────────────────────────────────────────────

def render_kpis(df: pd.DataFrame):
    """Render CA-style KPI metric cards."""
    total_sales = df["Taxable Value"].sum()
    total_gst = df["Total GST"].sum()
    avg_gst_rate = df["GST Rate (%)"].mean() if not df.empty else 0
    top_hsn_sales = df.groupby("HSN Code")["Taxable Value"].sum().max()
    top_hsn_pct = (top_hsn_sales / total_sales * 100) if total_sales else 0
    total_invoices = df["Invoice Number"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total Taxable Sales", f"₹{total_sales:,.0f}")
    c2.metric("🧾 Total GST Collected", f"₹{total_gst:,.0f}")
    c3.metric("📊 Avg GST Rate", f"{avg_gst_rate:.1f}%")
    c4.metric("🏆 Top HSN Share", f"{top_hsn_pct:.1f}%")
    c5.metric("📄 Total Invoices", f"{total_invoices:,}")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def chart_top_items(df: pd.DataFrame):
    """Horizontal bar chart of top items by taxable value."""
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
        title="📦 Top Items by Sales (Taxable Value)",
        labels={"Taxable Value": "Taxable Value (₹)", "Item Name": "Item"},
        color="Taxable Value",
        color_continuous_scale="Viridis",
        text="Taxable Value",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


def chart_hsn_sales(df: pd.DataFrame):
    """Bar chart of HSN-wise taxable sales."""
    hsn_df = (
        df.groupby("HSN Code")["Taxable Value"]
        .sum()
        .reset_index()
        .sort_values("Taxable Value", ascending=False)
    )
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


def chart_item_gst(df: pd.DataFrame):
    """Horizontal bar chart of top GST-generating items."""
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
        title="💸 Top GST-Generating Items",
        labels={"Total GST": "Total GST (₹)", "Item Name": "Item"},
        color="Total GST",
        color_continuous_scale="Oranges",
        text="Total GST",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


# ── Anomaly detection ─────────────────────────────────────────────────────────

def detect_gst_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """
    Identify rows where effective tax % deviates significantly from the
    declared GST Rate by more than `threshold` percentage points.
    """
    anom = df[
        (df["Taxable Value"] > 0)
        & (abs(df["Effective Tax %"] - df["GST Rate (%)"]) > threshold)
    ][
        [
            "Invoice Number", "Item Name", "HSN Code",
            "Taxable Value", "GST Rate (%)", "Total GST",
            "Effective Tax %", "Date",
        ]
    ].copy()
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
    tbl["GST %"] = tbl["Total_GST"] / tbl["Taxable_Value"] * 100
    tbl["GST %"] = tbl["GST %"].round(2)
    return tbl


# ── Main dashboard ────────────────────────────────────────────────────────────

def main():
    st.title("🧾 Sales & GST Analysis Dashboard")
    st.caption(
        "Item-wise • HSN-wise • GST-wise  |  CA-style Reporting  |  "
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
    tab_sales, tab_gst, tab_hsn, tab_anomaly, tab_export = st.tabs(
        ["📦 Sales Analysis", "🧾 GST Analysis", "🔢 HSN Analysis",
         "⚠️ Anomaly Detection", "📥 Export"]
    )

    # ── Tab 1: Sales Analysis ─────────────────────────────────────────────────
    with tab_sales:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_top_items(df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_gst_distribution(df), use_container_width=True)

        st.markdown("#### Item + HSN + GST Breakdown Table")
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

    # ── Tab 3: HSN Analysis ───────────────────────────────────────────────────
    with tab_hsn:
        st.plotly_chart(chart_hsn_sales(df), use_container_width=True)

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

        # Highlight top HSN
        top_hsn = hsn_detail.iloc[0]
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

    # ── Tab 4: Anomaly Detection ──────────────────────────────────────────────
    with tab_anomaly:
        st.markdown("#### ⚠️ GST Rate Anomalies")
        st.caption(
            "Rows where **Effective Tax %** deviates by more than 2 percentage "
            "points from the declared **GST Rate (%)** are flagged below."
        )
        threshold = st.slider(
            "Deviation threshold (percentage points)", 0.5, 10.0, 2.0, 0.5
        )
        anom_df = detect_gst_anomalies(df, threshold)

        if anom_df.empty:
            st.success("✅ No GST rate anomalies detected within the selected threshold.")
        else:
            st.warning(f"⚠️ {len(anom_df)} anomalous line item(s) detected.")
            st.dataframe(
                anom_df.style.format(
                    {
                        "Taxable Value": "₹{:,.0f}",
                        "Total GST": "₹{:,.0f}",
                        "Effective Tax %": "{:.2f}%",
                        "GST Rate (%)": "{:.0f}%",
                        "Deviation (pp)": "{:+.2f}",
                    }
                ),
                use_container_width=True,
            )
            csv_anom = anom_df.to_csv(index=False).encode()
            st.download_button(
                "⬇️ Download Anomalies (CSV)",
                data=csv_anom,
                file_name="gst_anomalies.csv",
                mime="text/csv",
            )

    # ── Tab 5: Export ─────────────────────────────────────────────────────────
    with tab_export:
        st.markdown("#### 📥 Export Filtered Data for Return Filing")
        st.caption(
            "Download filtered data as CSV for use in GST return preparation "
            "or further analysis in Excel."
        )

        # Summary export
        summary = item_hsn_gst_table(df)
        csv_summary = summary.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download HSN + Item Summary (CSV)",
            data=csv_summary,
            file_name="hsn_item_gst_summary.csv",
            mime="text/csv",
        )

        # Full line-item export
        export_cols = [
            "Date", "Invoice Number", "Party Name", "Item Name", "HSN Code",
            "Quantity", "Taxable Value", "GST Rate (%)",
            "CGST Amount", "SGST Amount", "IGST Amount", "Total GST",
            "Effective Tax %", "Month Name", "Year",
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
