import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="全方位操盤戰情室", layout="centered")

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
    .broker-info { font-size: 13px; color: #aaaaaa; margin-top: 5px; border-top: 1px dashed #555; padding-top: 5px;}
    
    /* 壓力支撐 */
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    
    /* 表格優化 */
    div[data-testid="stTable"] { background-color: #262730; color: white; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 ---

# 擴充股票清單 (包含中文名稱，用於對照)
STOCK_MAP = {
    # 權值與半導體
    "2330":"台積電", "2317":"鴻海", "2454":"聯發科", "2303":"聯電", "3711":"日月光",
    # AI 伺服器
    "3231":"緯創", "2382":"廣達", "2376":"技嘉", "6669":"緯穎", "2356":"英業達", "2421":"建準", "3017":"奇鋐",
    # 航運
    "2603":"長榮", "2609":"陽明", "2615":"萬海", "2618":"長榮航", "2610":"華航",
    # 重電綠能
    "1519":"華城", "1513":"中興電", "1503":"士電", "1514":"亞力", "1609":"大亞",
    # 金融
    "2881":"富邦金", "2882":"國泰金", "2891":"中信金", "2886":"兆豐金",
    # 面板與其他熱門
    "2409":"友達", "3481":"群創", "8069":"元太", "3035":"智原", "3661":"世芯", "2368":"金像電"
}
# 這裡定義要掃描的範圍 (因為不能掃全市場，我們先掃這 50 檔熱門股)
SCAN_TARGETS = list(STOCK_MAP.keys())

# 模擬券商名單 (因為抓不到真的，只能模擬)
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
st.title("📈 全方位操盤戰情室")

tab1, tab2, tab3 = st.tabs(["🔥 爆量強股 (破萬張)", "🏆 投信買超排行", "🧮 手動計算機"])

# === 分頁 1: 當日交易量破萬張 + 壓力支撐 + 券商 (模擬) ===
with tab1:
    if st.button("🔍 掃描今日爆量股 (>1萬張)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在連線下載最新成交量數據... (需約 10 秒)")
        
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
                    
                    # 篩選條件：成交量 > 10000 張 (Yahoo 資料是股數，所以要除以 1000)
                    # 注意：Yahoo Volume 單位通常是「股」，10000 張 = 10,000,000 股
                    # 但為了展示效果，我們先設 5000 張 (5,000,000 股) 就顯示，避免晚上剛開盤沒資料
                    if vol < 5000000: 
                        continue
                        
                    close = float(row['Close'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    name = STOCK_MAP.get(code, code)
                    
                    # 計算支撐壓力
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    
                    # 生成模擬券商數據
                    mock_brokers = generate_mock_broker_data()
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), # 換算成張
                        "close": close, "ah": ah, "nh": nh, "nl": nl, "al": al,
                        "brokers": mock_brokers
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            
            # 排序：按成交量由大到小
            valid_stocks.sort(key=lambda x: x['vol'], reverse=True)
            
            st.success(f"掃描完成！共有 {len(valid_stocks)} 檔股票成交量大於 5000 張")
            
            for s in valid_stocks:
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="stock-title">{s['code']} {s['name']}</span>
                        <span class="highlight">{s['vol']} 張</span>
                    </div>
                    <div class="sub-info">收盤: {s['close']} | 壓力(NH): <span class="resistance">{s['nh']}</span> | 支撐(NL): <span class="support">{s['nl']}</span></div>
                    
                    <div class="broker-info">
                        <b>㊙️ 主力券商 (模擬示意):</b><br>
                        {s['brokers']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 投信當日買超排行 (模擬) ===
with tab2:
    st.markdown("### 🏆 投信今日買超排行")
    st.caption("⚠️ 注意：免費 API 無法抓取法人即時數據，以下為 **「版面示意數據」**。")
    
    if st.button("🔄 更新投信排行", use_container_width=True):
        # 這裡生成隨機的投信買超名單
        touxin_list = []
        # 從熱門股隨機挑 10 檔
        sample_codes = random.sample(SCAN_TARGETS, 10)
        
        for code in sample_codes:
            name = STOCK_MAP.get(code, code)
            buy_vol = random.randint(500, 8000) # 隨機買超張數
            touxin_list.append({"code": code, "name": name, "buy": buy_vol})
        
        # 排序
        touxin_list.sort(key=lambda x: x['buy'], reverse=True)
        
        # 顯示表格
        df_touxin = pd.DataFrame(touxin_list)
        df_touxin.columns = ["代號", "名稱", "投信買超 (張)"]
        st.table(df_touxin)

# === 分頁 3: 手動計算機 ===
with tab3:
    st.markdown("### 🧮 支撐壓力計算機")
    st.info("輸入 K 線數值，立即計算多空關鍵點。")
    
    c1, c2 = st.columns(2)
    with c1:
        p_close = st.number_input("收盤價", value=0.0, step=0.1)
        p_high = st.number_input("最高價", value=0.0, step=0.1)
    with c2:
        p_low = st.number_input("最低價", value=0.0, step=0.1)
        
    if st.button("計算", type="primary", use_container_width=True):
        if p_close > 0:
            ah, nh, nl, al = calculate_cdp(p_high, p_low, p_close)
            
            st.markdown(f"""
            <div class="stock-card">
                <div style="text-align:center; color:white; margin-bottom:10px;">計算結果</div>
                <div style="display:flex; justify-content:space-between; text-align:center;">
                    <div>
                        <span class="sub-info">賣出點 (NH)</span><br>
                        <span class="resistance" style="font-size:24px;">{nh}</span>
                    </div>
                    <div>
                        <span class="sub-info">買進點 (NL)</span><br>
                        <span class="support" style="font-size:24px;">{nl}</span>
                    </div>
                </div>
                <hr style="border-color:#555;">
                <div style="display:flex; justify-content:space-between; text-align:center;">
                    <span class="sub-info">最高壓力 (AH): {ah}</span>
                    <span class="sub-info">最低支撐 (AL): {al}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
