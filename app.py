import streamlit as st
import pandas as pd
import yfinance as yf

# --- 1. 設定頁面 ---
st.set_page_config(page_title="隔日沖雷達", layout="centered")

# --- CSS 優化 (手機卡片風) ---
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
    .big-number { font-size: 24px; font-weight: bold; color: #ffffff; }
    .label { font-size: 14px; color: #aaaaaa; }
    .resistance { color: #ff6c6c; font-weight: bold; }
    .support { color: #4bceff; font-weight: bold; }
    .limit-up { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 5px; border-radius: 5px; font-size: 12px; }
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

# --- 3. 定義熱門股清單 (涵蓋AI、航運、重電、權值) ---
# 這裡列出了市場上最活潑的股票，您可以自己隨時來這裡增加
HOT_STOCKS = [
    "2330", "2317", "2603", "2609", "2615", "3231", "2382", "6669", "2376", "2356", # 權值、航運、AI
    "1519", "1503", "1513", "1514", "3035", "3443", "3661", "2454", "2379", "3037", # 重電、IC設計
    "3017", "2449", "6274", "8069", "5347", "3008", "2409", "3481", "2618", "2610", # 面板、航空
    "1605", "2059", "2368", "2383", "3044", "3532", "4968", "4919", "4958", "5269",
    "6176", "6213", "6415", "6456", "6719", "6753", "8046", "8210", "8996", "9958"
]

# --- 4. 介面開始 ---
st.title("🔥 市場熱門股掃描")
st.caption("自動掃描成交量大、波動大的熱門標的 (資料來源: Yahoo Finance)")

tab1, tab2 = st.tabs(["🚀 熱門股排行 (真實)", "🧮 手動計算機"])

# === 功能一：批量掃描 ===
with tab1:
    if st.button("開始掃描市場 (需約 10-20 秒)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        st.info("正在連線下載最新股價，請稍候...")
        
        # 1. 準備代號清單
        tickers = [f"{s}.TW" for s in HOT_STOCKS]
        
        try:
            # 2. 批量下載資料 (速度快)
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
            
            results = []
            
            # 3. 整理數據
            for i, stock_id in enumerate(HOT_STOCKS):
                try:
                    # 處理 yfinance 的多層索引結構
                    df = data[f"{stock_id}.TW"]
                    if df.empty:
                        continue
                        
                    # 取得最新一筆
                    row = df.iloc[-1]
                    
                    # 必須確認該股今日有交易
                    if pd.isna(row['Close']):
                        continue

                    close = float(row['Close'])
                    high = float(row['High'])
                    low = float(row['Low'])
                    open_p = float(row['Open'])
                    
                    # 計算漲跌幅
                    change_pct = ((close - open_p) / open_p) * 100 
                    
                    # 計算 CDP
                    ah, nh, nl, al, cdp = calculate_cdp(high, low, close)
                    
                    results.append({
                        "code": stock_id,
                        "close": close,
                        "high": high,
                        "low": low,
                        "change": change_pct,
                        "ah": ah, "nh": nh, "nl": nl, "al": al
                    })
                except:
                    continue
                
                # 更新進度條
                progress_bar.progress((i + 1) / len(HOT_STOCKS))

            # 4. 排序：只顯示漲勢最強的前 20 名 (主力最愛)
            results.sort(key=lambda x: x['change'], reverse=True)
            top_stocks = results[:20]
            
            progress_bar.empty() # 移除進度條
            st.success(f"掃描完成！列出漲勢最強的前 {len(top_stocks)} 檔")

            # 5. 顯示卡片
            for s in top_stocks:
                # 判斷是否大漲 (漲幅 > 3%)
                fire_icon = "🔥" if s['change'] > 3 else ""
                
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 20px; font-weight: bold;">{s['code']} {fire_icon}</span>
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
            st.error(f"掃描時發生錯誤：{e}")
    else:
        st.markdown("👇 點擊按鈕，系統會自動抓取 60 檔熱門股並算出明日點位")

# === 功能二：手動計算 ===
with tab2:
    st.info("查詢不在清單上的股票，請手動輸入")
    stock_input = st.text_input("輸入代號 (如 2618)", "")
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
                    st.markdown(f"""
                    <div class="stock-card">
                        <b>{stock_input}</b><br>
                        壓力(NH): <span class="resistance">{nh}</span> | 支撐(NL): <span class="support">{nl}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("查無資料")
            except:
                st.error("查詢錯誤")
