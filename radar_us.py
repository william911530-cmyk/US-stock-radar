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

print("🔥 QUANTUM CORE v4.0 // 華爾街終極裝甲版 (保證不漏大股與ETF) 🔥")

# ==========================================
# 🚀 階段一：無敵解析與菁英護城河
# ==========================================
print("📋 [1/4] 正在同步全市場清單...")
all_stocks_dict = {}

# 🌟 絕對護城河：強制寫入主流巨頭與熱門 ETF，就算美國官方伺服器當機也絕不漏掉！
elite_vanguard = {
    "NVDA": "NVIDIA Corp", "AAPL": "Apple Inc.", "MSFT": "Microsoft", 
    "TSLA": "Tesla Inc", "PLTR": "Palantir Tech", "AMZN": "Amazon", 
    "GOOGL": "Alphabet Inc", "META": "Meta Platforms", "AMD": "Advanced Micro Devices",
    "TSM": "Taiwan Semiconductor", "AVGO": "Broadcom", "SMCI": "Super Micro Computer",
    "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ Trust", "VOO": "Vanguard S&P 500 ETF",
    "SMH": "VanEck Semiconductor ETF", "SOXX": "iShares Semiconductor ETF",
    "TQQQ": "ProShares UltraPro QQQ", "UPRO": "ProShares UltraPro S&P500"
}
for k, v in elite_vanguard.items():
    all_stocks_dict[k] = v

try:
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    res_nasdaq = requests.get(nasdaq_url, headers=headers, timeout=20)
    res_other = requests.get(other_url, headers=headers, timeout=20)
    
    # 🌟 關鍵修復：不再依賴欄位名稱 (防 BOM 亂碼)，直接用 iloc 鎖定絕對位置
    if res_nasdaq.status_code == 200:
        df_nasdaq = pd.read_csv(io.StringIO(res_nasdaq.text), sep="|")
        for i in range(len(df_nasdaq)):
            sym = str(df_nasdaq.iloc[i, 0]).strip()
            name = str(df_nasdaq.iloc[i, 1]).strip()
            # 長度正常且避開結尾的檔案時間註記
            if 1 <= len(sym) <= 6 and "File Creation" not in sym:
                sym_yf = sym.replace('.', '-')
                all_stocks_dict[sym_yf] = name

    if res_other.status_code == 200:
        df_other = pd.read_csv(io.StringIO(res_other.text), sep="|")
        for i in range(len(df_other)):
            sym = str(df_other.iloc[i, 0]).strip()
            name = str(df_other.iloc[i, 1]).strip()
            if 1 <= len(sym) <= 6 and "File Creation" not in sym:
                sym_yf = sym.replace('.', '-')
                all_stocks_dict[sym_yf] = name

    tickers = sorted(list(all_stocks_dict.keys()))
    all_stocks_json_data = [{"Code": k, "Name": v} for k, v in all_stocks_dict.items()]

    print(f"✅ 成功鎖定 {len(tickers)} 檔全市場大數據庫 (已防護所有主流股與 ETF)！")
    
    with open("all_stocks.json", "w", encoding="utf-8") as f:
        json.dump(all_stocks_json_data, f, ensure_ascii=False)

except Exception as e:
    print(f"⚠️ 官方連線不穩，已啟動菁英護城河模式: {e}")
    tickers = sorted(list(all_stocks_dict.keys()))

# ==========================================
# 🚀 階段二：降載極速批次下載 (免疫錯位與丟包)
# ==========================================
print(f"📦 [2/4] 開始極速分批下載實時行情...")
all_closes = pd.DataFrame()

# 🌟 關鍵修復：將批次縮小到 150，徹底防止 Yahoo URI 過長導致的「整批股票憑空消失」
batch_size = 150
batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在加載第 {idx+1}/{len(batches)} 批次...")
    try:
        df_batch = yf.download(batch, period="15d", progress=False, timeout=20)
        
        if not df_batch.empty and 'Close' in df_batch:
            close_data = df_batch['Close']
            
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
            df_stock = all_closes[ticker].dropna()
            
            if isinstance(df_stock, pd.DataFrame):
                df_stock = df_stock.iloc[:, 0]
            
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
                all_calculated_results.append(stock_entry)
                
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
