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

print("🔥 QUANTUM CORE v2.1 // 華爾街全市場動能雷達（無敵面具版）啟動 🔥")

# ==========================================
# 🚀 階段一：戴上面具直連 NASDAQ Trader 撈取全美股名冊
# ==========================================
print("📋 [1/4] 正在偽裝安全身份，對接美國官方金融數據中心...")
tickers = []
all_stocks_json_data = []

try:
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    
    # 🌟 核心修復：加上頂級真人瀏覽器 Header，徹底瓦解 NASDAQ 官方 403 阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("   📥 正在安全押送 NASDAQ 上市列表...")
    res_nasdaq = requests.get(nasdaq_url, headers=headers, timeout=20)
    
    print("   📥 正在安全押送 Other Market 上市列表...")
    res_other = requests.get(other_url, headers=headers, timeout=20)
    
    # 利用 io.StringIO 將文字串流無痛轉換為 Pandas Dataframe
    df_nasdaq = pd.read_csv(io.StringIO(res_nasdaq.text), sep="|")
    df_other = pd.read_csv(io.StringIO(res_other.text), sep="|")
    
    # 數據清洗與過濾
    for _, row in df_nasdaq.iterrows():
        if 'Symbol' in row and 'Test Issue' in row:
            symbol = str(row['Symbol']).strip()
            name = str(row['Security Name']).strip()
            if row['Test Issue'] == 'N' and len(symbol) <= 4 and symbol.isalpha():
                tickers.append(symbol)
                all_stocks_json_data.append({"Code": symbol, "Name": name})
            
    for _, row in df_other.iterrows():
        if 'ACT Symbol' in row and 'Test Issue' in row:
            symbol = str(row['ACT Symbol']).strip()
            name = str(row['Security Name']).strip()
            if row['Test Issue'] == 'N' and len(symbol) <= 4 and symbol.isalpha():
                tickers.append(symbol)
                all_stocks_json_data.append({"Code": symbol, "Name": name})

    # 去除重複項
    tickers = sorted(list(set(tickers)))
    print(f"✅ 完美突破防線！成功鎖定全美股合計 {len(tickers)} 檔上市企業大數據庫！")
    
    # 寫入歷史名冊，供前端下拉選單即時檢索
    with open("all_stocks.json", "w", encoding="utf-8") as f:
        json.dump(all_stocks_json_data, f, ensure_ascii=False)

except Exception as e:
    print(f"❌ 嚴重錯誤：安全身份遭識破或網路中斷: {e}")
    sys.exit(1)

# ==========================================
# 🚀 階段二：全美股高頻分批批次下載 (Bulk Download)
# ==========================================
print(f"📦 [2/4] 開始分批押送全美股實時行情...")
results = []
full_data = pd.DataFrame()

# 將幾千檔美股切成每 400 檔一小批，在美國雲端機房用大水管高速下載
batch_size = 400
batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在強行加載第 {idx+1}/{len(batches)} 批次美股即時數據...")
    try:
        batch_data = yf.download(batch, period="1mo", group_by='ticker', progress=False, timeout=30)
        if not batch_data.empty:
            if full_data.empty:
                full_data = batch_data
            else:
                full_data = pd.concat([full_data, batch_data], axis=1)
        time.sleep(1) 
    except Exception as e:
        print(f"   ⚠️ 第 {idx+1} 批次遭遇亂流: {e}")

# ==========================================
# 🚀 階段三：全市場多維度量化動能特徵計算
# ==========================================
print("📊 [3/4] 正在對幾千檔美股進行強勢動能篩選與大數據精煉...")

ticker_to_name = {s['Code']: s['Name'] for s in all_stocks_json_data}

if not full_data.empty:
    is_multi = isinstance(full_data.columns, pd.MultiIndex)
    
    for ticker in tickers:
        name = ticker_to_name.get(ticker, "US Listed Stock")
        
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
                
                # 鐵血策略：未站上 5 日線直接無情淘汰
                if current_price < ma5:
                    continue
                
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
# 🚀 階段四：黃金 JSON 實體交割
# ==========================================
print("\n" + "="*60)
if results:
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    
    top20_us = final_df.head(20)
    print("🏆 全美股大盤篩選完畢！最強前 20 檔極限動能榜單 🏆")
    print(top20_us.to_string())
    
    top20_us.to_json("top20_us.json", orient="records", force_ascii=False)
    final_df.to_json("all_calculated_us.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 全球最強量化數據已成功押送回大廳！")
else:
    print("📉 當前美股進入全面盤整，無符合條件標的。")
    with open("top20_us.json", "w", encoding="utf-8") as f: f.write("[]")
    with open("all_calculated_us.json", "w", encoding="utf-8") as f: f.write("[]")
print("="*60)
