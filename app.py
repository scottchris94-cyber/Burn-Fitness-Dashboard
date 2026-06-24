import streamlit as st
import pandas as pd
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
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRHzA-fwBnL6URgQpHeM6ezWfk46qhlKwVgtBXm9vqJkRjOS9rXhngAE1VCbjyxhQ/pub?gid=237304684&single=true&output=csv"

@st.cache_data(ttl=60)
def fetch_live_data(url):
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    
    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str).str.strip()
    
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

# Generate the 12-Month Projected Budget Engine
all_months = ["Jan", "Feb", "Mar", "Apr", "May",
