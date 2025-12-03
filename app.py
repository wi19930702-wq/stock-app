import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
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
    .card-red { border-left: 6px solid #ff4b4b; }   /* 隔日沖/強勢 */
    .card-green { border-left: 6px solid #00c853; } /* 轉弱/計算機 */
    .card-gold { border-left: 6px solid #ffd700; }  /* 營收 */
    
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
    }
    
    /* 營收數據區塊 */
    .rev-box {
        display: flex;
        justify-content: space-between;
        background-color: #363940;
        padding: 8px;
        border-radius: 6px;
        margin-top: 8px;
        font-size: 13px;
    }
    .rev-up { color: #ff4b4b; font-weight: bold; }
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
    h, l, c = float(high), float(low), float(close)
    cdp = (h + l + c * 2) / 4
    ah = cdp + (h - l)
    nh = cdp * 2 - l
    nl = cdp * 2 - h
    al = cdp - (h - l)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

def generate_mock_broker_html():
    # 模擬主力分點
    BROKER_POOLS = [("凱基-台北", "#d32f2f"), ("富邦-建國", "#1976d2"), ("美林", "#444"), ("摩根大通", "#444"), ("統一-嘉義", "#444"), ("永豐金-虎尾", "#444")]
    selected = random.sample(BROKER_POOLS, 3)
    html_parts = []
    for name, color in selected:
        vol = random.randint(500, 3000)
        html_parts.append(f'<span style="background-color:{color}; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:4px; color:white; display:inline-block; margin-bottom:2px;">{name} +{vol}</span>')
    return "".join(html_parts)

# --- 4. 介面設計 ---
st.title("📈 全方位操盤戰情室")

# 顯示台灣時間，讓您確認系統沒跑掉
tw_tz = pytz.timezone('Asia/Taipei')
now_str = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M')
st.caption(f"系統時間 (台灣): {now_str}")

tab1, tab2, tab3, tab4 = st.tabs(["🔥 隔日沖雷達", "📉 盤中轉弱雷達", "🧮 計算機", "💰 營收創高"])

# === 分頁 1: 隔日沖雷達 (自動抓最新收盤) ===
with tab1:
    st.markdown("### 🔥 熱門股 & 隔日支撐壓力")
    st.info("自動抓取最新收盤數據 (晚上看即為明日觀察名單)。")
    
    if st.button("掃描熱門股 (強制刷新)", use_container_width=True):
        st.cache_data.clear() # 清除快取
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        try:
            data = yf.download(tickers, period="5d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    # 自動抓最後一筆 (最新數據)
                    last_row = df.iloc[-1]
                    
                    if pd.isna(last_row['Volume']): continue
                    
                    vol = int(last_row['Volume'])
                    close = float(last_row['Close'])
                    op = float(last_row['Open'])
                    high = float(last_row['High'])
                    low = float(last_row['Low'])
                    
                    # 篩選條件：量>1000 且 漲幅>1% (強勢股)
                    if vol < 1000000: continue
                    pct = ((close - op) / op) * 100
                    if pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    
                    # 計算支撐壓力
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    bk_html = generate_mock_broker_html()
                    
                    # 日期字串
                    try:
                        date_str = last_row.name.strftime('%m/%d')
                    except:
                        date_str = str(last_row.name)[5:10]
                    
                    results.append({
                        "code":code, "name":name, "vol":int(vol/1000), 
                        "close":close, "pct":pct, "nh":nh, "nl":nl, 
                        "bk":bk_html, "date":date_str
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            if not results: 
                st.warning("目前無符合「強勢」標的。")
            else:
                st.success(f"掃描完成！計算基準日：{results[0]['date']} (支撐壓力適用於次一交易日)")
                for s in results:
                    html_code = f"""<div class="stock-card card-red"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa; font-size:12px;">{s['code']}</span></div><span style="color:#aaa; font-size:12px;">資料: {s['date']}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span style="color:#ff4b4b; font-weight:bold;">+{round(s['pct'], 2)}%</span><span style="font-size:13px; color:#ccc;">量: {s['vol']} 張 | 收: {s['close']}</span></div><div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;"><span class="resistance">壓: {s['nh']}</span> <span class="support">撐: {s['nl']}</span></div><div style="margin-top:8px; font-size:12px; color:#aaa;">⚡ 模擬主力: {s['bk']}</div></div>"""
                    st.markdown(html_code, unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 2: 盤中轉弱雷達 (新功能) ===
with tab2:
    st.markdown("### 📉 盤中即時轉弱雷達")
    st.warning("⚠️ 訊號定義：目前價格 < 今日開盤價 (開高走低或轉弱)。")
    
    if st.button("掃描轉弱股", use_container_width=True):
        st.cache_data.clear() # 盤中一定要清除快取
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        bearish_results = []
        
        try:
            # 盤中建議抓 1d, 1m (或 5d 1d) 這裡用日線判斷即可
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    row = df.iloc[-1]
                    if pd.isna(row['Open']) or pd.isna(row['Close']): continue
                    
                    current_price = float(row['Close']) # 盤中 Close 即為現價
                    open_price = float(row['Open'])
                    vol = int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    
                    # 篩選：有量 (至少500張) 且 跌破開盤價
                    if vol < 500000: continue
                    
                    if current_price < open_price:
                        diff = open_price - current_price
                        drop_pct = (diff / open_price) * 100
                        
                        name = STOCK_MAP.get(code, code)
                        # 計算 CDP (給參考)
                        ah, nh, nl, al, cdp = calculate_cdp(row['High'], row['Low'], current_price)
                        
                        bearish_results.append({
                            "code":code, "name":name, "now":current_price, "open":open_price,
                            "drop": drop_pct, "nl": nl
                        })
                        
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
                
            progress_bar.empty()
            bearish_results.sort(key=lambda x: x['drop'], reverse=True) # 跌越深排越前
            
            if not bearish_results:
                st.success("目前無轉弱訊號 (市場強勢)。")
            else:
                st.error(f"發現 {len(bearish_results)} 檔轉弱股！")
                for s in bearish_results:
                    html_code = f"""<div class="stock-card card-green"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa; font-size:12px;">{s['code']}</span></div><span class="bearish-alert">跌破開盤</span></div><div style="display:flex; justify-content:space-between; margin-top:8px;"><div style="text-align:center;"><span style="color:#aaa; font-size:12px;">開盤價</span><br><span style="font-weight:bold; color:#fff;">{s['open']}</span></div><div style="text-align:center;"><span style="color:#aaa; font-size:12px;">目前價</span><br><span style="font-weight:bold; color:#00e676;">{s['now']}</span></div><div style="text-align:center;"><span style="color:#aaa; font-size:12px;">防守(NL)</span><br><span style="font-weight:bold; color:#00e676;">{s['nl']}</span></div></div></div>"""
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

# === 分頁 4: 營收創高 (模擬) ===
with tab4:
    st.markdown("### 💰 月營收創新高 (模擬)")
    if st.button("掃描營收強勢股", use_container_width=True):
        targets = random.sample(SCAN_TARGETS, 10)
        for code in targets:
            name = STOCK_MAP.get(code, code)
            try:
                stock = yf.Ticker(f"{code}.TW")
                hist = stock.history(period="1d")
                price = round(hist['Close'].iloc[-1], 2) if not hist.empty else "N/A"
            except: price = "N/A"
            rev, yoy, mom = generate_mock_revenue()
            html_code = f"""<div class="stock-card card-gold"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{name}</span> <span style="color:#aaa; font-size:12px;">{code}</span> <span class="tag tag-rev">營收創高</span></div><span style="color:white; font-weight:bold;">${price}</span></div><div class="rev-box"><div>單月營收: <span style="color:white;">{rev} 億</span></div><div>年增(YoY): <span class="rev-up">+{yoy}%</span></div><div>月增(MoM): <span class="rev-up">+{mom}%</span></div></div></div>"""
            st.markdown(html_code, unsafe_allow_html=True)
