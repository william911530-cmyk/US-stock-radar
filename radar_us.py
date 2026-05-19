import sys
import os
import io
import requests
import pandas as pd
import yfinance as yf
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

print("🔥 QUANTUM CORE v5.0 // 華爾街純血企業・獨立狙擊版 🔥")

# ==========================================
# 🚀 階段一：精準名冊解析 (剃除 ETF)
# ==========================================
print("📋 [1/3] 正在同步全美股代號 (剔除 ETF，鎖定純血企業)...")
all_stocks_dict = {}

# 🌟 絕對護城河：不管納斯達克名單怎麼變，這幾尊大佛絕對不允許被漏掉
elite_vanguard = {
    "NVDA": "NVIDIA Corp", "AAPL": "Apple Inc.", "MSFT": "Microsoft", 
    "TSLA": "Tesla Inc", "PLTR": "Palantir Tech", "AMZN": "Amazon", 
    "GOOGL": "Alphabet Inc", "META": "Meta Platforms", "AMD": "Advanced Micro Devices",
    "TSM": "Taiwan Semiconductor", "AVGO": "Broadcom", "SMCI": "Super Micro Computer"
}
for k, v in elite_vanguard.items():
    all_stocks_dict[k] = v

try:
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    res_nasdaq = requests.get(nasdaq_url, headers=headers, timeout=20)
    res_other = requests.get(other_url, headers=headers, timeout=20)
    
    # 抓取 NASDAQ (剔除 ETF)
    if res_nasdaq.status_code == 200:
        df_nasdaq = pd.read_csv(io.StringIO(res_nasdaq.text), sep="|").fillna('')
        for _, row in df_nasdaq.iterrows():
            sym = str(row.get('Symbol', '')).strip()
            name = str(row.get('Security Name', '')).strip()
            is_etf = str(row.get('ETF', 'N')).strip() == 'Y'
            test_issue = str(row.get('Test Issue', '')).strip()
            
            if sym and test_issue != 'Y' and not is_etf and 1 <= len(sym) <= 5 and "File Creation" not in sym:
                all_stocks_dict[sym.replace('.', '-')] = name

    # 抓取 Other Market (剔除 ETF)
    if res_other.status_code == 200:
        df_other = pd.read_csv(io.StringIO(res_other.text), sep="|").fillna('')
        for _, row in df_other.iterrows():
            sym = str(row.get('ACT Symbol', '')).strip()
            name = str(row.get('Security Name', '')).strip()
            is_etf = str(row.get('ETF', 'N')).strip() == 'Y'
            test_issue = str(row.get('Test Issue', '')).strip()
            
            if sym and test_issue != 'Y' and not is_etf and 1 <= len(sym) <= 5 and "File Creation" not in sym:
                all_stocks_dict[sym.replace('.', '-')] = name

    tickers = sorted(list(all_stocks_dict.keys()))
    all_stocks_json_data = [{"Code": k, "Name": v} for k, v in all_stocks_dict.items()]

    print(f"✅ 成功鎖定 {len(tickers)} 檔純血美股上市企業。")
    with open("all_stocks.json", "w", encoding="utf-8") as f:
        json.dump(all_stocks_json_data, f, ensure_ascii=False)

except Exception as e:
    print(f"⚠️ 官方連線不穩，已啟動菁英名單: {e}")
    tickers = sorted(list(all_stocks_dict.keys()))

# ==========================================
# 🚀 階段二與三：20 倍速獨立狙擊運算 (絕對免疫錯位 Bug)
# ==========================================
print(f"📦 [2/3] 啟動多執行緒獨立報價抓取 (預估耗時 2~3 分鐘)...")

all_calculated_results = [] 
momentum_candidates = []    

# 定義單兵作戰任務：只管好自己這檔股票的死活
def process_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="15d")
        
        if df.empty or len(df) < 11:
            return None
            
        close_prices = df['Close']
        current_price = float(close_prices.iloc[-1])
        prev10_price = float(close_prices.iloc[-11])
        ma5 = float(close_prices.tail(5).mean())
        
        roc10 = ((current_price - prev10_price) / prev10_price) * 100
        bias = ((current_price - ma5) / ma5) * 100
        score = (roc10 * 1.5) + (bias * 3.5)
        
        result_data = {
            "代號": ticker, "名稱": all_stocks_dict.get(ticker, ""),
            "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
            "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
        }
        
        return result_data, current_price >= ma5
    except Exception:
        return None

# 放出 20 個機器人同時去抓，完全避免資料表合併錯誤！
completed_count = 0
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(process_stock, ticker): ticker for ticker in tickers}
    for future in as_completed(futures):
        completed_count += 1
        if completed_count % 500 == 0:
            print(f"   🔄 進度回報: 已無損掃描 {completed_count} / {len(tickers)} 檔...")
            
        res = future.result()
        if res:
            stock_data, is_strong = res
            all_calculated_results.append(stock_data) # 不管強弱，全部留存報價庫！
            if is_strong:
                momentum_candidates.append(stock_data) # 站上5日線，晉級強勢榜！

# ==========================================
# 🚀 階段四：黃金 JSON 實體輸出
# ==========================================
print("\n" + "="*60)
print(f"📊 結算：成功取得 {len(all_calculated_results)} 檔企業之有效報價。")

if momentum_candidates:
    df_momentum = pd.DataFrame(momentum_candidates)
    df_momentum = df_momentum.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    top20_us = df_momentum.head(20)
    top20_us.to_json("top20_us.json", orient="records", force_ascii=False)
    print("🏆 強勢衝鋒前 20 榜單已生成。")
else:
    with open("top20_us.json", "w", encoding="utf-8") as f: f.write("[]")

if all_calculated_results:
    df_all_calc = pd.DataFrame(all_calculated_results)
    df_all_calc = df_all_calc.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    df_all_calc.to_json("all_calculated_us.json", orient="records", force_ascii=False)
    print("💾 SUCCESS: 全量即時報價庫已就緒！")
else:
    with open("all_calculated_us.json", "w", encoding="utf-8") as f: f.write("[]")

print("="*60)
