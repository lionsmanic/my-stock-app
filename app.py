import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# === 1. 網頁基本設定 ===
st.set_page_config(page_title="AI 股市戰情室 (完整訊號版)", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# === 2. 巨量中文名稱資料庫 ===
STOCK_NAME_MAP = {
    # --- 晶圓代工 ---
    "2330.TW": "台積電", "2303.TW": "聯電", "5347.TWO": "世界先進", "6770.TW": "力積電", "3711.TW": "日月光投控",
    # --- 系統組裝 (AI/PC) ---
    "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "6669.TW": "緯穎", "2356.TW": "英業達", 
    "2376.TW": "技嘉", "2357.TW": "華碩", "2324.TW": "仁寶", "4938.TW": "和碩", "2301.TW": "光寶科", 
    "2353.TW": "宏碁", "2377.TW": "微星",
    # --- IC 設計 (高價/中低價) ---
    "2454.TW": "聯發科", "3034.TW": "聯詠", "2379.TW": "瑞昱", "3035.TW": "智原", "3443.TW": "創意", 
    "3661.TW": "世芯-KY", "3529.TW": "力旺", "6531.TW": "愛普", "4961.TW": "天鈺", "8016.TW": "矽創", 
    "6415.TW": "矽力-KY", "6756.TW": "威鋒電子", "2458.TW": "義隆", "6202.TW": "盛群",
    # --- 記憶體 ---
    "2408.TW": "南亞科", "2344.TW": "華邦電", "2337.TW": "旺宏", "3260.TWO": "威剛", "8299.TWO": "群聯", 
    "2451.TW": "創見", "8271.TWO": "宇瞻", "4967.TW": "十銓",
    # --- PCB / CCL / 被動元件 ---
    "3037.TW": "欣興", "8046.TW": "南電", "3189.TW": "景碩", "2368.TW": "金像電", "2313.TW": "華通", 
    "6269.TW": "台郡", "4958.TW": "臻鼎-KY", "2383.TW": "台光電", "6213.TW": "聯茂", "6274.TW": "台燿",
    "2327.TW": "國巨", "2492.TW": "華新科", "3026.TW": "禾伸堂", "2456.TW": "奇力新",
    # --- 散熱 ---
    "3017.TW": "奇鋐", "3324.TWO": "雙鴻", "3653.TW": "健策", "2421.TW": "建準", "6230.TW": "超眾",
    # --- 重電 / 綠能 / 電纜 ---
    "1513.TW": "中興電", "1519.TW": "華城", "1503.TW": "士電", "1504.TW": "東元", "1605.TW": "華新", 
    "6806.TW": "森崴能源", "9958.TW": "世紀鋼", "3708.TW": "上緯投控", "6443.TW": "元晶", "6477.TW": "安集",
    # --- 航運 (貨櫃/散裝/航空) ---
    "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", 
    "2606.TW": "裕民", "2605.TW": "華新", "2637.TW": "慧洋-KY", "5608.TW": "四維航", "2612.TW": "中航",
    "2618.TW": "長榮航", "2610.TW": "華航", "2634.TW": "漢翔", "2645.TW": "長榮航太",
    # --- 傳產龍頭 (塑膠/水泥/鋼鐵/紡織) ---
    "1301.TW": "台塑", "1303.TW": "南亞", "1326.TW": "台化", "6505.TW": "台塑化", 
    "1101.TW": "台泥", "1102.TW": "亞泥", "2002.TW": "中鋼", "2014.TW": "中鴻", "2027.TW": "大成鋼",
    "1402.TW": "遠東新", "1476.TW": "儒鴻", "1477.TW": "聚陽", "9910.TW": "豐泰", "9904.TW": "寶成",
    # --- 金融 (金控) ---
    "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金", "2884.TW": "玉山金", 
    "2892.TW": "第一金", "5880.TW": "合庫金", "2885.TW": "元大金", "2880.TW": "華南金", "2883.TW": "開發金", 
    "2887.TW": "台新金", "2890.TW": "永豐金", "2888.TW": "新光金", "2889.TW": "國票金",
    # --- 生技 ---
    "1795.TW": "美時", "6446.TW": "藥華藥", "4743.TWO": "合一", "1760.TW": "寶齡富錦", "4147.TW": "中裕",
    # --- 美股 ---
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOG": "Google", "AMZN": "Amazon", "NVDA": "NVIDIA", "AMD": "AMD", 
    "INTC": "Intel", "TSLA": "Tesla", "META": "Meta", "SMCI": "Supermicro", "PLTR": "Palantir", "AVGO": "Broadcom", 
    "MU": "Micron", "QCOM": "Qualcomm", "TXN": "Texas Instruments", "ASML": "ASML", "NFLX": "Netflix"
}

def get_stock_name(ticker):
    base_name = STOCK_NAME_MAP.get(ticker.upper())
    if base_name: return base_name
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
    
    # 1. 估值與基本面
    if eps is not None:
        if eps < 0: score -= 3 
        else:
            fair_value = eps * target_pe
            upside = (fair_value - price) / price
            if upside > 0.2: reasons.append("股價低估"); score += 2
            elif upside < -0.2: score -= 1.5

    if pe and 0 < pe < 20: reasons.append("PE便宜"); score += 1
    if pb and pb < 1: reasons.append("PB超值"); score += 2
    elif pb and pb < 1.5: score += 1
    
    if rev_growth > 0.2: reasons.append("營收飆"); score += 1
    elif rev_growth < -0.1: score -= 1

    # 2. 趨勢 (Trend)
    if price > row['SMA_240']:
        if prev_row['Close'] < prev_row['SMA_240']: reasons.append("🚀突破年線"); score += 2.5
        else: score += 1
    else:
        if prev_row['Close'] > prev_row['SMA_240']: reasons.append("跌破年線"); score -= 2

    # 3. 型態與量能
    if (price > row['Open']) and (prev_row['Close'] > prev_row['Open']) and (prev2_row['Close'] > prev2_row['Open']) and (price > prev_row['Close']):
        reasons.append("🔥連三紅"); score += 2
    
    if row['Volume'] > row['Vol_SMA5'] * 1.8 and price > row['Open']:
        reasons.append("💰爆量"); score += 1.5

    # 4. 指標
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
    
    with st.spinner(f'AI 正在執行深度運算 (含 T-1/T-2 訊號)...'):
        for ticker in ticker_list:
            ticker = ticker.strip()
            if not ticker: continue
            
            try:
                stock = yf.Ticker(ticker)
                
                try:
                    info = stock.info
                    fundamentals = {
                        'eps': info.get('trailingEps', None),
                        'pe': info.get('trailingPE', None),
                        'pb': info.get('priceToBook', None),
                        'rev_growth': info.get('revenueGrowth', 0)
                    }
                except: fundamentals = {'eps': None, 'pe': None, 'pb': None, 'rev_growth': 0}

                # 抓取 MAX 資料以計算 20年線
                df = stock.history(period="max")
                if len(df) < 250: continue
                
                df['SMA_20'] = df['Close'].rolling(window=20).mean()
                df['SMA_60'] = df['Close'].rolling(window=60).mean()
                df['SMA_240'] = df['Close'].rolling(window=240).mean()
                df['SMA_1200'] = df['Close'].rolling(window=1200).mean()
                df['SMA_4800'] = df['Close'].rolling(window=4800).mean()
                
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

                score_0, sig_0, reason_0 = calculate_score_for_row(row_0, row_1, row_2, row_3, fundamentals, target_pe)
                score_1, sig_1, _ = calculate_score_for_row(row_1, row_2, row_3, row_4, fundamentals, target_pe)
                score_2, sig_2, _ = calculate_score_for_row(row_2, row_3, row_4, df.iloc[-6], fundamentals, target_pe)

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

                is_undervalued_gem = False
                gem_reason = ""
                if fundamentals['eps'] and fundamentals['eps'] > 0:
                    current_price = row_0['Close']
                    if not pd.isna(row_0['SMA_4800']) and current_price < row_0['SMA_4800']:
                        is_undervalued_gem = True
                        gem_reason = "🔥跌破20年線(歷史底)"
                    elif not pd.isna(row_0['SMA_1200']) and current_price < row_0['SMA_1200']:
                        is_undervalued_gem = True
                        gem_reason = "跌破5年線(長線低)"
                    elif not pd.isna(row_0['SMA_240']) and current_price < row_0['SMA_240'] and fundamentals['rev_growth'] > -0.05:
                        is_undervalued_gem = True
                        gem_reason = "跌破年線(回檔)"

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
    st.header("🗂️ 產業與自選設定")
    PRESET_DICT = {
        "📝 我的自選觀察清單 (Custom)": {"codes": "2330.TW, 2317.TW, 2603.TW, 0050.TW", "pe": 20},
        
        # --- 電子大族群 ---
        "🤖 AI 伺服器/組裝": {"codes": "2330.TW, 2317.TW, 2382.TW, 3231.TW, 6669.TW, 2356.TW, 2376.TW, 2357.TW, 2324.TW, 4938.TW, 2301.TW, NVDA, AMD", "pe": 25},
        "💡 IC 設計 (高價/IP)": {"codes": "2454.TW, 3034.TW, 2379.TW, 3035.TW, 3661.TW, 3443.TW, 3529.TW, 6531.TW, 4961.TW, 6415.TW, 6756.TW", "pe": 35},
        "❄️ 散熱模組 (AI關鍵)": {"codes": "3017.TW, 3324.TWO, 3653.TW, 2421.TW, 6230.TW", "pe": 25},
        "🏗️ CoWoS 設備/檢測": {"codes": "3131.TW, 3583.TW, 6196.TW, 6187.TWO, 5443.TWO", "pe": 28},
        "⚡ PCB / 被動元件": {"codes": "3037.TW, 8046.TW, 3189.TW, 2368.TW, 2313.TW, 6269.TW, 2383.TW, 2327.TW, 2492.TW, 3026.TW", "pe": 18},
        "💾 記憶體/封測": {"codes": "2408.TW, 2344.TW, 2337.TW, 3260.TWO, 8299.TWO, 2451.TW, 3711.TW, 2303.TW, 6770.TW, MU", "pe": 15},
        
        # --- 傳產與金融 ---
        "🔌 重電/綠能/電纜": {"codes": "1513.TW, 1519.TW, 1503.TW, 1504.TW, 1605.TW, 6806.TW, 9958.TW, 3708.TW, 6443.TW", "pe": 25},
        "🚢 航運/航空/軍工": {"codes": "2603.TW, 2609.TW, 2615.TW, 2606.TW, 2637.TW, 2618.TW, 2610.TW, 2634.TW, 2645.TW", "pe": 10},
        "🛢️ 塑化/鋼鐵/紡織": {"codes": "1301.TW, 1303.TW, 1326.TW, 6505.TW, 1101.TW, 2002.TW, 2014.TW, 1402.TW, 1476.TW, 9910.TW", "pe": 12},
        "💰 金融金控 (完整版)": {"codes": "2881.TW, 2882.TW, 2891.TW, 2886.TW, 2884.TW, 2892.TW, 5880.TW, 2885.TW, 2880.TW, 2883.TW, 2887.TW, 2890.TW, 2888.TW", "pe": 15},
        
        # --- 其他 ---
        "🇺🇸 美股科技巨頭": {"codes": "AAPL, MSFT, GOOG, AMZN, NVDA, TSLA, META, SMCI, AVGO, QCOM, INTC, AMD, MU", "pe": 30},
    }
    
    selected_group = st.selectbox("選擇族群", list(PRESET_DICT.keys()))
    group_data = PRESET_DICT[selected_group]
    st.divider()
    target_pe = st.slider(f"合理本益比基準", 5, 60, group_data["pe"])
    user_tickers = st.text_area("觀察清單", value=group_data["codes"], height=100)
    
    st.info("💎 **新增功能**：資料庫已擴充至 150+ 檔個股，涵蓋 IC設計、散熱、被動元件、航運、全金控。")

st.title("🏛️ AI 股市戰情室 (完整訊號版)")
st.caption(f"六大面向 + **T-2時光機** + **20年線價值挖掘** | 基準本益比: **{target_pe}倍**")

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

    # 定義通用欄位設定
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
            # 這裡確保顯示 T-1, T-2 訊號
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