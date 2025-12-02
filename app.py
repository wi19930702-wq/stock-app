import streamlit as st
import pandas as pd
import random

# --- 1. 手機版面設定 ---
st.set_page_config(page_title="隔日沖戰情室", layout="centered")

# --- CSS 優化 ---
st.markdown("""
<style>
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .big-number { font-size: 24px; font-weight: bold; color: #ffffff; }
    .label { font-size: 14px; color: #aaaaaa; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算邏輯 ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

# --- 3. 介面開始 ---
st.title("📱 隔日沖隨身操盤")

tab1, tab2 = st.tabs(["🧮 快速計算機", "📡 市場雷達 (模擬)"])

# === 功能一：手動計算機 ===
with tab1:
    st.markdown("### 輸入今日 K 線數據")
    col1, col2 = st.columns(2)
    with col1:
        p_close = st.number_input("收盤價", value=100.0, step=0.5)
        p_high = st.number_input("最高價", value=100.0, step=0.5)
    with col2:
        p_low = st.number_input("最低價", value=95.0, step=0.5)
        
    if st.button("計算明日點位", type="primary", use_container_width=True):
        ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
        st.markdown(f"""
        <div class="stock-card" style="border-left: 6px solid #4CAF50;">
            <div style="text-align: center;">
                <span class="label">關鍵主力倒貨區 (NH)</span><br>
                <span class="big-number resistance">{nh}</span>
            </div>
            <hr style="margin: 10px 0; border-color: #444;">
            <div style="display: flex; justify-content: space-between;">
                <div><span class="label">最高壓力 (AH)</span><br><span class="resistance">{ah}</span></div>
                <div style="text-align: right;"><span class="label">買進支撐 (NL)</span><br><span class="support">{nl}</span></div>
            </div>
            <div style="margin-top: 10px; text-align: center;"><span class="label">中關價 (CDP): {cdp}</span></div>
        </div>
        """, unsafe_allow_html=True)

# === 功能二：市場雷達 (隨機生成 10 檔) ===
with tab2:
    st.markdown("### 🔥 主力鎖碼熱門股")
    
    # 這裡增加了一個按鈕，點下去會隨機產生資料
    if st.button("🔄 重新掃描市場", type="primary", use_container_width=True):
        
        # 這是股票清單庫，你可以自己加更多名字進去
        stock_names = ["2330 台積電", "2317 鴻海", "2603 長榮", "3231 緯創", "2382 廣達", "3035 智原", "1519 華城", "4966 譜瑞", "6669 緯穎", "2454 聯發科"]
        brokers = ["凱基-台北", "美林", "摩根大通", "虎尾幫", "富邦-建國"]
        
        # 隨機挑選並生成數據
        for name in stock_names:
            base_price = random.randint(50, 800)
            close = base_price
            high = int(base_price * 1.05) # 模擬大漲
            low = int(base_price * 0.98)
            vol = random.randint(2000, 50000)
            broker = random.choice(brokers)
            
            ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
            
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px; font-weight: bold;">{name}</span>
                    <span style="background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{broker}</span>
                </div>
                <div style="margin-top: 5px; color: #ddd; font-size: 13px;">買超: {vol} 張 | 收盤: {close}</div>
                <hr style="margin: 8px 0; border-color: #555;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><span class="label">壓力 (NH)</span><br><span class="resistance">{nh}</span></div>
                    <div><span class="label">支撐 (NL)</span><br><span class="support">{nl}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👆 請點擊上方按鈕開始掃描")
