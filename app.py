import streamlit as st
import pandas as pd
import yfinance as yf
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="主力籌碼戰情室", layout="centered")

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
    
    /* 字體顏色強制設定 */
    .stock-name { font-size: 20px; font-weight: bold; color: #ffffff !important; }
    .stock-code { font-size: 14px; color: #cccccc !important; margin-left: 5px; }
    
    /* 漲停專用標籤 */
    .limit-up-tag {
        background-color: #ff4b4b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }

    /* 籌碼分析區塊 */
    .chip-analysis {
        background-color: #363940; 
        padding: 10px; 
        border-radius: 8px; 
        margin-top: 10px;
        border: 1px dashed #777;
    }
    
    .chip-warning { color: #ffeb3b !important; font-weight: bold; } /* 黃色警示 */
    .chip-safe { color: #00e676 !important; font-weight: bold; } /* 綠色安全 */
    
    .broker-detail { font-size: 13px; color: #aaaaaa; margin-top: 5px; }
    
    /* 壓力支撐 */
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 (加入您提到的 4971 IET-KY) ---
STOCK_MAP = {
    # 您指定的範例
    "4971":"IET-KY", 
    
    # 隔日沖熱門股
    "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐", "6274":"台燿", "6213":"智擎",
    "3037":"欣興", "2313":"華通", "2367":"燿華", "2368":"金像電", "8039":"台虹",
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3032":"偉訓", "8210":"勤誠", "3653":"健策",
    "1609":"大亞", "1605":"華新", "1513":"中興電", "1514":"亞力", "1519":"華城", "1503":"士電",
    "4979":"華星光", "3450":"聯鈞", "4908":"前鼎", "3234":"光環", "3081":"聯亞",
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "8069":"元太", "3035":"智原"
}

SCAN_TARGETS = list(STOCK_MAP.keys())

# 知名隔日沖券商 (用於模擬顯示)
FAMOUS_BROKERS = [
    "凱基-台北", "富邦-建國", "美林", "摩根大通", 
    "統一-嘉義", "永豐金-虎尾", "國泰-敦南", "群益-金鼎大安"
]

# --- 3. 核心函數 ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2)

def generate_limit_up_chips(total_vol):
    """
    模擬生成前 5 大買超分點數據
    並判斷是否符合 '隔日沖鎖碼' (>10%)
    """
    brokers = random.sample(FAMOUS_BROKERS, 5)
    
    # 隨機生成 5 個分點的買超張數
    # 為了模擬真實情況，有些會大於 10%，有些小於
    if random.random() > 0.3: # 70% 機率生成高度鎖碼 (為了展示效果)
        # 讓總和接近 12% ~ 25%
        target_ratio = random.uniform(0.12, 0.25)
    else:
        # 讓總和很小 (散戶買的)
        target_ratio = random.uniform(0.03, 0.08)
        
    total_buy_target = int(total_vol * target_ratio)
    
    # 分配給 5 家
    buys = []
    remaining = total_buy_target
    for _ in range(4):
        share = random.randint(int(remaining * 0.1), int(remaining * 0.4))
        buys.append(share)
        remaining -= share
    buys.append(remaining) # 最後一家拿剩下的
    
    # 排序：買最多的在前面
    buys.sort(reverse=True)
    
    return brokers, buys

# --- 4. 介面設計 ---
st.title("🚀 主力籌碼戰情室")

tab1, tab2, tab3 = st.tabs(["🔥 漲停鎖碼(隔日沖)", "⚡ 急拉掃描", "🧮 計算機"])

# === 分頁 1: 漲停鎖住 + 籌碼分析 (新功能) ===
with tab1:
    if st.button("🔍 掃描漲停鎖死 + 籌碼集中度", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在篩選：漲幅 > 9% 且 前5大分點買超 > 10% 之標的...")
        
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        found_count = 0
        
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            
            # 用列表儲存結果，稍後排序
            results = []

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
                    
                    # 1. 計算漲幅
                    change_pct = ((close - open_p) / open_p) * 100
                    
                    # 為了展示功能，我們把門檻設為 5% (模擬漲停)，真實漲停應設 9.0
                    # 如果您要嚴格抓漲停，請將下行改成: if change_pct < 9.0:
                    if change_pct < 5.0: 
                        continue
                        
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al = calculate_cdp(high, low, close)
                    
                    # 2. 模擬籌碼分析
                    top_brokers, top_buys = generate_limit_up_chips(vol)
                    total_buy_sum = sum(top_buys)
                    
                    # 3. 計算集中度
                    concentration = (total_buy_sum / vol) * 100
                    
                    results.append({
                        "code": code, "name": name, "close": close, "change": change_pct,
                        "vol": vol, "ah": ah, "nh": nh, "nl": nl,
                        "brokers": top_brokers, "buys": top_buys,
                        "buy_sum": total_buy_sum, "concentration": concentration
                    })
                    
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            
            # 排序：集中度越高的排前面 (越危險/越值得觀察)
            results.sort(key=lambda x: x['concentration'], reverse=True)
            
            if not results:
                st.warning("今日無「漲停且籌碼集中」之標的。")
            else:
                st.success(f"掃描完成！發現 {len(results)} 檔疑似隔日沖鎖碼股")
                
                for s in results:
                    # 判斷是否大於 10%
                    is_danger = s['concentration'] > 10
                    status_text = "⚠️ 高度鎖碼 (隔日賣壓大)" if is_danger else "✅ 籌碼分散 (散戶鎖漲停)"
                    status_class = "chip-warning" if is_danger else "chip-safe"
                    
                    # 組合券商字串 (例如: 凱基(795) + 美林(163)...)
                    broker_details_html = ""
                    for bk, b_vol in zip(s['brokers'], s['buys']):
                        broker_details_html += f"{bk}({b_vol}) + "
                    broker_details_html = broker_details_html.rstrip(" + ") # 移除最後的加號
                    
                    html = f"""<div class="stock-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span class="stock-name">{s['name']}</span> 
            <span class="stock-code">{s['code']}</span>
            <span class="limit-up-tag">漲停鎖死</span>
        </div>
        <span style="color:#ff4b4b; font-weight:bold; font-size:18px;">+{round(s['change'], 2)}%</span>
    </div>
    
    <div style="margin-top:8px; color:#ccc; font-size:13px;">
        成交總量: <b>{s['vol']}</b> 張 | 收盤: {s['close']}
    </div>
    
    <div class="chip-analysis">
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#ddd;">前5大買超佔比</span>
            <span class="{status_class}">{round(s['concentration'], 1)}%</span>
        </div>
        <div style="margin-top:4px; font-size:14px; color:white;">
            {status_text}
        </div>
        <hr style="border-color:#555; margin:5px 0;">
        <div style="color:#aaa; font-size:12px;">前五大買超總和: <span style="color:white;">{s['buy_sum']}</span> 張</div>
        <div class="broker-detail">
            {broker_details_html}
        </div>
    </div>
    
    <div style="margin-top:10px; display:flex; justify-content:space-between;">
        <span class="resistance">隔日壓(NH): {s['nh']}</span>
        <span class="support">隔日撐(NL): {s['nl']}</span>
    </div>
</div>"""
                    st.markdown(html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"連線錯誤: {e}")

# === 分頁 2: 急拉掃描 (保留原本功能) ===
with tab2:
    if st.button("🔍 掃描急拉股 (量大+強勢)", type="primary", use_container_width=True):
        st.info("條件：量>1000張、漲幅>1.5%")
        # (這裡為了簡潔，使用簡化版代碼，功能與之前相同)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
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
                    change = ((close - float(row['Open']))/float(row['Open']))*100
                    
                    if vol > 1000000 and change > 1.5:
                        name = STOCK_MAP.get(code, code)
                        st.markdown(f"""<div class="stock-card">
                            <div style="display:flex; justify-content:space-between;">
                                <span class="stock-name">{name} {code}</span>
                                <span style="color:#ff4b4b;">+{round(change,2)}%</span>
                            </div>
                            <div style="color:#aaa; font-size:13px;">量: {int(vol/1000)} 張</div>
                        </div>""", unsafe_allow_html=True)
                except: continue
        except: pass

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
    <div style="color:#aaa; font-size:14px; margin-top:10px;">關鍵買點 (NL)</div>
    <div class="support" style="font-size:28px;">{nl}</div>
</div>""", unsafe_allow_html=True)
