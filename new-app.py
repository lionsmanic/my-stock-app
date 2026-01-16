import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# === 1. 網頁基本設定 ===
st.set_page_config(page_title="AI 全球股市戰情室 (旗艦版)", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# === 2. 巨量多國語系名稱資料庫 ===
STOCK_NAME_MAP = {
    # --- 台股：半導體/AI ---
    "2330.TW": "台積電", "2303.TW": "聯電", "5347.TWO": "世界先進", "6770.TW": "力積電", "3711.TW": "日月光投控",
    "2454.TW": "聯發科", "3034.TW": "聯詠", "2379.TW": "瑞昱", "3035.TW": "智原", "3443.TW": "創意", "3661.TW": "世芯-KY", "3529.TW": "力旺",
    "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達", "2376.TW": "技嘉", "2357.TW": "華碩",
    # --- 台股：零組件/光學/被動 ---
    "3008.TW": "大立光", "3406.TW": "玉晶光", "2327.TW": "國巨", "2492.TW": "華新科", "3026.TW": "禾伸堂",
    "3037.TW": "欣興", "8046.TW": "南電", "3189.TW": "景碩", "2368.TW": "金像電", "2313.TW": "華通",
    # --- 台股：傳產/金融 ---
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
    "1513.TW": "中興電", "1519.TW": "華城", "1503.TW": "士電", "1605.TW": "華新",
    "1301.TW": "台塑", "1303.TW": "南亞", "2002.TW": "中鋼", "1101.TW": "台泥", "9910.TW": "豐泰", "9904.TW": "寶成",
    "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金", "2884.TW": "玉山金",
    
    # --- 美股：科技巨頭 (Magnificent 7) ---
    "AAPL": "Apple (蘋果)", "MSFT": "Microsoft (微軟)", "GOOG": "Alphabet (谷歌)", "AMZN": "Amazon (亞馬遜)", 
    "NVDA": "NVIDIA (輝達)", "TSLA": "Tesla (特斯拉)", "META": "Meta (臉書)",
    
    # --- 美股：半導體 ---
    "AMD": "AMD (超微)", "INTC": "Intel (英特爾)", "QCOM": "Qualcomm (高通)", "AVGO": "Broadcom (博通)", 
    "MU": "Micron (美光)", "TXN": "TI (德儀)", "ASML": "ASML (艾司摩爾)", "TSM": "台積電ADR", "ARM": "Arm Holdings",
    
    # --- 美股：SaaS / 軟體 / 資安 ---
    "CRM": "Salesforce", "ADBE": "Adobe", "ORCL": "Oracle (甲骨文)", "NOW": "ServiceNow", "SNOW": "Snowflake",
    "PLTR": "Palantir", "CRWD": "CrowdStrike", "PANW": "Palo Alto Networks", "UBER": "Uber", "ABNB": "Airbnb",
    
    # --- 美股：醫療 / 製藥 ---
    "LLY": "Eli Lilly (禮來)", "NVO": "Novo Nordisk (諾和諾德)", "JNJ": "Johnson & Johnson", "PFE": "Pfizer (輝瑞)", 
    "MRK": "Merck (默克)", "UNH": "UnitedHealth", "ABBV": "AbbVie",
    
    # --- 美股：消費 / 零售 ---
    "COST": "Costco (好市多)", "WMT": "Walmart (沃爾瑪)", "PG": "P&G (寶僑)", "KO": "Coca-Cola (可口可樂)", 
    "PEP": "PepsiCo (百事)", "MCD": "McDonald's (麥當勞)", "SBUX": "Starbucks (星巴克)", "NKE": "Nike (耐吉)",
    
    # --- 美股：金融 / 支付 / 區塊鏈 ---
    "JPM": "JPMorgan (摩根大通)", "BAC": "Bank of America", "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal",
    "COIN": "Coinbase", "MSTR": "MicroStrategy", "HOOD": "Robinhood",
    
    # --- 美股：ETF ---
    "SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF", "SOXX": "半導體 ETF", "TLT": "20年美債 ETF", "GLD": "黃金 ETF",
    "XLK": "科技股 ETF", "XLV": "醫療保健 ETF", "XLE": "能源 ETF"
}

def get_stock_name(ticker):
    base_name = STOCK_NAME_MAP.get(ticker.upper())
    if base_name: return base_name
    # 處理台股後綴
    if ".TWO" in ticker.upper(): return STOCK_NAME_MAP.get(ticker.upper().replace(".TWO", ".TW"), ticker.upper())
    elif ".TW" in ticker.upper(): return STOCK_NAME_MAP.get(ticker.upper().replace(".TW", ".TWO"), ticker.upper())
    return ticker.upper()

# === 3. 核心運算 ===

def calculate_score_for_row(row, prev_row, prev2_row, prev3_row, fundamentals, target_pe):
    score = 0
    reasons = []
    
    eps = fundamentals.get('eps')
    pe = fundamentals.get('pe')
    pb = fundamentals.get('pb')
    rev_growth = fundamentals.get('rev_growth')
    price = row['Close']
    
    # --- 1. 估值與基本面 ---
    if eps is not None:
        if eps < 0: score -= 3 # 虧損重扣
        else:
            fair_value = eps * target_pe
            upside = (fair_value - price) / price
            if upside > 0.2: reasons.append("股價低估"); score += 2
            elif upside < -0.2: score -= 1.5

    # 針對美股，放寬 PE 標準 (美股通常較高)，這裡做簡單的判斷
    is_us_stock = not (".TW" in str(row.name) or ".TWO" in str(row.name)) # 簡單判斷
    
    # PE 判斷
    if pe:
        if 0 < pe < 20: reasons.append("PE<20"); score += 1
        elif is_us_stock and 0 < pe < 30: score += 0.5 # 美股 PE<30 算合理

    # PB 判斷
    if pb and pb < 1.5: reasons.append("PB低"); score += 1
    
    if rev_growth > 0.2: reasons.append("營收高成長"); score += 1
    elif rev_growth < -0.1: score -= 1

    # --- 2. 趨勢 (Trend) ---
    if price > row['SMA_240']:
        if prev_row['Close'] < prev_row['SMA_240']: reasons.append("🚀突破年線"); score += 2.5
        else: score += 1
    else:
        if prev_row['Close'] > prev_row['SMA_240']: reasons.append("跌破年線"); score -= 2

    # --- 3. 型態與量能 ---
    if (price > row['Open']) and (prev_row['Close'] > prev_row['Open']) and (prev2_row['Close'] > prev2_row['Open']) and (price > prev_row['Close']):
        reasons.append("🔥連三紅"); score += 2
    
    if row['Volume'] > row['Vol_SMA5'] * 1.8 and price > row['Open']:
        reasons.append("💰爆量"); score += 1.5

    # --- 4. 指標 ---
    if prev_row['MACD_Hist'] < 0 and row['MACD_Hist'] > 0: reasons.append("MACD翻紅"); score += 1.5
    if row['RSI'] < 30: reasons.append("RSI超賣"); score += 1
    if row['RSI'] > 75: reasons.append("RSI過熱"); score -= 2

    if score >= 4: suggestion = "💎 強力買進"
    elif score >= 1.5: suggestion = "✅ 偏多"
    elif score <= -3: suggestion = "🚨 賣出"
    elif score <= -1: suggestion = "⚠️ 偏空"
    else: suggestion = "⚪ 觀望"
    
    return score, suggestion, ", ".join(reasons)

@st.cache_data(ttl=600)
def get_analysis_matrix(ticker_list, target_pe):
    results = []
    
    with st.spinner(f'AI 正在跨國掃描中 (請稍候，美股歷史數據較大)...'):
        for ticker in ticker_list:
            ticker = ticker.strip()
            if not ticker: continue
            
            try:
                stock = yf.Ticker(ticker)
                
                # 基本面
                try:
                    info = stock.info
                    fundamentals = {
                        'eps': info.get('trailingEps', None),
                        'pe': info.get('trailingPE', None),
                        'pb': info.get('priceToBook', None),
                        'rev_growth': info.get('revenueGrowth', 0)
                    }
                except: fundamentals = {'eps': None, 'pe': None, 'pb': None, 'rev_growth': 0}

                # 抓取歷史數據 (Max 用於 20年線)
                df = stock.history(period="max")
                if len(df) < 250: continue
                
                # 指標計算
                df['SMA_20'] = df['Close'].rolling(window=20).mean()
                df['SMA_60'] = df['Close'].rolling(window=60).mean()
                df['SMA_240'] = df['Close'].rolling(window=240).mean()   # 年線
                df['SMA_1200'] = df['Close'].rolling(window=1200).mean() # 5年線
                df['SMA_4800'] = df['Close'].rolling(window=4800).mean() # 20年線
                
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0))
                loss = (-delta.where(delta < 0, 0))
                rs = gain.ewm(com=13, min_periods=14, adjust=False).mean() / loss.ewm(com=13, min_periods=14, adjust=False).mean()
                df['RSI'] = 100 - (100 / (1 + rs))
                
                exp12 = df['Close'].ewm(span=12, adjust=False).mean()
                exp26 = df['Close'].ewm(span=26, adjust=False).mean()
                df['MACD_Hist'] = (exp12 - exp26) - (exp12 - exp26).ewm(span=9, adjust=False).mean()
                df['Vol_SMA5'] = df['Volume'].rolling(window=5).mean()

                row_0, row_1, row_2, row_3 = df.iloc[-1], df.iloc[-2], df.iloc[-3], df.iloc[-4]
                row_4 = df.iloc[-5]

                # 訊號計算
                score_0, sig_0, reason_0 = calculate_score_for_row(row_0, row_1, row_2, row_3, fundamentals, target_pe)
                score_1, sig_1, _ = calculate_score_for_row(row_1, row_2, row_3, row_4, fundamentals, target_pe)
                score_2, sig_2, _ = calculate_score_for_row(row_2, row_3, row_4, df.iloc[-6], fundamentals, target_pe)

                # 驗證
                price_0 = row_0['Close']
                price_2 = row_2['Close']
                roi_t2 = (price_0 - price_2) / price_2
                
                validation = "➖"
                if "買進" in sig_2 or "偏多" in sig_2:
                    validation = f"✅ 準 (+{int(roi_t2*100)}%)" if roi_t2 > 0 else f"❌ 誤 ({int(roi_t2*100)}%)"
                elif "賣出" in sig_2 or "偏空" in sig_2:
                    validation = f"✅ 準 ({int(roi_t2*100)}%)" if roi_t2 < 0 else f"❌ 誤 (+{int(roi_t2*100)}%)"

                fair_price = "-"
                if fundamentals['eps'] and fundamentals['eps'] > 0:
                    fair_price = round(fundamentals['eps'] * target_pe, 2)

                # 落難績優股判斷
                is_undervalued_gem = False
                gem_reason = ""
                # 美股通常用較長均線判斷，且 EPS > 0
                if fundamentals['eps'] and fundamentals['eps'] > 0:
                    current_price = row_0['Close']
                    if not pd.isna(row_0['SMA_4800']) and current_price < row_0['SMA_4800']:
                        is_undervalued_gem = True
                        gem_reason = "🔥跌破20年線"
                    elif not pd.isna(row_0['SMA_1200']) and current_price < row_0['SMA_1200']:
                        is_undervalued_gem = True
                        gem_reason = "跌破5年線"
                    elif not pd.isna(row_0['SMA_240']) and current_price < row_0['SMA_240'] and fundamentals['rev_growth'] > -0.05:
                        is_undervalued_gem = True
                        gem_reason = "跌破年線"

                results.append({
                    "代號": ticker.upper(),
                    "名稱": get_stock_name(ticker),
                    "現價": round(price_0, 2),
                    "漲跌幅": (price_0 - row_1['Close']) / row_1['Close'],
                    "今日訊號 (T-0)": sig_0,
                    "昨日訊號 (T-1)": sig_1,
                    "前日訊號 (T-2)": sig_2,
                    "📝 策略理由": reason_0,
                    "T-2 驗證": validation,
                    "合理價": fair_price,
                    "Score": score_0,
                    "IsGem": is_undervalued_gem,
                    "GemReason": gem_reason
                })
            except: continue
            
    return pd.DataFrame(results)

