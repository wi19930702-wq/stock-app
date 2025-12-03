import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime, date

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
    .card-green { border-left: 6px solid #00c853; } /* 計算機 */
    .card-red { border-left: 6px solid #ff4b4b; }   /* 當沖 */
    .card-gold { border-left: 6px solid #ffd700; }  /* 營收 */
    
    /* 字體與標籤 */
    .big-label { font-size: 14px; color: #aaaaaa; }
    .big-value { font-size: 24px; font-weight: bold; color: #ffffff; }
    
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #00e676; font-weight: bold; }
    
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
        color: white;
    }
    .tag-rev { background-color: #f57f17; }
    
    /* 日期標籤 */
    .date-badge {
        background-color: #444;
        color: #bbb;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        float: right;
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
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

def generate_mock_revenue():
    rev = round(random.uniform(10, 500), 1)
    yoy = round(random.uniform(15, 120), 1)
    mom = round(random.uniform(5, 30), 1)
    return rev, yoy, mom

def generate_mock_broker_html():
    BROKER_POOLS = [("凱基-台北", "#d32f2f"), ("富邦-建國", "#1976d2"), ("美林", "#444"), ("摩根大通", "#444"), ("統一-嘉義", "#444"), ("永豐金-虎尾", "#444")]
    selected = random.sample(BROKER_POOLS, 3)
    html_parts = []
    for name, color in selected:
        vol = random.randint(500, 3000)
        html_parts.append(f'<span style="background-color:{color}; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:4px; color:white; display:inline-block; margin-bottom:2px;">{name} +{vol}</span>')
    return "".join(html_parts)

# --- 4. 側邊欄設定 (模式切換) ---
st.sidebar.title("⚙️ 設定")
data_mode = st.sidebar.radio(
    "選擇掃描模式：",
    ("🔥 今日即時 (盤中衝刺)", "🌙 昨日收盤 (盤前做功課)"),
    index=1  # 預設改成昨日收盤，方便您早上看
)
is_look_back = "昨日" in data_mode

# --- 5. 介面設計 ---
tab1, tab2, tab3 = st.tabs(["🧮 計算機", "🚀 當沖掃描", "💰 營收創高"])

# === 分頁 1: 經典計算機 ===
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
            st.markdown(f"""<div class="stock-card card-green" style="text-align:center;">
<div style="color:#aaa; margin-bottom:10px;">中關價 (CDP): {cdp}</div>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px; margin-bottom:10px;">
<div><div class="big-label">賣出壓力 (NH)</div><div class="big-value resistance">{nh}</div></div>
<div><div class="big-label">買進支撐 (NL)</div><div class="big-value support">{nl}</div></div>
</div>
<div style="display:flex; justify-content:space-between;">
<div><div style="font-size:12px; color:#aaa;">最高壓力 (AH)</div><div style="font-size:16px; color:#ff6c6c;">{ah}</div></div>
<div><div style="font-size:12px; color:#aaa;">最低支撐 (AL)</div><div style="font-size:16px; color:#00e676;">{al}</div></div>
</div>
</div>""", unsafe_allow_html=True)

# === 分頁 2: 當沖掃描 (修正日期抓取邏輯) ===
with tab2:
    st.markdown(f"### 🔍 熱門股掃描 - {data_mode}")
    
    if st.button(f"開始掃描 ({'看昨天' if is_look_back else '看即時'})", use_container_width=True):
        progress_bar = st.progress(0)
        tickers = [f"{c}.TW" for c in SCAN_TARGETS]
        results = []
        
        # 取得今天日期字串
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 抓取 5 天資料，確保有歷史數據
            data = yf.download(tickers, period="5d", group_by='ticker', threads=True)
            
            for i, code in enumerate(SCAN_TARGETS):
                try:
                    df = data[f"{code}.TW"]
                    if df.empty: continue
                    
                    # --- 關鍵修正：智慧日期判斷 ---
                    # 取得最後一筆資料
                    last_row = df.iloc[-1]
                    last_date = str(last_row.name)[:10]
                    
                    if is_look_back:
                        # 模式：看昨天收盤
                        
                        # 如果最後一筆是「今天」，那就代表 Yahoo 已經更新到開盤了，我們要退回上一筆
                        if last_date == today_str:
                            if len(df) >= 2:
                                row = df.iloc[-2] # 抓倒數第二筆 (昨天)
                            else:
                                continue # 資料不足，跳過
                        else:
                            # 如果最後一筆不是今天 (例如昨天晚上 Yahoo 更新了昨收)，那就直接用最後一筆
                            row = last_row
                    else:
                        # 模式：看即時
                        row = last_row
                    
                    # 再次確認抓到的日期
                    data_date = str(row.name)[:10]

                    if pd.isna(row['Volume']): continue
                    
                    vol = int(row['Volume'])
                    close = float(row['Close'])
                    op = float(row['Open'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    
                    # 篩選條件
                    if vol < 1000000: continue
                    pct = ((close - op) / op) * 100
                    if pct < 1.0: continue
                    
                    name = STOCK_MAP.get(code, code)
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    bk_html = generate_mock_broker_html()
                    
                    results.append({
                        "code":code, "name":name, "vol":int(vol/1000), 
                        "close":close, "pct":pct, "nh":nh, "nl":nl, 
                        "bk":bk_html, "date":data_date
                    })
                except: continue
                progress_bar.progress((i+1)/len(SCAN_TARGETS))
            
            progress_bar.empty()
            results.sort(key=lambda x: x['pct'], reverse=True)
            
            if not results: 
                st.warning("查無符合標的 (可能剛開盤量不足，或假日無數據)")
            else:
                st.success(f"掃描完成！顯示資料日期：{results[0]['date']}")
                for s in results:
                    st.markdown(f"""<div class="stock-card card-red">
<div style="display:flex; justify-content:space-between;">
<div>
    <span style="font-size:18px; font-weight:bold; color:white;">{s['name']}</span> 
    <span style="color:#aaa; font-size:12px;">{s['code']}</span>
</div>
<span class="date-badge">{s['date']}</span>
</div>
<div style="display:flex; justify-content:space-between; margin-top:5px;">
    <span style="color:#ff4b4b; font-weight:bold;">+{round(s['pct'], 2)}%</span>
    <span style="font-size:13px; color:#ccc;">量: {s['vol']} 張 | 收: {s['close']}</span>
</div>
<div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px solid #444; padding-top:8px;">
<span class="resistance">壓: {s['nh']}</span> <span class="support">撐: {s['nl']}</span>
</div>
<div style="margin-top:8px; font-size:12px; color:#aaa;">⚡ 模擬主力: {s['bk']}</div>
</div>""", unsafe_allow_html=True)
        except: st.error("連線錯誤")

# === 分頁 3: 營收創高 (模擬) ===
with tab3:
    st.markdown("### 💰 月營收創新高 (模擬)")
    st.caption("⚠️ 注意：營收數據為模擬展示 (Yahoo API 無法取得營收)")
    if st.button("掃描營收強勢股", use_container_width=True):
        targets = random.sample(SCAN_TARGETS, 10)
        for code in targets:
            name = STOCK_MAP.get(code, code)
            try:
                stock = yf.Ticker(f"{code}.TW")
                hist = stock.history(period="1d")
                if hist.empty: continue
                price = round(hist['Close'].iloc[-1], 2)
            except: price = "N/A"
            rev, yoy, mom = generate_mock_revenue()
            
            st.markdown(f"""<div class="stock-card card-gold">
<div style="display:flex; justify-content:space-between;">
<div><span style="font-size:18px; font-weight:bold; color:white;">{name}</span> <span style="color:#aaa; font-size:12px;">{code}</span> <span class="tag tag-rev">營收創高</span></div>
<span style="color:white; font-weight:bold;">${price}</span>
</div>
<div class="rev-box">
<div>單月營收: <span style="color:white;">{rev} 億</span></div>
<div>年增(YoY): <span class="rev-up">+{yoy}%</span></div>
<div>月增(MoM): <span class="rev-up">+{mom}%</span></div>
</div>
</div>""", unsafe_allow_html=True)
