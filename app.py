import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Dashboard", layout="wide", initial_sidebar_state="expanded")

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

# Try to load live data, fallback if empty
try:
    df_live = load_data(sheet_url)
    df_live["Status"] = "Actual"
except:
    df_live = pd.DataFrame()

# Generate the 12-Month Projected Budget Engine
all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
proj_data = []

for m in all_months:
    # Set alternating membership dues
    mem_dues = 55000 if m in ["Jan", "Mar", "Jun", "Oct"] else 45000
    misc_income = 4000
    target_revenue = 118000
    
    # PT Revenue is the difference required to hit 118k
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

# Merge Live Actuals with Future Projections
if not df_live.empty and "Month" in df_live.columns:
    actual_months = df_live["Month"].tolist()
    # Remove projected months if we already have actuals for them
    df_proj = df_proj[~df_proj["Month"].isin(actual_months)]
    df = pd.concat([df_live, df_proj], ignore_index=True)
else:
    df = df_proj

# Ensure strict chronological order for the charts
df["Month_Num"] = pd.Categorical(df["Month"], categories=all_months, ordered=True)
df = df.sort_values("Month_Num").drop(columns=["Month_Num"])

# Calculate dynamic columns
df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100

# 3. Sidebar Configuration
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter data by month for the owner review. Future months display projected targets.")
selected_month = st.sidebar.selectbox("Select Month", ["All Year to Date"] + df["Month"].tolist())

# Identify the current real-world month to exclude from YTD KPI calculations
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
st.markdown("---")

# 5. Top KPI Row
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

st.markdown("---")

# 6. Detailed Charts Row
st.markdown("#### Operating Cash Flow (Revenue vs Expenses)")
fig_cash = go.Figure()

colors_income = ["#2ecc71" if status == "Actual" else "#82e0aa" for status in df["Status"]]
colors_expense = ["#e74c3c" if status == "Actual" else "#f1948a" for status in df["Status"]]

fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Total Income"], name="Income", marker_color=colors_income))
fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Operating Expenses"], name="Op Expenses", marker_color=colors_expense))
fig_cash.update_layout(barmode='group', margin=dict(t=30, b=0, l=0, r=0))
st.plotly_chart(fig_cash, use_container_width=True)
st.caption("Darker bars indicate Actuals from Google Sheets. Lighter bars indicate Projected baselines.")

st.markdown("---")

# 7. Actionable Owner Metrics Row
st.markdown("### Critical Decision Metrics")
st.markdown("**The Profit Drain (Operating vs Non-Operating)**")
fig_drain = go.Figure()
fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Operating Income"], name="Operating Profit", marker_color="#27ae60"))
fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Non-Operating Expenses"], name="Debt/Draws Drain", marker_color="#c0392b"))
fig_drain.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0))
st.plotly_chart(fig_drain, use_container_width=True)
st.caption("Compares floor profitability to the cash leaving for owner draws and loans.")

# 8. Owner Distribution & Decision Guide (Editable Fields)
st.markdown("---")
st.markdown("### Owner Distribution & Decision Guide")
st.markdown("The fields below are populated with the suggested waterfall distribution based on the selected month's live revenue and operating expenses. You can edit these amounts to test custom scenarios and see how it impacts the final cash balance.")

current_month_name = view_df["Month"].iloc[-1]
current_live_revenue = view_df["Total Income"].iloc[-1]
current_live_opex = view_df["Operating Expenses"].iloc[-1]
is_projected = view_df["Status"].iloc[-1]
fixed_debt = 8095

# Calculate suggested baseline defaults
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

st.markdown(f"**Based on {current_month_name} Revenue ({is_projected}):** `${current_live_revenue:,.2f}` | **Operating Expenses:** `${current_live_opex:,.2f}`")

wf_col1, wf_col2, wf_col3 = st.columns(3)

with wf_col1:
    test_dufresne = st.number_input("DuFresne Draw", value=float(s_dufresne), step=500.0)
with wf_col2:
    test_tushman = st.number_input("Tushman Draw", value=float(s_tushman), step=500.0)
with wf_col3:
    test_reserve = st.number_input("Cash Reserve Added", value=float(s_reserve), step=500.0)

# Calculate final balance based on the user's manual inputs
final_balance = current_live_revenue - current_live_opex - fixed_debt - test_dufresne - test_tushman - test_reserve

if final_balance < 0:
    st.error(f"Status: Alert - This scenario results in a cash deficit. | Deficit: ${final_balance:,.2f}")
elif final_balance > 0:
    st.success(f"Status: Excellent - This scenario results in a retained surplus. | Surplus: ${final_balance:,.2f}")
else:
    st.warning(f"Status: Exact Breakeven. All cash allocated. | Remaining Balance: $0.00")

# 9. Raw Data Table Toggle
if st.checkbox("Show Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}",
        "Operating Expenses": "${:,.2f}",
        "Non-Operating Expenses": "${:,.2f}",
        "PT Revenue": "${:,.2f}",
        "Membership Dues": "${:,.2f}",
        "Remaining Cash": "${:,.2f}"
    }))
