import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. Load Data from Google Sheets
# MAKE SURE your actual published CSV link is between the quotes below!
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRHzA-fwBnL6URgQpHeM6ezWfk46qhlKwVgtBXm9vqJkRjOS9rXhngAE1VCbjyxhQ/pub?gid=237304684&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data(url):
    df = pd.read_csv(url)
    
    # Drop any blank rows that Google Sheets accidentally exported
    df = df.dropna(how='all')
    
    # List of financial columns that need to be cleaned
    numeric_cols = [
        "Total Income", "Operating Expenses", "Non-Operating Expenses", 
        "Remaining Cash", "PT Revenue", "Membership Dues", "Total Payroll"
    ]
    
    # Strip out dollar signs and commas, then convert to numbers
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Fill any empty cells with 0 so math doesn't break
    df = df.fillna(0)
            
    return df

df = load_data(sheet_url)

# Calculate dynamic columns
df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100
df["PT to Payroll Ratio"] = df["PT Revenue"] / df["Total Payroll"]

# 3. Sidebar Configuration
st.sidebar.title("⚙️ Dashboard Controls")
st.sidebar.markdown("Filter data by month for the owner review.")
selected_month = st.sidebar.selectbox("Select Month", ["All Year to Date"] + df["Month"].tolist())

if selected_month != "All Year to Date":
    view_df = df[df["Month"] == selected_month]
else:
    view_df = df

# 4. Main Header
st.title("🔥 Burn Fitness 2, LLC")
st.markdown("### Executive Financial Overview")
st.markdown("---")

# 5. Top KPI Row (High-Level Owner View)
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
    st.metric("Net Cash Flow", f"${current_cash:,.2f}", 
              delta="Target Positive" if current_cash > 0 else "Burn Warning", 
              delta_color="normal" if current_cash > 0 else "inverse")
with col4:
    st.metric("Operating Profit Margin", f"{avg_margin:.1f}%")

st.markdown("---")

# 6. Detailed Charts Row
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 📈 Operating Cash Flow (Revenue vs Expenses)")
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Total Income"], name="Income", marker_color="#2ecc71"))
    fig_cash.add_trace(go.Bar(x=df["Month"], y=df["Operating Expenses"], name="Op Expenses", marker_color="#e74c3c"))
    fig_cash.update_layout(barmode='group', margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_cash, use_container_width=True)

with right_col:
    st.markdown("#### 💰 Revenue Breakdown")
    # Taking average of the period for the pie chart
    pie_data = {
        "Category": ["Personal Training", "Membership Dues", "Other Income"],
        "Amount": [
            view_df["PT Revenue"].sum(),
            view_df["Membership Dues"].sum(),
            view_df["Total Income"].sum() - view_df["PT Revenue"].sum() - view_df["Membership Dues"].sum()
        ]
    }
    fig_pie = px.pie(pie_data, values="Amount", names="Category", hole=0.4, 
                     color_discrete_sequence=["#3498db", "#9b59b6", "#95a5a6"])
    fig_pie.update_layout(margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# 7. Actionable Owner Metrics Row
st.markdown("### 🔍 Critical Decision Metrics")
metric_col1, metric_col2 = st.columns(2)

with metric_col1:
    st.markdown("**PT to Payroll Health Ratio** *(Target > 1.1)*")
    fig_ratio = px.line(df, x="Month", y="PT to Payroll Ratio", markers=True)
    fig_ratio.add_hline(y=1.1, line_dash="dot", line_color="red", annotation_text="Danger Zone")
    fig_ratio.update_layout(height=250, margin=dict(t=10, b=0, l=0, r=0))
    st.plotly_chart(fig_ratio, use_container_width=True)
    st.caption("Measures if PT revenue is sufficiently covering total company payroll.")

with metric_col2:
    st.markdown("**The Profit Drain (Operating vs Non-Operating)**")
    fig_drain = go.Figure()
    fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Operating Income"], name="Operating Profit", marker_color="#27ae60"))
    fig_drain.add_trace(go.Bar(x=df["Month"], y=df["Non-Operating Expenses"], name="Debt/Draws Drain", marker_color="#c0392b"))
    fig_drain.update_layout(height=250, margin=dict(t=10, b=0, l=0, r=0))
    st.plotly_chart(fig_drain, use_container_width=True)
    st.caption("Compares floor profitability to the cash leaving for owner draws and loans.")

# 8. Raw Data Table Toggle
if st.checkbox("Show Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}",
        "Operating Expenses": "${:,.2f}",
        "Non-Operating Expenses": "${:,.2f}",
        "Remaining Cash": "${:,.2f}"
    }))
# --- ADD THIS TO THE VERY BOTTOM OF app.py ---

st.markdown("---")
st.markdown("### 🏛️ Owner Distribution & Decision Guide")
st.markdown("This section calculates the exact draw structure and cash reserve status based on the selected month's live revenue.")

