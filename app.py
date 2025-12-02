import streamlit as st
import pandas as pd
import yfinance as yf

# --- 1. 設定頁面 ---
st.set_page_config(page_title="隔日沖雷達", layout="centered")

# --- CSS 優化 (白色大字體 + 手機卡片風) ---
st.markdown("""
<style>
    /* 卡片背景 */
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 關鍵：所有股票名稱與數字強制白色 */
    .stock-title { font-size: 22px; font-weight: bold; color: #ffffff !important; }
    .big-number { font-size: 24px; font-weight: bold; color: #ffffff !important; }
    
    /* 副標題灰色 */
    .label { font-size: 14px; color: #bbbbbb !important; }
    
    /* 壓力支撐顏色 */
    .resistance { color: #ff6c6c; font-weight: bold; font-size: 18px; }
    .support { color: #4bceff; font-weight: bold; font-size: 18px; }
    
    /* 輸入框標籤顏色 */
    .stNumberInput label { color: #ffffff !important; }
    .stTextInput label { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算 (CDP) ---
def calculate_cdp(high, low, close):
    cdp = (high + low + close * 2) / 4
    ah = cdp + (high - low)
    nh = cdp * 2 - low
    nl = cdp * 2 - high
    al = cdp - (high - low)
    return round(ah, 2), round(nh, 2), round(nl, 2), round(al, 2), round(cdp, 2)

# --- 3. 定義隔日沖熱門股名單 (含中文) ---
STOCK_MAP = {
    "1519": "華城", "1513": "中興電", "1503": "士電", "1514": "亞力", "1609": "大亞",
    "3231": "緯創", "2382": "廣達", "2376": "技嘉", "6669": "緯穎", "2356": "英業達",
    "3017": "奇鋐", "3324": "雙鴻", "2421": "建準", "3653": "健策",
    "3035": "智原", "3661": "世芯", "3443": "創意", "3529": "力旺", "6643": "M31",
    "2368": "金像電", "6274": "台燿", "8358": "金居", "2383": "台光電",
    "2609": "陽明", "2603": "長榮", "2615": "萬海", "2618": "長榮航", "2610": "華航",
    "8069": "元太", "4968": "立積", "3532": "台勝科", "6415": "矽力", "2454": "聯發科",
    "2449": "京元電", "6213": "智擎", "4763": "材料", "1504": "東元"
}
HOT_STOCKS = list(STOCK_MAP.keys())

# --- 4. 介面開始 ---
st.title("🔥 隔日沖主力戰場")

# 分成三個分頁，滿足所有需求
tab1, tab2, tab3 = st.tabs(["🚀 熱門掃描", "🔍 個股搜尋", "🧮 手動計算"])

# === 分頁一：熱門股批量掃描 ===
with tab1:
    if st.button("開始掃描主力股", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("分析中...")
        tickers = [f"{s}.TW" for s in HOT_STOCKS]
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            results = []
            for i, stock_id in enumerate(HOT_STOCKS):
                try:
                    df = data[f"{stock_id}.TW"]
                    if df.empty or pd.isna(df.iloc[-1]['Close']): continue
                    row = df.iloc[-1]
                    c, h, l, o = float(row['Close']), float(row['High']), float(row['Low']), float(row['Open'])
                    change_pct = ((c - o) / o) * 100 
                    ah, nh, nl, al, cdp = calculate_cdp(h, l, c)
                    name = STOCK_MAP.get(stock_id, stock_id)
                    results.append({"code": stock_id, "name": name, "c": c, "h": h, "l": l, "chg": change_pct, "nh": nh, "nl": nl})
                except: continue
                progress_bar.progress((i + 1) / len(HOT_STOCKS))

            results.sort(key=lambda x: x['chg'], reverse=True)
            top_stocks = results[:20]
            progress_bar.empty()

            for s in top_stocks:
                fire = "🔥" if s['chg'] > 3 else ""
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="stock-title">{s['code']} {s['name']} {fire}</span>
                        <span style="color:#ff4b4b; font-weight:bold;">{round(s['chg'], 2)}%</span>
                    </div>
                    <div class="label" style="margin-top:5px;">收盤: {round(s['c'], 2)} | 高: {s['h']} | 低: {s['l']}</div>
                    <hr style="border-color:#555;">
                    <div style="display:flex; justify-content:space-between; text-align:center;">
                        <div><span class="label">壓力 (NH)</span><br><span class="resistance">{s['nh']}</span></div>
                        <div><span class="label">支撐 (NL)</span><br><span class="support">{s['nl']}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e: st.error(f"錯誤：{e}")
    else:
        st.caption("點擊按鈕掃描重電、AI、航運等 50+ 檔熱門股")

# === 分頁二：萬能個股搜尋 (修復搜不到的問題) ===
with tab2:
    st.info("輸入代號 (如 2330, 8069)，自動偵測上市櫃")
    stock_input = st.text_input("輸入股票代號", "")
    
    if st.button("🔍 搜尋"):
        if stock_input:
            with st.spinner("搜尋中..."):
                # 1. 先試試看上市 (.TW)
                target = f"{stock_input}.TW"
                stock = yf.Ticker(target)
                data = stock.history(period="1d")
                
                # 2. 如果上市沒資料，改試上櫃 (.TWO)
                if data.empty:
                    target = f"{stock_input}.TWO"
                    stock = yf.Ticker(target)
                    data = stock.history(period="1d")

                if not data.empty:
                    c = data['Close'].iloc[-1]
                    h = data['High'].iloc[-1]
                    l = data['Low'].iloc[-1]
                    ah, nh, nl, al, cdp = calculate_cdp(h, l, c)
                    
                    # 嘗試抓取名稱 (如果有的話)
                    name = STOCK_MAP.get(stock_input, "")
                    
                    st.success(f"成功找到：{stock_input} {name}")
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="stock-title">{stock_input} {name}</span>
                        </div>
                        <div class="label" style="margin-top:5px;">收盤: {round(c, 2)} | 高: {h} | 低: {l}</div>
                        <hr style="border-color:#555;">
                        <div style="display:flex; justify-content:space-between; text-align:center;">
                            <div><span class="label">壓力 (NH)</span><br><span class="resistance">{nh}</span></div>
                            <div><span class="label">支撐 (NL)</span><br><span class="support">{nl}</span></div>
                        </div>
                        <div style="text-align:center; margin-top:10px;"><span class="label">中關價 (CDP): {cdp}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"找不到代號 {stock_input}，請確認是否輸入正確 (或使用手動計算功能)")

# === 分頁三：手動計算機 (救星功能) ===
with tab3:
    st.warning("遇到查不到的股票，直接輸入價格即可計算！")
    
    col1, col2 = st.columns(2)
    with col1:
        p_close = st.number_input("收盤價", value=0.0, step=0.5)
        p_high = st.number_input("最高價", value=0.0, step=0.5)
    with col2:
        p_low = st.number_input("最低價", value=0.0, step=0.5)
        
    if st.button("🧮 開始計算"):
        if p_close > 0:
            ah, nh, nl, al, cdp = calculate_cdp(p_high, p_low, p_close)
            st.markdown(f"""
            <div class="stock-card">
                <div style="text-align:center; margin-bottom:10px;">
                    <span class="stock-title">手動計算結果</span>
                </div>
                <hr style="border-color:#555;">
                <div style="display:flex; justify-content:space-between; text-align:center;">
                    <div><span class="label">壓力 (NH)</span><br><span class="resistance">{nh}</span></div>
                    <div><span class="label">支撐 (NL)</span><br><span class="support">{nl}</span></div>
                </div>
                <div style="text-align:center; margin-top:10px;">
                    <span class="label">最高壓力 (AH): {ah}</span> | <span class="label">最低支撐 (AL): {al}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("請輸入大於 0 的價格")
