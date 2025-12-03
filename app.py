import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
import pytz # 引入時區套件

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
    .card-red { border-left: 6px solid #ff4b4b; }
    .card-green { border-left: 6px solid #00c853; }
    .card-gold { border-left: 6px solid #ffd700; }
    
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    
    .date-badge {
        background-color: #444;
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        float: right;
    }
    
    /* 新增：K線數據顯示區，方便驗證 */
    .ohlc-info {
        font-size: 11px;
        color: #888;
        background-color: #333;
        padding: 4px;
        border-radius: 4px;
        margin-top: 5px;
        text-align: center;
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
    # 強制轉型，避免數據格式錯誤
    h, l, c = float(high), float(low), float(close)
    cdp = (h + l + c * 2) / 4
    ah = cdp + (h - l)
    nh = cdp * 2 - l
    nl = cdp * 2 - h
    al = cdp - (h - l)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

def generate_mock_broker_html():
    BROKER_POOLS = [("凱基-台北", "#d32f2f"), ("富邦-建國", "#1976d2"), ("美林", "#444"), ("摩根大通", "#444"), ("統一-嘉義", "#444"), ("永豐金-虎尾", "#444")]
    selected = random.sample(BROKER_POOLS, 3)
    html_parts = []
    for name, color in selected:
        vol = random.randint(500, 3000)
        html_parts.append(f'<span style="background-color:{color}; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:4px; color:white; display:inline-block; margin-bottom:2px;">{name} +{vol}</span>')
    return "".join(html_parts)

# --- 4. 側邊欄設定 ---
st.sidebar.title("⚙️ 設定")

# 這次直接讓您選「資料來源」，不做太複雜的智慧判斷，避免誤判
data_source = st.sidebar.radio(
    "選擇計算基準：",
    ("📅 昨收 (用來預測今日)", "⚡ 即時 (盤中即時運算)"),
    index=0 
)

# --- 5. 介面設計 ---
tab1, tab2, tab3 = st.tabs(["🧮 計算機", "🚀 當沖掃描", "💰 營收創高"])

# === 分頁 1: 計算機 ===
with tab1:
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

# === 分頁 2: 當沖掃描 (修正版) ===
with tab2:
    st.markdown(f"### 🔍 熱門股掃描")
    
    # 強制清除快取按鈕
    if st.button("開始掃描 (強制刷新)", use_container_width=True):
        st.cache_data.clear() # 1. 強制清除 Streamlit 快取
        
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        # 2. 取得正確的台灣時間
        tw_tz = pytz.timezone('Asia/Taipei')
        now_tw = datetime.now(tw_tz)
        today_str = now_tw.strftime('%Y-%m-%d')
        
        try:
            # 抓取 5 天資料
            data = yf.download(tickers, period="5d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    # 取得最後一筆
                    last_row = df.iloc[-1]
                    try:
                        last_date_str = last_row.name.strftime('%Y-%m-%d')
                    except:
                        last_date_str = str(last_row.name)[:10]
                    
                    # --- 邏輯修正 ---
                    target_row = None
                    
                    if "昨收" in data_source:
                        # 模式 A: 昨收 (用來做今天的功課)
                        # 如果最新資料的日期等於今天 (代表盤中資料已進來)，我們不能用，要退回上一筆
                        if last_date_str == today_str:
                            if len(df) >= 2:
                                target_row = df.iloc[-2]
                            else:
                                continue # 資料不足
                        else:
                            # 如果最新資料不是今天 (是昨天收盤)，直接用
                            target_row = last_row
                    else:
                        # 模式 B: 即時
                        target_row = last_row
                    
                    # 取得最終用於計算的日期
                    try:
                        calc_date = target_row.name.strftime('%Y-%m-%d')
                    except:
                        calc_date = str(target_row.name)[:10]

                    if pd.isna(target_row['Volume']): continue
                    
                    # 抓取數值
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
                    
                    # 計算 CDP
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    bk_html = generate_mock_broker_html()
                    
                    results.append({
                        "code":code, "name":name, "vol":int(vol/1000), 
                        "close":close, "pct":pct, "nh":nh, "nl":nl, 
                        "bk":bk_html, "date":calc_date,
                        "high": high, "low": low # 儲存 H/L 以供顯示
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            if not results: 
                st.warning(f"查無符合標的。")
            else:
                st.success(f"掃描完成！計算基準日：{results[0]['date']} (請核對下方 K 線數據)")
                for s in results:
                    # 在卡片中顯示 OHLC 數據，證明是用哪一天的資料算的
                    ohlc_text = f"計算依據 (K線): 高 {s['high']} | 低 {s['low']} | 收 {s['close']}"
                    
                    html_code = f"""<div class="stock-card card-red"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> <span style="color:#aaa; font-size:12px;">{s['code']}</span></div><span class="date-badge">{s['date']}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span style="color:#ff4b4b; font-weight:bold;">+{round(s['pct'], 2)}%</span><span style="font-size:13px; color:#ccc;">量: {s['vol']} 張 | 收: {s['close']}</span></div><div class="ohlc-info">{ohlc_text}</div><div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;"><span class="resistance">壓: {s['nh']}</span> <span class="support">撐: {s['nl']}</span></div><div style="margin-top:8px; font-size:12px; color:#aaa;">⚡ 模擬主力: {s['bk']}</div></div>"""
                    st.markdown(html_code, unsafe_allow_html=True)
        except: st.error("連線錯誤，請稍後再試")

# === 分頁 3: 營收創高 (模擬) ===
with tab3:
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
            
            rev = round(random.uniform(10, 500), 1)
            yoy = round(random.uniform(15, 120), 1)
            mom = round(random.uniform(5, 30), 1)
            
            html_code = f"""<div class="stock-card card-gold"><div style="display:flex; justify-content:space-between;"><div><span style="font-size:18px; font-weight:bold; color:white;">{name}</span> <span style="color:#aaa; font-size:12px;">{code}</span> <span class="tag tag-rev">營收創高</span></div><span style="color:white; font-weight:bold;">${price}</span></div><div class="rev-box"><div>單月營收: <span style="color:white;">{rev} 億</span></div><div>年增(YoY): <span class="rev-up">+{yoy}%</span></div><div>月增(MoM): <span class="rev-up">+{mom}%</span></div></div></div>"""
            st.markdown(html_code, unsafe_allow_html=True)
