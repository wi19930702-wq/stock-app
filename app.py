import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="當沖戰情室", layout="centered")

st.markdown("""
<style>
    /* 全局背景色與卡片 */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 字體顏色優化 (強制白色) */
    .stock-title { font-size: 22px; font-weight: bold; color: #ffffff !important; }
    .sub-info { font-size: 14px; color: #cccccc !important; }
    .highlight { color: #ff4b4b; font-weight: bold; }
    
    /* 修正原本跑版的區塊 */
    .broker-box {
        background-color: #363940; 
        padding: 10px; 
        border-radius: 8px; 
        margin-top: 10px;
        font-size: 13px; 
        color: #e0e0e0;
        border: 1px dashed #666;
    }
    
    /* 壓力支撐 */
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    
    /* 表格優化 */
    div[data-testid="stTable"] { background-color: #262730; color: white; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 ---

# 擴充股票清單 (包含中文名稱)
STOCK_MAP = {
    # 電子權值 & AI
    "2330":"台積電", "2317":"鴻海", "2454":"聯發科", "2303":"聯電", "3711":"日月光",
    "3231":"緯創", "2382":"廣達", "2376":"技嘉", "6669":"緯穎", "2356":"英業達",
    "3017":"奇鋐", "3324":"雙鴻", "2421":"建準", "3653":"健策", "3035":"智原",
    # 航運 & 傳產
    "2603":"長榮", "2609":"陽明", "2615":"萬海", "2618":"長榮航", "2610":"華航",
    "1519":"華城", "1513":"中興電", "1503":"士電", "1609":"大亞",
    # 面板 & 其他熱門當沖
    "2409":"友達", "3481":"群創", "6116":"彩晶", "8069":"元太", "2368":"金像電",
    "2449":"京元電", "6274":"台燿", "4968":"立積", "3532":"台勝科", "5347":"世界"
}
SCAN_TARGETS = list(STOCK_MAP.keys())

# 模擬券商名單
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
    """生成模擬的券商買超前五名"""
    data = []
    for _ in range(5):
        bk = random.choice(BROKERS)
        vol = random.randint(500, 5000)
        data.append(f"{bk} (+{vol})")
    return " | ".join(data)

# --- 4. 介面設計 ---
st.title("⚡ 當沖戰情室")

tab1, tab2, tab3 = st.tabs(["🔥 爆量當沖股", "🏆 投信排行(模擬)", "🧮 手動計算"])

# === 分頁 1: 爆量當沖 (嚴格篩選) ===
with tab1:
    if st.button("🔍 掃描 1 萬張以上 + 有波動", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在篩選：成交量 > 10,000 張 且 波動率 > 2% ...")
        
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        valid_stocks = []
        
        try:
            # 批量下載數據
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty or pd.isna(df.iloc[-1]['Volume']): continue
                    
                    row = df.iloc[-1]
                    vol = int(row['Volume'])
                    
                    # --- 關鍵修正：篩選條件 ---
                    # 1. 成交量必須大於 10,000 張 (Yahoo 資料是股數，1張=1000股)
                    if vol < 10000000:  # 10,000,000 股 = 10,000 張
                        continue
                        
                    close = float(row['Close'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    open_p = float(row['Open'])
                    
                    # 2. 波動率篩選 (當沖要有波動才好做)
                    # 振幅 = (最高-最低) / 開盤
                    amplitude = ((high - low) / open_p) * 100
                    if amplitude < 2.0: # 振幅小於 2% 的死魚股不要顯示
                        continue

                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    mock_brokers = generate_mock_broker_data()
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "ah": ah, "nh": nh, "nl": nl, "al": al,
                        "brokers": mock_brokers, "amp": amplitude
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            valid_stocks.sort(key=lambda x: x['vol'], reverse=True)
            
            if not valid_stocks:
                st.warning("今日市場冷清，暫無符合「萬張且有波動」的標的。")
            else:
                st.success(f"掃描完成！發現 {len(valid_stocks)} 檔熱門當沖標的")
                
                for s in valid_stocks:
                    # 這裡使用去掉縮排的 HTML 寫法，解決跑版問題
                    html_content = f"""
                    <div class="stock-card">
                        <div style="display:flex; justify-content:space-between;">
                            <span class="stock-title">{s['code']} {s['name']}</span>
                            <span class="highlight">{s['vol']} 張</span>
                        </div>
                        <div class="sub-info">
                            收盤: {s['close']} | 振幅: {round(s['amp'], 2)}%
                        </div>
                        <div style="margin-top:5px; display:flex; justify-content:space-between;">
                             <span class="resistance">壓力(NH): {s['nh']}</span>
                             <span class="support">支撐(NL): {s['nl']}</span>
                        </div>
                        <div class="broker-box">
                            <b>㊙️ 主力券商 (模擬):</b><br>
                            {s['brokers']}
                        </div>
                    </div>
                    """
                    st.markdown(html_content, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 投信排行 (模擬) ===
with tab2:
    st.markdown("### 🏆 投信今日買超 (模擬數據)")
    if st.button("🔄 更新排行", use_container_width=True):
        touxin_list = []
        sample_codes = random.sample(SCAN_TARGETS, 12)
        for code in sample_codes:
            name = STOCK_MAP.get(code, code)
            buy_vol = random.randint(500, 12000)
            touxin_list.append({"code": code, "name": name, "buy": buy_vol})
        
        touxin_list.sort(key=lambda x: x['buy'], reverse=True)
        
        # 使用自訂 HTML 表格美化
        for item in touxin_list:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #444;">
                <span style="color:white; font-weight:bold;">{item['code']} {item['name']}</span>
                <span style="color:#ff4b4b;">+{item['buy']} 張</span>
            </div>
            """, unsafe_allow_html=True)

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
            st.markdown(f"""
            <div class="stock-card" style="text-align:center;">
                <div style="color:#aaa; font-size:14px;">關鍵賣點 (NH)</div>
                <div class="resistance" style="font-size:28px;">{nh}</div>
                <hr style="border-color:#555; margin:10px 0;">
                <div style="color:#aaa; font-size:14px;">關鍵買點 (NL)</div>
                <div class="support" style="font-size:28px;">{nl}</div>
            </div>
            """, unsafe_allow_html=True)
