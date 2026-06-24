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
