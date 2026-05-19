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

print("🔥 QUANTUM CORE v6.0 // 華爾街靜默潛行版 (防禦 Yahoo 封鎖) 🔥")

# ==========================================
# 🚀 階段一：精準名冊解析 (剃除 ETF)
# ==========================================
print("📋 [1/3] 正在同步全美股代號 (剔除 ETF，鎖定純血企業)...")
all_stocks_dict = {}

# 🌟 絕對護城河：這些科技巨頭不管怎樣都必須在名單內！
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
    
    if res_nasdaq.status_code == 200:
        df_nasdaq = pd.read_csv(io.StringIO(res_nasdaq.text), sep="|").fillna('')
        for _, row in df_nasdaq.iterrows():
            sym = str(row.get('Symbol', '')).strip()
            name = str(row.get('Security Name', '')).strip()
            is_etf = str(row.get('ETF', 'N')).strip() == 'Y'
            test_issue = str(row.get('Test Issue', '')).strip()
            if sym and test_issue != 'Y' and not is_etf and 1 <= len(sym) <= 5 and "File Creation" not in sym:
                all_stocks_dict[sym.replace('.', '-')] = name

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
# 🚀 階段二：靜默小批次下載 (徹底迴避 Yahoo 反爬蟲封鎖)
# ==========================================
print(f"📦 [2/3] 啟動靜默小批次下載 (預估耗時 3~5 分鐘，請耐心等待)...")

all_closes = pd.DataFrame()
# 🌟 關鍵修復：每次只拿 80 檔，避免 URL 太長或觸發 DDoS 警報
batch_size = 80 
batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]

for idx, batch in enumerate(batches):
    if idx % 5 == 0:
        print(f"   🔄 正在加載第 {idx+1} 到 {min(idx+5, len(batches))} 批次...")
    
    try:
        df_batch = yf.download(batch, period="15d", progress=False, timeout=15)
        
        if not df_batch.empty:
            # 精準抽取 Close 欄位
            if isinstance(df_batch.columns, pd.MultiIndex):
                if 'Close' in df_batch.columns.levels[0]:
                    close_data = df_batch['Close']
                else:
                    close_data = pd.DataFrame()
            elif 'Close' in df_batch.columns:
                close_data = df_batch[['Close']]
                close_data.columns = [batch[0]] # 單檔股票防錯
            else:
                close_data = pd.DataFrame()

            if not close_data.empty:
                if all_closes.empty:
                    all_closes = close_data
                else:
                    # 合併並去除可能重複的欄位
                    all_closes = pd.concat([all_closes, close_data], axis=1)
                    all_closes = all_closes.loc[:, ~all_closes.columns.duplicated()]
                    
    except Exception as e:
        pass # 安靜跳過單一失敗的批次
        
    # 🌟 核心防禦：每批次強迫休息 1.5 秒，偽裝成人類網速
    time.sleep(1.5)

print(f"✅ 成功從 Yahoo 取回 {len(all_closes.columns)} 檔股票的有效報價！")

# ==========================================
# 🚀 階段三：全量報價庫與動能精煉
# ==========================================
print("📊 [3/3] 正在進行多維度量化特徵運算...")

all_calculated_results = [] 
momentum_candidates = []    

if not all_closes.empty:
    for ticker in all_closes.columns:
        df_stock = all_closes[ticker].dropna()
        
        if len(df_stock) >= 11:
            current_price = float(df_stock.iloc[-1])
            prev10_price = float(df_stock.iloc[-11])
            ma5 = float(df_stock.tail(5).mean())
            
            roc10 = ((current_price - prev10_price) / prev10_price) * 100
            bias = ((current_price - ma5) / ma5) * 100
            score = (roc10 * 1.5) + (bias * 3.5)
            
            stock_entry = {
                "代號": ticker, "名稱": all_stocks_dict.get(ticker, "US Stock"),
                "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
                "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
            }
            # 🌟 無條件加入總報價庫
            all_calculated_results.append(stock_entry)
            
            # 站上5日線才晉級強勢榜
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
    print(f"💾 SUCCESS: 已成功生成 {len(all_calculated_results)} 檔美股的全量即時報價庫！")
else:
    with open("all_calculated_us.json", "w", encoding="utf-8") as f: f.write("[]")

print("="*60)
