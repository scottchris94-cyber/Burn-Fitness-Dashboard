import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Financials", layout="wide", initial_sidebar_state="expanded")

# Custom CSS to force a cleaner, modern look
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 600; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# 2. Load Live Data & Generate Projections
# MAKE SURE your actual published CSV link is between the quotes below
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRHzA-fwBnL6URgQpHeM6ezWfk46qhlKwVgtBXm9vqJkRjOS9rXhngAE1VCbjyxhQ/pub?gid=237304684&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data(url):
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    
    numeric_cols = [
        "Total Income", "Operating Expenses", "Non-Operating Expenses", 
        "Remaining Cash", "PT Revenue", "Membership Dues", "Total Payroll"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df = df.fillna(0)
    return df

try:
    df_live = load_data(sheet_url)
    df_live["Status"] = "Actual"
except:
    df_live = pd.DataFrame()

# Generate the 12-Month Projected Budget Engine
all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
proj_data = []

for m in all_months:
    mem_dues = 55000 if m in ["Jan", "Mar", "Jun", "Oct"] else 45000
    misc_income = 4000
    target_revenue = 118000
    pt_revenue = target_revenue - mem_dues - misc_income
    
    proj_data.append({
        "Month": m,
        "Total Income": target_revenue,
        "Operating Expenses": 97450,
        "Non-Operating Expenses": 8095, 
        "Remaining Cash": 0,
        "PT Revenue": pt_revenue,
        "Membership Dues": mem_dues,
        "Total Payroll": 0, 
        "Status": "Projected"
    })

df_proj = pd.DataFrame(proj_data)

if not df_live.empty and "Month" in df_live.columns:
    actual_months = df_live["Month"].tolist()
    df_proj = df_proj[~df_proj["Month"].isin(actual_months)]
    df = pd.concat([df_live, df_proj], ignore_index=True)
else:
    df = df_proj

df["Month_Num"] = pd.Categorical(df["Month"], categories=all_months, ordered=True)
df = df.sort_values("Month_Num").drop(columns=["Month_Num"])

df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100

# 3. Sidebar Configuration
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter data by month for the owner review. Future months display projected targets.")
selected_month = st.sidebar.selectbox("Select Month", ["All Year to Date"] + df["Month"].tolist())

current_month_abbr = datetime.now().strftime("%b")

if selected_month != "All Year to Date":
    view_df = df[df["Month"] == selected_month]
    kpi_df = view_df  
else:
    view_df = df
    kpi_df = df[(df["Status"] == "Actual") & (df["Month"] != current_month_abbr)]

# 4. Main Header
st.title("Burn Fitness 2, LLC")
st.markdown("### Executive Financial Overview")

# 5. Top KPI Row (Modern Card Design)
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    current_revenue = kpi_df["Total Income"].sum()
    current_op_income = kpi_df["Operating Income"].sum()
    current_cash = kpi_df["Remaining Cash"].sum()
    avg_margin = kpi_df["Profit Margin (%)"].mean()

    with col1:
        st.metric("Total Income (YTD Completed)", f"${current_revenue:,.2f}")
    with col2:
        st.metric("Operating Income", f"${current_op_income:,.2f}")
    with col3:
        st.metric("Net Cash Flow", f"${current_cash:,.2f}")
    with col4:
        st.metric("Operating Profit Margin", f"{avg_margin:.1f}%")

st.write("") # Spacing

# 6. Owner Distribution & Decision Guide (Moved Up)
st.markdown("### Owner Distribution & Decision Guide")
st.markdown("Review and adjust the baseline distribution scenarios based on live operating constraints.")

with st.container(border=True):
    current_month_name = view_df["Month"].iloc[-1]
    current_live_revenue = view_df["Total Income"].iloc[-1]
    current_live_opex = view_df["Operating Expenses"].iloc[-1]
    is_projected = view_df["Status"].iloc[-1]
    fixed_debt = 8095

    # Baseline Calculations
    cash_after_fixed = current_live_revenue - current_live_opex - fixed_debt
    s_dufresne = 7500
    s_tushman = 5000
    cash_after_base = cash_after_fixed - s_dufresne - s_tushman

    s_reserve = 0
    if cash_after_base > 0:
        s_reserve = min(cash_after_base, 2000)
    cash_after_reserve = cash_after_base - s_reserve

    if cash_after_reserve > 0:
        d_extra = min(cash_after_reserve, 2500)
        s_dufresne += d_extra
        cash_after_reserve -= d_extra
        
    if cash_after_reserve > 0:
        t_extra = min(cash_after_reserve, 5000)
        s_tushman += t_extra
        cash_after_reserve -= t_extra

    st.markdown(f"**Scenario Basis: {current_month_name} ({is_projected})** | Revenue: `${current_live_revenue:,.2f}` | OpEx: `${current_live_opex:,.2f}`")
    
    wf_col1, wf_col2, wf_col3 = st.columns(3)

    with wf_col1:
        # Hardcoded minimum value to ensure DuFresne never drops below 7500
        safe_dufresne_start = max(float(s_dufresne), 7500.0)
        test_dufresne = st.number_input("DuFresne Draw (Min $7,500)", value=safe_dufresne_start, min_value=7500.0, step=500.0)
    with wf_col2:
        test_tushman = st.number_input("Tushman Draw", value=float(s_tushman), step=500.0)
    with wf_col3:
        test_reserve = st.number_input("Cash Reserve Added", value=float(s_reserve), step=500.0)

    final_balance = current_live_revenue - current_live_opex - fixed_debt - test_dufresne - test_tushman - test_reserve

    if final_balance < 0:
        st.error(f"WARNING: This scenario results in a cash deficit of ${abs(final_balance):,.2f}.")
    elif final_balance > 0:
        st.success(f"APPROVED: This scenario results in a retained surplus of ${final_balance:,.2f}.")
    else:
        st.info(f"BREAKEVEN: All cash accurately allocated. Remaining balance is $0.00.")

st.write("") # Spacing

# 7. Modern Financial Charts
st.markdown("### Financial Visualizations")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Annual Revenue vs. Expenses Trend**")
    fig_trend = go.Figure()
    
    # Modern styling: Clean bars for OpEx, sleek line for Revenue
    fig_trend.add_trace(go.Bar(
        x=df["Month"], y=df["Operating Expenses"], 
        name="Operating Expenses", 
        marker_color="#cbd5e1", # Sleek slate gray
        opacity=0.8
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["Month"], y=df["Total Income"], 
        name="Total Revenue", 
        mode='lines+markers',
        line=dict(color="#0f172a", width=3), # Deep corporate navy
        marker=dict(size=8)
    ))
    
    fig_trend.update_layout(
        template="plotly_white",
        margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with chart_col2:
    st.markdown(f"**Monthly Cash Flow Waterfall ({current_month_name})**")
    
    # Highly professional waterfall chart to visualize the selected month's exact cash flow
    fig_waterfall = go.Figure(go.Waterfall(
        name="20", orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["Revenue", "OpEx", "Debt", "DuFresne", "Tushman", "Reserve", "Final Balance"],
        y=[
            current_live_revenue, 
            -current_live_opex, 
            -fixed_debt, 
            -test_dufresne, 
            -test_tushman, 
            -test_reserve, 
            final_balance
        ],
        connector={"line":{"color":"#cbd5e1"}},
        decreasing={"marker":{"color":"#ef4444"}}, # Professional red
        increasing={"marker":{"color":"#10b981"}}, # Professional green
        totals={"marker":{"color":"#3b82f6"}}      # Professional blue
    ))
    
    fig_waterfall.update_layout(
        template="plotly_white",
        margin=dict(t=10, b=10, l=0, r=0),
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

st.write("")

# 8. Raw Data Table Toggle
with st.expander("View Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}",
        "Operating Expenses": "${:,.2f}",
        "Non-Operating Expenses": "${:,.2f}",
        "PT Revenue": "${:,.2f}",
        "Membership Dues": "${:,.2f}",
        "Remaining Cash": "${:,.2f}"
    }), use_container_width=True)
