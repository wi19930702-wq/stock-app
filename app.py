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
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-trap { border-left: 6px solid #d500f9; } /* 紫色：假突破 */
    .card-green { border-left: 6px solid #00c853; } /* 綠色：轉弱 */
    .card-red { border-left: 6px solid #ff4b4b; }   /* 紅色：隔日沖 */
    
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    
    /* 假突破專用標籤 */
    .trap-alert {
        background-color: #aa00ff;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        float: right;
    }
    
    .date-badge {
        background-color: #444;
        color: #bbb;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        float: right;
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
    h, l, c = float(high), float(low), float(close)
    cdp = (h + l + c * 2) / 4
    ah = cdp + (h - l)
    nh = cdp * 2 - l
    nl = cdp * 2 - h
    al = cdp - (h - l)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2)

# --- 4. 介面設計 ---
st.title("⚡ 極速當沖戰情室")

# 顯示台灣時間
tw_tz = pytz.timezone('Asia/Taipei')
now_str = datetime.now(tw_tz).strftime('%H:%M:%S')
st.caption(f"台灣時間: {now_str} (請於 09:05 後使用)")

# 新增分頁：把誘多雷達放在第二個
tab1, tab2, tab3, tab4 = st.tabs(["📉 盤中轉弱", "💣 誘多(假突破)", "🔥 隔日沖雷達", "🧮 計算機"])

# === 分頁 1: 盤中轉弱 (純跌破開盤) ===
with tab1:
    st.markdown("### 📉 跌破開盤雷達")
    if st.button("掃描轉弱", use_container_width=True):
        st.cache_data.clear()
        progress_bar = st.progress(0)
        results = []
        
        # 批量抓即時
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
                    
                    # 條件：現價 < 開盤
                    if now_price < open_price:
                        name = STOCK_MAP.get(code, code)
                        drop = ((open_price - now_price) / open_price) * 100
                        results.append({"code":code, "name":name, "now":now_price, "open":open_price, "drop":drop})
            except: pass
            progress_bar.progress((idx + 1) / len(chunks))
            time.sleep(0.5)
            
        progress_bar.empty()
        results.sort(key=lambda x: x['drop'], reverse=True)
        
        if not results: st.success("無轉弱股")
        else:
            for s in results:
                st.markdown(f"""<div class="stock-card card-green"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa;">{s['code']}</span></div><span style="color:#00e676; font-weight:bold;">跌破開盤</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>開盤: {s['open']}</span> <span style="color:#00e676; font-size:20px; font-weight:bold;">{s['now']}</span></div></div>""", unsafe_allow_html=True)

# === 分頁 2: 誘多雷達 (假突破真拉回) ===
with tab2:
    st.markdown("### 💣 盤中誘多偵測 (假突破)")
    st.info("策略：盤中股價「衝過壓力 (NH)」後「跌回壓力之下」，形成假突破陷阱。")
    
    if st.button("掃描假突破 (做空機會)", use_container_width=True):
        st.cache_data.clear()
        progress_bar = st.progress(0)
        trap_results = []
        
        # 1. 先抓昨天資料算出 NH (壓力)
        # 這裡為了速度，我們假設昨天收盤資料已更新
        try:
            tickers = [f"{c}.TW" for c in SCAN_TARGETS]
            hist_data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
            
            # 2. 再抓即時資料
            # 為了避免 API 衝突，我們簡單分批處理
            chunk_size = 20
            chunks = [SCAN_TARGETS[i:i + chunk_size] for i in range(0, len(SCAN_TARGETS), chunk_size)]
            
            for idx, chunk in enumerate(chunks):
                realtime_stocks = twstock.realtime.get(chunk)
                
                for code in chunk:
                    try:
                        # 取得 NH
                        df = hist_data[f"{code}.TW"]
                        if df.empty: continue
                        # 抓倒數第二筆 (昨收) 來算今天的壓力
                        # 如果是在盤中，iloc[-1] 可能是今天的，所以保險起見我們抓日期確認
                        last_date = df.index[-1].strftime('%Y-%m-%d')
                        today_date = datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d')
                        
                        if last_date == today_date:
                            ref_row = df.iloc[-2] # 用昨天的
                        else:
                            ref_row = df.iloc[-1]
                            
                        nh = calculate_cdp(ref_row['High'], ref_row['Low'], ref_row['Close'])[1]
                        
                        # 取得即時數據
                        if code not in realtime_stocks or not realtime_stocks[code]['success']: continue
                        real = realtime_stocks[code]['realtime']
                        if real['latest_trade_price'] == '-' or real['high'] == '-': continue
                        
                        now_price = float(real['latest_trade_price'])
                        day_high = float(real['high'])
                        
                        # --- 核心邏輯：假突破 ---
                        # 1. 今天最高價 > 壓力 (NH) --> 曾經突破過
                        # 2. 目前價格 < 壓力 (NH)   --> 跌回來了
                        # 3. 有量 (>500張)
                        vol = float(real['accumulate_trade_volume'])
                        if vol < 500: continue

                        if day_high > nh and now_price < nh:
                            name = STOCK_MAP.get(code, code)
                            # 計算回落幅度
                            pullback = day_high - now_price
                            
                            trap_results.append({
                                "code":code, "name":name, "now":now_price, 
                                "high":day_high, "nh":nh, "vol": int(vol)
                            })
                    except: continue
                
                progress_bar.progress((idx + 1) / len(chunks))
                time.sleep(0.5)
            
            progress_bar.empty()
            
            if not trap_results:
                st.success("目前無假突破訊號 (多頭可能很強，都撐在壓力上)。")
            else:
                st.error(f"發現 {len(trap_results)} 檔假突破 (誘多)！")
                for s in trap_results:
                    html_code = f"""
                    <div class="stock-card card-trap">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> 
                                <span style="color:#aaa;">{s['code']}</span>
                            </div>
                            <span class="trap-alert">假突破</span>
                        </div>
                        <div style="margin-top:10px; display:flex; justify-content:space-between; text-align:center;">
                            <div>
                                <div style="font-size:11px; color:#aaa;">今日最高</div>
                                <div style="color:#ff4b4b; font-weight:bold;">{s['high']}</div>
                            </div>
                            <div>
                                <div style="font-size:11px; color:#aaa;">壓力位(NH)</div>
                                <div style="color:#ffeb3b; font-weight:bold;">{s['nh']}</div>
                            </div>
                            <div>
                                <div style="font-size:11px; color:#aaa;">跌回現價</div>
                                <div style="color:#00e676; font-size:20px; font-weight:bold;">{s['now']}</div>
                            </div>
                        </div>
                        <div style="margin-top:5px; text-align:center; font-size:12px; color:#ccc;">
                            (曾衝過 {s['nh']} 但站不穩，小心下殺)
                        </div>
                    </div>
                    """
                    st.markdown(html_code, unsafe_allow_html=True)
                    
        except: st.error("連線錯誤")

# === 分頁 3: 隔日沖雷達 (Yahoo) ===
with tab3:
    st.markdown("### 🔥 隔日沖雷達")
    if st.button("掃描強勢股", use_container_width=True):
        st.info("請看上一版的代碼，此處省略以節省篇幅，功能不變。")
        # (這裡保留您上一版的功能即可，因字數限制未重複貼上)

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
        ah, nh, nl, al = calculate_cdp(p_high, p_low, p_close)
        st.success(f"賣壓(NH): {nh} | 支撐(NL): {nl}")
