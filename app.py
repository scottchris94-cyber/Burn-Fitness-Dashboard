import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Burn Fitness Overview", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for an aggressively consolidated, mobile-friendly UI
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 1rem; }
    
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 600; color: #1e293b; }
    h1 { font-size: 2rem !important; margin-bottom: 0.5rem !important; padding-bottom: 0.5rem !important; }
    h3 { font-size: 1.25rem !important; margin-top: 1rem !important; margin-bottom: 0.75rem !important; padding-bottom: 0rem !important; }
    
    div[data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #64748b !important; margin-bottom: -5px; }
    div[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
    
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Load Live Data & Generate Projections
# MAKE SURE your actual published CSV links are between the quotes below
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRHzA-fwBnL6URgQpHeM6ezWfk46qhlKwVgtBXm9vqJkRjOS9rXhngAE1VCbjyxhQ/pub?gid=237304684&single=true&output=csv"
trainer_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBh5tuhKZXYy3U-6jgWIVc6_V8TLOK0C-o4HDDeX8b7m1S_HBfngL-8Dttrdkycg/pub?gid=1523309006&single=true&output=csv"

@st.cache_data(ttl=60)
def fetch_live_data(url):
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    
    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str).str.strip()
    
    numeric_cols = [
        "Total Income", "Operating Expenses", "Non-Operating Expenses", "Remaining Cash", 
        "PT Revenue", "Membership Dues", "Total Payroll", "Total Memberships", 
        "Total Cancels", "Total EFT Gained", "Total EFT Lost", "MTD PT Revenue",
        "NMS", "PT Revenue Lost", "PT Intros Sold", "POS Referrals", "PFGs", "Retail Sold"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df = df.fillna(0)
    
    if "Total Income" in df.columns and "Operating Expenses" in df.columns:
        df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
        df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100
        df["Profit Margin (%)"] = df["Profit Margin (%)"].fillna(0)
        
    return df

try:
    df_live_full = fetch_live_data(sheet_url)
    
    ytd_row = df_live_full[df_live_full["Month"].str.upper() == "YTD"].copy()
    avg_row = df_live_full[df_live_full["Month"].str.upper() == "AVG"].copy()
    
    df_live = df_live_full[~df_live_full["Month"].str.upper().isin(["YTD", "AVG"])].copy()
    
    df_live = df_live[(df_live["Total Income"] != 0) | (df_live["Operating Expenses"] != 0)]
    df_live["Status"] = "Actual"
except:
    df_live = pd.DataFrame()
    ytd_row = pd.DataFrame()
    avg_row = pd.DataFrame()

all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
proj_data = []

for m in all_months:
    mem_dues = 55000 if m in ["Jan", "Mar", "Jun", "Oct"] else 45000
    misc_income = 4000
    target_revenue = 118000
    pt_revenue = target_revenue - mem_dues - misc_income
    
    proj_data.append({
        "Month": m, "Total Income": target_revenue, "Operating Expenses": 97450,
        "Non-Operating Expenses": 8095, "Remaining Cash": 0, "PT Revenue": pt_revenue,
        "Membership Dues": mem_dues, "Total Payroll": 0, "Total Memberships": 0,
        "Total Cancels": 0, "Total EFT Gained": 0, "Total EFT Lost": 0, "MTD PT Revenue": 0,
        "NMS": 0, "PT Revenue Lost": 0, "PT Intros Sold": 0, "POS Referrals": 0, 
        "PFGs": 0, "Retail Sold": 0, "Status": "Projected"
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

if "Operating Income" not in df.columns:
    df["Operating Income"] = df["Total Income"] - df["Operating Expenses"]
    df["Profit Margin (%)"] = (df["Operating Income"] / df["Total Income"]) * 100

# 3. Sidebar Configuration
try:
    st.sidebar.image("burnlogo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter data by month for the review.")

ytd_label = "Year-to-Date (YTD)"
selected_month = st.sidebar.selectbox("Select Month", [ytd_label] + df["Month"].tolist())

st.sidebar.markdown("---")
st.sidebar.markdown("### Facility Metrics")
# Dynamic ARPM variable tied directly to the UI
active_members = st.sidebar.number_input("Total Active Members (for ARPM)", value=1400, step=10)

actuals_df = df[df["Status"] == "Actual"]

if selected_month == ytd_label:
    is_ytd = True
    view_df = actuals_df 
else:
    view_df = df[df["Month"] == selected_month]
    is_ytd = False

# 4. Main Header
st.title("Burn Fitness Overview")

# --- SECTION 1: FINANCIAL PERFORMANCE ---
st.markdown("### Financial Performance")
with st.container(border=True):
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if is_ytd:
        current_revenue = actuals_df["Total Income"].sum()
        current_op_income = actuals_df["Operating Income"].sum()
        current_cash = actuals_df["Remaining Cash"].sum()
        avg_margin = f"{(current_op_income / current_revenue * 100):.1f}%" if current_revenue > 0 else "0.0%"
        
        margin_label = "Op Margin (YTD)"
        op_label = "Net Op Income"
        
        # ARPM YTD Logic: Calculate average monthly revenue, divide by live active member input
        months_count = len(actuals_df) if not actuals_df.empty else 1
        avg_monthly_rev = current_revenue / months_count
        current_arpm = avg_monthly_rev / active_members if active_members > 0 else 0
        
    else:
        current_revenue = view_df["Total Income"].sum()
        current_op_income = view_df["Operating Income"].sum()
        current_cash = view_df["Remaining Cash"].sum()
        
        if selected_month == datetime.now().strftime("%b"):
            avg_margin = "N/A"
            margin_label = "Op Margin"
            op_label = "Net Op Income (Inc)"
        else:
            avg_margin = f"{view_df['Profit Margin (%)'].mean():.1f}%" if not view_df.empty else "0.0%"
            margin_label = "Op Margin"
            op_label = "Net Op Income"
            
        # ARPM Single Month Logic
        current_arpm = current_revenue / active_members if active_members > 0 else 0

    # ARPM Baseline / Delta Logic
    avg_rev = avg_row["Total Income"].values[0] if not avg_row.empty and "Total Income" in avg_row.columns else 0
    avg_arpm = avg_rev / active_members if active_members > 0 else 0
    
    arpm_delta = current_arpm - avg_arpm if not is_ytd else None
    
    def fmt_arpm_delta(d_val):
        if d_val is None: return None
        prefix = "+$" if d_val >= 0 else "-$"
        return f"{prefix}{abs(d_val):,.2f} vs avg"

    with col1:
        st.metric("Total Revenue", f"${current_revenue:,.2f}")
    with col2:
        st.metric(op_label, f"${current_op_income:,.2f}")
    with col3:
        st.metric("Net Cash Flow", f"${current_cash:,.2f}")
    with col4:
        st.metric(margin_label, avg_margin)
    with col5:
        st.metric("ARPM", f"${current_arpm:,.2f}", delta=fmt_arpm_delta(arpm_delta))

# --- SECTION 2: MONTHLY PERFORMANCE ---
if is_ytd:
    st.markdown("### YTD Performance")
else:
    st.markdown("### Monthly Performance")

with st.container(border=True):
    def get_val(df_source, col_name, is_ytd_mode):
        if is_ytd_mode:
            return ytd_row[col_name].values[0] if not ytd_row.empty and col_name in ytd_row.columns else 0
        else:
            return df_source[col_name].iloc[-1] if not df_source.empty and col_name in df_source.columns else 0

    def get_avg(col_name):
        return avg_row[col_name].values[0] if not avg_row.empty and col_name in avg_row.columns else 0

    def calc_delta(val, avg):
        return val - avg if not is_ytd else None

    def fmt_delta(d_val, is_currency=False):
        if d_val is None: return None
        prefix = "+$" if is_currency and d_val >= 0 else "-$" if is_currency else "+" if d_val >= 0 else ""
        return f"{prefix}{abs(d_val):,.2f} vs avg" if is_currency else f"{prefix}{d_val:,.0f} vs avg"

    m_mem = get_val(view_df, "Total Memberships", is_ytd)
    m_can = get_val(view_df, "Total Cancels", is_ytd)
    m_eft_g = get_val(view_df, "Total EFT Gained", is_ytd)
    m_eft_l = get_val(view_df, "Total EFT Lost", is_ytd)
    m_nms = get_val(view_df, "NMS", is_ytd)
    
    m_pt_sold = get_val(view_df, "MTD PT Revenue", is_ytd)
    m_pt_lost = get_val(view_df, "PT Revenue Lost", is_ytd)
    m_pt_intro = get_val(view_df, "PT Intros Sold", is_ytd)
    m_pos = get_val(view_df, "POS Referrals", is_ytd)
    m_pfg = get_val(view_df, "PFGs", is_ytd)
    
    m_retail = get_val(view_df, "Retail Sold", is_ytd)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("New Memberships", f"{m_mem:,.0f}", delta=fmt_delta(calc_delta(m_mem, get_avg("Total Memberships"))))
    with col2: st.metric("Cancels", f"{m_can:,.0f}", delta=fmt_delta(calc_delta(m_can, get_avg("Total Cancels"))), delta_color="inverse")
    with col3: st.metric("EFT Gained", f"${m_eft_g:,.2f}", delta=fmt_delta(calc_delta(m_eft_g, get_avg("Total EFT Gained")), True))
    with col4: st.metric("EFT Lost", f"${m_eft_l:,.2f}", delta=fmt_delta(calc_delta(m_eft_l, get_avg("Total EFT Lost")), True), delta_color="inverse")
    with col5: st.metric("NMS", f"${m_nms:,.2f}", delta=fmt_delta(calc_delta(m_nms, get_avg("NMS")), True))

    col6, col7, col8, col9, col10 = st.columns(5)
    with col6: st.metric("PT Sold", f"${m_pt_sold:,.2f}", delta=fmt_delta(calc_delta(m_pt_sold, get_avg("MTD PT Revenue")), True))
    with col7: st.metric("PT Lost", f"${m_pt_lost:,.2f}", delta=fmt_delta(calc_delta(m_pt_lost, get_avg("PT Revenue Lost")), True), delta_color="inverse")
    with col8: st.metric("Intros Sold", f"{m_pt_intro:,.0f}", delta=fmt_delta(calc_delta(m_pt_intro, get_avg("PT Intros Sold"))))
    with col9: st.metric("POS Referrals", f"{m_pos:,.0f}", delta=fmt_delta(calc_delta(m_pos, get_avg("POS Referrals"))))
    with col10: st.metric("PFGs", f"{m_pfg:,.0f}", delta=fmt_delta(calc_delta(m_pfg, get_avg("PFGs"))))

    col11, col12, col13, col14, col15 = st.columns(5)
    with col11: st.metric("Retail Sold", f"${m_retail:,.2f}", delta=fmt_delta(calc_delta(m_retail, get_avg("Retail Sold")), True))

# --- SECTION 3: TRAINER MONTHLY TOTALS ---
st.markdown("### Trainer Monthly Totals")
with st.container(border=True):
    try:
        if trainer_sheet_url == "PASTE_YOUR_TRAINER_CSV_LINK_HERE":
            st.info("Awaiting Trainer Data. Paste your secondary CSV link into the code to activate this module.")
        else:
            df_trainers = pd.read_csv(trainer_sheet_url, header=1)
            
            if "Unnamed: 0" in df_trainers.columns:
                df_trainers = df_trainers.rename(columns={"Unnamed: 0": "Month"})
            
            cols_to_hide = ["Unnamed: 16", "Unnamed: 17", "Unnamed: 18"]
            df_trainers = df_trainers.drop(columns=[c for c in cols_to_hide if c in df_trainers.columns])
            
            df_trainers = df_trainers.head(15)
            df_trainers = df_trainers.dropna(how='all')
            
            st.dataframe(df_trainers.fillna(""), use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.warning("Could not load Trainer Data. Please ensure the Google Sheet tab is published as a CSV and the link is correct.")


# --- SECTION 4: OWNER ACCESS ONLY (SECURED) ---
st.markdown("### Owner Access Only")

# The Security Gate
pin_input = st.text_input("Enter 4-Digit Owner PIN to unlock this section:", type="password")

# CHANGE "1234" TO YOUR DESIRED PIN BEFORE COMMITTING
if pin_input == "1234": 

    if is_ytd:
        guide_df = actuals_df
    else:
        guide_df = view_df

    with st.container(border=True):
        if not guide_df.empty:
            current_month_name = guide_df["Month"].iloc[-1]
            current_live_revenue = guide_df["Total Income"].iloc[-1]
            current_live_opex = guide_df["Operating Expenses"].iloc[-1]
            is_projected = guide_df["Status"].iloc[-1]
        else:
            current_month_name = "N/A"
            current_live_revenue = 0.0
            current_live_opex = 0.0
            is_projected = "No Data"
            
        fixed_debt = 8095
        
        st.markdown(f"**Distribution Scenario Basis: {current_month_name} ({is_projected})**")

        rev_col, opex_col, debt_col = st.columns(3)
        with rev_col:
            test_revenue = st.number_input("Projected Total Revenue", value=float(current_live_revenue), step=1000.0)
        with opex_col:
            st.metric("Live OpEx", f"${current_live_opex:,.2f}")
        with debt_col:
            st.metric("Fixed Debt", f"${fixed_debt:,.2f}")

        cash_after_fixed = test_revenue - current_live_opex - fixed_debt
        s_dufresne = 7500
        s_tushman = 0  
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
            t_extra = min(cash_after_reserve, 10000)
            s_tushman += t_extra
            cash_after_reserve -= t_extra
        
        wf_col1, wf_col2, wf_col3 = st.columns(3)

        with wf_col1:
            safe_dufresne_start = max(float(s_dufresne), 7500.0)
            test_dufresne = st.number_input("DuFresne Draw (Min $7,500)", value=safe_dufresne_start, min_value=7500.0, step=500.0)
        with wf_col2:
            test_tushman = st.number_input("Tushman Draw", value=float(s_tushman), step=500.0)
        with wf_col3:
            test_reserve = st.number_input("Cash Reserve Added", value=float(s_reserve), step=500.0)

        final_balance = test_revenue - current_live_opex - fixed_debt - test_dufresne - test_tushman - test_reserve

        if final_balance < 0:
            st.error(f"WARNING: This scenario results in a cash deficit of ${abs(final_balance):,.2f}.")
        elif final_balance > 0:
            st.success(f"APPROVED: This scenario results in a retained surplus of ${final_balance:,.2f}.")
        else:
            st.info(f"BREAKEVEN: All cash accurately allocated. Remaining balance is $0.00.")

        st.markdown("---")
        
        # --- CASH RUNWAY CALCULATOR ---
        st.markdown("**Cumulative Cash Runway**")
        st.caption("Input your total banked cash to instantly calculate your operational runway against live OpEx.")
        
        runway_col1, runway_col2 = st.columns(2)
        
        default_bank_cash = max(float(actuals_df["Remaining Cash"].sum()), 0.0)
        
        with runway_col1:
            total_banked_cash = st.number_input("Total Banked Cash Balance", value=default_bank_cash, step=1000.0)
            
        runway_months = total_banked_cash / current_live_opex if current_live_opex > 0 else 0
        
        with runway_col2:
            st.metric("Months of OpEx Funded", f"{runway_months:.1f} Months")
            
        if runway_months < 1.0:
            st.error("Caution: Less than 1 month of operating expenses held in reserve.")
        elif runway_months < 2.0:
            st.warning("Stable: Between 1 to 2 months of operating expenses held in reserve.")
        else:
            st.success("Healthy: Over 2 months of operating expenses fully funded in reserve.")

elif pin_input != "":
    st.error("Incorrect PIN. Access Denied.")

# 8. Raw Data Table Toggle
with st.expander("View Raw Financial Data"):
    st.dataframe(df.style.format({
        "Total Income": "${:,.2f}", "Operating Expenses": "${:,.2f}", "Non-Operating Expenses": "${:,.2f}",
        "PT Revenue": "${:,.2f}", "Membership Dues": "${:,.2f}", "Remaining Cash": "${:,.2f}",
        "Total Memberships": "{:,.0f}", "Total Cancels": "{:,.0f}", "Total EFT Gained": "${:,.2f}",
        "Total EFT Lost": "${:,.2f}", "MTD PT Revenue": "${:,.2f}", "NMS": "${:,.2f}", 
        "PT Revenue Lost": "${:,.2f}", "PT Intros Sold": "{:,.0f}", "POS Referrals": "{:,.0f}",
        "PFGs": "{:,.0f}", "Retail Sold": "${:,.2f}"
    }), use_container_width=True)
