"""
Retail Sales Performance Dashboard  |  Streamlit version
=========================================================
Interactive web version of the Power BI dashboard built for the
"Data Visualization: Turning Retail Sales Data into a Visual Story" project.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Data file (keep it in the same folder as app.py, or in a /data sub-folder):
    Cleaned_retail_customer_sales_dataset.xlsx   (or Retail_Sales_Analysis_Ready.csv)
"""

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page setup and design tokens (same palette as the Power BI dashboard)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Retail Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",
)

GOLD, TEAL, DARK, BROWN, SAND, PAPER = (
    "#D1AE4B", "#416870", "#2F4E56", "#A65F3C", "#E6D199", "#F8F6F0",
)
SEGMENT_COLORS = {"Consumer": TEAL, "Corporate": GOLD, "Home Office": BROWN}
CATEGORY_COLORS = [TEAL, GOLD, BROWN, DARK, SAND]
GITHUB_URL = "https://github.com/eshasharma-ai/retail-sales-data-visualization"

DATA_CANDIDATES = [
    "Cleaned_retail_customer_sales_dataset.xlsx",
    "data/Cleaned_retail_customer_sales_dataset.xlsx",
    "Retail_Sales_Analysis_Ready.csv",
    "data/Retail_Sales_Analysis_Ready.csv",
]

