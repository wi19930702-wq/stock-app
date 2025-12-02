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
    
    /* 字體顏色強制設定 */
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
        border: 1px solid #555;
    }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    
    /* 券商區塊 */
    .broker-box {
        font-size: 13px; 
        color: #aaaaaa; 
        margin-top: 5px; 
        border-top: 1px dashed #555; 
        padding-top: 8px;
    }
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
    /* 特別標註重點券商顏色 */
    .kgi-tag { background-color: #d32f2f; color: white; border: 1px solid #ff5252; } /* 凱基台北紅 */
    .fubon-tag { background-color: #1976d2; color: white; border: 1px solid #448aff; } /* 富邦藍 */
    .foreign-tag { background-color: #388e3c; color: white; border: 1px solid #69f0ae; } /* 外資綠 */
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 (擴充熱門股名單) ---
STOCK_MAP = {
    # 隔日沖熱門 - 中小型電子 & PCB
    "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐", "6274":"台燿", "6213":"智擎",
    "3037":"欣興", "2313":"華通", "2367":"燿華", "2368":"金像電", "8039":"台虹", "6191":"精成科",
    "3035":"智原", "3532":"台勝科", "6182":"合晶", "5347":"世界", "8069":"元太", "4968":"立積",
    "2449":"京元電", "6147":"頎邦", "3260":"威剛", "8299":"群聯",
    
    # 散熱 & 機殼
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3032":"偉訓", "8210":"勤誠", "3653":"健策", 
    "2486":"一詮", "3483":"力致", "3338":"泰碩",
    
    # 重電 & 綠能
    "1609":"大亞", "1605":"華新", "1513":"中興電", "1514":"亞力", "1519":"華城", "1503":"士電", 
    "1504":"東元", "3708":"上緯投控", "9958":"世紀鋼",
    
    # 網通 & 光通訊
    "4979":"華星光", "3450":"聯鈞", "4908":"前鼎", "3234":"光環", "3081":"聯亞", "6442":"光聖",
    "3704":"合勤控", "5388":"中磊",
    
    # 航運 & 其他
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "2618":"長榮航", "2610":"華航", "2634":"漢翔"
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

def generate_mock_broker_html():
    """
    生成模擬券商顯示。
    注意：這是「模擬」的，因為免費 API 抓不到真實分點。
    這裡我們鎖定市場最知名的隔日沖分點。
    """
    # 定義知名隔日沖與外資分點
    BROKER_POOLS = [
        ("凱基-台北", "kgi-tag"), 
        ("富邦-建國", "fubon-tag"), 
        ("美林", "foreign-tag"), 
        ("摩根大通", "foreign-tag"), 
        ("統一-嘉義", "broker-tag"), 
        ("永豐金-虎尾", "broker-tag"), 
        ("國泰-敦南", "broker-tag"),
        ("群益-金鼎大安", "broker-tag")
    ]
    
    # 隨機挑選 3 家顯示
    selected = random.sample(BROKER_POOLS, 3)
    
    html_parts = []
    for name, css_class in selected:
        vol = random.randint(600, 3500) # 模擬張數
        html_parts.append(f'<span class="broker-tag {css_class}">{name} +{vol}</span>')
        
    return " ".join(html_parts)

# --- 4. 介面設計 ---
st.title("🚀 主力飆股戰情室")

# 警示語，避免誤會
st.caption("⚠️ 注意：股價與支撐壓力為 Yahoo 真實數據；券商分點與投信排行為模擬數據（免費源無法取得）。")

tab1, tab2, tab3 = st.tabs(["⚡ 隔日沖熱門", "🏆 投信排行(模擬)", "🧮 計算機"])

# === 分頁 1: 急拉飆股 (模擬券商版) ===
with tab1:
    if st.button("🔍 掃描全市場 (顯示主力分點)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        
        st.info("條件：量>1000張、漲幅>1% (顯示潛在隔日沖標的)...")
        
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        valid_stocks = []
        
        try:
            # 批量下載加快速度
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
                    
                    # --- 寬鬆篩選邏輯，確保有資料 ---
                    # 1. 價格 < 350
                    if close > 350: continue
                    
                    # 2. 成交量 > 1000 張
                    if vol < 1000000: continue 
                    
                    # 3. 漲幅 > 1.0% (只要紅盤轉強就顯示)
                    change_pct = ((close - open_p) / open_p) * 100
                    if change_pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    
                    # 生成模擬的券商 HTML
                    brokers_html = generate_mock_broker_html()
                    
                    valid_stocks.append({
                        "code": code, "name": name, "vol": int(vol/1000), 
                        "close": close, "change": change_pct,
                        "nh": nh, "nl": nl, "brokers_html": brokers_html
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            
            # 排序：漲幅大的在上面
            valid_stocks.sort(key=lambda x: x['change'], reverse=True)
            
            if not valid_stocks:
                st.warning("今日市場極度冷清，無符合標的。")
            else:
                st.success(f"掃描完成！發現 {len(valid_stocks)} 檔主力介入股")
                
                for s in valid_stocks:
                    html = f"""<div class="stock-card">
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
    <div class="broker-box">
        <div style="margin-bottom:4px; font-weight:bold; color:#e0e0e0;">⚡ 疑似隔日沖主力 (模擬):</div>
        {s['brokers_html']}
    </div>
</div>"""
                    st.markdown(html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 投信排行 (模擬) ===
with tab2:
    st.markdown("### 🏆 投信買超排行 (模擬數據)")
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
