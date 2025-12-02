import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="主力飆股戰情室", layout="centered")

st.markdown("""
<style>
    /* 卡片樣式優化 */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 修正亂碼問題，使用強制顏色 */
    .stock-name { font-size: 20px; font-weight: bold; color: #ffffff !important; }
    .stock-code { font-size: 14px; color: #cccccc !important; margin-left: 5px; }
    .highlight-red { color: #ff4b4b !important; font-weight: bold; font-size: 18px; }
    
    /* 壓力支撐區塊 */
    .level-box {
        display: flex; 
        justify-content: space-between; 
        background-color: #363940; 
        padding: 8px; 
        border-radius: 6px; 
        margin: 8px 0;
    }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    
    /* 券商區塊 */
    .broker-box {
        font-size: 13px; 
        color: #aaaaaa; 
        margin-top: 5px; 
        border-top: 1px dashed #555; 
        padding-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 (擴充名單) ---
STOCK_MAP = {
    # 飆股與熱門中小型
    "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐", "6274":"台燿", "6213":"智擎",
    "3037":"欣興", "2313":"華通", "2367":"燿華", "2368":"金像電", "8039":"台虹", "6191":"精成科",
    # 散熱 & 機殼
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3032":"偉訓", "8210":"勤誠", "3653":"健策", "2486":"一詮",
    # 重電 & 電纜
    "1609":"大亞", "1605":"華新", "1513":"中興電", "1514":"亞力", "1519":"華城", "1503":"士電", "1504":"東元",
    # 網通 & 光通訊
    "4979":"華星光", "3450":"聯鈞", "4908":"前鼎", "3234":"光環", "3081":"聯亞", "6442":"光聖",
    # IC 設計 & 半導體
    "3035":"智原", "3532":"台勝科", "6182":"合晶", "5347":"世界", "8069":"元太", "4968":"立積", "3006":"晶豪科",
    # 航運
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "2618":"長榮航", "2610":"華航"
}

SCAN_TARGETS = list(STOCK_MAP.keys())

# 模擬券商
BROKERS = ["凱基-台北", "美林", "台灣摩根", "元大-土城永寧", "富邦-建國", "國泰-敦南", "永豐金-虎尾", "統一-嘉義"]

# --- 3. 核心函數 ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2)

def generate_mock_broker_data():
    data = []
    for _ in range(random.randint(3, 5)):
        bk = random.choice(BROKERS)
        vol = random.randint(800, 3000)
        data.append(f"{bk}")
    return " | ".join(data)

# --- 4. 介面設計 ---
st.title("🚀 主力飆股戰情室")

tab1, tab2, tab3 = st.tabs(["⚡ 急拉隔日沖", "🏆 投信排行(模擬)", "🧮 計算機"])

# === 分頁 1: 急拉飆股 (放寬標準版) ===
with tab1:
    if st.button("🔍 掃描今日急拉股 (量大+強勢)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        
        # 顯示目前的篩選條件
        st.info("篩選：股價<300、量>1500、漲幅>1.5% (鎖定隔日沖標的)...")
        
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        valid_stocks = []
        
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    # 檢查資料是否存在
                    if df.empty: continue
                    
                    # 取得最新一筆資料
                    row = df.iloc[-1]
                    
                    # 確保成交量不是 NaN
                    if pd.isna(row['Volume']): continue

                    vol = int(row['Volume'])
                    close = float(row['Close'])
                    open_p = float(row['Open'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    
                    # --- 寬鬆篩選邏輯 ---
                    # 1. 價格 < 300
                    if close > 300: continue
                    
                    # 2. 成交量 > 1500 張 (放寬門檻，確保有資料)
                    if vol < 1500000: continue 
                    
                    # 3. 漲幅 > 1.5% (放寬門檻，只要轉強就顯示)
                    change_pct = ((close - open_p) / open_p) * 100
                    if change_pct < 1.5: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    mock_brokers = generate_mock_broker_data()
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "change": change_pct,
                        "nh": nh, "nl": nl, "brokers": mock_brokers
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            
            # 排序：漲幅大的在上面
            valid_stocks.sort(key=lambda x: x['change'], reverse=True)
            
            if not valid_stocks:
                st.warning("今日無符合「急拉強勢」的標的 (可能行情不好)。")
            else:
                st.success(f"掃描完成！發現 {len(valid_stocks)} 檔強勢標的")
                
                for s in valid_stocks:
                    # 無縮排 HTML，確保不會跑版
                    html = f"""<div class="stock-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div><span class="stock-name">{s['name']}</span> <span class="stock-code">{s['code']}</span></div>
        <span class="highlight-red">+{round(s['change'], 2)}%</span>
    </div>
    <div style="margin-top:5px; color:#ccc; font-size:13px;">
        成交量: {s['vol']} 張 | 收盤: {s['close']}
    </div>
    <div class="level-box">
        <span class="resistance">賣壓(NH): {s['nh']}</span>
        <span class="support">支撐(NL): {s['nl']}</span>
    </div>
    <div class="broker-box">
        <b>⚡ 隔日沖券商 (模擬):</b><br>{s['brokers']}
    </div>
</div>"""
                    st.markdown(html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 投信排行 (模擬) ===
with tab2:
    st.markdown("### 🏆 投信買超排行 (模擬)")
    if st.button("🔄 更新排行", use_container_width=True):
        touxin_list = []
        sample_codes = random.sample(SCAN_TARGETS, 10)
        for code in sample_codes:
            name = STOCK_MAP.get(code, code)
            buy_vol = random.randint(300, 6000)
            touxin_list.append({"code": code, "name": name, "buy": buy_vol})
        
        touxin_list.sort(key=lambda x: x['buy'], reverse=True)
        
        for item in touxin_list:
            st.markdown(f"""<div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #444;">
    <div><span style="color:white; font-weight:bold;">{item['name']}</span> <span style="color:#aaa; font-size:12px;">{item['code']}</span></div>
    <span style="color:#ff4b4b; font-weight:bold;">+{item['buy']} 張</span>
</div>""", unsafe_allow_html=True)

# === 分頁 3: 手動計算 ===
with tab3:
    st.markdown("### 🧮 支撐壓力計算機")
    c1, c2 = st.columns(2)
    with c1:
        p_close = st.number_input("收盤價", value=0.0, step=0.1)
        p_high = st.number_input("最高價", value=0.0, step=0.1)
    with c2:
        p_low = st.number_input("最低價", value=0.0, step=0.1)
        
    if st.button("計算點位", type="primary", use_container_width=True):
        if p_close > 0:
            ah, nh, nl, al = calculate_cdp(p_high, p_low, p_close)
            st.markdown(f"""<div class="stock-card" style="text-align:center;">
    <div style="color:#aaa; font-size:14px;">關鍵賣點 (NH)</div>
    <div class="resistance" style="font-size:28px;">{nh}</div>
    <hr style="border-color:#555; margin:10px 0;">
    <div style="color:#aaa; font-size:14px;">關鍵買點 (NL)</div>
    <div class="support" style="font-size:28px;">{nl}</div>
</div>""", unsafe_allow_html=True)
