import streamlit as st
import pandas as pd
import yfinance as yf

# --- 1. 頁面設定 ---
st.set_page_config(page_title="隔日沖輔助戰情室", layout="centered")

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
    
    .stock-name { font-size: 20px; font-weight: bold; color: #ffffff !important; }
    .stock-code { font-size: 14px; color: #cccccc !important; margin-left: 5px; }
    .highlight-red { color: #ff4b4b !important; font-weight: bold; font-size: 18px; }
    
    /* 壓力支撐區塊 */
    .level-box {
        display: flex; 
        justify-content: space-between; 
        background-color: #363940; 
        padding: 10px; 
        border-radius: 6px; 
        margin: 10px 0;
        border: 1px solid #555;
    }
    .resistance { color: #ff6c6c; font-weight: bold; font-size: 16px; }
    .support { color: #4bceff; font-weight: bold; font-size: 16px; }
    
    /* 計算機結果 */
    .result-pass { color: #ff4b4b; font-weight: bold; font-size: 20px; border: 2px solid #ff4b4b; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px;}
    .result-fail { color: #00c853; font-weight: bold; font-size: 20px; border: 2px solid #00c853; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px;}
    
    /* 警示語 */
    .warning-text { font-size: 12px; color: #aaa; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 ---
STOCK_MAP = {
    # 您的截圖與熱門股
    "2449":"京元電", "2313":"華通", "1504":"東元", "1605":"華新", "3481":"群創", "2317":"鴻海", "2303":"聯電",
    "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐", "6274":"台燿", "6213":"智擎",
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3653":"健策", "1519":"華城", "1513":"中興電",
    "4979":"華星光", "3450":"聯鈞", "3234":"光環", "3035":"智原", "8069":"元太", "2609":"陽明", "2603":"長榮"
}
SCAN_TARGETS = list(STOCK_MAP.keys())

# --- 3. 核心函數 ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2)

# --- 4. 介面設計 ---
st.title("🛡️ 隔日沖輔助戰情室")

tab1, tab2 = st.tabs(["🧮 籌碼集中度計算", "🔥 真實股價掃描"])

# === 分頁 1: 籌碼集中度計算機 (配合籌碼 K 線使用) ===
with tab1:
    st.markdown("### 配合「籌碼K線」使用")
    st.info("請輸入您在籌碼K線看到的數據，幫您判斷是否符合「10% 隔日沖警戒」。")
    
    col1, col2 = st.columns(2)
    with col1:
        total_vol = st.number_input("今日總成交量 (張)", value=0, step=100)
    with col2:
        top5_buy = st.number_input("前5大分點買超總和 (張)", value=0, step=100)
        
    st.caption("例如：京元電總量 48313，前五大買超 (1857+1410+1103+1081+...) = 6386")
    
    if st.button("計算集中度", type="primary", use_container_width=True):
        if total_vol > 0:
            concentration = (top5_buy / total_vol) * 100
            
            st.markdown(f"### 📊 計算結果：{round(concentration, 2)}%")
            
            if concentration >= 10:
                st.markdown(f"""
                <div class="result-pass">
                    ⚠️ 高度鎖碼 (警報)<br>
                    <span style="font-size:14px; color:#ddd;">主力佔比 > 10%，隔日開高易有賣壓</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-fail">
                    ✅ 籌碼分散 (安全)<br>
                    <span style="font-size:14px; color:#ddd;">主力佔比 < 10%，尚未形成絕對控制</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("請輸入成交量")

# === 分頁 2: 真實股價掃描 (Yahoo Finance) ===
with tab2:
    if st.button("🔍 掃描即時行情 (真實股價)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在連線 Yahoo Finance 取得真實報價與支撐壓力...")
        
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
                    
                    # 篩選條件：量 > 1000 且 漲幅 > 1%
                    if vol < 1000000: continue 
                    change_pct = ((close - open_p) / open_p) * 100
                    if change_pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "change": change_pct,
                        "nh": nh, "nl": nl
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            valid_stocks.sort(key=lambda x: x['change'], reverse=True)
            
            st.success(f"掃描完成！以下數據來自 Yahoo Finance (真實)")
            
            for s in valid_stocks:
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><span class="stock-name">{s['name']}</span> <span class="stock-code">{s['code']}</span></div>
                        <span class="highlight-red">+{round(s['change'], 2)}%</span>
                    </div>
                    <div style="margin-top:5px; color:#ccc; font-size:13px;">
                        成交量: {s['vol']} 張 | 收盤: {s['close']}
                    </div>
                    
                    <div class="level-box">
                        <div style="text-align:center; width:48%;">
                            <span style="color:#aaa; font-size:12px;">賣出壓力 (NH)</span><br>
                            <span class="resistance">{s['nh']}</span>
                        </div>
                        <div style="text-align:center; width:48%; border-left:1px solid #555;">
                            <span style="color:#aaa; font-size:12px;">買進支撐 (NL)</span><br>
                            <span class="support">{s['nl']}</span>
                        </div>
                    </div>
                    <div class="warning-text">
                        💡 貼心提醒：請搭配「分頁1」輸入籌碼K線數據，計算主力集中度。
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")
