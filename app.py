import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="飆股戰情室", layout="centered")

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
    
    /* 強制字體顏色 (解決投信看不到字的問題) */
    .stock-name-text { font-size: 18px; font-weight: bold; color: #ffffff !important; }
    .stock-code-text { font-size: 14px; color: #aaaaaa !important; }
    
    .highlight { color: #ff4b4b; font-weight: bold; }
    .sub-info { font-size: 13px; color: #cccccc !important; }
    
    /* 券商框框 */
    .broker-box {
        background-color: #363940; 
        padding: 10px; 
        border-radius: 8px; 
        margin-top: 10px;
        font-size: 13px; 
        color: #e0e0e0;
        border: 1px dashed #666;
    }
    
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 (換血：移除牛皮股，加入中小型飆股) ---

STOCK_MAP = {
    # PCB & 軟板 (亞電概念)
    "4939":"亞電", "6269":"台郡", "8046":"南電", "3037":"欣興", "2313":"華通", "6274":"台燿", "2368":"金像電", "5349":"先豐",
    # 電線電纜 & 重電 (最近很熱)
    "1609":"大亞", "1605":"華新", "1513":"中興電", "1514":"亞力", "1504":"東元",
    # 散熱 & 機殼
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3032":"偉訓", "8210":"勤誠",
    # 網通 & 光通訊
    "4979":"華星光", "3450":"聯鈞", "4908":"前鼎", "3234":"光環",
    # IC 設計 & 半導體 (中小型)
    "3035":"智原", "3532":"台勝科", "6182":"合晶", "5347":"世界", "8069":"元太", "4968":"立積", "6213":"智擎",
    # 航運 (波動大)
    "2603":"長榮", "2609":"陽明", "2615":"萬海", "2618":"長榮航", "2610":"華航",
    # AI 組裝 (篩選掉太貴的)
    "3231":"緯創", "2356":"英業達", "2382":"廣達", "2376":"技嘉"
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
        vol = random.randint(500, 3000)
        data.append(f"{bk} (+{vol})")
    return " | ".join(data)

# --- 4. 介面設計 ---
st.title("🚀 中小型飆股戰情室")

tab1, tab2, tab3 = st.tabs(["⚡ 爆量急拉股", "🏆 投信排行(模擬)", "🧮 手動計算"])

# === 分頁 1: 爆量當沖 (嚴格篩選: 300元以下 + 1萬張 + 高波動) ===
with tab1:
    if st.button("🔍 掃描 300元以下 + 爆量萬張", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("篩選條件：股價 < 300、成交量 > 10,000、振幅 > 3% ...")
        
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
                    close = float(row['Close'])
                    
                    # --- 關鍵修正：篩選條件 ---
                    
                    # 1. 價格篩選：只看 300 元以下的股票 (小資/主力好拉)
                    if close > 300:
                        continue
                        
                    # 2. 成交量篩選：大於 10,000 張 (Yahoo 資料是股數)
                    # 註：10,000,000 股 = 10,000 張
                    if vol < 10000000: 
                        continue
                        
                    high = float(row['High'])
                    low = float(row['Low'])
                    open_p = float(row['Open'])
                    
                    # 3. 波動率篩選：振幅 > 3% (確保是活潑股)
                    if open_p > 0:
                        amplitude = ((high - low) / open_p) * 100
                        if amplitude < 3.0: # 剔除死魚
                            continue
                    else:
                        amplitude = 0

                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    mock_brokers = generate_mock_broker_data()
                    
                    # 計算漲跌幅
                    change_pct = ((close - open_p) / open_p) * 100
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "ah": ah, "nh": nh, "nl": nl, "amp": amplitude,
                        "change": change_pct, "brokers": mock_brokers
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            
            # 排序：優先顯示波動大的 (當沖最愛)
            valid_stocks.sort(key=lambda x: x['vol'], reverse=True)
            
            if not valid_stocks:
                st.warning("今日掃描後，無符合「300元以下、萬張且高波動」的標的。")
            else:
                st.success(f"掃描完成！發現 {len(valid_stocks)} 檔中小型熱門股")
                
                for s in valid_stocks:
                    color = "#ff4b4b" if s['change'] >= 0 else "#00c853"
                    
                    html_content = f"""
                    <div class="stock-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span class="stock-name-text">{s['name']}</span> 
                                <span class="stock-code-text">{s['code']}</span>
                            </div>
                            <span class="highlight" style="font-size:18px;">{s['vol']} 張</span>
                        </div>
                        
                        <div style="margin-top:8px; display:flex; justify-content:space-between;">
                             <span class="sub-info">收盤: <b>{s['close']}</b></span>
                             <span style="color:{color}; font-weight:bold;">漲幅 {round(s['change'], 2)}%</span>
                        </div>
                        
                        <hr style="border-color:#444; margin:8px 0;">
                        
                        <div style="display:flex; justify-content:space-between;">
                             <span class="resistance">壓力(NH): {s['nh']}</span>
                             <span class="support">支撐(NL): {s['nl']}</span>
                        </div>
                        
                        <div class="broker-box">
                            <b>⚡ 隔日沖券商 (模擬):</b><br>
                            {s['brokers']}
                        </div>
                    </div>
                    """
                    st.markdown(html_content, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 投信排行 (修復顯示問題) ===
with tab2:
    st.markdown("### 🏆 投信買超排行 (模擬)")
    
    if st.button("🔄 更新排行", use_container_width=True):
        touxin_list = []
        # 從清單隨機挑選，確保有名字
        sample_codes = random.sample(SCAN_TARGETS, 12)
        
        for code in sample_codes:
            name = STOCK_MAP.get(code, code)
            buy_vol = random.randint(300, 5000)
            touxin_list.append({"code": code, "name": name, "buy": buy_vol})
        
        touxin_list.sort(key=lambda x: x['buy'], reverse=True)
        
        # 使用 Flex 排版並強制字體顏色
        for item in touxin_list:
            st.markdown(f"""
            <div style="
                display:flex; 
                justify-content:space-between; 
                align-items:center;
                padding:12px; 
                border-bottom:1px solid #444;
                background-color: #262730;
                margin-bottom: 2px;
                border-radius: 5px;
            ">
                <div>
                    <span style="color:white; font-size:16px; font-weight:bold;">{item['name']}</span>
                    <span style="color:#aaa; font-size:13px; margin-left:5px;">{item['code']}</span>
                </div>
                <span style="color:#ff4b4b; font-weight:bold;">+{item['buy']} 張</span>
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
