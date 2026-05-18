import os
import sys
import pandas as pd
import yfinance as yf
import json
import warnings

warnings.filterwarnings('ignore')

print("🔥 QUANTUM CORE v1.0 // 美股標普500動能雷達啟動 🔥")

# ==========================================
# 🚀 階段一：自動獲取 S&P 500 完整名單
# ==========================================
print("📋 [1/3] 正在向 Wikipedia 同步 S&P 500 最新成分股名單...")
try:
    # 這是業界標準作法：直接讀取維基百科表格，100% 不會被擋
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    payload = pd.read_html(url)
    df_sp500 = payload[0]
    
    # 提取 Ticker (代號) 與 Security (公司名稱)
    # 美股有些代號帶點（如 BRK.B），yfinance 要改成 BRK-B
    tickers = df_sp500['Symbol'].str.replace('.', '-', regex=False).tolist()
    ticker_to_name = dict(zip(tickers, df_sp500['Security']))
    
    print(f"✅ 成功獲取 {len(tickers)} 檔 S&P 500 完整企業名冊！")
except Exception as e:
    print(f"❌ 獲取標普名單失敗: {e}")
    sys.exit(1)

# ==========================================
# 🚀 階段二：美股極速批次下載 (Bulk Download)
# ==========================================
print(f"📦 [2/3] 正在從 Yahoo Finance 批次押送 500 檔美股即時行情...")
results = []
full_data = pd.DataFrame()

try:
    # 🌟 重大優勢：在美國雲端主機抓美股，直接下一把大水管下載，0阻擋、3秒結案！
    full_data = yf.download(tickers, period="1mo", group_by='ticker', progress=False, timeout=30)
    print("✅ 批量行情下載完畢！")
except Exception as e:
    print(f"❌ 批量行情下載崩潰: {e}")
    sys.exit(1)

# ==========================================
# 🚀 階段三：多維度量化特徵運算
# ==========================================
print("📊 [3/3] 正在對 500 檔美股進行強勢動能特徵篩選...")

if not full_data.empty:
    is_multi = isinstance(full_data.columns, pd.MultiIndex)
    
    for ticker in tickers:
        name = ticker_to_name.get(ticker, "US Stock")
        
        try:
            has_data = False
            df_stock = pd.DataFrame()
            
            if is_multi:
                if ticker in full_data.columns.levels[0]:
                    df_stock = full_data[ticker].dropna(subset=['Close'])
                    has_data = True
            else:
                if ticker in full_data.columns:
                    df_stock = full_data[[ticker]].dropna()
                    df_stock.columns = ['Close']
                    has_data = True
            
            if has_data and len(df_stock) >= 15:
                close_prices = df_stock['Close']
                current_price = float(close_prices.iloc[-1])
                prev10_price = float(close_prices.iloc[-11])
                ma5 = float(df_stock['Close'].tail(5).mean())
                
                # 策略門檻：未站上 5 日線直接無情淘汰
                if current_price < ma5:
                    continue
                
                # 計算 10 日動能與 5 日線乖離率
                roc10 = ((current_price - prev10_price) / prev10_price) * 100
                bias = ((current_price - ma5) / ma5) * 100
                score = (roc10 * 1.5) + (bias * 3.5)
                
                results.append({
                    "代號": ticker, "名稱": name,
                    "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
                    "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
                })
        except Exception:
            continue

# ==========================================
# 🚀 階段四：黃金 JSON 實體輸出
# ==========================================
print("\n" + "="*60)
if results:
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    
    # 篩選前 20 名美股妖股
    top20_us = final_df.head(20)
    print("🏆 美股全市場動能最強 20 檔「妖股排行榜」 🏆")
    print(top20_us.to_string())
    
    # 輸出成 top20_us.json
    top20_us.to_json("top20_us.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 資料已成功寫入 top20_us.json！")
else:
    print("📉 當前美股大盤波動極度低迷，無符合條件標的。")
    with open("top20_us.json", "w", encoding="utf-8") as f:
        f.write("[]")
print("="*60)