def plot_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="max")
        if len(df) < 60:
            st.error("資料不足，無法繪圖")
            return

        df['SMA_60'] = df['Close'].rolling(window=60).mean()
        df['SMA_240'] = df['Close'].rolling(window=240).mean()
        df['SMA_1200'] = df['Close'].rolling(window=1200).mean()
        df['SMA_4800'] = df['Close'].rolling(window=4800).mean() 
        
        display_days = 750 
        if len(df) > display_days:
            plot_df = df.tail(display_days)
        else:
            plot_df = df
        
        fig = go.Figure(data=[go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='K線')])
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_60'], line=dict(color='green', width=1), name='季線 (60MA)'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_240'], line=dict(color='blue', width=2), name='年線 (240MA)'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_1200'], line=dict(color='orange', width=2, dash='dot'), name='5年線 (1200MA)'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_4800'], line=dict(color='red', width=3, dash='dash'), name='🔥20年線 (4800MA)'))
        
        fig.update_layout(title=f"{get_stock_name(ticker)} ({ticker}) - 長線價值檢視", yaxis_title="價格", xaxis_rangeslider_visible=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
    except: st.error("無法繪製圖表")

# === 4. 介面佈局 ===
with st.sidebar:
    st.header("🌍 全球產業與族群設定")
    
    # === 巨量選股清單 ===
    PRESET_DICT = {
        "📝 自選觀察清單 (Custom)": {"codes": "NVDA, TSLA, 2330.TW, PLTR, MSTR", "pe": 30},
        
        # --- 美股 (US Stocks) ---
        "🇺🇸 美股七雄 (Magnificent 7)": {"codes": "AAPL, MSFT, GOOG, AMZN, NVDA, TSLA, META", "pe": 30},
        "☁️ SaaS 軟體與資安": {"codes": "CRM, ADBE, ORCL, NOW, SNOW, PLTR, CRWD, PANW, UBER, ABNB", "pe": 40},
        "⚙️ 美股半導體巨頭": {"codes": "AMD, INTC, QCOM, AVGO, MU, TXN, ASML, TSM, ARM", "pe": 25},
        "💊 全球醫療與製藥": {"codes": "LLY, NVO, JNJ, PFE, MRK, UNH, ABBV", "pe": 25},
        "🛍️ 美國民生消費": {"codes": "COST, WMT, PG, KO, PEP, MCD, SBUX, NKE", "pe": 22},
        "💳 美股金融與支付": {"codes": "JPM, BAC, V, MA, PYPL, COIN, MSTR, HOOD", "pe": 18},
        "📊 全球重要 ETF": {"codes": "SPY, QQQ, SOXX, TLT, GLD, XLK, XLV, XLE", "pe": 20},
        
        # --- 台股 (TW Stocks) ---
        "🤖 AI 伺服器/組裝": {"codes": "2330.TW, 2317.TW, 2382.TW, 3231.TW, 6669.TW, 2356.TW, 2376.TW, 2357.TW, 2324.TW, 4938.TW, 2301.TW", "pe": 25},
        "💡 IC 設計 (高價/IP)": {"codes": "2454.TW, 3034.TW, 2379.TW, 3035.TW, 3661.TW, 3443.TW, 3529.TW, 6531.TW, 4961.TW, 6415.TW", "pe": 35},
        "❄️ 散熱/光學/被動": {"codes": "3017.TW, 3324.TWO, 3653.TW, 2421.TW, 3008.TW, 3406.TW, 2327.TW, 2492.TW, 3026.TW", "pe": 22},
        "🏗️ CoWoS/PCB/網通": {"codes": "3131.TW, 3583.TW, 6196.TW, 3037.TW, 8046.TW, 3189.TW, 2368.TW, 2313.TW, 2345.TW, 5388.TWO", "pe": 20},
        "🔌 重電/綠能/軍工": {"codes": "1513.TW, 1519.TW, 1503.TW, 1504.TW, 1605.TW, 6806.TW, 9958.TW, 2634.TW, 2645.TW", "pe": 25},
        "🚢 航運/鋼鐵/塑化": {"codes": "2603.TW, 2609.TW, 2615.TW, 2606.TW, 2618.TW, 2610.TW, 2002.TW, 2014.TW, 1301.TW, 1303.TW, 1101.TW", "pe": 12},
        "💰 台灣全金控 (14家)": {"codes": "2881.TW, 2882.TW, 2891.TW, 2886.TW, 2884.TW, 2892.TW, 5880.TW, 2885.TW, 2880.TW, 2883.TW, 2887.TW, 2890.TW, 2888.TW, 2889.TW", "pe": 15},
    }
    
    selected_group = st.selectbox("選擇市場與族群", list(PRESET_DICT.keys()))
    group_data = PRESET_DICT[selected_group]
    
    st.divider()
    target_pe = st.slider(f"合理本益比基準", 5, 80, group_data["pe"])
    user_tickers = st.text_area("觀察清單", value=group_data["codes"], height=100)
    
    st.info("💡 **小撇步**：\n美股代號直接輸入 (如 NVDA)，台股需加 .TW (上市) 或 .TWO (上櫃)。")

st.title("🌍 AI 全球股市戰情室 (旗艦版)")
st.caption(f"六大面向 + T-2回測 + **20年線價值挖掘** | 基準本益比: **{target_pe}倍**")

# === 執行 ===
ticker_list = [x.strip() for x in user_tickers.split(',')]
df_result = get_analysis_matrix(ticker_list, target_pe)

if not df_result.empty:
    df_long = df_result[df_result['Score'] >= 2.5].sort_values(by='Score', ascending=False)
    df_gem = df_result[df_result['IsGem'] == True].sort_values(by='GemReason', ascending=False)
    df_short = df_result[df_result['Score'] <= -2].sort_values(by='Score', ascending=True)
    df_watch = df_result[(df_result['Score'] > -2) & (df_result['Score'] < 2.5)]

    def style_signal(val):
        color = 'black'
        if '買進' in str(val) or '偏多' in str(val): color = 'green'
        elif '賣出' in str(val) or '偏空' in str(val): color = 'red'
        elif '✅' in str(val): color = 'blue'
        return f'color: {color}; font-weight: bold'

    st.divider()
    t_gem, t1, t2, t3 = st.tabs([f"💎 落難績優股 (破線) ({len(df_gem)})", f"🚀 強力買進 ({len(df_long)})", f"📉 建議賣出 ({len(df_short)})", f"👀 觀望 ({len(df_watch)})"])

    cols_config = {
        "現價": st.column_config.NumberColumn(format="$%.2f"),
        "漲跌幅": st.column_config.NumberColumn(format="%.2f%%"),
        "合理價": st.column_config.NumberColumn(format="$%.2f", help="EPS x 合理PE"),
        "📝 策略理由": st.column_config.TextColumn(width="medium"), 
        "GemReason": st.column_config.TextColumn(label="低估狀態"),
        "Score": None, "IsGem": None
    }

    with t_gem:
        if not df_gem.empty:
            st.success("以下股票 EPS>0，且股價跌破長期均線 (20年/5年/1年)：")
            st.dataframe(df_gem.style.applymap(style_signal, subset=['今日訊號 (T-0)']), column_config=cols_config, use_container_width=True, hide_index=True)
        else: st.info("目前無「跌破長期均線」的績優股")

    with t1:
        if not df_long.empty:
            st.dataframe(df_long.style.applymap(style_signal, subset=['今日訊號 (T-0)', '昨日訊號 (T-1)', '前日訊號 (T-2)', 'T-2 驗證']), column_config=cols_config, use_container_width=True, hide_index=True)
        else: st.info("今日無強力買進訊號")

    with t2:
        if not df_short.empty:
            st.dataframe(df_short.style.applymap(style_signal, subset=['今日訊號 (T-0)', '昨日訊號 (T-1)', '前日訊號 (T-2)', 'T-2 驗證']), column_config=cols_config, use_container_width=True, hide_index=True)
        else: st.success("無危險賣出訊號")

    with t3:
        st.dataframe(df_watch.style.applymap(style_signal, subset=['今日訊號 (T-0)', '昨日訊號 (T-1)', '前日訊號 (T-2)', 'T-2 驗證']), column_config=cols_config, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📊 長線 K 線與 20 年線檢視")
    sel = st.selectbox("選擇股票", [f"{r['名稱']} ({r['代號']})" for i, r in df_result.iterrows()])
    if sel: plot_chart(sel.split('(')[-1].replace(')', ''))
else:
    st.error("無法取得數據")
