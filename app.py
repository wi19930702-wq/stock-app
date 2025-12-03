import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="當沖計算機 (經典版)", layout="centered")

st.markdown("""
<style>
    /* 計算機專用卡片 (還原最一開始的綠色風格) */
    .calc-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #00c853; /* 經典綠 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        margin-top: 20px;
    }
    
    /* 掃描頁面的卡片 (紅色風格) */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 大字體優化 */
    .big-label { font-size: 16px; color: #aaaaaa; margin-bottom: 5px; }
    .big-value { font-size: 28px; font-weight: bold; color: #ffffff; }
    
    .resistance { color: #ff6c6c; font-weight: bold; } /* 壓力紅 */
    .support { color: #00e676; font-weight: bold; } /* 支撐綠 */
    
    /* 券商標籤 */
    .broker-tag {
        display: inline-block;
        background-color: #444;
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .kgi-tag { background-color: #d32f2f; color: white; border: 1px solid #ff5252; }
    .fubon-tag { background-color: #1976d2; color: white; border: 1px solid #448aff; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算函數 (CDP) ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

# --- 3. 掃描用資料 (保留給分頁2使用) ---
STOCK_MAP = {
    "4939":"亞電", "8046":"南電", "6269":"台郡", "6274":"台燿", "6213":"智擎",
    "3037":"欣興", "2313":"華通", "2367":"燿華", "2368":"金像電", "8039":"台虹",
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3032":"偉訓", "8210":"勤誠", "3653":"健策", 
    "1609":"大亞", "1605":"華新", "1513":"中興電", "1514":"亞力", "1519":"華城", "1503":"士電", 
    "4979":"華星光", "3450":"聯鈞", "4908":"前鼎", "3234":"光環", "3081":"聯亞",
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "2618":"長榮航", "2610":"華航"
}
SCAN_TARGETS = list(STOCK_MAP.keys())

def generate_mock_broker_html():
    # 模擬顯示隔日沖券商
    BROKER_POOLS = [("凱基-台北", "kgi-tag"), ("富邦-建國", "fubon-tag"), ("美林", "broker-tag"), ("摩根大通", "broker-tag"), ("統一-嘉義", "broker-tag"), ("永豐金-虎尾", "broker-tag")]
    selected = random.sample(BROKER_POOLS, 3)
    html_parts = []
    for name, css_class in selected:
        vol = random.randint(600, 3500)
        html_parts.append(f'<span class="broker-tag {css_class}">{name} +{vol}</span>')
    return " ".join(html_parts)

# --- 4. 介面設計 ---

# 分頁設定：計算機放第一個 (Tab 1)
tab1, tab2 = st.tabs(["🧮 快速計算機", "🚀 飆股掃描"])

# === 分頁 1: 經典計算機 (還原最初版本) ===
with tab1:
    st.markdown("### ⚡ 當沖支撐壓力計算")
    st.info("輸入今日 K 線數據，立即計算明日關鍵點位。")
    
    col1, col2 = st.columns(2)
    with col1:
        p_close = st.number_input("收盤價", value=0.0, step=0.1, format="%.2f")
        p_high = st.number_input("最高價", value=0.0, step=0.1, format="%.2f")
    with col2:
        p_low = st.number_input("最低價", value=0.0, step=0.1, format="%.2f")
        
    # 大按鈕
    if st.button("開始計算", type="primary", use_container_width=True):
        if p_close > 0:
            ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
            
            # 經典綠色卡片設計
            st.markdown(f"""
            <div class="calc-card">
                <div style="font-size:14px; color:#aaa; margin-bottom:10px;">中關價 (CDP): {cdp}</div>
                
                <div style="display:flex; justify-content:space-between; margin-bottom:15px; border-bottom:1px solid #444; padding-bottom:15px;">
                    <div style="width:50%;">
                        <div class="big-label">賣出壓力 (NH)</div>
                        <div class="big-value resistance">{nh}</div>
                    </div>
                    <div style="width:50%; border-left:1px solid #444;">
                        <div class="big-label">買進支撐 (NL)</div>
                        <div class="big-value support">{nl}</div>
                    </div>
                </div>
                
                <div style="display:flex; justify-content:space-between;">
                    <div style="width:50%;">
                        <div style="font-size:12px; color:#888;">最高壓力 (AH)</div>
                        <div style="font-size:18px; color:#ff6c6c;">{ah}</div>
                    </div>
                    <div style="width:50%;">
                        <div style="font-size:12px; color:#888;">最低支撐 (AL)</div>
                        <div style="font-size:18px; color:#00e676;">{al}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("請輸入大於 0 的價格")

# === 分頁 2: 飆股掃描 (保留原本的模擬券商功能) ===
with tab2:
    st.markdown("### 🔍 市場熱門股掃描")
    if st.button("掃描全市場 (含主力分點)", use_container_width=True):
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        valid_stocks = []
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    row = df.iloc[-1]
                    if pd.isna(row['Volume']): continue
                    vol = int(row['Volume'])
                    close = float(row['Close'])
                    open_p = float(row['Open'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    
                    if close > 350 or vol < 1000000: continue 
                    change_pct = ((close - open_p) / open_p) * 100
                    if change_pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    brokers_html = generate_mock_broker_html()
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "change": change_pct,
                        "nh": nh, "nl": nl, "brokers_html": brokers_html
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            valid_stocks.sort(key=lambda x: x['change'], reverse=True)
            
            if not valid_stocks:
                st.warning("無符合標的。")
            else:
                for s in valid_stocks:
                    html = f"""<div class="stock-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="font-size:13px; color:#ccc;">{s['code']}</span></div>
        <span style="color:#ff4b4b; font-weight:bold;">+{round(s['change'], 2)}%</span>
    </div>
    <div style="margin-top:5px; color:#ccc; font-size:13px;">量: {s['vol']} 張 | 收: {s['close']}</div>
    <div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;">
        <span class="resistance">壓: {s['nh']}</span>
        <span class="support">撐: {s['nl']}</span>
    </div>
    <div style="margin-top:8px; padding-top:5px; border-top:1px dashed #555;">
        <div style="font-size:12px; color:#aaa; margin-bottom:3px;">⚡ 模擬主力:</div>
        {s['brokers_html']}
    </div>
</div>"""
                    st.markdown(html, unsafe_allow_html=True)
        except Exception as e: st.error(f"錯誤: {e}")
