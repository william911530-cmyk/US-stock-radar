import sys
import os
import io
import requests
import pandas as pd
import yfinance as yf
import json
import time
import warnings

warnings.filterwarnings('ignore')

print("🔥 QUANTUM CORE v3.1 // 華爾街全市場無限制掃描版 (解鎖 ETF) 🔥")

# ==========================================
# 🚀 階段一：暴力無損解析，對接全美股名冊
# ==========================================
print("📋 [1/4] 正在同步全美股代號 (包含所有 ETF 與龍頭股)...")
all_stocks_dict = {}

try:
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    res_nasdaq = requests.get(nasdaq_url, headers=headers, timeout=20)
    res_other = requests.get(other_url, headers=headers, timeout=20)
    
    # 🌟 關鍵修復：強制將空值補為字串，徹底防止 Pandas 誤殺資料！
    df_nasdaq = pd.read_csv(io.StringIO(res_nasdaq.text), sep="|").fillna('')
    df_other = pd.read_csv(io.StringIO(res_other.text), sep="|").fillna('')
    
    # 擷取 NASDAQ 上市股票與 ETF
    for _, row in df_nasdaq.iterrows():
        symbol = str(row.get('Symbol', '')).strip()
        name = str(row.get('Security Name', '')).strip()
        test_issue = str(row.get('Test Issue', '')).strip()
        
        # 只要不是測試股，且代號長度正常，通通抓進來！
        if symbol and test_issue != 'Y' and len(symbol) <= 6:
            sym_yf = symbol.replace('.', '-') # Yahoo 格式轉換
            all_stocks_dict[sym_yf] = name
            
    # 擷取 NYSE/AMEX 上市股票與 ETF
    for _, row in df_other.iterrows():
        symbol = str(row.get('ACT Symbol', '')).strip()
        name = str(row.get('Security Name', '')).strip()
        test_issue = str(row.get('Test Issue', '')).strip()
        
        if symbol and test_issue != 'Y' and len(symbol) <= 6:
            sym_yf = symbol.replace('.', '-')
            all_stocks_dict[sym_yf] = name

    tickers = sorted(list(all_stocks_dict.keys()))
    all_stocks_json_data = [{"Code": k, "Name": v} for k, v in all_stocks_dict.items()]

    print(f"✅ 成功鎖定 {len(tickers)} 檔全美股大數據庫 (已解鎖 NVDA, AAPL 及所有 ETF)！")
    
    with open("all_stocks.json", "w", encoding="utf-8") as f:
        json.dump(all_stocks_json_data, f, ensure_ascii=False)

except Exception as e:
    print(f"❌ 金融中心連線中斷: {e}")
    sys.exit(1)

# ==========================================
# 🚀 階段二：高頻分批下載 (徹底免疫錯位)
# ==========================================
print(f"📦 [2/4] 開始極速分批下載實時行情...")
all_closes = pd.DataFrame()

# 每次吞 300 檔，加速下載
batch_size = 300
batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在加載第 {idx+1}/{len(batches)} 批次...")
    try:
        # 直接指定抓取 15天 的 Close 收盤價
        df_batch = yf.download(batch, period="15d", progress=False, timeout=20)
        
        if not df_batch.empty and 'Close' in df_batch:
            close_data = df_batch['Close']
            
            # 如果這批剛好只有一檔成功，會回傳 Series，需轉為 DataFrame
            if isinstance(close_data, pd.Series):
                close_data = close_data.to_frame()
                close_data.columns = [batch[0]]
                
            if all_closes.empty:
                all_closes = close_data
            else:
                all_closes = pd.concat([all_closes, close_data], axis=1)
                
    except Exception as e:
        print(f"   ⚠️ 第 {idx+1} 批次下載異常: {e}")
    
    time.sleep(0.5)

# ==========================================
# 🚀 階段三：全量報價庫與動能精煉
# ==========================================
print("📊 [3/4] 正在進行多維度量化特徵運算...")

all_calculated_results = [] 
momentum_candidates = []    

if not all_closes.empty:
    for ticker in tickers:
        if ticker in all_closes.columns:
            # 抽出該檔股票的收盤價歷史
            df_stock = all_closes[ticker].dropna()
            
            # 防止重複代號產生的雙重欄位錯誤
            if isinstance(df_stock, pd.DataFrame):
                df_stock = df_stock.iloc[:, 0]
            
            if len(df_stock) >= 11:
                current_price = float(df_stock.iloc[-1])
                prev10_price = float(df_stock.iloc[-11])
                ma5 = float(df_stock.tail(5).mean())
                
                roc10 = ((current_price - prev10_price) / prev10_price) * 100
                bias = ((current_price - ma5) / ma5) * 100
                score = (roc10 * 1.5) + (bias * 3.5)
                
                # 🌟 不論大盤 ETF 或個股，全部收錄進報價總庫！
                stock_entry = {
                    "代號": ticker, "名稱": all_stocks_dict.get(ticker, ""),
                    "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
                    "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
                }
                all_calculated_results.append(stock_entry)
                
                # 只有站上5日線的股票，才有資格角逐左側的 Top 20 排行榜
                if current_price >= ma5:
                    momentum_candidates.append(stock_entry)

# ==========================================
# 🚀 階段四：黃金 JSON 實體輸出
# ==========================================
print("\n" + "="*60)

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
    print(f"💾 SUCCESS: 已成功為 {len(all_calculated_results)} 檔美股建立了全量即時報價庫！")
else:
    with open("all_calculated_us.json", "w", encoding="utf-8") as f: f.write("[]")

print("="*60)
