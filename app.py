import streamlit as st
import pandas as pd
import yfinance as yf

# --- 1. 設定頁面 ---
st.set_page_config(page_title="隔日沖雷達", layout="centered")

# --- CSS 優化 (白色大字體 + 手機卡片風) ---
st.markdown("""
<style>
    .stock-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* 股票名稱與代號改為白色 */
    .stock-title { font-size: 20px; font-weight: bold; color: #ffffff; }
    
    .label { font-size: 14px; color: #aaaaaa; }
    .resistance { color: #ff6c6c; font-weight: bold; font-size: 18px;}
    .support { color: #4bceff; font-weight: bold; font-size: 18px;}
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

# --- 3. 定義隔日沖熱門股名單 (代號對照表) ---
# 這裡篩選了波動大、主力愛玩的股票 (重電、AI、散熱、IP、航運)
STOCK_MAP = {
    # 重電與綠能
    "1519": "華城", "1513": "中興電", "1503": "士電", "1514": "亞力", "1609": "大亞",
    
    # AI 組裝與伺服器
    "3231": "緯創", "2382": "廣達", "2376": "技嘉", "6669": "緯穎", "2356": "英業達",
    
    # 散熱族群 (當沖熱門)
    "3017": "奇鋐", "3324": "雙鴻", "2421": "建準", "3653": "健策",
    
    # IP 與高價IC (主力控盤)
    "3035": "智原", "3661": "世芯-KY", "3443": "創意", "3529": "力旺", "6643": "M31",
    
    # PCB / CCL / 網通
    "2368": "金像電", "6274": "台燿", "8358": "金居", "2383": "台光電", "3715": "定穎投控",
    
    # 航運 (人氣指標)
    "2609": "陽明", "2603": "長榮", "2615": "萬海", "2618": "長榮航", "2610": "華航",
    
    # 其他熱門飆股
    "8069": "元太", "4968": "立積", "3532": "台勝科", "6415": "矽力", "2454": "聯發科",
    "2449": "京元電", "6213": "智擎", "4763": "材料-KY", "1504": "東元"
}

HOT_STOCKS = list(STOCK_MAP.keys())

# --- 4. 介面開始 ---
st.title("🔥 隔日沖主力戰場")
st.caption("鎖定高波動、高周轉熱門股 (資料來源: Yahoo Finance)")

tab1, tab2 = st.tabs(["🚀 熱門股掃描", "🧮 個股查詢"])

# === 功能一：批量掃描 ===
with tab1:
    if st.button("開始掃描主力股 (約 15 秒)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在分析市場數據，請稍候...")
        
        tickers = [f"{s}.TW" for s in HOT_STOCKS]
        
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            results = []
            
            for i, stock_id in enumerate(HOT_STOCKS):
                try:
                    df = data[f"{stock_id}.TW"]
                    if df.empty: continue
                    row = df.iloc[-1]
                    # 確保有收盤價
                    if pd.isna(row['Close']): continue

                    close = float(row['Close'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    open_p = float(row['Open'])
                    
                    # 計算漲跌幅
                    change_pct = ((close - open_p) / open_p) * 100 
                    
                    # 計算 CDP
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    
                    # 取得中文名稱
                    name = STOCK_MAP.get(stock_id, stock_id)
                    
                    results.append({
                        "code": stock_id,
                        "name": name,
                        "close": close, "high": high, "low": low,
                        "change": change_pct,
                        "ah": ah, "nh": nh, "nl": nl
                    })
                except: continue
                progress_bar.progress((i + 1) / len(HOT_STOCKS))

            # 排序：只顯示漲幅最大的前 20 檔 (最容易被隔日沖鎖定)
            results.sort(key=lambda x: x['change'], reverse=True)
            top_stocks = results[:20]
            
            progress_bar.empty()
            st.success(f"掃描完成！列出今日最強勢前 {len(top_stocks)} 檔")

            for s in top_stocks:
                fire_icon = "🔥" if s['change'] > 3 else ""
                
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="stock-title">{s['code']} {s['name']} {fire_icon}</span>
                        <span style="color: #ff4b4b; font-weight: bold;">漲幅 {round(s['change'], 2)}%</span>
                    </div>
                    <div style="margin-top: 5px; color: #ddd; font-size: 13px;">
                        收盤: {round(s['close'], 2)} | 高: {s['high']} | 低: {s['low']}
                    </div>
                    <hr style="margin: 8px 0; border-color: #555;">
                    <div style="display: flex; justify-content: space-between; text-align: center;">
                        <div>
                            <span class="label">壓力 (NH)</span><br>
                            <span class="resistance">{s['nh']}</span>
                        </div>
                        <div>
                            <span class="label">支撐 (NL)</span><br>
                            <span class="support">{s['nl']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"錯誤：{e}")
    else:
        st.markdown("👇 點擊按鈕，自動掃描重電、AI、IP、航運等主力熱門股")

# === 功能二：手動查詢 ===
with tab2:
    st.info("輸入代號查詢不在清單上的股票")
    stock_input = st.text_input("輸入代號 (如 3231)", "")
    
    if st.button("查詢個股"):
        if stock_input:
            try:
                stock = yf.Ticker(f"{stock_input}.TW")
                data = stock.history(period="1d")
                if not data.empty:
                    c = data['Close'].iloc[-1]
                    h = data['High'].iloc[-1]
                    l = data['Low'].iloc[-1]
                    ah, nh, nl, al, cdp = calculate_cdp(h, l, c)
                    
                    # 嘗試找名稱 (這裡手動查詢可能沒有中文名，但有代號)
                    display_name = STOCK_MAP.get(stock_input, stock_input)
                    
                    st.markdown(f"""
                    <div class="stock-card">
                        <b class="stock-title">{display_name}</b><br>
                        <div style="margin-top: 10px; display: flex; justify-content: space-between;">
                            <div>壓力(NH): <span class="resistance">{nh}</span></div>
                            <div>支撐(NL): <span class="support">{nl}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("查無資料")
            except:
                st.error("查詢錯誤")
