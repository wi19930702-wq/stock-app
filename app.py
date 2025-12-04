import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import time

# --- 1. 頁面設定 ---
st.set_page_config(page_title="全方位操盤手", layout="centered")

st.markdown("""
<style>
    .stock-card { background-color: #262730; padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .card-red { border-left: 6px solid #ff4b4b; }
    .card-green { border-left: 6px solid #00c853; }
    .card-trap { border-left: 6px solid #aa00ff; }
    .card-gold { border-left: 6px solid #ffd700; }
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    .date-badge { background-color: #444; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; float: right; }
    .tag { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 5px; color: white; background-color: #555; }
    
    /* 更新時間標籤 */
    .update-time {
        text-align: center;
        background-color: #d32f2f;
        color: white;
        padding: 8px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 15px;
        font-size: 14px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料準備 ---
STOCK_MAP = {
    "2330":"台積電", "2317":"鴻海", "2382":"廣達", "3231":"緯創", "2376":"技嘉", "6669":"緯穎", "2356":"英業達",
    "2454":"聯發科", "2303":"聯電", "3711":"日月光", "3443":"創意", "3661":"世芯", "3035":"智原",
    "3324":"雙鴻", "3017":"奇鋐", "2421":"建準", "3653":"健策", "3032":"偉訓", "8210":"勤誠", "2486":"一詮",
    "3338":"泰碩", "3483":"力致", "6117":"迎廣", "1519":"華城", "1513":"中興電", "1503":"士電", "1514":"亞力",
    "1504":"東元", "1609":"大亞", "1605":"華新", "3708":"上緯", "9958":"世紀鋼", "6806":"森崴",
    "2368":"金像電", "6274":"台燿", "8358":"金居", "4979":"華星光", "3450":"聯鈞", "3234":"光環", "3081":"聯亞",
    "6442":"光聖", "4908":"前鼎", "5388":"中磊", "4939":"亞電", "8046":"南電", "6269":"台郡", "5349":"先豐",
    "6213":"智擎", "3037":"欣興", "2313":"華通", "2367":"燿華", "8039":"台虹", "6191":"精成科", "6147":"頎邦",
    "3260":"威剛", "3532":"台勝科", "6182":"合晶", "5347":"世界", "8069":"元太", "4968":"立積", "3006":"晶豪科",
    "2609":"陽明", "2615":"萬海", "2603":"長榮", "2618":"長榮航", "2610":"華航", "2634":"漢翔", "8033":"雷虎"
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

# --- 4. 介面設計 ---
st.title("⚡ 極速當沖戰情室")
tz = pytz.timezone('Asia/Taipei')
current_time = datetime.now(tz).strftime('%H:%M:%S')
st.caption(f"系統時間 (台灣): {current_time}")

tab1, tab2, tab3, tab4 = st.tabs(["📉 盤中轉弱", "💣 誘多假突破", "🔥 隔日沖雷達", "🧮 計算機"])

# === 分頁 1: 盤中轉弱 ===
with tab1:
    st.markdown("### 📉 盤中轉弱雷達")
    
    # 使用 session_state 來強制刷新
    if 'refresh_key' not in st.session_state:
        st.session_state.refresh_key = 0

    if st.button("掃描轉弱股 (跌幅大優先)", key="btn1", use_container_width=True):
        st.session_state.refresh_key += 1 # 強制更新金鑰
        st.cache_data.clear() # 清除所有快取
        
        progress = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        # 顯示當下掃描時間
        scan_time = datetime.now(tz).strftime('%H:%M:%S')
        
        try:
            # 這裡不使用快取，直接抓取
            data = yf.download(tickers, period="5d", group_by='ticker', progress=False, interval="1d")
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    # 抓最新一筆 (即時)
                    row = df.iloc[-1]
                    if pd.isna(row['Open']): continue
                    
                    now_p = float(row['Close'])
                    open_p = float(row['Open'])
                    vol = int(row['Volume'])
                    
                    if vol < 500000: continue # 過濾無量股
                    
                    # 邏輯：現價 < 開盤 (轉弱)
                    if now_p < open_p:
                        name = STOCK_MAP.get(code, code)
                        drop = ((open_p - now_p) / open_p) * 100
                        results.append({"code":code, "name":name, "now":now_p, "open":open_p, "drop":drop, "vol":vol})
                except: continue
                progress.progress((i+1)/len(SCAN_TARGETS))
            progress.empty()
            
            # 排序：跌幅最大的排最上面
            results.sort(key=lambda x: x['drop'], reverse=True)
            
            # 顯示強制更新時間
            st.markdown(f"<div class='update-time'>✅ 掃描完成！資料時間: {scan_time}</div>", unsafe_allow_html=True)
            
            if not results: st.info("目前無轉弱股")
            else:
                for s in results:
                    st.markdown(f"""<div class="stock-card card-green"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span class="tag" style="background-color:#1b5e20;">跌破開盤 {round(s['drop'], 2)}%</span></div><div style="display:flex; justify-content:space-between; margin-top:10px;"><div><div style="font-size:11px; color:#aaa;">開盤價</div><div style="color:white; font-weight:bold;">{s['open']}</div></div><div><div style="font-size:11px; color:#aaa;">目前價</div><div style="color:#00e676; font-weight:bold; font-size:22px;">{s['now']}</div></div></div><div style="font-size:11px; color:#aaa; margin-top:5px;">成交量: {int(s['vol']/1000)} 張</div></div>""", unsafe_allow_html=True)
        except: st.error("連線忙碌中，請重試")

# === 分頁 2: 誘多假突破 ===
with tab2:
    st.markdown("### 💣 盤中誘多偵測")
    if st.button("掃描假突破 (回落大優先)", key="btn2", use_container_width=True):
        st.cache_data.clear()
        scan_time = datetime.now(tz).strftime('%H:%M:%S')
        progress = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        try:
            data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    valid_rows = df.dropna(subset=['Close'])
                    if len(valid_rows) < 2: continue
                    
                    prev_row = valid_rows.iloc[-2]
                    nh = calculate_cdp(prev_row['High'], prev_row['Low'], prev_row['Close'])[1]
                    
                    curr_row = valid_rows.iloc[-1]
                    now_p = float(curr_row['Close'])
                    high_p = float(curr_row['High'])
                    
                    if high_p > nh and now_p < nh:
                        name = STOCK_MAP.get(code, code)
                        diff = high_p - now_p
                        results.append({"code":code, "name":name, "now":now_p, "high":high_p, "nh":nh, "diff":diff})
                except: continue
                progress.progress((i+1)/len(SCAN_TARGETS))
            progress.empty()
            
            # 排序：回落幅度(diff)最大的排最上面
            results.sort(key=lambda x: x['diff'], reverse=True)
            
            st.markdown(f"<div class='update-time'>✅ 掃描完成！資料時間: {scan_time}</div>", unsafe_allow_html=True)
            
            if not results: st.info("無假突破訊號")
            else:
                for s in results:
                    st.markdown(f"""<div class="stock-card card-trap"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span class="tag" style="background-color:#aa00ff;">假突破</span></div><div style="display:flex; justify-content:space-between; margin-top:10px;"><div><div style="font-size:11px; color:#aaa;">今日最高</div><div style="color:#ff4b4b; font-weight:bold;">{s['high']}</div></div><div><div style="font-size:11px; color:#aaa;">壓力(NH)</div><div style="color:#ffd700; font-weight:bold;">{s['nh']}</div></div><div><div style="font-size:11px; color:#aaa;">目前價</div><div style="color:#00e676; font-weight:bold;">{s['now']}</div></div></div></div>""", unsafe_allow_html=True)
        except: st.error("連線忙碌中")

# === 分頁 3: 隔日沖雷達 ===
with tab3:
    st.markdown("### 🔥 隔日沖雷達")
    if st.button("掃描強勢股 (漲幅大優先)", key="btn3", use_container_width=True):
        st.cache_data.clear()
        scan_time = datetime.now(tz).strftime('%H:%M:%S')
        progress = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        try:
            data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    valid_rows = df.dropna(subset=['Close', 'Volume'])
                    if valid_rows.empty: continue
                    
                    row = valid_rows.iloc[-1]
                    vol = int(row['Volume'])
                    if vol < 500000: continue
                    
                    close = float(row['Close'])
                    op = float(row['Open'])
                    pct = ((close - op) / op) * 100 if op > 0 else 0
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al, cdp = calculate_cdp(row['High'], row['Low'], close)
                    date_str = str(row.name)[:10]
                    
                    results.append({"code":code, "name":name, "vol":int(vol/1000), "close":close, "pct":pct, "nh":nh, "nl":nl, "date":date_str})
                except: continue
                progress.progress((i+1)/len(SCAN_TARGETS))
            progress.empty()
            
            # 排序：漲幅最大的排最上面
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            st.markdown(f"<div class='update-time'>✅ 掃描完成！資料時間: {scan_time}</div>", unsafe_allow_html=True)
            
            if not results: st.warning("無資料")
            else:
                for s in results:
                    c_cls = "card-red" if s['pct']>=0 else "card-green"
                    c_col = "#ff4b4b" if s['pct']>=0 else "#00e676"
                    sign = "+" if s['pct']>=0 else ""
                    st.markdown(f"""<div class="stock-card {c_cls}"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span class="date-badge">{s['date']}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span style="color:{c_col}; font-weight:bold; font-size:18px;">{sign}{round(s['pct'], 2)}%</span><span style="color:#ccc; font-size:13px;">量: {s['vol']} 張</span></div><div style="margin-top:8px; padding-top:5px; border-top:1px solid #444; display:flex; justify-content:space-between;"><span class="resistance">壓: {s['nh']}</span> <span class="support">撐: {s['nl']}</span></div></div>""", unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 4: 計算機 ===
with tab4:
    st.markdown("### ⚡ 支撐壓力計算機")
    c1, c2 = st.columns(2)
    with c1:
        p_close = st.number_input("收盤價", 0.0, step=0.1, format="%.2f")
        p_high = st.number_input("最高價", 0.0, step=0.1, format="%.2f")
    with c2:
        p_low = st.number_input("最低價", 0.0, step=0.1, format="%.2f")
    if st.button("計算", key="btn4", use_container_width=True):
        if p_close > 0:
            ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
            st.markdown(f"""<div class="stock-card card-green" style="text-align:center;"><div style="color:#aaa; margin-bottom:10px;">中關價 (CDP): {cdp}</div><div style="display:flex; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:15px; margin-bottom:15px;"><div><div class="calc-label" style="font-size:14px; color:#aaa;">賣出壓力 (NH)</div><div class="calc-val-res" style="font-size:26px; font-weight:bold; color:#ff6c6c;">{nh}</div></div><div><div class="calc-label" style="font-size:14px; color:#aaa;">買進支撐 (NL)</div><div class="calc-val-sup" style="font-size:26px; font-weight:bold; color:#00e676;">{nl}</div></div></div><div style="display:flex; justify-content:space-between;"><div><div style="font-size:12px; color:#aaa;">最高壓力 (AH)</div><div style="font-size:16px; color:#ff6c6c; font-weight:bold;">{ah}</div></div><div><div style="font-size:12px; color:#aaa;">最低支撐 (AL)</div><div style="font-size:16px; color:#00e676; font-weight:bold;">{al}</div></div></div></div>""", unsafe_allow_html=True)
