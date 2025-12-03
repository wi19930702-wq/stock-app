import streamlit as st
import pandas as pd
import yfinance as yf
import twstock
import time
import random

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="極速當沖戰情室", layout="centered")

st.markdown("""
<style>
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-green { border-left: 6px solid #00c853; } /* 轉弱做空 */
    .card-red { border-left: 6px solid #ff4b4b; }   /* 隔日沖 */
    
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    
    /* 盤中轉弱專用 */
    .bearish-alert {
        background-color: #1b5e20;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        float: right;
    }
    
    /* 即時標籤 */
    .live-tag {
        background-color: #d50000;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 ---
STOCK_MAP = {
    "2330":"台積電", "2317":"鴻海", "2382":"廣達", "3231":"緯創", "2376":"技嘉", "6669":"緯穎", "2356":"英業達",
    "2454":"聯發科", "2303":"聯電", "3711":"日月光", "3443":"創意", "3661":"世芯", "3035":"智原",
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3653":"健策", "3032":"偉訓", "8210":"勤誠", "2486":"一詮",
    "3338":"泰碩", "3483":"力致", "6117":"迎廣",
    "1519":"華城", "1513":"中興電", "1503":"士電", "1514":"亞力", "1504":"東元", 
    "1609":"大亞", "1605":"華新", "3708":"上緯", "9958":"世紀鋼", "6806":"森崴",
    "2368":"金像電", "6274":"台燿", "8358":"金居", "4979":"華星光", "3450":"聯鈞", 
    "3234":"光環", "3081":"聯亞", "6442":"光聖", "4908":"前鼎", "5388":"中磊",
    "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐", "6213":"智擎", "3037":"欣興", 
    "2313":"華通", "2367":"燿華", "8039":"台虹", "6191":"精成科", "6147":"頎邦", "3260":"威剛",
    "3532":"台勝科", "6182":"合晶", "5347":"世界", "8069":"元太", "4968":"立積", "3006":"晶豪科",
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "2618":"長榮航", "2610":"華航", 
    "2634":"漢翔", "8033":"雷虎", "4763":"材料"
}
SCAN_TARGETS = list(STOCK_MAP.keys())

# --- 3. 核心函數 ---
def calculate_cdp(high, low, close):
    try:
        h, l, c = float(high), float(low), float(close)
        cdp = (h + l + c * 2) / 4
        ah = cdp + (h - l)
        nh = cdp * 2 - l
        nl = cdp * 2 - h
        al = cdp - (h - l)
        return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2)
    except:
        return 0,0,0,0

def generate_mock_broker_html():
    BROKER_POOLS = [("凱基-台北", "#d32f2f"), ("富邦-建國", "#1976d2"), ("美林", "#444"), ("摩根大通", "#444"), ("統一-嘉義", "#444"), ("永豐金-虎尾", "#444")]
    selected = random.sample(BROKER_POOLS, 3)
    html_parts = []
    for name, color in selected:
        vol = random.randint(500, 3000)
        html_parts.append(f'<span style="background-color:{color}; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:4px; color:white; display:inline-block; margin-bottom:2px;">{name} +{vol}</span>')
    return "".join(html_parts)

# --- 4. 介面設計 ---
st.title("⚡ 極速當沖戰情室")

# 分頁順序調整：把盤中即時轉弱放到第一個，方便您 9:05 使用
tab1, tab2, tab3 = st.tabs(["📉 盤中轉弱 (TWSE即時)", "🔥 隔日沖雷達 (Yahoo)", "🧮 計算機"])

# === 分頁 1: 盤中轉弱雷達 (改用 Twstock 即時源) ===
with tab1:
    st.markdown("### 📉 9:00~13:30 即時做空雷達")
    st.info("🔥 資料來源：證交所即時資訊 (無延遲)。適合 09:05 開盤後使用。")
    st.warning("⚠️ 請勿頻繁刷新 (建議間隔 10 秒)，以免被證交所封鎖 IP。")
    
    if st.button("🚀 掃描轉弱股 (即時)", use_container_width=True):
        st.cache_data.clear()
        progress_bar = st.progress(0)
        
        results = []
        
        # Twstock 支援批量抓取，我們把 80 檔分批抓，避免太暴力
        chunk_size = 20
        chunks = [SCAN_TARGETS[i:i + chunk_size] for i in range(0, len(SCAN_TARGETS), chunk_size)]
        
        total_chunks = len(chunks)
        
        for idx, chunk in enumerate(chunks):
            try:
                # 批量抓取即時資料
                stocks = twstock.realtime.get(chunk)
                
                # 解析資料
                for code, data in stocks.items():
                    if not data['success']: continue
                    
                    real = data['realtime']
                    info = data['info']
                    
                    # 確保有成交價
                    if real['latest_trade_price'] == '-' or real['open'] == '-': continue
                    
                    current_price = float(real['latest_trade_price'])
                    open_price = float(real['open'])
                    high_price = float(real['high'])
                    low_price = float(real['low'])
                    
                    # 9:00 開盤後，如果「現價 < 開盤」 (轉弱訊號)
                    if current_price < open_price:
                        name = STOCK_MAP.get(code, code)
                        
                        # 計算跌幅 (距離開盤跌了多少)
                        drop_from_open = ((open_price - current_price) / open_price) * 100
                        
                        # 計算昨天的 CDP (這裡還是要用昨收來算今日支撐)
                        # 注意：Twstock 即時資料沒有「昨收」，我們用 open_price 近似估算或忽略
                        # 為了準確，我們簡單顯示即時狀態即可
                        
                        results.append({
                            "code": code, "name": name, 
                            "now": current_price, "open": open_price,
                            "high": high_price, "low": low_price,
                            "drop": drop_from_open
                        })
            except Exception as e:
                pass # 忽略錯誤，繼續下一批
            
            # 更新進度條
            progress_bar.progress((idx + 1) / total_chunks)
            time.sleep(1) # 稍微休息一下，避免被鎖 IP
            
        progress_bar.empty()
        
        # 排序：跌越深 (距離開盤越遠) 的排前面
        results.sort(key=lambda x: x['drop'], reverse=True)
        
        if not results:
            st.success("目前無轉弱訊號 (多方強勢)。")
        else:
            st.error(f"發現 {len(results)} 檔轉弱股 (現價 < 開盤)！")
            for s in results:
                html_code = f"""
                <div class="stock-card card-green">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:20px; font-weight:bold; color:white;">{s['name']}</span> 
                            <span style="color:#aaa; font-size:14px;">{s['code']}</span>
                            <span class="live-tag">LIVE</span>
                        </div>
                        <span class="bearish-alert">跌破開盤 {round(s['drop'], 2)}%</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; text-align:center;">
                        <div>
                            <div style="font-size:12px; color:#aaa;">今日開盤</div>
                            <div style="font-size:18px; font-weight:bold; color:#fff;">{s['open']}</div>
                        </div>
                        <div>
                            <div style="font-size:12px; color:#aaa;">目前價格</div>
                            <div style="font-size:24px; font-weight:bold; color:#00e676;">{s['now']}</div>
                        </div>
                        <div>
                            <div style="font-size:12px; color:#aaa;">今日最高</div>
                            <div style="font-size:18px; font-weight:bold; color:#ff4b4b;">{s['high']}</div>
                        </div>
                    </div>
                    <div style="margin-top:5px; text-align:center; font-size:12px; color:#aaa;">
                        (建議：反彈不過 {s['open']} 可試空，停損設今日高點 {s['high']})
                    </div>
                </div>
                """
                st.markdown(html_code, unsafe_allow_html=True)

# === 分頁 2: 隔日沖雷達 (Yahoo 盤後數據) ===
with tab2:
    st.markdown("### 🔥 隔日沖雷達 (盤前/盤後做功課)")
    st.info("使用 Yahoo 數據，適合盤後分析主力籌碼。")
    
    if st.button("掃描強勢股", use_container_width=True):
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        try:
            # 抓取 5 天資料
            data = yf.download(tickers, period="5d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    # 抓取最新收盤 (無論是昨收還是今收，反正就是最新一根 K 棒)
                    target_row = df.iloc[-1]
                    
                    if pd.isna(target_row['Volume']): continue
                    
                    vol = int(target_row['Volume'])
                    close = float(target_row['Close'])
                    op = float(target_row['Open'])
                    high = float(target_row['High'])
                    low = float(target_row['Low'])
                    
                    # 篩選條件
                    if vol < 1000000: continue
                    pct = ((close - op) / op) * 100
                    if pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    bk_html = generate_mock_broker_html()
                    
                    try:
                        d_str = target_row.name.strftime('%Y-%m-%d')
                    except:
                        d_str = str(target_row.name)[:10]
                    
                    results.append({
                        "code":code, "name":name, "vol":int(vol/1000), 
                        "close":close, "pct":pct, "nh":nh, "nl":nl, 
                        "bk":bk_html, "date": d_str
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            if not results: 
                st.warning("無符合標的。")
            else:
                for s in results:
                    html_code = f"""<div class="stock-card card-red"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa; font-size:12px;">{s['code']}</span></div><span class="date-badge">{s['date']}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span style="color:#ff4b4b; font-weight:bold;">+{round(s['pct'], 2)}%</span><span style="font-size:13px; color:#ccc;">量: {s['vol']} 張 | 收: {s['close']}</span></div><div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;"><span class="resistance">壓: {s['nh']}</span> <span class="support">撐: {s['nl']}</span></div><div style="margin-top:8px; font-size:12px; color:#aaa;">⚡ 模擬主力: {s['bk']}</div></div>"""
                    st.markdown(html_code, unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 3: 計算機 ===
with tab3:
    st.markdown("### ⚡ 支撐壓力計算機")
    c1, c2 = st.columns(2)
    with c1:
        p_close = st.number_input("收盤價", 0.0, step=0.5, format="%.2f")
        p_high = st.number_input("最高價", 0.0, step=0.5, format="%.2f")
    with c2:
        p_low = st.number_input("最低價", 0.0, step=0.5, format="%.2f")
        
    if st.button("計算", type="primary", use_container_width=True):
        if p_close > 0:
            ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
            html_code = f"""<div class="stock-card card-green" style="text-align:center;"><div style="color:#aaa; margin-bottom:10px;">中關價 (CDP): {cdp}</div><div style="display:flex; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px; margin-bottom:10px;"><div><div class="big-label">賣出壓力 (NH)</div><div class="big-value resistance">{nh}</div></div><div><div class="big-label">買進支撐 (NL)</div><div class="big-value support">{nl}</div></div></div><div style="display:flex; justify-content:space-between;"><div><div style="font-size:12px; color:#aaa;">最高壓力 (AH)</div><div style="font-size:16px; color:#ff6c6c;">{ah}</div></div><div><div style="font-size:12px; color:#aaa;">最低支撐 (AL)</div><div style="font-size:16px; color:#00e676;">{al}</div></div></div></div>"""
            st.markdown(html_code, unsafe_allow_html=True)
