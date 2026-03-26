# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from datetime import datetime

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

def get_us_market_analysis(markets, news):
    prompt = f"""请作为资深美股分析师，为我分析当前美股市场：

【美股三大指数】
{markets}

【最新美股新闻】
{news}

请生成简短分析：
1. 三大指数走势分析
2. 科技股表现（苹果、微软、英伟达、特斯拉等）
3. 美联储政策影响
4. 短期走势预判
5. 投资建议

请用简洁中文，每部分不超过2句话。"""

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        print("正在调用DeepSeek AI分析...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"AI分析生成失败: {result}"
    except Exception as e:
        return f"AI分析调用失败: {str(e)}"

def fetch_sp500_from_stooq():
    try:
        r = requests.get("https://stooq.com/q/d/l/?s=spx.us&i=d", timeout=15)
        lines = r.text.strip().split("\n")
        if len(lines) >= 2:
            header = lines[0].split(",")
            prev_close = None
            current = None
            
            for i in range(len(lines)-1, 0, -1):
                parts = lines[i].split(",")
                if len(parts) >= 5:
                    try:
                        close_price = float(parts[4])
                        if current is None:
                            current = close_price
                            if i > 1:
                                prev_parts = lines[i-1].split(",")
                                if len(prev_parts) >= 5:
                                    prev_close = float(prev_parts[4])
                        elif prev_close is None:
                            prev_close = close_price
                            break
                    except:
                        continue
            
            if current and prev_close:
                pct = (current - prev_close) / prev_close * 100
                return f"{current:.2f}", f"{pct:.2f}"
    except Exception as e:
        print(f"Stooq S&P500 failed: {e}")
    return None, None

def fetch_us_market():
    markets = {}
    
    time.sleep(1)
    
    for code, name in [("usDJI", "道琼斯"), ("usIXIC", "纳斯达克")]:
        try:
            url = f"https://qt.gtimg.cn/q={code}"
            response = requests.get(url, headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=10)
            response.encoding = "gbk"
            data = response.text.strip()
            
            if "none_match" not in data and "~" in data:
                parts = data.split("~")
                if len(parts) > 32:
                    price = parts[3].strip()
                    change_pct = parts[32].strip()
                    if not change_pct or change_pct == "0":
                        prev_close = parts[4].strip()
                        if price and prev_close:
                            try:
                                pct = (float(price) - float(prev_close)) / float(prev_close) * 100
                                change_pct = f"{pct:.2f}"
                            except:
                                change_pct = "0"
                    if price and price not in ["0", ""]:
                        markets[name] = f"{price} ({change_pct}%)"
        except Exception as e:
            print(f"获取{name}失败: {e}")
        
        time.sleep(0.5)
    
    sp_price, sp_pct = fetch_sp500_from_stooq()
    if sp_price:
        markets["标普500"] = f"{sp_price} ({sp_pct}%)"
    else:
        for code in ["usSPX", "USINX", "us.INX"]:
            try:
                url = f"https://qt.gtimg.cn/q={code}"
                response = requests.get(url, headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=10)
                response.encoding = "gbk"
                data = response.text.strip()
                if "none_match" not in data and "~" in data:
                    parts = data.split("~")
                    if len(parts) > 3 and parts[3].strip() not in ["0", ""]:
                        price = parts[3].strip()
                        change_pct = parts[32].strip() if len(parts) > 32 else "0"
                        markets["标普500"] = f"{price} ({change_pct}%)"
                        break
            except:
                pass
            time.sleep(0.3)
    
    return markets

def fetch_stocks_data():
    stocks = {}
    
    all_stocks = ["usAAPL", "usMSFT", "usNVDA", "usTSLA", "usGOOGL", "usAMZN", "usMETA", "usAVGO", "usNFLX", "usAMD", "usBABA", "usJD", "usPDD", "usBIDU", "usNIO", "usXPEV"]
    
    for stock_code in all_stocks:
        try:
            url = f"https://qt.gtimg.cn/q={stock_code}"
            response = requests.get(url, headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=10)
            response.encoding = "gbk"
            data = response.text.strip()
            
            if "~" in data:
                parts = data.split("~")
                if len(parts) > 31:
                    price = parts[3].strip()
                    prev_close = parts[4].strip()
                    change_pct = parts[31].strip()
                    
                    if not change_pct or change_pct == "0":
                        if price and prev_close:
                            try:
                                pct = (float(price) - float(prev_close)) / float(prev_close) * 100
                                change_pct = f"{pct:.2f}"
                            except:
                                change_pct = "0"
                    
                    if price and price not in ["0", ""]:
                        stocks[stock_code] = f"${price} ({change_pct}%)"
        except:
            pass
    
    return stocks

def fetch_us_stock_news():
    news_items = []
    
    sources = [
        ("https://finance.sina.com.cn/stock/", ["美股", "纳斯达克", "道琼斯", "美联储", "苹果", "微软", "英伟达", "特斯拉", "AI", "关税", "特朗普"]),
        ("https://finance.sina.com.cn/tech/", ["美股", "AI", "苹果", "微软", "英伟达"]),
    ]
    
    for url, keywords in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://finance.sina.com.cn"}
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            for item in soup.select("h2 a, .news-item a, h3 a, p a")[:40]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 8 and href and "http" in href:
                    for kw in keywords:
                        if kw in title:
                            if title not in str(news_items):
                                news_items.append(f"• {title}\n  {href}")
                            break
        except Exception as e:
            print(f"获取新闻失败: {e}")
    
    if not news_items:
        return "暂无相关新闻\n  https://finance.sina.com.cn/stock/"
    
    return "\n\n".join(news_items[:15])

def send_us_report():
    print("获取美股数据...")
    markets = fetch_us_market()
    stocks = fetch_stocks_data()
    news = fetch_us_stock_news()
    
    market_text = "\n".join([f"{k}: {v}" for k, v in markets.items()])
    
    tech_stocks = f"""苹果 Apple (AAPL): {stocks.get('usAAPL', '数据获取中')} | https://finance.sina.com.cn/stock/quote/AAPL.html
微软 Microsoft (MSFT): {stocks.get('usMSFT', '数据获取中')} | https://finance.sina.com.cn/stock/quote/MSFT.html
英伟达 Nvidia (NVDA): {stocks.get('usNVDA', '数据获取中')} | https://finance.sina.com.cn/stock/quote/NVDA.html
特斯拉 Tesla (TSLA): {stocks.get('usTSLA', '数据获取中')} | https://finance.sina.com.cn/stock/quote/TSLA.html
谷歌 Alphabet (GOOGL): {stocks.get('usGOOGL', '数据获取中')} | https://finance.sina.com.cn/stock/quote/GOOGL.html
亚马逊 Amazon (AMZN): {stocks.get('usAMZN', '数据获取中')} | https://finance.sina.com.cn/stock/quote/AMZN.html
Meta (META): {stocks.get('usMETA', '数据获取中')} | https://finance.sina.com.cn/stock/quote/META.html
博通 Broadcom (AVGO): {stocks.get('usAVGO', '数据获取中')} | https://finance.sina.com.cn/stock/quote/AVGO.html
Netflix (NFLX): {stocks.get('usNFLX', '数据获取中')} | https://finance.sina.com.cn/stock/quote/NFLX.html
AMD (AMD): {stocks.get('usAMD', '数据获取中')} | https://finance.sina.com.cn/stock/quote/AMD.html"""

    china_stocks = f"""阿里巴巴 (BABA): {stocks.get('usBABA', '数据获取中')} | https://finance.sina.com.cn/stock/quote/BABA.html
京东 (JD): {stocks.get('usJD', '数据获取中')} | https://finance.sina.com.cn/stock/quote/JD.html
拼多多 (PDD): {stocks.get('usPDD', '数据获取中')} | https://finance.sina.com.cn/stock/quote/PDD.html
百度 (BIDU): {stocks.get('usBIDU', '数据获取中')} | https://finance.sina.com.cn/stock/quote/BIDU.html
蔚来 (NIO): {stocks.get('usNIO', '数据获取中')} | https://finance.sina.com.cn/stock/quote/NIO.html
小鹏汽车 (XPEV): {stocks.get('usXPEV', '数据获取中')} | https://finance.sina.com.cn/stock/quote/XPEV.html"""
    
    print("正在生成AI分析...")
    ai_analysis = get_us_market_analysis(market_text, news)
    
    subject = f"美股市场简报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    body = f"""美股市场全面简报
{'='*60}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【美股三大指数实时行情】
{market_text}

【AI深度分析】
{ai_analysis}

{'='*60}

【科技巨头实时行情】
{tech_stocks}

【热门中概股】
{china_stocks}

{'='*60}

【指数实时行情链接】
道琼斯工业: https://finance.sina.com.cn/stock/quote/DJIA.html
纳斯达克综合: https://finance.sina.com.cn/stock/quote/IXIC.html
标普500指数: https://finance.sina.com.cn/stock/quote/SPX.html

【美股收盘时间】
- 纽约时间16:00收盘（北京时间次日05:00）
- 盘前交易: 04:00-09:30
- 盘后交易: 16:00-20:00

【综合金融数据平台】
- 新浪财经美股: https://finance.sina.com.cn/stock/
- 腾讯财经美股: https://stockapp.finance.qq.com/mstats/search?type=USAll
- 东方财富美股: https://data.eastmoney.com/ggqy/mggs.html
- 富途牛牛: https://www.futunn.com/
- 华尔街见闻: https://wallstreetcn.com/

【美股相关新闻】
{news}

{'='*60}
"""
    
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    print("发送邮件...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL_2, msg.as_string())
    server.quit()
    print("发送成功!")

if __name__ == "__main__":
    send_us_report()
