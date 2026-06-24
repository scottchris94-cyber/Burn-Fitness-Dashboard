import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. Load Live Data & Generate Projections
# MAKE SURE your actual published CSV link is between the quotes below!
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
        "Non-Operating Expenses": 8095, # Base fixed debt for projections
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

if selected_month != "All Year to Date":
    view_df = df[df["Month"] == selected_month]
else:
    view_df = df

# 4. Main Header
st.title("Burn Fitness 2, LLC")
st.markdown("### Executive Financial Overview")
st.markdown("---")

# 5. Top KPI Row
col1, col2, col3, col4 = st.columns(4)
current_revenue = view_df["Total Income"].sum()
current_op_income = view_df["Operating Income"].sum()
current_cash = view_df["Remaining Cash"].sum()
avg_margin = view_df["Profit Margin (%)"].mean()

with col1:
    st.metric("Total Income", f"${current_revenue:,.2f}")
with col2:
    st.metric("Operating Income", f"${current_op_income:,.2f}")
with col3:
    st.metric("Net Cash Flow", f"${current_cash:,.2f}")
with col4:
    st.metric("Operating Profit Margin", f"{avg_margin:.1f}%")

st.markdown("---")

# 6. Detailed Charts Row (Full Width Cash Flow)
st.markdown("#### Operating Cash Flow (Revenue vs Expenses)")
fig_cash = go.Figure()

# Differentiate Actual vs Projected in the chart colors
colors_income = ["#2ecc71" if status == "Actual" else "#82e0aa" for status in df["Status"]]
colors_expense = ["#e74c3c" if status == "Actual" else "#f1948a" for status in df["Status"]]

fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Total Income"], name="Income", marker_color=colors_income))
fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Operating Expenses"], name="Op Expenses", marker_color=colors_expense))
fig_cash.update_layout(barmode='group', margin=dict(t=30, b=0, l=0, r=0))
st.plotly_chart(fig_cash, use_container_width=True)
st.caption("Darker bars indicate Actuals from Google Sheets. Lighter bars indicate Projected baselines.")

st.markdown("---")

# 7. Actionable Owner Metrics Row (Full Width Profit Drain)
st.markdown("### Critical Decision Metrics")
st.markdown("**The Profit Drain (Operating vs Non-Operating)**")
fig_drain = go.Figure()
fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Operating Income"], name="Operating Profit", marker_color="#27ae60"))
fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Non-Operating Expenses"], name="Debt/Draws Drain", marker_color="#c0392b"))
fig_drain.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0))
st.plotly_chart(fig_drain, use_container_width=True)
st.caption("Compares floor profitability to the cash leaving for owner draws and loans.")

# 8. Owner Distribution & Decision Guide
st.markdown("---")
st.markdown("### Owner Distribution & Decision Guide")
st.markdown("This section calculates the exact draw structure and cash reserve status based on the selected month's revenue.")

def calculate_waterfall(revenue):
    op_ex = 97450
    debt = 8095
    base_dufresne = 7500
    base_tushman = 5000
    reserve_cap = 2000
    dufresne_cap = 10000
    tushman_cap = 10000

    cash_after_fixed = revenue - op_ex - debt
    
    dufresne_actual = base_dufresne
    tushman_actual = base_tushman
    cash_after_base = cash_after_fixed - dufresne_actual - tushman_actual
    
    reserve_actual = 0
    if cash_after_base > 0:
        reserve_actual = min(cash_after_base, reserve_cap)
    cash_after_reserve = cash_after_base - reserve_actual
    
    if cash_after_reserve > 0:
        dufresne_extra = min(cash_after_reserve, dufresne_cap - base_dufresne)
        dufresne_actual += dufresne_extra
        cash_after_reserve -= dufresne_extra
        
    if cash_after_reserve > 0:
        tushman_extra = min(cash_after_reserve, tushman_cap - base_tushman)
        tushman_actual += tushman_extra
        cash_after_reserve -= tushman_extra
        
    surplus_deficit = cash_after_reserve
    
    if surplus_deficit < 0:
        if revenue >= 116000:
            status = "Alert: Almost breakeven. Deficit narrowing."
        else:
            status = "Alert: Both mins paid. Cash reserve absorbs loss."
    elif surplus_deficit == 0 and reserve_actual == 0:
        status = "Warning: Exact breakeven. Both at base mins."
    elif reserve_actual > 0 and reserve_actual < reserve_cap:
        status = "Good: Reserve building."
    elif reserve_actual == reserve_cap and dufresne_actual < dufresne_cap:
        status = "Good: DuFresne growing."
    elif dufresne_actual == dufresne_cap and tushman_actual < tushman_cap:
        status = "Good: Tushman growing."
    else:
        status = f"Excellent: Both capped. Surplus building (${surplus_deficit:,.0f})."
        
    return {
        "Revenue": revenue,
        "DuFresne": dufresne_actual,
        "Tushman": tushman_actual,
        "Reserve": reserve_actual,
        "Surplus/Deficit": surplus_deficit,
        "Decision": status
    }

# Apply to Current Month View
current_month_name = view_df["Month"].iloc[-1]
current_live_revenue = view_df["Total Income"].iloc[-1]
is_projected = view_df["Status"].iloc[-1]

waterfall_result = calculate_waterfall(current_live_revenue)

st.markdown(f"**Based on {current_month_name} Revenue ({is_projected}):** `${current_live_revenue:,.2f}`")

wf_col1, wf_col2, wf_col3 = st.columns(3)

with wf_col1:
    st.info(f"**DuFresne Draw:**\n\n${waterfall_result['DuFresne']:,.2f}")
with wf_col2:
    st.info(f"**Tushman Draw:**\n\n${waterfall_result['Tushman']:,.2f}")
with wf_col3:
    st.info(f"**Cash Reserve Added:**\n\n${waterfall_result['Reserve']:,.2f}")

if waterfall_result['Surplus/Deficit'] < 0:
    st.error(f"**Status:** {waterfall_result['Decision']} | **Deficit:** ${waterfall_result['Surplus/Deficit']:,.2f}")
elif waterfall_result['Surplus/Deficit'] > 0:
    st.success(f"**Status:** {waterfall_result['Decision']} | **Surplus:** ${waterfall_result['Surplus/Deficit']:,.2f}")
else:
    st.warning(f"**Status:** {waterfall_result['Decision']} | **Surplus/Deficit:** $0.00")

# 9. What-If Simulator
st.markdown("#### What-If Simulator")
st.caption("Adjust the slider to see how future revenue changes the distribution.")
sim_revenue = st.slider("Simulate Total Revenue:", min_value=100000, max_value=140000, value=int(current_live_revenue), step=1000)
sim_result = calculate_waterfall(sim_revenue)

st.write(f"If revenue hits **${sim_revenue:,.0f}**, the result is:")
st.markdown(f"> {sim_result['Decision']} | DuFresne: **${sim_result['DuFresne']:,.0f}** | Tushman: **${sim_result['Tushman']:,.0f}** | Reserve: **${sim_result['Reserve']:,.0f}**")

# 10. Raw Data Table Toggle
if st.checkbox("Show Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}",
        "Operating Expenses": "${:,.2f}",
        "Non-Operating Expenses": "${:,.2f}",
        "PT Revenue": "${:,.2f}",
        "Membership Dues": "${:,.2f}",
        "Remaining Cash": "${:,.2f}"
    }))
