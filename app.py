import streamlit as st
import pandas as pd
import yfinance as yf
import twstock
import time
import random
from datetime import datetime, timedelta
import pytz

# --- 1. 頁面與 CSS 設定 ---
st.set_page_config(page_title="全方位操盤手", layout="centered")

st.markdown("""
<style>
    /* 卡片通用樣式 */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-red { border-left: 6px solid #ff4b4b; }   /* 漲 */
    .card-green { border-left: 6px solid #00c853; } /* 跌 */
    .card-trap { border-left: 6px solid #d500f9; }  /* 假突破 */
    
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    
    .date-badge {
        background-color: #444;
        color: #bbb;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        float: right;
    }
    
    /* 做空訊號標籤 */
    .short-signal {
        background-color: #ffeb3b;
        color: #000;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
        margin-top: 5px;
        display: inline-block;
    }
    
    /* 假突破標籤 */
    .trap-alert {
        background-color: #aa00ff;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 (80+ 檔熱門股) ---
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
        return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)
    except:
        return 0,0,0,0,0

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

# 顯示台灣時間
tw_tz = pytz.timezone('Asia/Taipei')
now_str = datetime.now(tw_tz).strftime('%H:%M:%S')
st.caption(f"台灣時間: {now_str}")

tab1, tab2, tab3, tab4 = st.tabs(["🔥 隔日沖雷達", "📉 盤中轉弱", "💣 誘多(假突破)", "🧮 計算機"])

# === 分頁 1: 隔日沖雷達 (Yahoo 盤後數據 - 修復版) ===
with tab1:
    st.markdown("### 🔥 尋找明日做空標的")
    st.info("策略：找出「今日爆量大漲」的股票 👉 明日開盤若開高走低，就是做空機會！")
    
    if st.button("掃描熱門股 (強制刷新)", use_container_width=True):
        st.cache_data.clear() # 強制清除快取
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        try:
            # 抓取 5 天資料，增加容錯率
            data = yf.download(tickers, period="5d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    # --- 關鍵修正：確保抓到非空值的最後一筆 ---
                    valid_rows = df.dropna(subset=['Close', 'Volume'])
                    if valid_rows.empty: continue
                    
                    last_row = valid_rows.iloc[-1]
                    
                    vol = int(last_row['Volume'])
                    close = float(last_row['Close'])
                    op = float(last_row['Open'])
                    high = float(last_row['High'])
                    low = float(last_row['Low'])
                    
                    # 篩選條件放寬：只要有量就顯示 (方便您做空)
                    if vol < 500000: continue # 至少 500 張
                    
                    # 計算漲跌幅
                    if op > 0:
                        pct = ((close - op) / op) * 100
                    else:
                        pct = 0
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    bk_html = generate_mock_broker_html()
                    
                    try:
                        d_str = last_row.name.strftime('%m/%d')
                    except:
                        d_str = str(last_row.name)[5:10]
                    
                    # 判斷是否為「隔日沖潛在賣壓」
                    is_target = False
                    if pct > 2.0: # 漲幅 > 2% 視為強勢，可能被隔日沖鎖定
                        is_target = True
                    
                    results.append({
                        "code":code, "name":name, "vol":int(vol/1000), 
                        "close":close, "pct":pct, "nh":nh, "nl":nl, 
                        "bk":bk_html, "date":d_str, "is_target": is_target
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            # 排序：漲幅大的排前面
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            if not results: 
                st.warning("目前無資料 (Yahoo API 連線異常，請稍後再試)。")
            else:
                st.success(f"掃描完成！顯示 {len(results)} 檔熱門股。")
                for s in results:
                    card_class = "card-red" if s['pct'] >= 0 else "card-green"
                    pct_color = "#ff4b4b" if s['pct'] >= 0 else "#00e676"
                    pct_sign = "+" if s['pct'] >= 0 else ""
                    
                    short_tip = ""
                    if s['is_target']:
                        short_tip = f"<div class='short-signal'>💣 潛在賣壓：明日若跌破 {s['close']} 可試空</div>"
                    
                    html_code = f"""<div class="stock-card {card_class}"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa; font-size:12px;">{s['code']}</span></div><span style="color:#aaa; font-size:12px;">資料: {s['date']}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span style="color:{pct_color}; font-weight:bold;">{pct_sign}{round(s['pct'], 2)}%</span><span style="font-size:13px; color:#ccc;">量: {s['vol']} 張 | 收: {s['close']}</span></div>{short_tip}<div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;"><span class="resistance">壓(NH): {s['nh']}</span> <span class="support">撐(NL): {s['nl']}</span></div><div style="margin-top:8px; font-size:12px; color:#aaa;">⚡ 模擬主力: {s['bk']}</div></div>"""
                    st.markdown(html_code, unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 2: 盤中轉弱雷達 (Twstock) ===
with tab2:
    st.markdown("### 📉 盤中轉弱雷達")
    st.info("🔥 資料來源：證交所即時 (09:00~13:30 使用)。")
    
    if st.button("掃描轉弱股", use_container_width=True):
        st.cache_data.clear()
        progress_bar = st.progress(0)
        results = []
        
        chunk_size = 20
        chunks = [SCAN_TARGETS[i:i + chunk_size] for i in range(0, len(SCAN_TARGETS), chunk_size)]
        
        for idx, chunk in enumerate(chunks):
            try:
                stocks = twstock.realtime.get(chunk)
                for code, data in stocks.items():
                    if not data['success']: continue
                    real = data['realtime']
                    if real['latest_trade_price'] == '-' or real['open'] == '-': continue
                    
                    now_price = float(real['latest_trade_price'])
                    open_price = float(real['open'])
                    
                    if now_price < open_price:
                        name = STOCK_MAP.get(code, code)
                        drop = ((open_price - now_price) / open_price) * 100
                        
                        # 簡單估算支撐 (昨收當參考)
                        # Twstock 沒給昨收，這裡僅顯示跌幅
                        results.append({"code":code, "name":name, "now":now_price, "open":open_price, "drop":drop})
            except: pass
            progress_bar.progress((idx + 1) / len(chunks))
            time.sleep(0.5) # 避免太快被擋
            
        progress_bar.empty()
        results.sort(key=lambda x: x['drop'], reverse=True)
        
        if not results: st.success("目前無轉弱訊號 (多方強勢)。")
        else:
            for s in results:
                st.markdown(f"""<div class="stock-card card-green"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span class="bearish-alert">跌破開盤</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>開盤: {s['open']}</span> <span style="color:#00e676; font-size:20px; font-weight:bold;">{s['now']}</span></div></div>""", unsafe_allow_html=True)

# === 分頁 3: 誘多雷達 (假突破) ===
with tab3:
    st.markdown("### 💣 盤中誘多偵測")
    if st.button("掃描假突破", use_container_width=True):
        st.cache_data.clear()
        progress_bar = st.progress(0)
        trap_results = []
        
        try:
            tickers = [f"{c}.TW" for c in SCAN_TARGETS]
            hist_data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
            
            chunk_size = 20
            chunks = [SCAN_TARGETS[i:i + chunk_size] for i in range(0, len(SCAN_TARGETS), chunk_size)]
            
            for idx, chunk in enumerate(chunks):
                realtime_stocks = twstock.realtime.get(chunk)
                for code in chunk:
                    try:
                        df = hist_data[f"{code}.TW"]
                        valid_rows = df.dropna(subset=['Close'])
                        if valid_rows.empty: continue
                        
                        # 抓倒數第二筆 (昨收) 來算今天的壓力
                        # 如果今天是交易日且 Yahoo 已更新盤中，那就要退回上一筆
                        # 這裡簡單抓倒數第二筆作為昨日參考
                        if len(valid_rows) >= 2:
                            ref_row = valid_rows.iloc[-2]
                        else:
                            ref_row = valid_rows.iloc[-1]
                            
                        nh = calculate_cdp(ref_row['High'], ref_row['Low'], ref_row['Close'])[1]
                        
                        if code not in realtime_stocks or not realtime_stocks[code]['success']: continue
                        real = realtime_stocks[code]['realtime']
                        if real['latest_trade_price'] == '-' or real['high'] == '-': continue
                        
                        now_price = float(real['latest_trade_price'])
                        day_high = float(real['high'])
                        vol = float(real['accumulate_trade_volume'])
                        
                        if vol < 500: continue

                        # 假突破邏輯：曾衝過 NH 但現在跌破 NH
                        if day_high > nh and now_price < nh:
                            name = STOCK_MAP.get(code, code)
                            trap_results.append({
                                "code":code, "name":name, "now":now_price, 
                                "high":day_high, "nh":nh
                            })
                    except: continue
                progress_bar.progress((idx + 1) / len(chunks))
                time.sleep(0.5)
            
            progress_bar.empty()
            
            if not trap_results: st.success("無假突破訊號。")
            else:
                for s in trap_results:
                    html_code = f"""<div class="stock-card card-trap"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span class="trap-alert">假突破</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>壓力: {s['nh']}</span> <span style="color:#00e676; font-size:20px; font-weight:bold;">{s['now']}</span></div></div>"""
                    st.markdown(html_code, unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 4: 計算機 ===
with tab4:
    st.markdown("### ⚡ 計算機")
    c1, c2 = st.columns(2)
    with c1:
        p_close = st.number_input("收盤", 0.0, step=0.5)
        p_high = st.number_input("最高", 0.0, step=0.5)
    with c2:
        p_low = st.number_input("最低", 0.0, step=0.5)
    if st.button("計算"):
        ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
        st.success(f"賣壓(NH): {nh} | 支撐(NL): {nl}")
