"""
Monthly Sales Dashboard with Debtor-wise Analysis
====================================================
Uses Tally sales export data (or generated demo data) to provide
interactive monthly and debtor-level sales insights.

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

# ── Sample-data generator ─────────────────────────────────────────────────────

def generate_sample_data() -> pd.DataFrame:
    """Return a realistic Tally-style sales export as a DataFrame."""
    rng = np.random.default_rng(42)

    debtors = [
        "ABC Traders", "XYZ Enterprises", "Delta Corp", "Sigma Solutions",
        "Prime Distributors", "Global Merchants", "Sunrise Industries",
        "Metro Supplies", "Apex Trading Co.", "Blue Star Pvt Ltd",
        "Zenith Exports", "Vertex Holdings",
    ]
    states = [
        "Maharashtra", "Gujarat", "Rajasthan", "Delhi",
        "Karnataka", "Tamil Nadu", "West Bengal", "Uttar Pradesh",
    ]

    rows = []
    invoice_no = 1001
    for month in range(1, 13):                          # Jan–Dec 2024
        n_invoices = rng.integers(25, 55)
        for _ in range(n_invoices):
            day = rng.integers(1, 29)
            debtor = rng.choice(debtors)
            state = rng.choice(states)
            sales_amount = round(float(rng.uniform(5_000, 200_000)), 2)
            gst_rate = rng.choice([5, 12, 18, 28])
            gst_amount = round(sales_amount * gst_rate / 100, 2)
            rows.append({
                "Date": pd.Timestamp(f"2024-{month:02d}-{day:02d}"),
                "Party Name": debtor,
                "Invoice Number": f"INV-{invoice_no:05d}",
                "Sales Amount": sales_amount,
                "GST Amount": gst_amount,
                "State": state,
            })
            invoice_no += 1

    return pd.DataFrame(rows)


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

    # Parse dates robustly
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    # Derived time columns
    df["Month"] = df["Date"].dt.month
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year
    df["Month-Year"] = df["Date"].dt.to_period("M").astype(str)

    # Net Sales (exclude GST when available)
    if "GST Amount" in df.columns:
        df["Net Sales"] = df["Sales Amount"] - df["GST Amount"].fillna(0)
    else:
        df["Net Sales"] = df["Sales Amount"]

    # Ensure numeric
    for col in ["Sales Amount", "Net Sales"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

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

    # Year filter (if multi-year data exists)
    years = sorted(df["Year"].unique())
    selected_years = st.sidebar.multiselect("Year", years, default=years)

    # Month filter
    month_opts = (
        df[df["Year"].isin(selected_years)]
        .sort_values("Month")[["Month", "Month Name"]]
        .drop_duplicates()
    )
    month_labels = month_opts["Month Name"].tolist()
    selected_months = st.sidebar.multiselect(
        "Month", month_labels, default=month_labels
    )
    selected_month_nums = month_opts[
        month_opts["Month Name"].isin(selected_months)
    ]["Month"].tolist()

    # Debtor filter
    debtors = sorted(df["Party Name"].unique())
    selected_debtors = st.sidebar.multiselect(
        "Debtor (Party Name)", debtors, default=debtors
    )

    # State filter
    if "State" in df.columns:
        states = sorted(df["State"].dropna().unique())
        selected_states = st.sidebar.multiselect("State", states, default=states)
    else:
        selected_states = []

    # Apply filters
    mask = (
        df["Year"].isin(selected_years)
        & df["Month"].isin(selected_month_nums)
        & df["Party Name"].isin(selected_debtors)
    )
    if selected_states:
        mask &= df["State"].isin(selected_states)

    return df[mask].copy()


# ── KPI cards ─────────────────────────────────────────────────────────────────

def render_kpis(df: pd.DataFrame):
    """Display top-level KPI metric cards."""
    total_sales = df["Net Sales"].sum()
    active_debtors = df["Party Name"].nunique()
    top_debtor_sales = df.groupby("Party Name")["Net Sales"].sum().max()
    top_pct = (top_debtor_sales / total_sales * 100) if total_sales else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Net Sales", f"₹{total_sales:,.0f}")
    c2.metric("👥 Active Debtors", f"{active_debtors}")
    c3.metric("🏆 Top Debtor Sales", f"₹{top_debtor_sales:,.0f}")
    c4.metric("📈 Top Debtor Share", f"{top_pct:.1f}%")


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
        title="🏆 Top 10 Debtors by Net Sales",
        labels={"Net Sales": "Net Sales (₹)", "Party Name": "Debtor"},
        color="Net Sales",
        color_continuous_scale="Blues",
        text="Net Sales",
    )
    fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return fig


def chart_monthly_trend(df: pd.DataFrame):
    """Line chart of monthly net sales trend."""
    monthly = (
        df.groupby(["Year", "Month", "Month Name"])["Net Sales"]
        .sum()
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly["Period"] = monthly["Month Name"] + " " + monthly["Year"].astype(str)
    fig = px.line(
        monthly,
        x="Period",
        y="Net Sales",
        markers=True,
        title="📅 Monthly Sales Trend",
        labels={"Net Sales": "Net Sales (₹)", "Period": "Month"},
        color_discrete_sequence=["#1f77b4"],
    )
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_layout(xaxis_tickangle=-45)
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
    # Keep a consistent calendar order for columns
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
        labels={"color": "Net Sales (₹)"},
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Debtor",
        coloraxis_colorbar_title="₹",
    )
    return fig


def chart_state_sales(df: pd.DataFrame):
    """Pie chart of sales contribution by state."""
    if "State" not in df.columns:
        return None
    state_df = df.groupby("State")["Net Sales"].sum().reset_index()
    fig = px.pie(
        state_df,
        names="State",
        values="Net Sales",
        title="🗺️ Sales by State",
        hole=0.35,
    )
    fig.update_traces(textinfo="percent+label")
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


# ── Main dashboard ────────────────────────────────────────────────────────────

def main():
    st.title("📊 Monthly Sales Dashboard — Debtor-wise Analysis")
    st.caption("Powered by Tally Sales Export  •  Built with Streamlit + Plotly")

    # Load & filter data
    df = render_sidebar(pd.DataFrame())   # first call to show file-upload widget
    if df.empty:
        st.warning("No data available for the selected filters. Please adjust your selections.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("### Key Performance Indicators")
    render_kpis(df)
    st.markdown("---")

    # ── Tabs for drill-down ───────────────────────────────────────────────────
    tab_overview, tab_debtor, tab_trends, tab_insights = st.tabs(
        ["📋 Overview", "👤 Debtor Analysis", "📅 Trends", "💡 Insights"]
    )

    # ── Tab 1: Overview ───────────────────────────────────────────────────────
    with tab_overview:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_top10_debtors(df), use_container_width=True)
        with col2:
            state_fig = chart_state_sales(df)
            if state_fig:
                st.plotly_chart(state_fig, use_container_width=True)

        st.markdown("#### Debtor-wise Monthly Breakdown")
        pivot_df = debtor_monthly_table(df)
        st.dataframe(
            pivot_df.style.format(
                {c: "₹{:,.0f}" for c in pivot_df.columns if c != "Party Name"}
            ),
            use_container_width=True,
            height=350,
        )
        # Download button
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
                Total_Net_Sales=("Net Sales", "sum"),
                Invoices=("Invoice Number", "nunique"),
                Active_Months=("Month", "nunique"),
            )
            .sort_values("Total_Net_Sales", ascending=False)
            .reset_index()
        )
        debtor_sum["Avg per Month"] = (
            debtor_sum["Total_Net_Sales"] / debtor_sum["Active_Months"]
        ).round(2)
        st.dataframe(
            debtor_sum.style.format(
                {"Total_Net_Sales": "₹{:,.0f}", "Avg per Month": "₹{:,.0f}"}
            ),
            use_container_width=True,
            height=350,
        )

    # ── Tab 3: Trends ─────────────────────────────────────────────────────────
    with tab_trends:
        st.plotly_chart(chart_monthly_trend(df), use_container_width=True)

        # Drill-down: Year → Month
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
                labels={"Net Sales": "Net Sales (₹)"},
            )
            fig_ym.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_ym, use_container_width=True)

        # Drill-down: Month → Debtor
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
            fig_drill.update_traces(
                texttemplate="₹%{x:,.0f}", textposition="outside"
            )
            fig_drill.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_drill, use_container_width=True)

    # ── Tab 4: Insights ───────────────────────────────────────────────────────
    with tab_insights:
        st.markdown("#### Customer Segmentation — Repeat vs New")
        seg_df = customer_segmentation(df)

        # Summary counts
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
            labels={"Total Net Sales": "Net Sales (₹)"},
            color_discrete_map={"🔄 Repeat": "#2ecc71", "🆕 New": "#e74c3c"},
        )
        fig_seg.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_seg, use_container_width=True)

        # Top contributor highlight
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

        # Download full filtered dataset
        st.markdown("---")
        csv_full = df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Filtered Data (CSV)",
            data=csv_full,
            file_name="filtered_sales_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
