import io
import json
import re
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import requests
import streamlit as st
import yfinance as yf

# Page Setup
st.set_page_config(
    page_title="PRO STOCK TERMINAL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# 1. THEME ENGINE (LIGHT, DARK, SYSTEM)
# -------------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "light"  # options: light, dark, system
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "Single stock terminal"

current_theme = st.session_state["theme_mode"]

# Styling Variables
if current_theme == "dark":
    app_bg = "linear-gradient(rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.96)), url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1920&q=80')"
    card_bg = "#1e293b"
    card_border = "#334155"
    text_main = "#f8fafc"
    text_sub = "#94a3b8"
    banner_bg = "linear-gradient(135deg, #78350f 0%, #b45309 100%)"
    banner_border = "#92400e"
    plotly_template = "plotly_dark"
elif current_theme == "system":
    # Balanced Glassmorphic Mode
    app_bg = "linear-gradient(rgba(30, 41, 59, 0.88), rgba(15, 23, 42, 0.92)), url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1920&q=80')"
    card_bg = "rgba(30, 41, 59, 0.85)"
    card_border = "#475569"
    text_main = "#f1f5f9"
    text_sub = "#cbd5e1"
    banner_bg = "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)"
    banner_border = "#1d4ed8"
    plotly_template = "plotly_dark"
else:
    # Light Theme
    app_bg = "linear-gradient(rgba(248, 250, 252, 0.90), rgba(241, 245, 249, 0.93)), url('https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1920&q=80')"
    card_bg = "#ffffff"
    card_border = "#cbd5e1"
    text_main = "#0f172a"
    text_sub = "#64748b"
    banner_bg = "linear-gradient(135deg, #b45309 0%, #d97706 100%)"
    banner_border = "#92400e"
    plotly_template = "plotly_white"

st.markdown(
    f"""
<style>
    .stApp {{
        background: {app_bg} no-repeat center center fixed !important;
        background-size: cover !important;
        color: {text_main} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }}

    .center-banner {{
        background: {banner_bg};
        border: 2px solid {banner_border};
        padding: 8px 16px;
        text-align: center;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 12px;
    }}
    .center-banner h1 {{
        font-size: 1.55rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        margin: 0 !important;
        letter-spacing: 0.5px;
    }}
    .center-banner p {{
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #fef3c7 !important;
        margin: 2px 0 0 0 !important;
    }}

    .content-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: {text_main} !important;
    }}

    .wireframe-box {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        color: {text_main} !important;
    }}

    .link-list a {{
        color: #2563eb !important;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.88rem;
        display: block;
        padding: 4px 0;
    }}
    .link-list a:hover {{
        color: #1d4ed8 !important;
        text-decoration: underline;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 2. NSE & BSE COMPLETE INDICES DATABASE
# -------------------------------------------------------------
INDEX_STOCK_POOLS = {
    # NSE Broad Indices
    "NSE: NIFTY 50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "SBIN",
        "LT", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS",
        "NTPC", "ONGC", "KOTAKBANK", "TITAN", "AXISBANK", "POWERGRID", "TATASTEEL", "COALINDIA",
        "BAJAJFINSV", "ASIANPAINT", "M&M", "ULTRACEMCO", "JSWSTEEL", "TECHM", "WIPRO",
        "NESTLEIND", "HINDALCO", "ADANIPORTS", "ADANIENT", "SBILIFE", "BAJAJ-AUTO", "DRREDDY",
        "CIPLA", "DIVISLAB", "APOLLOHOSP", "EICHERMOT", "BRITANNIA", "SHRIRAMFIN", "TRENT",
        "BEL", "BPCL", "TATACONSUM", "HEROMOTOCO", "GRASIM", "LTIM"
    ],
    "NSE: NIFTY NEXT 50": [
        "ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "ATGL", "AMBUJACEM", "BANKBARODA",
        "BERGEPAINT", "BOSCHLTD", "CANBK", "CHOLAFIN", "COLPAL", "DLF", "GAIL", "GODREJCP",
        "HAL", "HAVELLS", "ICICIGI", "ICICIPRULI", "IOC", "IRCTC", "IRFC", "JINDALSTEL",
        "JIOFIN", "LICI", "MARICO", "PIDILITIND", "PFC", "PNB", "RECLTD", "SIEMENS", "SRF",
        "TATAPOWER", "TORNTPHARM", "TVSMOTOR", "VBL", "VEDL", "ZOMATO", "ZYDUSLIFE"
    ],
    "NSE: NIFTY MIDCAP 100": [
        "ASHOKLEY", "ASTRAL", "AUROPHARMA", "BALKRISIND", "BATAINDIA", "BHARATFORG", "BHEL",
        "COFORGE", "CONCOR", "CUMMINSIND", "DIXON", "ESCORTS", "FEDERALBNK", "GMRINFRA",
        "HINDPETRO", "IDFCFIRSTB", "INDHOTEL", "JUBLFOOD", "LUPIN", "MFSL", "MPHASIS",
        "OBEROIRLTY", "PERSISTENT", "POLYCAB", "SAIL", "SUNDARMFIN", "SUPREMEIND", "VOLTAS"
    ],
    "NSE: NIFTY SMALLCAP 100": [
        "AMBER", "ANGELONE", "BSOFT", "CANFINHOME", "CENTURYPLY", "CESC", "CLEAN", "CREDITACC",
        "CYIENT", "DEVYANI", "EIDPARRY", "FORTIS", "GLENMARK", "HAPPSTMNDS", "JBCHEPHARM",
        "KAYNES", "KEC", "LATENTVIEW", "MEDANTA", "RADICO", "RBLBANK", "SONACOMS", "TRITURBINE"
    ],
    # NSE Sectoral Indices
    "NSE: NIFTY BANK": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "BANKBARODA",
        "PNB", "IDFCFIRSTB", "AUBANK", "FEDERALBNK", "BANDHANBNK"
    ],
    "NSE: NIFTY IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM", "TECHM", "PERSISTENT", "COFORGE", "MPHASIS", "LTTS"
    ],
    "NSE: NIFTY PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN", "AUROPHARMA", "TORNTPHARM",
        "ZYDUSLIFE", "ALKEM", "GLENMARK", "MANKIND", "BIOCON", "IPCALAB"
    ],
    "NSE: NIFTY AUTO": [
        "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR",
        "BHARATFORG", "ASHOKLEY", "BOSCHLTD", "MRF", "BALKRISIND", "TIINDIA"
    ],
    "NSE: NIFTY FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", "GODREJCP", "DABUR",
        "MARICO", "COLPAL", "VBL", "PGHH", "UBL", "RADICO", "BALRAMCHIN"
    ],
    "NSE: NIFTY ENERGY": [
        "RELIANCE", "NTPC", "ONGC", "POWERGRID", "COALINDIA", "BPCL", "IOC", "GAIL", "ADANIGREEN", "TATAPOWER"
    ],
    "NSE: NIFTY METAL": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL", "NMDC", "SAIL", "NATIONALUM", "APLAPOLLO", "HINDZINC"
    ],
    "NSE: NIFTY INFRA": [
        "LT", "RELIANCE", "BHARTIARTL", "NTPC", "POWERGRID", "ULTRACEMCO", "ONGC", "GRASIM", "ADANIPORTS", "IOC"
    ],
    "NSE: NIFTY REALTY": [
        "DLF", "GODREJPROP", "LODHA", "OBEROIRLTY", "PHOENIXLTD", "BRIGADE", "PRESTIGE", "SOBHA", "MAHLIFE"
    ],
    "NSE: NIFTY PSU BANK": [
        "SBIN", "BANKBARODA", "PNB", "CANBK", "UNIONBANK", "INDIANB", "IOB", "UCOBANK", "CENTRALBK", "MAHABANK"
    ],
    # BSE Indices
    "BSE: SENSEX 30": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "SBIN",
        "LT", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS",
        "NTPC", "KOTAKBANK", "TITAN", "AXISBANK", "POWERGRID", "TATASTEEL", "BAJAJFINSV",
        "ASIANPAINT", "M&M", "ULTRACEMCO", "JSWSTEEL", "TECHM", "WIPRO", "NESTLEIND", "INDUSINDBK"
    ],
    "BSE: BSE 100": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "SBIN",
        "LT", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "HAL", "BEL",
        "ZOMATO", "TRENT", "JIOFIN", "SIEMENS", "ABB", "CHOLAFIN", "VEDL", "DLF", "IOC"
    ],
    "BSE: BSE MIDCAP": [
        "ACC", "ASTRAL", "AUROPHARMA", "BALKRISIND", "BATAINDIA", "COFORGE", "DIXON",
        "FEDERALBNK", "IDFCFIRSTB", "LUPIN", "MPHASIS", "POLYCAB", "SAIL", "VOLTAS", "ZEEL"
    ],
    "BSE: BSE SMALLCAP": [
        "AMBER", "ANGELONE", "AVANTIFEED", "BALAJIAMIN", "CAMPUS", "CDSL", "CYIENT",
        "DELTACORP", "EASEMYTRIP", "FINEORG", "GRINDWELL", "HAPPSTMNDS", "IEX", "KNRCON"
    ]
}

# -------------------------------------------------------------
# 3. EXHAUSTIVE 20+ FINANCIAL TERMINOLOGIES DICTIONARY
# -------------------------------------------------------------
TERMINOLOGIES = [
    {
        "term": "P/E Ratio (Price to Earnings)",
        "formula": "CMP / Earnings Per Share (EPS)",
        "meaning": "Company ke har ₹1 munafay (profit) ko khareedne ke liye market kitne rupaye de raha hai.",
        "impact": "Kam P/E (>15) undervalued ho sakta hai, aur bohot zyada P/E stock ko mehnga darshata hai.",
        "target": "15 to 35"
    },
    {
        "term": "PEG Ratio (PE to Growth)",
        "formula": "P/E Ratio / Annual EPS Growth Rate",
        "meaning": "P/E ko company ke profit badhne ki raftaar se tulna karta hai.",
        "impact": "PEG < 1.0 matlab company high growth ke muqable saste valuation par mil rahi hai.",
        "target": "0.1 se 1.8"
    },
    {
        "term": "ROCE (Return on Capital Employed)",
        "formula": "EBIT / (Total Assets - Current Liabilities)",
        "meaning": "Equity aur Loan dono paise ko milakar company ne kitne percent return banaya.",
        "impact": "High ROCE (>15%) behtareen management aur solid business efficiency ka saboot hai.",
        "target": "> 15.0%"
    },
    {
        "term": "ROE (Return on Equity)",
        "formula": "Net Income / Shareholders' Equity",
        "meaning": "Shareholders ke lagaye hue paise par net profit kitna percent kamaya gaya.",
        "impact": "High ROE shareholder ke capital ko tezi se multiply karta hai.",
        "target": "> 15.0%"
    },
    {
        "term": "ROA (Return on Assets)",
        "formula": "Net Income / Total Assets",
        "meaning": "Company ke paas jitni kul sampatti hai, uspar kitna profit kamaya.",
        "impact": "Banks aur manufacturing firms ke asset utilization ko samajhne ke liye zaroori hai.",
        "target": "> 6.0%"
    },
    {
        "term": "Debt to Equity Ratio (D/E)",
        "formula": "Total Debt / Shareholders' Equity",
        "meaning": "Company ke upar karz uske khud ke assets ke muqable kitna guna hai.",
        "impact": "D/E < 0.5 hone se mandi me company dubne ka koi khatra nahi rehta.",
        "target": "< 0.5"
    },
    {
        "term": "Interest Coverage Ratio",
        "formula": "EBIT / Interest Expense",
        "meaning": "Company apne saalana operating munafay se karz ka byaaj kitni baar chuka sakti hai.",
        "impact": "High Coverage (>3.5x) hone se company loan default nahi karti.",
        "target": "> 3.5x"
    },
    {
        "term": "OPM (Operating Profit Margin)",
        "formula": "(Operating Profit / Revenue) * 100",
        "meaning": "Kacha maal aur factory kharche nikalne ke baad bacha hua munafa.",
        "impact": "Expanding OPM company ke pricing power aur moat ko dikhata hai.",
        "target": "> 12.0%"
    },
    {
        "term": "NPM (Net Profit Margin)",
        "formula": "(Net Profit After Tax / Revenue) * 100",
        "meaning": "Byaaj, Tax aur sabhi kharche katne ke baad aakhiri bacha shuddh munafa.",
        "impact": "Yeh batata hai ki sales ka kitna hissa seedhe shareholders ki jeb me ja raha hai.",
        "target": "> 10.0%"
    },
    {
        "term": "Free Cash Flow (FCF)",
        "formula": "Operating Cash Flow - Capital Expenditure (CapEx)",
        "meaning": "Nayi factory/machinery lagane ke baad hath me bacha hua asli cash.",
        "impact": "Positive FCF wali companies dividend deti hain aur karz chukati hain.",
        "target": "Positive (FCF > 0)"
    },
    {
        "term": "CFO (Cash Flow from Operations)",
        "formula": "Cash generated from core business operations",
        "meaning": "Asli cash jo company ke bank account me aaya (accounting profit se alag).",
        "impact": "CFO hamesha net profit se zyada hona chahiye taaki udhar ki kami na ho.",
        "target": "CFO > 80% of PAT"
    },
    {
        "term": "P/B Ratio (Price to Book)",
        "formula": "CMP / Book Value Per Share",
        "meaning": "Company ki balance sheet ki net worth ke hisaab se share ka bhav.",
        "impact": "Banks aur NBFCs ke valuation judge karne ke liye best metric hai.",
        "target": "Industry dependent (< 3.0)"
    },
    {
        "term": "EV/EBITDA",
        "formula": "Enterprise Value / EBITDA",
        "meaning": "Company ko karz samet poora khareedne par cash profit ke muqable kitna time lagega.",
        "impact": "Capital-intensive sectors (Steel, Cement) ke valuation ka sabse accurate rasta.",
        "target": "< 12x"
    },
    {
        "term": "Dividend Yield",
        "formula": "(Dividend Per Share / CMP) * 100",
        "meaning": "Stock khareedne par kitne percent yearly cash return dividend ke roop me milega.",
        "impact": "High dividend yield regular income aur defensive stocks ki nishani hai.",
        "target": "1% to 5%"
    },
    {
        "term": "Current Ratio",
        "formula": "Current Assets / Current Liabilities",
        "meaning": "Agle 1 saal ke karz chukane ke liye short-term assets kitne guna hain.",
        "impact": "Current ratio > 1.33 hone par company liquidity crisis me nahi fasti.",
        "target": "> 1.33"
    },
    {
        "term": "Quick Ratio (Acid-Test)",
        "formula": "(Current Assets - Inventory) / Current Liabilities",
        "meaning": "Bina inventory beche emergency me karz chukane ki kshamta.",
        "impact": "Yeh emergency financial solvency ko test karta hai.",
        "target": "> 1.0"
    },
    {
        "term": "Sales CAGR (3Y & 5Y)",
        "formula": "Compound Annual Growth Rate of Revenue",
        "meaning": "Pichle 3 aur 5 saal me sales har saal lagatar kis raftaar se badhi.",
        "impact": "Double digit growth (>12%) growth stock ka sabse bada pillar hai.",
        "target": "> 12.0%"
    },
    {
        "term": "PAT CAGR (Profit Growth)",
        "formula": "Compound Annual Growth Rate of Net Profit",
        "meaning": "Pichle 3 aur 5 saal me shuddh munafa kitni raftaar se multiply hua.",
        "impact": "Sales growth se zyada profit growth honi chahiye (Operating leverage).",
        "target": "> 15.0%"
    },
    {
        "term": "Market Capitalization (M-Cap)",
        "formula": "Total Shares Outstanding * CMP",
        "meaning": "Stock market me poori company ki kul keemat.",
        "impact": "Large Cap me safety zyada hoti hai, Small Cap me return aur risk zyada.",
        "target": "> ₹100 Cr"
    },
    {
        "term": "Beta (Volatility Index)",
        "formula": "Covariance(Stock, Market) / Variance(Market)",
        "meaning": "Nifty ke 1% hilne par yeh stock kitna percent hilta hai.",
        "impact": "Beta < 1.0 matlab stock stable hai, Beta > 1.5 matlab bohot volatile hai.",
        "target": "0.7 to 1.3"
    }
]

# -------------------------------------------------------------
# 4. ROBUST STOCK DATA FETCH & AUDIT ENGINE
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def analyze_stock_full(symbol):
    clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    full_sym = f"{clean_sym}.NS"

    try:
        t = yf.Ticker(full_sym)
        info = t.info

        live_price = info.get("currentPrice", info.get("regularMarketPrice", info.get("previousClose", 0)))
        prev_close = info.get("previousClose", live_price)
        day_change = round(((live_price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
        day_change_abs = round(live_price - prev_close, 2) if prev_close else 0.0

        mcap = info.get("marketCap", 0) / 10000000
        if mcap <= 0:
            return None

        pe = info.get("trailingPE", None)
        peg = info.get("pegRatio", None)
        debt_to_equity = info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else 0

        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow

        # ROE Fallback
        roe = None
        if info.get("returnOnEquity") is not None:
            roe = round(info.get("returnOnEquity") * 100, 2)
        else:
            try:
                if not fin.empty and not bs.empty:
                    net_inc = fin.loc["Net Income"].iloc[0] if "Net Income" in fin.index else 0
                    equity = bs.loc["Stockholders Equity"].iloc[0] if "Stockholders Equity" in bs.index else 0
                    if equity > 0 and net_inc:
                        roe = round((net_inc / equity) * 100, 2)
            except Exception:
                roe = None

        # ROCE Calculation
        roce = None
        ebit = 0
        try:
            if not fin.empty and not bs.empty:
                ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else fin.loc["Operating Income"].iloc[0]
                tot_assets = bs.loc["Total Assets"].iloc[0] if "Total Assets" in bs.index else 0
                curr_liab = bs.loc["Current Liabilities"].iloc[0] if "Current Liabilities" in bs.index else 0
                cap_employed = tot_assets - curr_liab
                if cap_employed > 0:
                    roce = round((ebit / cap_employed) * 100, 2)
        except Exception:
            roce = roe

        int_cov = 999.0
        try:
            if not fin.empty and "Interest Expense" in fin.index:
                int_exp = abs(fin.loc["Interest Expense"].iloc[0])
                if int_exp > 0 and ebit:
                    int_cov = round(ebit / int_exp, 2)
        except Exception:
            int_cov = 10.0

        # Growth metrics
        s_1y = info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0
        p_1y = info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else 0
        s_3y, s_5y, p_3y, p_5y = 0.0, 0.0, 0.0, 0.0
        opm_now, opm_3y = 0.0, 0.0

        if not fin.empty and "Total Revenue" in fin.index:
            rev = fin.loc["Total Revenue"].dropna()
            if len(rev) >= 3 and rev.iloc[2] > 0:
                s_3y = ((rev.iloc[0] / rev.iloc[2]) ** (1 / 3) - 1) * 100
            if len(rev) >= 4 and rev.iloc[-1] > 0:
                s_5y = ((rev.iloc[0] / rev.iloc[-1]) ** (1 / len(rev)) - 1) * 100

        if not fin.empty and "Net Income" in fin.index:
            pat = fin.loc["Net Income"].dropna()
            if len(pat) >= 3 and pat.iloc[2] > 0:
                p_3y = ((pat.iloc[0] / pat.iloc[2]) ** (1 / 3) - 1) * 100
            if len(pat) >= 4 and pat.iloc[-1] > 0:
                p_5y = ((pat.iloc[0] / pat.iloc[-1]) ** (1 / len(pat)) - 1) * 100

        if not fin.empty and "Operating Income" in fin.index and "Total Revenue" in fin.index:
            op_inc = fin.loc["Operating Income"].dropna()
            tot_rev = fin.loc["Total Revenue"].dropna()
            if len(op_inc) > 0 and tot_rev.iloc[0] > 0:
                opm_now = (op_inc.iloc[0] / tot_rev.iloc[0]) * 100
            if len(op_inc) >= 3 and tot_rev.iloc[2] > 0:
                opm_3y = (op_inc.iloc[2] / tot_rev.iloc[2]) * 100

        cfo_last, cfo_3y, pat_3y = 0.0, 0.0, 0.0
        if not cf.empty and "Operating Cash Flow" in cf.index:
            cfos = cf.loc["Operating Cash Flow"].dropna()
            if len(cfos) > 0:
                cfo_last = cfos.iloc[0] / 10000000
                cfo_3y = cfos.iloc[:3].sum() / 10000000

        if not fin.empty and "Net Income" in fin.index:
            pat_3y = fin.loc["Net Income"].iloc[:3].sum() / 10000000

        c1_details = [
            ("Sales Growth 3Y", f"{round(s_3y,1)}%", "> 12.0%", s_3y > 12),
            ("Sales Growth 5Y", f"{round(s_5y,1)}%", "> 10.0%", s_5y > 10),
            ("Profit Growth 3Y", f"{round(p_3y,1)}%", "> 15.0%", p_3y > 15),
            ("Profit Growth 5Y", f"{round(p_5y,1)}%", "> 12.0%", p_5y > 12),
            ("Sales Growth 1Y", f"{round(s_1y,1)}%", "> 10.0%", s_1y > 10),
            ("Profit Growth 1Y", f"{round(p_1y,1)}%", "> 10.0%", p_1y > 10),
        ]
        c2_details = [
            ("ROCE", f"{roce}%" if roce is not None else "N/A", "> 15.0%", roce is not None and roce > 15),
            ("ROE", f"{roe}%" if roe is not None else "N/A", "> 15.0%", roe is not None and roe > 15),
        ]
        c3_details = [
            ("Debt to Equity", f"{round(debt_to_equity,2)}", "< 0.50", debt_to_equity < 0.5),
            ("Interest Coverage", f"{round(int_cov,1)}x", "> 3.5x", int_cov > 3.5),
        ]
        cfo_target = round(pat_3y * 0.8, 2)
        c4_details = [
            ("CFO Last Year", f"₹{round(cfo_last,1)} Cr", "> ₹0.0 Cr", cfo_last > 0),
            ("CFO 3Y Total", f"₹{round(cfo_3y,1)} Cr", f"> 80% PAT (₹{cfo_target} Cr)", cfo_3y > cfo_target),
        ]
        c5_details = [
            ("OPM Trend", f"{round(opm_now,1)}% (vs 3Y: {round(opm_3y,1)}%)", "Higher than 3Y ago", opm_now > opm_3y),
            ("OPM Level", f"{round(opm_now,1)}%", "> 12.0%", opm_now > 12),
        ]
        peg_val = peg if peg else 1.0
        c6_details = [
            ("P/E Ratio", f"{round(pe,1)}" if pe else "N/A", "< 45.0", pe is not None and pe < 45),
            ("PEG Ratio", f"{round(peg_val,2)}", "0.10 to 1.80", 0.1 < peg_val < 1.8),
        ]
        c7_details = [
            ("Market Cap", f"₹{round(mcap,1)} Cr", "> ₹100.0 Cr", mcap > 100)
        ]

        criteria_list = [
            {"id": 1, "title": "1. Growth", "passed": all(d[3] for d in c1_details), "details": c1_details},
            {"id": 2, "title": "2. ROCE & ROE", "passed": all(d[3] for d in c2_details), "details": c2_details},
            {"id": 3, "title": "3. Low Debt", "passed": all(d[3] for d in c3_details), "details": c3_details},
            {"id": 4, "title": "4. Cash Flow", "passed": all(d[3] for d in c4_details), "details": c4_details},
            {"id": 5, "title": "5. OPM Margins", "passed": all(d[3] for d in c5_details), "details": c5_details},
            {"id": 6, "title": "6. Valuation", "passed": all(d[3] for d in c6_details), "details": c6_details},
            {"id": 7, "title": "7. Base Size", "passed": all(d[3] for d in c7_details), "details": c7_details},
        ]

        total_passed = sum(1 for c in criteria_list if c["passed"])

        return {
            "symbol": clean_sym,
            "full_sym": full_sym,
            "name": info.get("shortName", clean_sym),
            "price": round(live_price, 2),
            "day_change": day_change,
            "day_change_abs": day_change_abs,
            "mcap": round(mcap, 2),
            "pe": round(pe, 2) if pe else "N/A",
            "roe": roe if roe is not None else "N/A",
            "roce": roce if roce is not None else "N/A",
            "score": total_passed,
            "criteria": criteria_list,
        }
    except Exception:
        return None

def display_candlestick(full_sym):
    try:
        df_hist = yf.download(full_sym, period="6mo", interval="1d")
        if not df_hist.empty:
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = [col[0] for col in df_hist.columns]

            fig = go.Figure(data=[go.Candlestick(
                x=df_hist.index,
                open=df_hist["Open"],
                high=df_hist["High"],
                low=df_hist["Low"],
                close=df_hist["Close"],
                increasing_line_color="#16a34a",
                decreasing_line_color="#dc2626"
            )])
            fig.update_layout(
                title=f"{full_sym} — 6-Month Technical Candlestick",
                yaxis_title="Price (₹)",
                template=plotly_template,
                xaxis_rangeslider_visible=False,
                height=380,
                margin=dict(l=10, r=10, t=35, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Chart data load nahi ho saka.")

# -------------------------------------------------------------
# 5. MAIN 3-COLUMN LAYOUT WITH LEVEL HEADERS
# -------------------------------------------------------------
left_col, center_col, right_col = st.columns([2.3, 6.2, 2.7], gap="medium")

# -------------------------------------------------------------
# LEFT COLUMN: NAVIGATION MENU
# -------------------------------------------------------------
with left_col:
    st.markdown("### 🎛️ Navigation")
    buttons = [
        "Single stock terminal",
        "NSE/BSE Index screener",
        "Scan PDF / Watchlist",
        "Important TERMINOLOGY GUIDE",
    ]

    for btn in buttons:
        is_selected = st.session_state["active_nav"] == btn
        if st.button(
            btn,
            key=f"nav_{btn}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["active_nav"] = btn
            st.rerun()

# -------------------------------------------------------------
# CENTER COLUMN: SHRINK HEADER + ACTIVE VIEWS
# -------------------------------------------------------------
with center_col:
    st.markdown(
        """
        <div class="center-banner">
            <h1>⚡ PRO STOCK TERMINAL</h1>
            <p>Live CMP, Interactive Charts, Concalls & 7-Stage Audit Engine</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    active = st.session_state["active_nav"]

    # SCREEN 1: SINGLE STOCK TERMINAL (FIXED WORKING FORM)
    if active == "Single stock terminal":
        st.markdown('<div class="content-card"><h3>🔍 Single Stock Live Analysis</h3>', unsafe_allow_html=True)
        
        with st.form("single_stock_form", clear_on_submit=False):
            f_col1, f_col2 = st.columns([4, 1.2])
            with f_col1:
                input_sym = st.text_input("Enter Stock Symbol:", value="RELIANCE", placeholder="e.g. TCS, INFY, TATAMOTORS")
            with f_col2:
                st.write("")
                submit_btn = st.form_submit_button("⚡ Scan Stock", use_container_width=True, type="primary")

        target_sym = input_sym.strip().upper() if input_sym else "RELIANCE"

        if target_sym:
            with st.spinner(f"Fetching Live Data for {target_sym}..."):
                stk = analyze_stock_full(target_sym)

            if stk:
                score = stk["score"]
                border_color = "#16a34a" if score >= 6 else ("#d97706" if score >= 4 else "#dc2626")
                chg_color = "#16a34a" if stk["day_change"] >= 0 else "#dc2626"
                chg_sym = "▲" if stk["day_change"] >= 0 else "▼"

                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-top:8px;">
                        <div>
                            <span style="font-size:1.6rem; font-weight:900;">{stk['name']} ({stk['symbol']})</span>
                            <div>
                                <span style="font-size:1.8rem; font-weight:900;">₹{stk['price']}</span>
                                <span style="font-size:1.1rem; font-weight:800; color:{chg_color}; margin-left:8px;">{chg_sym} {stk['day_change_abs']} ({stk['day_change']}%)</span>
                                <span style="font-size:0.92rem; color:{text_sub}; margin-left:14px;">M-Cap: <b>₹{stk['mcap']} Cr</b> | P/E: <b>{stk['pe']}</b> | ROCE: <b>{stk['roce']}%</b> | ROE: <b>{stk['roe']}%</b></span>
                            </div>
                        </div>
                        <div style="font-size:1.35rem; font-weight:900; color:{border_color}; background: rgba(0,0,0,0.06); padding: 6px 16px; border-radius:10px;">
                            {score} / 7 Passed
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
                    <div style="margin-top: 14px; display:flex; gap:10px; flex-wrap:wrap;">
                        <a href="https://www.screener.in/company/{stk['symbol']}/#concalls" target="_blank" style="padding:6px 12px; background:#eff6ff; color:#1d4ed8; text-decoration:none; border-radius:6px; font-size:0.85rem; font-weight:700; border:1px solid #bfdbfe;">📞 Concall / Transcripts</a>
                        <a href="https://www.screener.in/company/{stk['symbol']}/#quarters" target="_blank" style="padding:6px 12px; background:#fffbeb; color:#b45309; text-decoration:none; border-radius:6px; font-size:0.85rem; font-weight:700; border:1px solid #fde68a;">📑 Quarterly Results</a>
                        <a href="https://in.tradingview.com/chart/?symbol=NSE:{stk['symbol']}" target="_blank" style="padding:6px 12px; background:#f0fdf4; color:#15803d; text-decoration:none; border-radius:6px; font-size:0.85rem; font-weight:700; border:1px solid #bbf7d0;">📈 TradingView Chart</a>
                        <a href="https://www.nseindia.com/get-quotes/equity?symbol={stk['symbol']}" target="_blank" style="padding:6px 12px; background:#faf5ff; color:#7e22ce; text-decoration:none; border-radius:6px; font-size:0.85rem; font-weight:700; border:1px solid #e9d5ff;">🏛️ NSE Corporate Filing</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("---")
                display_candlestick(stk["full_sym"])

                st.markdown("#### 📋 7-Stage Parameter Comparison Breakdown")
                rows = []
                for c in stk["criteria"]:
                    for d in c["details"]:
                        rows.append({
                            "Category": c["title"],
                            "Condition Rule": d[0],
                            "Stock Actual Value": d[1],
                            "Benchmark Target": d[2],
                            "Result": "✅ PASS" if d[3] else "❌ FAIL"
                        })
                st.table(pd.DataFrame(rows))
            else:
                st.error("Stock data nahi mil paya. Valid NSE symbol check karein (e.g. TCS, RELIANCE, INFY).")
        st.markdown("</div>", unsafe_allow_html=True)

    # SCREEN 2: ALL NSE/BSE INDICES SCREENER (COMPLETE INDICES LIST)
    elif active == "NSE/BSE Index screener":
        st.markdown('<div class="content-card"><h3>🏛️ Scan Entire NSE / BSE Index</h3>', unsafe_allow_html=True)
        c_sel, c_btn = st.columns([4, 1.5])
        with c_sel:
            selected_idx = st.selectbox("Choose Index to Scan:", list(INDEX_STOCK_POOLS.keys()), index=0)
        with c_btn:
            st.write("")
            scan_now = st.button("🚀 Scan Index", use_container_width=True, type="primary")

        if scan_now:
            pool = INDEX_STOCK_POOLS[selected_idx]
            results = []
            bar = st.progress(0)
            status = st.empty()

            for i, s in enumerate(pool):
                status.text(f"Scanning ({i+1}/{len(pool)}): {s}")
                d = analyze_stock_full(s)
                if d:
                    results.append(d)
                bar.progress((i + 1) / len(pool))

            bar.empty()
            status.empty()
            results.sort(key=lambda x: x["score"], reverse=True)
            st.session_state["last_scan_results"] = results

        scan_res = st.session_state.get("last_scan_results", [])
        if scan_res:
            st.write(f"### Results ({len(scan_res)} Stocks Analyzed):")
            for stk in scan_res:
                score = stk["score"]
                border_color = "#16a34a" if score >= 6 else ("#d97706" if score >= 4 else "#dc2626")
                with st.expander(f"{stk['name']} ({stk['symbol']}) — ₹{stk['price']} | Score: {score}/7"):
                    rows = []
                    for c in stk["criteria"]:
                        for d in c["details"]:
                            rows.append({
                                "Rule": d[0],
                                "Actual": d[1],
                                "Benchmark": d[2],
                                "Status": "✅ PASS" if d[3] else "❌ FAIL"
                            })
                    st.table(pd.DataFrame(rows))
        st.markdown("</div>", unsafe_allow_html=True)

    # SCREEN 3: SCAN PDF / WATCHLIST (REPAIRED PARSING & LIVE SCAN)
    elif active == "Scan PDF / Watchlist":
        st.markdown('<div class="content-card"><h3>📄 Custom Watchlist & Scanned PDF Symbols</h3>', unsafe_allow_html=True)
        scanned_symbols = st.session_state.get("pdf_symbols", [])

        if scanned_symbols:
            st.success(f"PDF se detect huye symbols: {', '.join(scanned_symbols)}")
        else:
            st.info("Right side panel se PDF statement upload karein ya direct symbols neeche comma-separated likhein.")

        custom_text = st.text_area(
            "Symbols (Comma-separated):",
            value=", ".join(scanned_symbols) if scanned_symbols else "INFY, TCS, LT, MARUTI, RELIANCE"
        )

        if st.button("🚀 Scan Custom Watchlist", type="primary"):
            tokens = [x.strip().upper() for x in custom_text.split(",") if x.strip()]
            results = []
            bar = st.progress(0)
            for i, s in enumerate(tokens):
                d = analyze_stock_full(s)
                if d:
                    results.append(d)
                bar.progress((i + 1) / len(tokens))
            bar.empty()
            results.sort(key=lambda x: x["score"], reverse=True)

            if results:
                st.write(f"### Watchlist Scan Results ({len(results)} Stocks):")
                for stk in results:
                    score = stk["score"]
                    with st.expander(f"**{stk['name']} ({stk['symbol']})** — ₹{stk['price']} | Score: **{score}/7 Passed**"):
                        rows = []
                        for c in stk["criteria"]:
                            for d in c["details"]:
                                rows.append({
                                    "Rule": d[0],
                                    "Stock Value": d[1],
                                    "Benchmark": d[2],
                                    "Result": "✅ PASS" if d[3] else "❌ FAIL"
                                })
                        st.table(pd.DataFrame(rows))
        st.markdown("</div>", unsafe_allow_html=True)

    # SCREEN 4: EXHAUSTIVE TERMINOLOGY GUIDE (20+ FINANCIAL METRICS)
    elif active == "Important TERMINOLOGY GUIDE":
        st.markdown('<div class="content-card"><h3>📖 Complete Financial Terminology Guide</h3>', unsafe_allow_html=True)
        search_kw = st.text_input("Search Financial Metric (e.g. ROCE, P/E, Debt, OPM, Cash Flow, CAGR):", "")

        filtered = [
            t for t in TERMINOLOGIES 
            if search_kw.lower() in t["term"].lower() or search_kw.lower() in t["meaning"].lower()
        ]

        st.caption(f"Showing {len(filtered)} Financial Terms")

        for item in filtered:
            st.markdown(
                f"""
                <div style="background:rgba(0,0,0,0.03); padding:14px; border-radius:8px; margin-bottom:12px; border:1px solid {card_border};">
                    <h4 style="color:#b45309; margin:0 0 4px 0;">📌 {item['term']}</h4>
                    <p style="font-size:0.85rem; color:{text_sub}; margin:0 0 6px 0;"><b>Formula:</b> <code>{item['formula']}</code></p>
                    <p style="margin:0 0 6px 0;"><b>Aasan Bhasha me Matlab:</b> {item['meaning']}</p>
                    <p style="color:#2563eb; margin:0 0 4px 0;"><b>Asar & Investor Impact:</b> {item['impact']}</p>
                    <span style="color:#16a34a; font-weight:700;">🎯 Benchmark / Ideal Value: {item['target']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# RIGHT COLUMN: THEME SWITCHER, UPLOADS & LINKS
# -------------------------------------------------------------
with right_col:
    # 1. THEME CONTROLLER (LIGHT, DARK, SYSTEM)
    st.markdown('<div class="wireframe-box">', unsafe_allow_html=True)
    st.markdown("<b>🎨 Select Theme</b>", unsafe_allow_html=True)
    th_col1, th_col2, th_col3 = st.columns(3)
    with th_col1:
        if st.button("☀️ Light", use_container_width=True, type="primary" if current_theme == "light" else "secondary"):
            st.session_state["theme_mode"] = "light"
            st.rerun()
    with th_col2:
        if st.button("🌙 Dark", use_container_width=True, type="primary" if current_theme == "dark" else "secondary"):
            st.session_state["theme_mode"] = "dark"
            st.rerun()
    with th_col3:
        if st.button("💻 System", use_container_width=True, type="primary" if current_theme == "system" else "secondary"):
            st.session_state["theme_mode"] = "system"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. JSON UPLOADER
    st.markdown('<div class="wireframe-box">', unsafe_allow_html=True)
    st.caption("Upload JSON Watchlist (.json)")
    up_json = st.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")
    if up_json:
        try:
            st.session_state["imported_watchlist"] = json.load(up_json)
            st.success("JSON loaded!")
        except Exception:
            st.error("Invalid JSON file.")
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. PDF STATEMENT UPLOADER (ENHANCED PARSER)
    st.markdown('<div class="wireframe-box">', unsafe_allow_html=True)
    st.caption("Auto-Scan PDF Statement (.pdf)")
    up_pdf = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    if up_pdf:
        try:
            reader = PdfReader(up_pdf)
            txt = "".join([p.extract_text() or "" for p in reader.pages[:10]])
            # Extract potential tickers (3 to 12 capital characters)
            tokens = re.findall(r"\b[A-Z]{3,12}\b", txt)
            # Match against comprehensive Nifty 50 + Next 50 + Midcap lists
            all_known = set()
            for stock_list in INDEX_STOCK_POOLS.values():
                all_known.update(stock_list)

            valid = list(set(tokens).intersection(all_known))
            if valid:
                st.session_state["pdf_symbols"] = valid
                st.success(f"{len(valid)} Stocks detected from PDF!")
            else:
                st.info("PDF upload hua par koi standard stock symbol match nahi hua.")
        except Exception as e:
            st.error(f"PDF parse error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. EXPORT BUTTON
    if st.button("📥 Export data", use_container_width=True):
        export_payload = json.dumps(st.session_state.get("last_scan_results", []), indent=2)
        st.download_button(
            "Click to Download JSON",
            data=export_payload,
            file_name="pro_stock_export.json",
            mime="application/json",
            use_container_width=True
        )

    # 5. DIRECT WORKING OFFICIAL LINKS
    st.markdown(
        """
        <div class="wireframe-box link-list" style="margin-top: 10px;">
            <h4 style="margin-top:0; color:#b45309;">Official Links:</h4>
            <ul>
                <li>• <a href="https://www.nseindia.com" target="_blank">LINK 1: NSE India Official</a></li>
                <li>• <a href="https://www.bseindia.com" target="_blank">LINK 2: BSE India Exchange</a></li>
                <li>• <a href="https://www.screener.in" target="_blank">LINK 3: Screener.in Concalls</a></li>
                <li>• <a href="https://in.tradingview.com" target="_blank">LINK 4: TradingView Charts</a></li>
                <li>• <a href="https://www.sebi.gov.in" target="_blank">LINK 5: SEBI Disclosures</a></li>
                <li>• <a href="https://www.rbi.org.in" target="_blank">LINK 6: RBI Official Rates</a></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
