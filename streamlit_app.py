import io
import json
import re
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import requests
import streamlit as st
import yfinance as yf

# Page Config
st.set_page_config(
    page_title="Terminal Pro: Screener, Charts & Concalls",
    page_icon="⚡",
    layout="wide",
)

# -------------------------------------------------------------
# THEME CONFIGURATION & BACKGROUND STYLING
# -------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

is_dark = st.session_state["theme"] == "dark"

bg_gradient = (
    "linear-gradient(rgba(10, 15, 29, 0.92), rgba(6, 10, 20, 0.96)), "
    "url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1920&q=80')"
    if is_dark
    else (
        "linear-gradient(rgba(248, 250, 252, 0.94), rgba(241, 245, 249, 0.97)), "
        "url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1920&q=80')"
    )
)

card_bg = "#0d1b2a" if is_dark else "#ffffff"
text_color = "#f8fafc" if is_dark else "#0f172a"
subtext_color = "#94a3b8" if is_dark else "#64748b"
card_border = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.1)"

st.markdown(
    f"""
<style>
    .stApp {{
        background-image: {bg_gradient};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: {text_color} !important;
        font-size: 16px !important;
    }}
    
    .main-title {{
        font-size: 2.1rem !important;
        font-weight: 900;
        color: {'#fbbf24' if is_dark else '#b45309'};
        letter-spacing: -0.5px;
    }}
    
    .sub-title {{
        font-size: 1rem !important;
        color: {subtext_color};
        margin-bottom: 0.8rem;
    }}

    .stock-card {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }}

    .term-card {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}

    .pill-pass {{
        display: inline-block;
        background-color: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        margin: 2px 4px 2px 0;
    }}
    .pill-fail {{
        display: inline-block;
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        margin: 2px 4px 2px 0;
    }}
    
    .link-btn {{
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
        margin-bottom: 6px;
    }}
    .link-concall {{
        background-color: rgba(96, 165, 250, 0.15);
        color: #60a5fa !important;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }}
    .link-result {{
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b !important;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    .link-exchange {{
        background-color: rgba(168, 85, 247, 0.15);
        color: #c084fc !important;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }}
    .link-chart {{
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80 !important;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# INDEX POOLS (NSE / BSE)
# -------------------------------------------------------------
INDEX_STOCK_POOLS = {
    "NIFTY 50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "SBIN",
        "LT", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS",
        "NTPC", "ONGC", "KOTAKBANK", "TITAN", "AXISBANK", "ADANIENT", "POWERGRID",
        "TATASTEEL", "COALINDIA", "BAJAJFINSV", "ASIANPAINT", "M&M", "ULTRACEMCO",
        "JSWSTEEL", "GRASIM", "LTIM", "TECHM", "WIPRO", "NESTLEIND", "HINDALCO",
        "ADANIPORTS", "SBILIFE", "BAJAJ-AUTO", "DRREDDY", "CIPLA", "DIVISLAB",
        "APOLLOHOSP", "EICHERMOT", "BRITANNIA", "SHRIRAMFIN", "TRENT", "BEL",
        "BPCL", "TATACONSUM", "HEROMOTOCO"
    ],
    "NIFTY BANK": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK",
        "BANKBARODA", "PNB", "IDFCFIRSTB", "AUBANK", "FEDERALBNK", "BANDHANBNK"
    ],
    "NIFTY IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM", "TECHM", "PERSISTENT", "COFORGE",
        "MPHASIS", "LTTS"
    ],
    "NIFTY PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN", "AUROPHARMA",
        "TORNTPHARM", "ZYDUSLIFE", "ALKEM", "GLENMARK", "MANKIND", "BIOCON"
    ],
    "NIFTY AUTO": [
        "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO",
        "TVSMOTOR", "BHARATFORG", "ASHOKLEY", "BOSCHLTD", "MRF", "BALKRISIND"
    ],
    "NIFTY ENERGY": [
        "RELIANCE", "NTPC", "ONGC", "POWERGRID", "COALINDIA", "BPCL", "IOC",
        "GAIL", "ADANIGREEN", "TATAPOWER"
    ],
    "NIFTY METAL": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL", "NMDC",
        "SAIL", "NATIONALUM", "APLAPOLLO"
    ],
    "BSE SENSEX 30": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "SBIN",
        "LT", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS",
        "NTPC", "KOTAKBANK", "TITAN", "AXISBANK", "POWERGRID", "TATASTEEL", "BAJAJFINSV",
        "ASIANPAINT", "M&M", "ULTRACEMCO", "JSWSTEEL", "TECHM", "WIPRO", "NESTLEIND", "INDUSINDBK"
    ]
}

# -------------------------------------------------------------
# TERMINOLOGY DATA (EASY DEFINITION + IMPACT)
# -------------------------------------------------------------
TERMINOLOGIES = [
    {
        "term": "P/E Ratio (Price to Earnings)",
        "full": "Market Price per Share / Earnings per Share (EPS)",
        "def": "Yeh batata hai ki company ke har 1 rupaye ke munafay (profit) ko khareedne ke liye aap stock market me kitne rupaye dene ko taiyar hain.",
        "example": "Agar company ka EPS ₹10 hai aur share price ₹200 hai, toh P/E = 20 hua.",
        "impact": "✅ Low P/E (Industry se kam): Stock sasta ya undervalued ho sakta hai.\n❌ High P/E: Stock mehnga hai ya market usse bohot zyada growth expect kar raha hai.",
        "ideal": "Aam taur par 15 se 35 ke beech accha maana jata hai."
    },
    {
        "term": "PEG Ratio (P/E to Growth)",
        "full": "P/E Ratio / Annual EPS Growth Rate",
        "def": "P/E ratio ko company ki munafay ki raftaar (profit growth) se tulna karta hai. Yeh batata hai ki mehnga P/E justified hai ya nahi.",
        "example": "P/E = 30 aur Profit Growth = 30% hai, toh PEG = 1.0.",
        "impact": "✅ PEG < 1.0: Stock apni growth ke muqable bohot sasta mil raha hai (Strong Buy signal).\n❌ PEG > 2.0: Growth ke hisab se stock bohot mehnga hai.",
        "ideal": "0.5 se 1.5 ke beech best value hoti hai."
    },
    {
        "term": "ROCE (Return on Capital Employed)",
        "full": "EBIT / (Total Assets - Current Liabilities)",
        "def": "Company ne business me lagaye gaye poore paise (Equity + Karz dono) par kitne percent ka munafa kamaya.",
        "example": "Agar business me kul ₹100 Cr laga hai aur EBIT ₹20 Cr hai, toh ROCE 20% hua.",
        "impact": "✅ High ROCE (> 15%): Company apne capital ko behtar tareeqe se use karke wealth create kar rahi hai.\n❌ Low ROCE: Paise ka galat use ho raha hai, lambe time me returns kam milenge.",
        "ideal": "15% se zyada lagataar hona chahiye."
    },
    {
        "term": "ROE (Return on Equity)",
        "full": "Net Income / Shareholders' Equity",
        "def": "Company sirf aam share holders ke lagaye gaye paise par kitna percent net profit generate kar rahi hai.",
        "example": "Shareholders ka paisa ₹50 Cr hai aur saalana net profit ₹10 Cr hai, toh ROE 20% hua.",
        "impact": "✅ High ROE: Shareholder ke har rupaye par tagda return milta hai.\n⚠️ Savdhani: Agar company par zyada karz ho tab bhi ROE artifically high dikh sakta hai, isliye ROCE ke sath dekhein.",
        "ideal": "15% se zyada hona healthy maana jata hai."
    },
    {
        "term": "Debt to Equity Ratio (D/E)",
        "full": "Total Debt / Total Shareholders' Equity",
        "def": "Company ke upar karz (loan) uske khud ke assets/equity ke muqable kitna guna hai.",
        "example": "Equity ₹100 Cr aur Karz ₹30 Cr hai, toh D/E = 0.30.",
        "impact": "✅ D/E < 0.5: Company financially surakshit (safe) hai, crisis me dubne ka khatra kam hai.\n❌ D/E > 1.5: Zyada byaaj bharna padega, mandi me bankruptcy ka risk rehta hai.",
        "ideal": "0.5 se kam (Debt-Free ya Low Debt best)."
    },
    {
        "term": "Interest Coverage Ratio",
        "full": "EBIT / Interest Expense",
        "def": "Company apne saalana operating profit se bank ke karz ka byaaj (interest) kitni baar chuka sakti hai.",
        "example": "Munafa ₹50 Cr aur byaaj ka kharcha ₹10 Cr hai, toh coverage = 5x.",
        "impact": "✅ High Coverage (> 3.5x): Company aasani se byaaj de sakti hai, default ka koi darr nahi.\n❌ Low Coverage (< 1.5x): Munafa kam hua toh company kangaal ho sakti hai.",
        "ideal": "Minimum 3.5x ya usse zyada."
    },
    {
        "term": "OPM (Operating Profit Margin %)",
        "full": "(Operating Profit / Revenue) * 100",
        "def": "Har ₹100 ki sales par raw material aur factory kharche nikalne ke baad kitne rupaye bachte hain.",
        "example": "Revenue ₹100 Cr aur Operating Profit ₹22 Cr, toh OPM 22% hua.",
        "impact": "✅ Badhta hua OPM (Margin Expansion): Pricing power tagdi hai aur company cost control kar rahi hai.\n❌ Girta hua OPM: Competition badh raha hai ya raw material mehnga ho raha hai.",
        "ideal": "12% se upar aur pichle saalon ke muqable badhta hua."
    },
    {
        "term": "Operating Cash Flow (CFO)",
        "full": "Cash generated from core operations",
        "def": "Asli cash jo company ke bank account me core business se aaya (Accounting profit aur cash flow me fark hota hai).",
        "example": "Paper par profit ₹100 Cr dikh raha hai lekin CFO sirf ₹20 Cr hai, iska matlab maal udhar par bika hai aur cash nahi aaya.",
        "impact": "✅ CFO > Net Profit: Quality of earnings bohot solid aur genuine hai.\n❌ Negative CFO: Company paper par munafa dikha rahi hai par cash khatam ho raha hai.",
        "ideal": "CFO hamesha positive aur Net profit ke 80% se zyada hona chahiye."
    },
    {
        "term": "Market Capitalization (M-Cap)",
        "full": "Total Outstanding Shares * Current Market Price",
        "def": "Poori company ko aaj ki taareekh me khareedne ki kul market value.",
        "example": "Large Cap (> ₹20,000 Cr), Mid Cap (₹5,000 - ₹20,000 Cr), Small Cap (< ₹5,000 Cr).",
        "impact": "Large Cap me safety zyada hoti hai, Small Cap me growth zyada aur risk zyada hota hai.",
        "ideal": "Screener filter me hum ₹100 Cr+ quality penny-stock trap se bachne ke liye lagate hain."
    }
]

# -------------------------------------------------------------
# ENGINE: FETCH REALTIME DATA & ROE FALLBACK ENGINE
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

        # ROE FALLBACK CALCULATION
        roe = None
        if info.get("returnOnEquity") is not None:
            roe = round(info.get("returnOnEquity") * 100, 2)
        else:
            try:
                if not fin.empty and not bs.empty:
                    net_inc = fin.loc["Net Income"].iloc[0] if "Net Income" in fin.index else 0
                    equity = (
                        bs.loc["Stockholders Equity"].iloc[0]
                        if "Stockholders Equity" in bs.index
                        else (bs.loc["Total Stockholder Equity"].iloc[0] if "Total Stockholder Equity" in bs.index else 0)
                    )
                    if equity > 0 and net_inc:
                        roe = round((net_inc / equity) * 100, 2)
            except Exception:
                roe = None

        # ROCE CALCULATION
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

        # Detailed Comparison Data
        c1_details = [
            ("Sales Growth 3Y", f"{round(s_3y,1)}%", "> 12.0%", s_3y > 12),
            ("Sales Growth 5Y", f"{round(s_5y,1)}%", "> 10.0%", s_5y > 10),
            ("Profit Growth 3Y", f"{round(p_3y,1)}%", "> 15.0%", p_3y > 15),
            ("Profit Growth 5Y", f"{round(p_5y,1)}%", "> 12.0%", p_5y > 12),
            ("Sales Growth 1Y", f"{round(s_1y,1)}%", "> 10.0%", s_1y > 10),
            ("Profit Growth 1Y", f"{round(p_1y,1)}%", "> 10.0%", p_1y > 10),
        ]
        c1_pass = all(d[3] for d in c1_details)

        c2_details = [
            ("ROCE", f"{roce}%" if roce is not None else "N/A", "> 15.0%", roce is not None and roce > 15),
            ("ROE", f"{roe}%" if roe is not None else "N/A", "> 15.0%", roe is not None and roe > 15),
        ]
        c2_pass = all(d[3] for d in c2_details)

        c3_details = [
            ("Debt to Equity", f"{round(debt_to_equity,2)}", "< 0.50", debt_to_equity < 0.5),
            ("Interest Coverage", f"{round(int_cov,1)}x", "> 3.5x", int_cov > 3.5),
        ]
        c3_pass = all(d[3] for d in c3_details)

        cfo_target = round(pat_3y * 0.8, 2)
        c4_details = [
            ("CFO Last Year", f"₹{round(cfo_last,1)} Cr", "> ₹0.0 Cr", cfo_last > 0),
            ("CFO 3Y Total", f"₹{round(cfo_3y,1)} Cr", f"> 80% of PAT (₹{cfo_target} Cr)", cfo_3y > cfo_target),
        ]
        c4_pass = all(d[3] for d in c4_details)

        c5_details = [
            ("OPM Trend", f"{round(opm_now,1)}% (vs 3Y: {round(opm_3y,1)}%)", "Higher than 3Y ago", opm_now > opm_3y),
            ("OPM Level", f"{round(opm_now,1)}%", "> 12.0%", opm_now > 12),
        ]
        c5_pass = all(d[3] for d in c5_details)

        peg_val = peg if peg else 1.0
        c6_details = [
            ("P/E Ratio", f"{round(pe,1)}" if pe else "N/A", "< 45.0", pe is not None and pe < 45),
            ("PEG Ratio", f"{round(peg_val,2)}", "Between 0.10 and 1.80", 0.1 < peg_val < 1.8),
        ]
        c6_pass = all(d[3] for d in c6_details)

        c7_details = [
            ("Market Cap", f"₹{round(mcap,1)} Cr", "> ₹100.0 Cr", mcap > 100)
        ]
        c7_pass = all(d[3] for d in c7_details)

        criteria_list = [
            {"id": 1, "title": "1. Growth", "passed": c1_pass, "details": c1_details},
            {"id": 2, "title": "2. ROCE & ROE", "passed": c2_pass, "details": c2_details},
            {"id": 3, "title": "3. Low Debt", "passed": c3_pass, "details": c3_details},
            {"id": 4, "title": "4. Cash Flow", "passed": c4_pass, "details": c4_details},
            {"id": 5, "title": "5. OPM Margins", "passed": c5_pass, "details": c5_details},
            {"id": 6, "title": "6. Valuation", "passed": c6_pass, "details": c6_details},
            {"id": 7, "title": "7. Base Size", "passed": c7_pass, "details": c7_details},
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


# Helper for Plotly Candlestick Chart
def display_stock_chart(full_sym):
    try:
        df_hist = yf.download(full_sym, period="6mo", interval="1d")
        if not df_hist.empty:
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = [col[0] for col in df_hist.columns]

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df_hist.index,
                        open=df_hist["Open"],
                        high=df_hist["High"],
                        low=df_hist["Low"],
                        close=df_hist["Close"],
                        name="Price",
                        increasing_line_color="#22c55e",
                        decreasing_line_color="#ef4444",
                    )
                ]
            )
            fig.update_layout(
                title=f"{full_sym} — 6-Month Technical Chart",
                yaxis_title="Price (₹)",
                template="plotly_dark" if is_dark else "plotly_white",
                xaxis_rangeslider_visible=False,
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Historical chart data uplabdh nahi hai.")
    except Exception as e:
        st.error(f"Chart load error: {e}")


# Helper to render interactive stock card
def render_stock_card(stk):
    score = stk["score"]
    border_color = "#22c55e" if score >= 6 else ("#f59e0b" if score >= 4 else "#ef4444")
    chg_color = "#22c55e" if stk["day_change"] >= 0 else "#ef4444"
    chg_symbol = "▲" if stk["day_change"] >= 0 else "▼"

    concall_url = f"https://www.screener.in/company/{stk['symbol']}/#concalls"
    results_url = f"https://www.screener.in/company/{stk['symbol']}/#quarters"
    tradingview_url = f"https://in.tradingview.com/chart/?symbol=NSE:{stk['symbol']}"
    yahoo_chart_url = f"https://finance.yahoo.com/quote/{stk['full_sym']}/chart"
    nse_official_url = f"https://www.nseindia.com/get-quotes/equity?symbol={stk['symbol']}"
    bse_official_url = f"https://www.bseindia.com/stock-share-price/{stk['symbol']}/"

    st.markdown(
        f"""
    <div class="stock-card" style="border-left: 6px solid {border_color};">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
            <div>
                <span style="font-size:1.55rem; font-weight:900;">{stk['name']} ({stk['symbol']})</span>
                <div style="margin-top:4px;">
                    <span style="font-size:1.6rem; font-weight:900; color:{'#ffffff' if is_dark else '#0f172a'};">
                        ₹{stk['price']}
                    </span>
                    <span style="font-size:1.05rem; font-weight:800; color:{chg_color}; margin-left:8px;">
                        {chg_symbol} {stk['day_change_abs']} ({stk['day_change']}%)
                    </span>
                    <span style="font-size:0.95rem; color:{subtext_color}; margin-left:14px;">
                        M-Cap: <b>₹{stk['mcap']} Cr</b> | P/E: <b>{stk['pe']}</b> | ROCE: <b>{stk['roce']}%</b> | ROE: <b>{stk['roe']}%</b>
                    </span>
                </div>
            </div>
            <div style="font-size:1.35rem; font-weight:900; color:{border_color}; background: rgba(255,255,255,0.06); padding: 5px 14px; border-radius:12px;">
                {score} / 7 Criteria Pass
            </div>
        </div>
        
        <!-- 7 Criteria Pills -->
        <div style="margin: 14px 0 10px 0;">
    """,
        unsafe_allow_html=True,
    )

    pill_html = ""
    for c in stk["criteria"]:
        cls = "pill-pass" if c["passed"] else "pill-fail"
        icon = "✅" if c["passed"] else "❌"
        pill_html += f'<span class="{cls}">{icon} {c["title"].split(".")[1]}</span>'
    st.markdown(pill_html + "</div>", unsafe_allow_html=True)

    # Action links
    st.markdown(
        f"""
    <div style="margin-top: 10px; display:flex; flex-wrap:wrap;">
        <a href="{concall_url}" target="_blank" class="link-btn link-concall">📞 Concall / Transcripts</a>
        <a href="{results_url}" target="_blank" class="link-btn link-result">📑 Quarterly Results (P&L)</a>
        <a href="{nse_official_url}" target="_blank" class="link-btn link-exchange">🏛️ NSE Official Page</a>
        <a href="{bse_official_url}" target="_blank" class="link-btn link-exchange">🏢 BSE India Page</a>
    </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.expander(f"🔍 Click to inspect {stk['symbol']} — Full Comparison Breakdown & Charts"):
        st.markdown("#### 📋 Parameter Comparison Breakdown")
        
        table_rows = []
        for c in stk["criteria"]:
            for d in c["details"]:
                table_rows.append({
                    "Heading Category": c["title"],
                    "Rule Condition": d[0],
                    "Stock Actual Value": d[1],
                    "Required Benchmark": d[2],
                    "Result": "✅ PASS" if d[3] else "❌ FAIL"
                })
        
        st.table(pd.DataFrame(table_rows))

        st.write("---")
        st.markdown("#### 📊 Interactive Technical Chart")
        
        c_link1, c_link2 = st.columns([1, 1])
        with c_link1:
            st.markdown(f'<a href="{tradingview_url}" target="_blank" class="link-btn link-chart">📈 Open TradingView Interactive Chart (Custom Indicators)</a>', unsafe_allow_html=True)
        with c_link2:
            st.markdown(f'<a href="{yahoo_chart_url}" target="_blank" class="link-btn link-chart">📉 Open Yahoo Finance Chart</a>', unsafe_allow_html=True)

        display_stock_chart(stk["full_sym"])


# -------------------------------------------------------------
# TOP TASKBAR (Import/Export, PDF Scanner & Theme Toggle)
# -------------------------------------------------------------
tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns([3, 1, 1, 1.5, 0.8])

with tcol1:
    st.markdown('<div class="main-title">⚡ PRO STOCK TERMINAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Live CMP, Interactive Charts, Concalls & 7-Stage Audit Engine</div>', unsafe_allow_html=True)

with tcol2:
    if st.button("📤 Export Data", use_container_width=True):
        exp_data = json.dumps(st.session_state.get("last_scan_results", []), indent=2)
        st.download_button("📥 Click Download", data=exp_data, file_name="stocks_audit.json", mime="application/json")

with tcol3:
    imp_file = st.file_uploader("📥 Import", type=["json"], label_visibility="collapsed")
    if imp_file:
        try:
            st.session_state["imported_tickers"] = json.load(imp_file)
            st.success("Loaded!")
        except Exception:
            st.error("Invalid JSON.")

with tcol4:
    pdf_file = st.file_uploader("📄 Upload PDF Scanner", type=["pdf"], label_visibility="collapsed")
    if pdf_file:
        try:
            reader = PdfReader(pdf_file)
            txt = "".join([p.extract_text() or "" for p in reader.pages[:4]])
            tokens = re.findall(r"\b[A-Z]{3,10}\b", txt)
            valid = list(set(tokens).intersection(INDEX_STOCK_POOLS["NIFTY 50"]))
            if valid:
                st.session_state["pdf_scanned_stocks"] = valid
                st.success(f"{len(valid)} Stocks Found in PDF!")
        except Exception as e:
            st.error(f"PDF error: {e}")

with tcol5:
    theme_label = "☀️ Light" if is_dark else "🌙 Dark"
    if st.button(theme_label, use_container_width=True):
        st.session_state["theme"] = "light" if is_dark else "dark"
        st.rerun()

st.write("---")

# -------------------------------------------------------------
# LEFT SIDEBAR NAVIGATION
# -------------------------------------------------------------
st.sidebar.title("🎛️ Terminal Navigation")
selected_feature = st.sidebar.radio(
    "Select Mode:",
    [
        "1. 🔍 Single Stock Terminal",
        "2. 🏛️ NSE / BSE Index Screener",
        "3. 📄 Scanned PDF / Watchlist",
        "4. 📖 Important Terminology Guide"
    ]
)

# -------------------------------------------------------------
# FEATURE 1: SINGLE STOCK TERMINAL
# -------------------------------------------------------------
if "1." in selected_feature:
    st.subheader("🔍 Single Stock Live Analysis")
    c1, c2 = st.columns([3, 1])
    with c1:
        single_sym = st.text_input(
            "Stock Symbol (e.g. RELIANCE, TCS, INFY, TATAMOTORS, HDFCBANK, TATAELXSI):",
            value="TCS"
        )
    with c2:
        st.write("")
        st.write("")
        btn_audit = st.button("⚡ Scan Stock Details", use_container_width=True, type="primary")

    if single_sym:
        with st.spinner(f"Analyzing {single_sym}..."):
            stock_info = analyze_stock_full(single_sym)
        if stock_info:
            render_stock_card(stock_info)
        else:
            st.error("Data nahi mila. Valid NSE symbol check karein.")

# -------------------------------------------------------------
# FEATURE 2: NSE / BSE INDEX SCREENER
# -------------------------------------------------------------
elif "2." in selected_feature:
    st.subheader("🏛️ Scan Entire NSE / BSE Index")
    ic1, ic2, ic3 = st.columns([2, 1, 1])

    with ic1:
        chosen_index = st.selectbox("Choose Index:", list(INDEX_STOCK_POOLS.keys()))
    with ic2:
        search_idx = st.text_input("Or Search Index Name:", placeholder="e.g. Bank, IT, Metal")
    with ic3:
        st.write("")
        st.write("")
        btn_idx = st.button("🚀 Scan Pure Index Ke Stocks", use_container_width=True, type="primary")

    target_idx = chosen_index
    if search_idx:
        for k in INDEX_STOCK_POOLS.keys():
            if search_idx.strip().upper() in k.upper():
                target_idx = k
                break

    st.caption(f"Scanning: **{target_idx}** ({len(INDEX_STOCK_POOLS[target_idx])} Stocks)")

    if btn_idx:
        pool = INDEX_STOCK_POOLS[target_idx]
        results = []
        p_bar = st.progress(0)
        status_txt = st.empty()

        for idx, s in enumerate(pool):
            status_txt.text(f"Fetching Live Data ({idx+1}/{len(pool)}): {s}")
            data = analyze_stock_full(s)
            if data:
                results.append(data)
            p_bar.progress((idx + 1) / len(pool))

        p_bar.empty()
        status_txt.empty()

        results.sort(key=lambda x: x["score"], reverse=True)
        st.session_state["last_scan_results"] = results

    saved_results = st.session_state.get("last_scan_results", [])
    if saved_results:
        fcol1, fcol2 = st.columns([1, 3])
        with fcol1:
            min_pass = st.slider("Minimum Pass Criteria", 0, 7, 4)

        filtered = [s for s in saved_results if s["score"] >= min_pass]
        st.markdown(f"### Shortlisted: Showing {len(filtered)} Stocks")

        for s in filtered:
            render_stock_card(s)

# -------------------------------------------------------------
# FEATURE 3: SCANNED PDF / WATCHLIST
# -------------------------------------------------------------
elif "3." in selected_feature:
    st.subheader("📄 Custom Watchlist & PDF Extracted Stocks")
    pdf_stocks = st.session_state.get("pdf_scanned_stocks", [])

    st.write(f"PDF Scanner detected symbols: **{', '.join(pdf_stocks) if pdf_stocks else 'None'}**")

    custom_text = st.text_area(
        "Custom Stocks List (Comma separated):",
        value=", ".join(pdf_stocks) if pdf_stocks else "INFY, TCS, LT, MARUTI"
    )

    if st.button("🚀 Scan Watchlist", type="primary"):
        tokens = [x.strip().upper() for x in custom_text.split(",") if x.strip()]
        results = []
        p_bar = st.progress(0)

        for idx, s in enumerate(tokens):
            data = analyze_stock_full(s)
            if data:
                results.append(data)
            p_bar.progress((idx + 1) / len(tokens))

        p_bar.empty()
        results.sort(key=lambda x: x["score"], reverse=True)

        for s in results:
            render_stock_card(s)

# -------------------------------------------------------------
# FEATURE 4: IMPORTANT TERMINOLOGY GUIDE
# -------------------------------------------------------------
elif "4." in selected_feature:
    st.subheader("📖 Fundamental & Screener Terminology Guide")
    st.markdown("Is screener me use hone wale sabhi important metrics ka aasaan bhasha me matlab, live example aur stock par unka asar:")

    search_term = st.text_input("🔍 Search Any Financial Term (e.g. ROCE, PEG, Debt, OPM, Cash Flow):", "")

    filtered_terms = TERMINOLOGIES
    if search_term:
        filtered_terms = [
            t for t in TERMINOLOGIES 
            if search_term.lower() in t["term"].lower() or search_term.lower() in t["def"].lower()
        ]

    for item in filtered_terms:
        with st.container():
            st.markdown(
                f"""
                <div class="term-card">
                    <h3 style="color:#fbbf24; margin-bottom:2px;">📌 {item['term']}</h3>
                    <p style="font-size:0.85rem; color:{subtext_color}; margin-bottom:8px;"><b>Formula:</b> <code>{item['full']}</code></p>
                    <p style="font-size:1rem; margin-bottom:6px;"><b>Aasaan Bhasha me Matlab:</b> {item['def']}</p>
                    <p style="font-size:0.95rem; color:#60a5fa; margin-bottom:6px;"><b>Udaharan (Example):</b> {item['example']}</p>
                    <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-top:8px;">
                        <span style="font-size:0.92rem; font-weight:700; color:#34d399;">📊 Asar & Investor Impact:</span>
                        <p style="font-size:0.9rem; margin-top:4px; white-space:pre-line;">{item['impact']}</p>
                        <span style="font-size:0.85rem; color:#facc15;">🎯 Benchmark (Kitna hona chahiye): <b>{item['ideal']}</b></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
