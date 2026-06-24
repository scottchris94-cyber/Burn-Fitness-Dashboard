import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. Load Data (Pre-loaded with Jan-Jun 2026 Data)
# To connect to your live sheet later, you would replace this block with:
# df = pd.read_excel('burn_fitness_data.xlsx')
data = {
    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "Total Income": [110871.94, 112839.05, 122855.63, 107871.29, 110694.36, 115760.00],
    "Operating Expenses": [94581.30, 90146.02, 97590.52, 99132.24, 93203.16, 90920.67],
    "Non-Operating Expenses": [21944.74, 24881.77, 26988.25, 16265.47, 15090.44, 12193.53],
    "Remaining Cash": [-5654.10, -2188.74, -1723.14, -7526.42, 2400.76, 12645.80],
    "PT Revenue": [48710.46, 65556.46, 63330.42, 58805.00, 62700.00, 60000.00],
    "Membership Dues": [45278.72, 45321.84, 55726.22, 46193.01, 45449.61, 55000.00],
    "Total Payroll": [44502.02, 47093.69, 46759.14, 57595.85, 51282.91, 53052.51]
}
df = pd.DataFrame(data)

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