# 1. Define the Waterfall Logic
def calculate_waterfall(revenue):
    # Hardcoded fixed obligations based on your table
    op_ex = 97450
    debt = 8095
    
    # Base minimum draws
    base_dufresne = 7500
    base_tushman = 5000
    
    # Caps
    reserve_cap = 2000
    dufresne_cap = 10000
    tushman_cap = 10000

    # Step 1: Pay OpEx and Debt
    cash_after_fixed = revenue - op_ex - debt
    
    # Step 2: Pay Base Draws (even if it causes a deficit, per the table)
    dufresne_actual = base_dufresne
    tushman_actual = base_tushman
    cash_after_base = cash_after_fixed - dufresne_actual - tushman_actual
    
    # Step 3: Fund Reserve (up to $2k cap)
    reserve_actual = 0
    if cash_after_base > 0:
        reserve_actual = min(cash_after_base, reserve_cap)
    cash_after_reserve = cash_after_base - reserve_actual
    
    # Step 4: Grow DuFresne (up to $10k cap)
    if cash_after_reserve > 0:
        dufresne_extra = min(cash_after_reserve, dufresne_cap - base_dufresne)
        dufresne_actual += dufresne_extra
        cash_after_reserve -= dufresne_extra
        
    # Step 5: Grow Tushman (up to $10k cap)
    if cash_after_reserve > 0:
        tushman_extra = min(cash_after_reserve, tushman_cap - base_tushman)
        tushman_actual += tushman_extra
        cash_after_reserve -= tushman_extra
        
    # Step 6: Remaining is Surplus/Deficit
    surplus_deficit = cash_after_reserve
    
    # Determine Status
    if surplus_deficit < 0:
        if revenue >= 116000:
            status = "🟡 Almost breakeven. Deficit narrowing."
        else:
            status = "🔴 Both mins paid. Cash reserve absorbs loss."
    elif surplus_deficit == 0 and reserve_actual == 0:
        status = "🟡 Exact breakeven. Both at base mins."
    elif reserve_actual > 0 and reserve_actual < reserve_cap:
        status = "🟢 Reserve building."
    elif reserve_actual == reserve_cap and dufresne_actual < dufresne_cap:
        status = "🟢 DuFresne growing."
    elif dufresne_actual == dufresne_cap and tushman_actual < tushman_cap:
        status = "🟢 Tushman growing."
    else:
        status = f"✅ Both capped. Surplus building (${surplus_deficit:,.0f})."
        
    return {
        "Revenue": revenue,
        "OpEx": op_ex,
        "Debt": debt,
        "DuFresne": dufresne_actual,
        "Tushman": tushman_actual,
        "Reserve": reserve_actual,
        "Surplus/Deficit": surplus_deficit,
        "Decision": status
    }

# 2. Apply to Current Month
# We use the most recent month's revenue from the filtered view_df
current_month_name = view_df["Month"].iloc[-1]
current_live_revenue = view_df["Total Income"].iloc[-1]

waterfall_result = calculate_waterfall(current_live_revenue)

# 3. Display the Output
st.markdown(f"**Based on {current_month_name} Revenue:** `${current_live_revenue:,.2f}`")

# Create a clean layout for the waterfall
wf_col1, wf_col2, wf_col3 = st.columns(3)

with wf_col1:
    st.info(f"**DuFresne Draw:**\n\n${waterfall_result['DuFresne']:,.2f}")
with wf_col2:
    st.info(f"**Tushman Draw:**\n\n${waterfall_result['Tushman']:,.2f}")
with wf_col3:
    st.info(f"**Cash Reserve Added:**\n\n${waterfall_result['Reserve']:,.2f}")

# Display Status and Deficit/Surplus
if waterfall_result['Surplus/Deficit'] < 0:
    st.error(f"**Status:** {waterfall_result['Decision']} | **Deficit:** ${waterfall_result['Surplus/Deficit']:,.2f}")
elif waterfall_result['Surplus/Deficit'] > 0:
    st.success(f"**Status:** {waterfall_result['Decision']} | **Surplus:** ${waterfall_result['Surplus/Deficit']:,.2f}")
else:
    st.warning(f"**Status:** {waterfall_result['Decision']} | **Surplus/Deficit:** $0.00")

# 4. Optional: "What-If" Calculator
st.markdown("#### 🧮 What-If Simulator")
st.caption("Adjust the slider to see how future revenue changes the distribution.")
sim_revenue = st.slider("Simulate Total Revenue:", min_value=100000, max_value=140000, value=int(current_live_revenue), step=1000)

sim_result = calculate_waterfall(sim_revenue)

st.write(f"If revenue hits **${sim_revenue:,.0f}**, the result is:")
st.markdown(f"> {sim_result['Decision']} | DuFresne: **${sim_result['DuFresne']:,.0f}** | Tushman: **${sim_result['Tushman']:,.0f}** | Reserve: **${sim_result['Reserve']:,.0f}**")
