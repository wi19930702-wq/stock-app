import streamlit as st
import pandas as pd
import random

# --- 1. 手機版面設定 ---
st.set_page_config(page_title="隔日沖戰情室", layout="centered") # layout="centered" 比較適合手機閱讀

# --- CSS 優化 (讓手機看起來像 App) ---
st.markdown("""
<style>
    /* 卡片樣式 */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* 強調數字 */
    .big-number {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
    }
    .label {
        font-size: 14px;
        color: #aaaaaa;
    }
    /* 壓力支撐顏色 */
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    
    /* 隱藏預設選單讓介面更乾淨 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算邏輯 (CDP) ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

# --- 3. 介面開始 ---
st.title("📱 隔日沖隨身操盤")

# 使用分頁 (Tabs) 切換功能
tab1, tab2 = st.tabs(["🧮 快速計算機", "📡 市場雷達 (模擬)"])

# === 功能一：手動計算機 (適合手機隨手算) ===
with tab1:
    st.markdown("### 輸入今日 K 線數據")
    st.info("適合當你看到某檔股票主力大買，想立刻算明天的點位時使用。")
    
    col1, col2 = st.columns(2)
    with col1:
        p_close = st.number_input("收盤價", value=100.0, step=0.5)
        p_high = st.number_input("最高價", value=100.0, step=0.5)
    with col2:
        p_low = st.number_input("最低價", value=95.0, step=0.5)
        
    if st.button("計算明日點位", type="primary", use_container_width=True):
        ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
        
        st.markdown("---")
        # 手機版結果顯示
        st.markdown(f"""
        <div class="stock-card" style="border-left: 6px solid #4CAF50;">
            <div style="text-align: center;">
                <span class="label">關鍵主力倒貨區 (NH)</span><br>
                <span class="big-number resistance">{nh}</span>
            </div>
            <hr style="margin: 10px 0; border-color: #444;">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span class="label">最高壓力 (AH)</span><br>
                    <span class="resistance">{ah}</span>
                </div>
                <div style="text-align: right;">
                    <span class="label">買進支撐 (NL)</span><br>
                    <span class="support">{nl}</span>
                </div>
            </div>
            <div style="margin-top: 10px; text-align: center;">
                <span class="label">中關價 (CDP): {cdp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# === 功能二：市場雷達 (模擬清單) ===
with tab2:
    st.markdown("### 🔥 主力鎖碼熱門股")
    
    # 模擬數據 (與之前相同，但顯示方式優化)
    if st.button("重新掃描市場", use_container_width=True):
        stocks = [
            {"name": "3231 緯創", "close": 110, "high": 110, "low": 108, "broker": "凱基-台北", "vol": 5000},
            {"name": "2609 陽明", "close": 45.5, "high": 45.5, "low": 43, "broker": "美林", "vol": 12000},
            {"name": "1519 華城", "close": 380, "high": 380, "low": 365, "broker": "摩根大通", "vol": 800}
        ]
        
        for s in stocks:
            ah, nh, nl, al, cdp = calculate_cdp(s['high'], s['low'], s['close'])
            
            # 使用 HTML 繪製卡片，不使用 dataframe
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px; font-weight: bold;">{s['name']}</span>
                    <span style="background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{s['broker']}</span>
                </div>
                <div style="margin-top: 5px; color: #ddd; font-size: 13px;">
                    買超: {s['vol']} 張 | 收盤: {s['close']}
                </div>
                <hr style="margin: 8px 0; border-color: #555;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div>
                        <span class="label">壓力 (NH)</span><br>
                        <span class="resistance">{nh}</span>
                    </div>
                    <div>
                        <span class="label">支撐 (NL)</span><br>
                        <span class="support">{nl}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

