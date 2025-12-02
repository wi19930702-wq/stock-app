import streamlit as st
import pandas as pd
import yfinance as yf

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
st.caption("資料來源：Yahoo Finance (延遲報價)")

tab1, tab2 = st.tabs(["🧮 手動計算機", "📈 查詢真實股價"])

# === 功能一：手動計算機 (最推薦) ===
with tab1:
    st.info("💡 這是最準確的方式！請看著您的看盤軟體輸入數據。")
    col1, col2 = st.columns(2)
    with col1:
        p_close = st.number_input("收盤價", value=222.0, step=0.5)
        p_high = st.number_input("最高價", value=225.0, step=0.5)
    with col2:
        p_low = st.number_input("最低價", value=220.0, step=0.5)
        
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

# === 功能二：真實股價查詢 ===
with tab2:
    st.markdown("### 🔍 輸入代號抓取股價")
    stock_id = st.text_input("輸入股票代號 (例如 2317)", "2317")
    
    if st.button("抓取最新股價", use_container_width=True):
        try:
            with st.spinner('正在連線 Yahoo Finance...'):
                stock = yf.Ticker(f"{stock_id}.TW")
                # 取得最新一天的資料
                data = stock.history(period="1d")
                
                if not data.empty:
                    # 抓取真實數據
                    real_close = data['Close'].iloc[-1]
                    real_high = data['High'].iloc[-1]
                    real_low = data['Low'].iloc[-1]
                    
                    # 計算
                    ah, nh, nl, al, cdp = calculate_cdp(real_high, real_low, real_close)
                    
                    st.success(f"成功抓到 {stock_id} 股價：{round(real_close, 2)}")
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 18px; font-weight: bold;">{stock_id} (即時運算)</span>
                        </div>
                        <div style="margin-top: 5px; color: #ddd; font-size: 13px;">
                            收盤: {round(real_close, 2)} | 高: {real_high} | 低: {real_low}
                        </div>
                        <hr style="margin: 8px 0; border-color: #555;">
                        <div style="display: flex; justify-content: space-between; text-align: center;">
                            <div><span class="label">壓力 (NH)</span><br><span class="resistance">{nh}</span></div>
                            <div><span class="label">支撐 (NL)</span><br><span class="support">{nl}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.warning("⚠️ 注意：Yahoo 資料可能有 15 分鐘延遲，且不包含主力籌碼資訊。")
                else:
                    st.error("找不到此股票資料，請確認代號是否正確。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