# Newer Streamlit versions use width="stretch"; older ones use use_container_width.
_STRETCH_PLOT = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.plotly_chart).parameters
    else {"use_container_width": True}
)
_STRETCH_DF = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.dataframe).parameters
    else {"use_container_width": True}
)

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {PAPER}; }}
    h1 {{ font-weight: 800; letter-spacing: -0.5px; }}
    .kpi {{ border: 1px solid {SAND}; border-radius: 10px; overflow: hidden;
            text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
    .kpi .value {{ background: #FAF8F2; padding: 18px 6px 10px 6px; font-size: 2.0rem;
                    font-weight: 800; color: #9C7C2E; }}
    .kpi .label {{ padding: 12px 6px; color: white; font-weight: 800; font-size: 1.15rem; }}
    .kpi.gold .label {{ background: #9C7C2E; }}
    .kpi.teal .label {{ background: {DARK}; }}
    .kpi.teal .value {{ color: {DARK}; }}
    .insight {{ background: #EEF3FA; border-left: 4px solid #2E74B5; padding: 8px 12px;
                border-radius: 4px; margin-bottom: 18px; font-size: 0.93rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def inr(value: float) -> str:
    """Format a rupee amount compactly: ₹76.73M, ₹10.96K, ₹950."""
    if abs(value) >= 1e6:
        return f"₹{value / 1e6:,.2f}M"
    if abs(value) >= 1e3:
        return f"₹{value / 1e3:,.2f}K"
    return f"₹{value:,.0f}"


def insight(text: str) -> None:
    st.markdown(f'<div class="insight"><b>Insight:</b> {text}</div>', unsafe_allow_html=True)


def show(fig: go.Figure) -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=60, b=10),
        title_font=dict(size=17),
    )
    st.plotly_chart(fig, **_STRETCH_PLOT)


def add_trend_line(fig: go.Figure, x: pd.Series, y: pd.Series) -> go.Figure:
    """Overlay a straight least-squares trend line on a scatter plot."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) > 2:
        slope, intercept = np.polyfit(d["x"], d["y"], 1)
        xs = np.array([d["x"].min(), d["x"].max()])
        fig.add_trace(
            go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Trend line",
                    line=dict(color=BROWN, width=3))
        )
    return fig


def find_data_file():
    here = Path(__file__).resolve().parent
    for name in DATA_CANDIDATES:
        path = here / name
        if path.exists():
            return path
    return None


@st.cache_data(show_spinner="Loading data...")
def load_data(source) -> pd.DataFrame:
    """Load the dataset from a path or an uploaded file and add date helper columns."""
    name = getattr(source, "name", str(source))
    df = pd.read_csv(source) if str(name).lower().endswith(".csv") else pd.read_excel(source)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df["Delivery_Date"] = pd.to_datetime(df["Delivery_Date"], errors="coerce")
    df["Year"] = df["Order_Date"].dt.year
    df["Month_Start"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    df["Is_Returned"] = df["Returned"].astype(str).str.strip().str.lower().eq("yes")
    return df


# --------------------------------------------------------------------------
# Load data (repo file first, upload as fallback)
# --------------------------------------------------------------------------
st.title("Retail Sales Performance Dashboard")
st.caption("Retail transactions across four regions of India, 2023-2024")

data_path = find_data_file()
if data_path is not None:
    data = load_data(data_path)
else:
    st.warning(
        "Dataset not found next to app.py. Upload "
        "`Cleaned_retail_customer_sales_dataset.xlsx` (or the CSV version) to continue."
    )
    uploaded = st.file_uploader("Upload the dataset", type=["xlsx", "csv"])
    if uploaded is None:
        st.stop()
    data = load_data(uploaded)

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.header("Filters")
years = sorted(data["Year"].dropna().astype(int).unique())
regions = sorted(data["Region"].dropna().unique())
categories = sorted(data["Product_Category"].dropna().unique())
segments = sorted(data["Customer_Segment"].dropna().unique())

sel_years = st.sidebar.multiselect("Year", years, default=years)
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)
sel_categories = st.sidebar.multiselect("Product Category", categories, default=categories)
sel_segments = st.sidebar.multiselect("Customer Segment", segments, default=segments)
st.sidebar.caption("Clear a filter's selections and add them back to reset it.")

df = data[
    data["Year"].isin(sel_years)
    & data["Region"].isin(sel_regions)
    & data["Product_Category"].isin(sel_categories)
    & data["Customer_Segment"].isin(sel_segments)
].copy()

if df.empty:
    st.warning("No transactions match the current filters. Please widen your selection.")
    st.stop()

# --------------------------------------------------------------------------
# KPI cards
# --------------------------------------------------------------------------
total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
profit_margin = total_profit / total_sales * 100 if total_sales else 0.0
avg_order_value = df.groupby("Transaction_ID")["Sales"].sum().mean()

kpis = [
    ("gold", inr(total_sales), "Total Sales"),
    ("gold", inr(total_profit), "Total Profit"),
    ("teal", f"{profit_margin:.2f}%", "Profit Margin"),
    ("teal", inr(avg_order_value), "Average Order Value"),
]
for col, (tone, value, label) in zip(st.columns(4), kpis):
    col.markdown(
        f'<div class="kpi {tone}"><div class="value">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
m1, m2, m3 = st.columns(3)
m1.metric("Transactions", f"{df['Transaction_ID'].nunique():,}")
m2.metric("Return rate", f"{df['Is_Returned'].mean() * 100:.1f}%")
m3.metric("Average customer rating", f"{df['Customer_Rating'].mean():.2f} / 5")
st.write("")

tab_overview, tab_customers, tab_relations, tab_experience, tab_data = st.tabs(
    ["Overview", "Customers", "Relationships", "Experience", "Data"]
)

# --------------------------------------------------------------------------
# TAB 1: Overview (mirrors the Power BI page)
# --------------------------------------------------------------------------
with tab_overview:
    monthly = df.groupby("Month_Start", as_index=False)["Sales"].sum()
    fig = px.line(monthly, x="Month_Start", y="Sales", markers=True,
                title="Monthly Sales Trend", labels={"Month_Start": "Month", "Sales": "Sales (₹)"})
    fig.update_traces(line_color=TEAL, marker_color=TEAL)
    show(fig)
    peak, low = monthly.loc[monthly["Sales"].idxmax()], monthly.loc[monthly["Sales"].idxmin()]
    insight(
        f"Sales peak in {peak['Month_Start']:%b %Y} at {inr(peak['Sales'])} and dip in "
        f"{low['Month_Start']:%b %Y} at {inr(low['Sales'])}; monthly sales average "
        f"{inr(monthly['Sales'].mean())}."
    )

    left, right = st.columns(2)
    with left:
        by_region = df.groupby("Region")["Sales"].sum().sort_values()
        colors = [GOLD if r == by_region.index[0] else TEAL for r in by_region.index]
        fig = go.Figure(go.Bar(x=by_region.index, y=by_region.values, marker_color=colors,
                            text=[inr(v) for v in by_region.values], textposition="outside"))
        fig.update_layout(title=f"Sales by Region: {by_region.index[0]} Lowest",
                        yaxis_title="Sales (₹)", xaxis_title="Region")
        show(fig)
    with right:
        by_segment = df.groupby("Customer_Segment", as_index=False)["Sales"].sum()
        fig = px.pie(by_segment, names="Customer_Segment", values="Sales", hole=0.45,
                    color="Customer_Segment", color_discrete_map=SEGMENT_COLORS,
                    title="Sales Share by Customer Segment")
        fig.update_traces(textinfo="label+percent")
        show(fig)

    top_region, bottom_region = by_region.index[-1], by_region.index[0]
    gap = (by_region.iloc[-1] - by_region.iloc[0]) / by_region.iloc[0] * 100 if by_region.iloc[0] else 0
    insight(
        f"{top_region} leads regional sales and {bottom_region} trails by about {gap:.0f}%, "
        "which makes the lowest region the first candidate for targeted promotion."
    )

    st.subheader("Category Scorecard")
    score = (
        df.groupby("Product_Category")
        .agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum"),
            Return_Rate=("Is_Returned", "mean"))
        .sort_values("Total_Sales")
    )
    score["Profit_Margin"] = score["Total_Profit"] / score["Total_Sales"] * 100
    score["Return_Rate"] = score["Return_Rate"] * 100
    cats = list(score.index)
    score.loc["Total"] = [total_sales, total_profit, df["Is_Returned"].mean() * 100, profit_margin]
    score = score[["Total_Sales", "Total_Profit", "Profit_Margin", "Return_Rate"]]
    score.columns = ["Total Sales", "Total Profit", "Profit Margin", "Return Rate"]
    score.index.name = "Product Category"

    styled = (
        score.style
        .format({"Total Sales": lambda v: inr(v), "Total Profit": lambda v: inr(v),
                "Profit Margin": "{:.2f}%", "Return Rate": "{:.1f}%"})
        .bar(subset=pd.IndexSlice[cats, ["Total Sales"]], color=SAND)
        .bar(subset=pd.IndexSlice[cats, ["Return Rate"]], color="#9AD9F5")
    )
    st.dataframe(styled, **_STRETCH_DF)

# --------------------------------------------------------------------------
# TAB 2: Customers
# --------------------------------------------------------------------------
with tab_customers:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x="Age", nbins=15, title="Customer Age Distribution",
                        labels={"Age": "Customer Age (Years)"}, color_discrete_sequence=[TEAL])
        fig.update_layout(yaxis_title="Number of Records", bargap=0.05)
        fig.add_vline(x=df["Age"].median(), line_dash="dash", line_color=BROWN,
                    annotation_text=f"Median {df['Age'].median():.0f}")
        show(fig)
        insight(
            f"Customers average {df['Age'].mean():.1f} years (median {df['Age'].median():.0f}); "
            f"the skewness of {df['Age'].skew():.2f} means the shape is close to symmetric."
        )
    with c2:
        fig = px.histogram(df, x="Income", nbins=40, title="Customer Income Distribution",
                        labels={"Income": "Customer Income (₹)"}, color_discrete_sequence=[GOLD])
        fig.update_layout(yaxis_title="Number of Records", bargap=0.05)
        fig.add_vline(x=df["Income"].median(), line_dash="dash", line_color=TEAL,
                    annotation_text=f"Median {inr(df['Income'].median())}")
        show(fig)
        insight(
            f"Income is right-skewed (skewness {df['Income'].skew():.1f}): the median "
            f"{inr(df['Income'].median())} sits below the mean {inr(df['Income'].mean())} because a few "
            "very high earners stretch the tail."
        )

    by_cat = df.groupby("Product_Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    fig = px.bar(by_cat, x="Product_Category", y="Sales", text=by_cat["Sales"].map(inr),
                title="Total Sales by Product Category", color_discrete_sequence=[TEAL],
                labels={"Product_Category": "Product Category", "Sales": "Sales (₹)"})
    fig.update_traces(textposition="outside")
    show(fig)
    top2 = by_cat["Sales"].head(2).sum() / by_cat["Sales"].sum() * 100
    insight(
        f"{by_cat.iloc[0]['Product_Category']} and {by_cat.iloc[1]['Product_Category']} together "
        f"generate {top2:.0f}% of revenue in the current selection."
    )

# --------------------------------------------------------------------------
# TAB 3: Relationships
# --------------------------------------------------------------------------
with tab_relations:
    fig = px.box(df, x="Product_Category", y="Sales", color="Product_Category",
                color_discrete_sequence=CATEGORY_COLORS, title="Sales Distribution by Product Category",
                labels={"Product_Category": "Product Category", "Sales": "Sales (₹)"})
    fig.update_layout(showlegend=False)
    show(fig)
    insight("Boxes show the typical order range per category; dots are unusually large orders. "
            "Furniture and Electronics have the widest spread and the biggest outliers.")

    s1, s2 = st.columns(2)
    with s1:
        fig = px.scatter(df, x="Sales", y="Profit", opacity=0.35, title="Sales vs Profit",
                        labels={"Sales": "Sales (₹)", "Profit": "Profit (₹)"},
                        color_discrete_sequence=[TEAL])
        show(add_trend_line(fig, df["Sales"], df["Profit"]))
        insight(f"Correlation {df['Sales'].corr(df['Profit']):.2f}: profit rises almost in step with sales.")
    with s2:
        fig = px.scatter(df, x="Discount", y="Profit", opacity=0.35, title="Discount vs Profit",
                        labels={"Profit": "Profit (₹)"}, color_discrete_sequence=[GOLD])
        show(add_trend_line(fig, df["Discount"], df["Profit"]))
        insight(f"Correlation {df['Discount'].corr(df['Profit']):.2f}: higher discounts go with "
                "slightly lower profit per transaction.")

    h1, h2 = st.columns(2)
    with h1:
        cols = ["Sales", "Profit", "Discount", "Quantity", "Age", "Income"]
        corr = df[cols].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        title="Correlation Heatmap of Numerical Variables")
        show(fig)
    with h2:
        pivot = df.pivot_table(values="Sales", index="Product_Category", columns="Region", aggfunc="mean")
        fig = px.imshow(pivot, text_auto=".0f", color_continuous_scale="YlGnBu",
                        title="Average Sales by Product Category and Region",
                        labels={"color": "Avg Sales (₹)"})
        show(fig)
    insight("Category drives order value far more than region, and age or income barely relate to spending.")

# --------------------------------------------------------------------------
# TAB 4: Experience
# --------------------------------------------------------------------------
with tab_experience:
    e1, e2 = st.columns(2)
    with e1:
        order = ["Low", "Medium", "High"]
        sat = df["Satisfaction_Level"].value_counts().reindex(order).fillna(0)
        fig = go.Figure(go.Bar(x=sat.index, y=sat.values, marker_color=[BROWN, SAND, TEAL],
                            text=sat.values.astype(int), textposition="outside"))
        fig.update_layout(title="Customer Satisfaction Level Distribution",
                        xaxis_title="Satisfaction Level", yaxis_title="Number of Records")
        show(fig)
        low_share = sat["Low"] / sat.sum() * 100 if sat.sum() else 0
        insight(f"{low_share:.1f}% of customers who recorded a level are Low satisfaction.")
    with e2:
        ret = df["Is_Returned"].map({True: "Returned", False: "Kept"}).value_counts()
        fig = px.pie(values=ret.values, names=ret.index, hole=0.5, title="Product Return Status",
                    color=ret.index, color_discrete_map={"Kept": TEAL, "Returned": BROWN})
        show(fig)
        insight(f"{df['Is_Returned'].mean() * 100:.1f}% of orders were returned "
                f"({int(df['Is_Returned'].sum()):,} of {len(df):,}).")

    rr = (df.groupby("Product_Category")["Is_Returned"].mean() * 100).sort_values(ascending=False)
    fig = px.bar(x=rr.index, y=rr.values, text=[f"{v:.1f}%" for v in rr.values],
                title="Return Rate by Product Category", color_discrete_sequence=[TEAL],
                labels={"x": "Product Category", "y": "Return Rate (%)"})
    fig.update_traces(textposition="outside")
    show(fig)
    insight(f"{rr.index[0]} has the highest return rate ({rr.iloc[0]:.1f}%); "
            f"{rr.index[-1]} has the lowest ({rr.iloc[-1]:.1f}%).")

# --------------------------------------------------------------------------
# TAB 5: Data
# --------------------------------------------------------------------------
with tab_data:
    st.write(f"Showing **{len(df):,}** of {len(data):,} transactions after filtering.")
    st.dataframe(df.drop(columns=["Month_Start", "Is_Returned"]).head(500), **_STRETCH_DF)
    st.download_button(
        "Download filtered data (CSV)",
        df.drop(columns=["Month_Start", "Is_Returned"]).to_csv(index=False).encode("utf-8"),
        file_name="filtered_retail_sales.csv",
        mime="text/csv",
    )

st.divider()
st.caption(f"Built by Esha Sharma  |  Source code: {GITHUB_URL}")