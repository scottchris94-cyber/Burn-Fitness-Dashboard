import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Financials", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a clean, modern corporate feel
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 600; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# 2. Load Live Data & Generate Projections
# MAKE SURE your actual published CSV link is between the quotes below
sheet_url = "PASTE_YOUR_COPIED_LINK_HERE"

@st.cache_data(ttl=600)
def load_data(url):
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    
    numeric_cols = [
        "Total Income", "Operating Expenses", "Non-Operating Expenses", 
        "Remaining Cash", "PT Revenue", "Membership Dues", "Total Payroll",
        "Total Memberships", "Total Cancels", "Total EFT Gained", "Total EFT Lost", "MTD PT Revenue"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df = df.fillna(0)
    
    # Calculate derived financial columns natively for all rows (including YTD/AVG)
    if "Total Income" in df.columns and "Operating Expenses" in df.columns:
        df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
        df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100
        df["Profit Margin (%)"] = df["Profit Margin (%)"].fillna(0)
        
    return df

try:
    df_live_full = load_data(sheet_url)
    
    # Extract the user-defined YTD and AVG rows directly from Google Sheets
    ytd_row = df_live_full[df_live_full["Month"] == "YTD"].copy()
    avg_row = df_live_full[df_live_full["Month"] == "AVG"].copy()
    
    # Isolate strictly the actual chronological months for the main dataframe
    df_live = df_live_full[~df_live_full["Month"].isin(["YTD", "AVG"])].copy()
    df_live["Status"] = "Actual"
except:
    df_live = pd.DataFrame()
    ytd_row = pd.DataFrame()
    avg_row = pd.DataFrame()

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
        "Total Memberships": 0,
        "Total Cancels": 0,
        "Total EFT Gained": 0,
        "Total EFT Lost": 0,
        "MTD PT Revenue": 0,
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

# Ensure columns exist for the merged dataframe
if "Operating Income" not in df.columns:
    df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
    df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100

# 3. Sidebar Configuration
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter data by month for the owner review. Future months display projected targets.")

current_month_abbr = datetime.now().strftime("%b")
ytd_label = "Completed Year-to-Date (Excludes Active Month)"

selected_month = st.sidebar.selectbox("Select Month", [ytd_label] + df["Month"].tolist())

# Establish a strictly "Completed" dataframe for the distribution guide
completed_df = df[(df["Status"] == "Actual") & (df["Month"] != current_month_abbr)]

if selected_month == ytd_label:
    # We bypass view_df entirely for metrics and use the YTD row you built in Sheets
    is_ytd = True
    view_df = completed_df 
else:
    view_df = df[df["Month"] == selected_month]
    is_ytd = False

# 4. Main Header
st.title("Burn Fitness 2, LLC")

# 5. Top KPI Row (Executive Financial Overview)
st.markdown("### Executive Financial Overview")
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    
    if is_ytd:
        # Pull directly from your YTD row in Google Sheets
        current_revenue = ytd_row["Total Income"].values[0] if not ytd_row.empty else 0
        current_op_income = ytd_row["Operating Income"].values[0] if not ytd_row.empty else 0
        current_cash = ytd_row["Remaining Cash"].values[0] if not ytd_row.empty else 0
        avg_margin = f"{ytd_row['Profit Margin (%)'].values[0]:.1f}%" if not ytd_row.empty else "0.0%"
        
        margin_label = "Operating Margin (Completed YTD)"
        op_label = "Operating Income"
    elif selected_month == current_month_abbr:
        # Live active month
        current_revenue = view_df["Total Income"].sum()
        current_op_income = view_df["Operating Income"].sum()
        current_cash = view_df["Remaining Cash"].sum()
        avg_margin = "N/A (Active Month)"
        
        margin_label = "Operating Profit Margin"
        op_label = "Operating Income (Incomplete)"
    else:
        # Standard completed month
        current_revenue = view_df["Total Income"].sum()
        current_op_income = view_df["Operating Income"].sum()
        current_cash = view_df["Remaining Cash"].sum()
        avg_margin = f"{view_df['Profit Margin (%)'].mean():.1f}%"
        
        margin_label = "Operating Profit Margin"
        op_label = "Operating Income"

    with col1:
        st.metric("Total Income", f"${current_revenue:,.2f}")
    with col2:
        st.metric(op_label, f"${current_op_income:,.2f}")
    with col3:
        st.metric("Net Cash Flow", f"${current_cash:,.2f}")
    with col4:
        st.metric(margin_label, avg_margin)
        
if not is_ytd and selected_month == current_month_abbr:
    st.caption("*Net Cash Flow reflects MTD data and may include non-operating expenses pulled prior to full revenue collection.")
st.write("") 

# 6. Performance Snapshot
if is_ytd:
    st.markdown("### Completed YTD Performance Snapshot")
    st.markdown("Year-to-Date operational totals pulled directly from your Google Sheets feed.")
else:
    st.markdown("### Month-to-Date (MTD) Performance Snapshot")
    st.markdown("Real-time operational metrics compared to your custom historical average.")

with st.container(border=True):
    mtd_col1, mtd_col2, mtd_col3, mtd_col4, mtd_col5 = st.columns(5)
    
    if is_ytd:
        # Pull directly from your YTD row in Google Sheets
        mtd_members = ytd_row["Total Memberships"].values[0] if not ytd_row.empty else 0
        mtd_cancels = ytd_row["Total Cancels"].values[0] if not ytd_row.empty else 0
        mtd_eft_gain = ytd_row["Total EFT Gained"].values[0] if not ytd_row.empty else 0
        mtd_eft_lost = ytd_row["Total EFT Lost"].values[0] if not ytd_row.empty else 0
        mtd_pt_rev = ytd_row["MTD PT Revenue"].values[0] if not ytd_row.empty else 0
        
        str_d_members, str_d_cancels, str_d_eft_gain, str_d_eft_lost = None, None, None, None
        
    else:
        # Compare current selected month to your custom AVG row in Google Sheets
        avg_members = avg_row["Total Memberships"].values[0] if not avg_row.empty else 0
        avg_cancels = avg_row["Total Cancels"].values[0] if not avg_row.empty else 0
        avg_eft_gain = avg_row["Total EFT Gained"].values[0] if not avg_row.empty else 0
        avg_eft_lost = avg_row["Total EFT Lost"].values[0] if not avg_row.empty else 0

        mtd_members = view_df["Total Memberships"].iloc[-1] if "Total Memberships" in view_df.columns else 0
        mtd_cancels = view_df["Total Cancels"].iloc[-1] if "Total Cancels" in view_df.columns else 0
        mtd_eft_gain = view_df["Total EFT Gained"].iloc[-1] if "Total EFT Gained" in view_df.columns else 0
        mtd_eft_lost = view_df["Total EFT Lost"].iloc[-1] if "Total EFT Lost" in view_df.columns else 0
        mtd_pt_rev = view_df["MTD PT Revenue"].iloc[-1] if "MTD PT Revenue" in view_df.columns else 0

        d_members = mtd_members - avg_members
        d_cancels = mtd_cancels - avg_cancels
        d_eft_gain = mtd_eft_gain - avg_eft_gain
        d_eft_lost = mtd_eft_lost - avg_eft_lost

        str_d_members = f"{'+' if d_members >= 0 else ''}{d_members:,.0f} vs avg"
        str_d_cancels = f"{'+' if d_cancels >= 0 else ''}{d_cancels:,.0f} vs avg"
        str_d_eft_gain = f"{'+$' if d_eft_gain >= 0 else '-$'}{abs(d_eft_gain):,.2f} vs avg"
        str_d_eft_lost = f"{'+$' if d_eft_lost >= 0 else '-$'}{abs(d_eft_lost):,.2f} vs avg"

    with mtd_col1:
        st.metric("Total Memberships", f"{mtd_members:,.0f}", delta=str_d_members)
    with mtd_col2:
        st.metric("Total Cancels", f"{mtd_cancels:,.0f}", delta=str_d_cancels, delta_color="inverse")
    with mtd_col3:
        st.metric("EFT Gained", f"${mtd_eft_gain:,.2f}", delta=str_d_eft_gain)
    with mtd_col4:
        st.metric("EFT Lost", f"${mtd_eft_lost:,.2f}", delta=str_d_eft_lost, delta_color="inverse")
    with mtd_col5:
        st.metric("PT Revenue (New/Renewals)", f"${mtd_pt_rev:,.2f}")

st.write("") 

# 7. Owner Distribution & Decision Guide
st.markdown("### Owner Distribution & Decision Guide")

if is_ytd:
    st.markdown("*(Note: The decision guide calculates distributions for a single operational month. Below reflects your most recently completed month.)*")
    guide_df = completed_df
else:
    st.markdown("Review and adjust the baseline distribution scenarios based on live operating constraints.")
    guide_df = view_df

with st.container(border=True):
    current_month_name = guide_df["Month"].iloc[-1]
    current_live_revenue = guide_df["Total Income"].iloc[-1]
    current_live_opex = guide_df["Operating Expenses"].iloc[-1]
    is_projected = guide_df["Status"].iloc[-1]
    fixed_debt = 8095

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

st.write("") 

# 8. Financial Visualizations
st.markdown("### Financial Visualizations")

with st.container(border=True):
    st.markdown("**Annual Revenue vs. Expenses Trend**")
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Bar(
        x=df["Month"], y=df["Operating Expenses"], 
        name="Operating Expenses", 
        marker_color="#cbd5e1", 
        opacity=0.8
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["Month"], y=df["Total Income"], 
        name="Total Revenue", 
        mode='lines+markers',
        line=dict(color="#0f172a", width=3), 
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

st.write("")

# 9. Raw Data Table Toggle
with st.expander("View Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}",
        "Operating Expenses": "${:,.2f}",
        "Non-Operating Expenses": "${:,.2f}",
        "PT Revenue": "${:,.2f}",
        "Membership Dues": "${:,.2f}",
        "Remaining Cash": "${:,.2f}",
        "Total Memberships": "{:,.0f}",
        "Total Cancels": "{:,.0f}",
        "Total EFT Gained": "${:,.2f}",
        "Total EFT Lost": "${:,.2f}",
        "MTD PT Revenue": "${:,.2f}"
    }), use_container_width=True)
