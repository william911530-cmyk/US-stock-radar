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
print("="*60)import os
import sys
import pandas as pd
import yfinance as yf
import json
import time
import warnings

warnings.filterwarnings('ignore')

print("🔥 QUANTUM CORE v2.0 // 華爾街全市場無死角動能雷達啟動 🔥")

# ==========================================
# 🚀 階段一：直連 NASDAQ Trader 撈取全美股名冊
# ==========================================
print("📋 [1/4] 正在對接美國官方金融數據中心，同步全美股代號...")
tickers = []
all_stocks_json_data = []

try:
    # 🌟 業界標準：直接讀取 NASDAQ 官方每日更新的全美股股票清單
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    
    df_nasdaq = pd.read_csv(nasdaq_url, sep="|")
    df_other = pd.read_csv(other_url, sep="|")
    
    # 提取代號與名稱
    for _, row in df_nasdaq.iterrows():
        symbol = str(row['Symbol']).strip()
        name = str(row['Security Name']).strip()
        # 過濾測試股、特別股與異常代號
        if row['Test Issue'] == 'N' and len(symbol) <= 4 and symbol.isalpha():
            tickers.append(symbol)
            all_stocks_json_data.append({"Code": symbol, "Name": name})
            
    for _, row in df_other.iterrows():
        symbol = str(row['ACT Symbol']).strip()
        name = str(row['Security Name']).strip()
        if row['Test Issue'] == 'N' and len(symbol) <= 4 and symbol.isalpha():
            tickers.append(symbol)
            all_stocks_json_data.append({"Code": symbol, "Name": name})

    # 去重
    tickers = sorted(list(set(tickers)))
    print(f"✅ 成功攔截全美股合計 {len(tickers)} 檔上市企業名冊！零死角鎖定！")
    
    # 存檔供前端選單與檢索使用
    with open("all_stocks.json", "w", encoding="utf-8") as f:
        json.dump(all_stocks_json_data, f, ensure_ascii=False)

except Exception as e:
    print(f"❌ 官方金融數據中心連線中斷: {e}")
    sys.exit(1)

# ==========================================
# 🚀 階段二：高頻分批批次下載 (Bulk Download)
# ==========================================
print(f"📦 [2/4] 開始分批押送全美股行情...")
results = []
full_data = pd.DataFrame()

# 將幾千檔美股切成每 400 檔一小批，在美國雲端機房用大水管高頻下載
batch_size = 400
batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在強行加載第 {idx+1}/{len(batches)} 批次美股即時數據...")
    try:
        # 在 GitHub Actions 的美國環境跑，直接批量下載，速度極快
        batch_data = yf.download(batch, period="1mo", group_by='ticker', progress=False, timeout=30)
        if not batch_data.empty:
            if full_data.empty:
                full_data = batch_data
            else:
                full_data = pd.concat([full_data, batch_data], axis=1)
        time.sleep(1) # 溫柔小停頓
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
    
    # 取全美股最強前 20 名
    top20_us = final_df.head(20)
    print("🏆 全美股大盤篩選完畢！最強前 20 檔極限動能榜單 🏆")
    print(top20_us.to_string())
    
    # 丟回大廳
    top20_us.to_json("top20_us.json", orient="records", force_ascii=False)
    
    # 順手把全市場算出來的結果存一份，這就是你下拉選單「即時觀測」的黃金水源！
    final_df.to_json("all_calculated_us.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 全球最強量化數據已成功押送回大廳！")
else:
    print("📉 當前美股進入全面恐慌或維護，無符合條件標的。")
    with open("top20_us.json", "w", encoding="utf-8") as f: f.write("[]")
    with open("all_calculated_us.json", "w", encoding="utf-8") as f: f.write("[]")
print("="*60)
