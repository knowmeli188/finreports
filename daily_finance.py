# -*- coding: utf-8 -*-
import requests
import subprocess
import json
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

STOCKS = {
    "新时达": "002527",
    "大湖股份": "600257",
    "永鼎股份": "600105",
    "澜起科技": "688008",
    "中际旭创": "300308",
}

def curl_get(url):
    try:
        process = subprocess.Popen(
            ["curl", "-s", "--max-time", "15", "-H", "Referer: https://finance.qq.com", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0 and stdout:
            return stdout
    except:
        pass
    return None

def fetch_global_markets():
    markets = {}
    
    text = curl_get("https://qt.gtimg.cn/q=hf_XAU,hf_XAG,hf_CL,hf_LCO")
    if text:
        for line in text.split("\n"):
            if '="' not in line:
                continue
            parts = line.split('="')[1].rstrip('";\n').split(",")
            if len(parts) >= 2:
                price = parts[0].strip()
                change = parts[1].strip()
                if "hf_XAU" in line and price and price not in ["0", ""]:
                    markets["现货黄金"] = "${}/盎司 ({}%)".format(price, change)
                elif "hf_XAG" in line and price and price not in ["0", ""]:
                    markets["现货白银"] = "${}/盎司 ({}%)".format(price, change)
                elif "hf_CL" in line and price and price not in ["0", ""]:
                    markets["WTI原油"] = "${}/桶 ({}%)".format(price, change)
                elif "hf_LCO" in line and price and price not in ["0", ""]:
                    markets["布伦特原油"] = "${}/桶 ({}%)".format(price, change)
    
    if "布伦特原油" not in markets:
        text = curl_get("https://qt.gtimg.cn/q=hf_OIL")
        if text and '="' in text:
            parts = text.split('="')[1].rstrip('";\n').split(",")
            if len(parts) >= 2:
                price = parts[0].strip()
                change = parts[1].strip()
                if price and price not in ["0", ""]:
                    markets["布伦特原油"] = f"${price}/桶 ({change}%)"
    
    text = curl_get("https://qt.gtimg.cn/q=usDJI,usIXIC")
    if text:
        for line in text.split("\n"):
            if "none_match" in line or "~" not in line:
                continue
            parts = line.split("~")
            if len(parts) > 32:
                code = parts[0]
                price = parts[3].strip()
                change = parts[32].strip() if len(parts) > 32 else "0"
                
                if not change or change == "0":
                    prev_close = parts[4].strip()
                    if price and prev_close:
                        try:
                            pct = (float(price) - float(prev_close)) / float(prev_close) * 100
                            change = f"{pct:.2f}"
                        except:
                            change = "0"
                
                if "DJI" in code and price and price not in ["0", ""]:
                    markets["道琼斯指数"] = f"{price} ({change}%)"
                elif "IXIC" in code and price and price not in ["0", ""]:
                    markets["纳斯达克"] = f"{price} ({change}%)"
    
    text = curl_get("https://qt.gtimg.cn/q=s_usINX")
    if text and "none_match" not in text and "~" in text:
        parts = text.split("~")
        if len(parts) > 5:
            price = parts[3].strip()
            change = parts[5].strip() if len(parts) > 5 else "0"
            if price and price not in ["0", ""]:
                markets["标普500"] = f"{price} ({change}%)"
    
    text = curl_get("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006")
    if text:
        for line in text.split("\n"):
            if "~" not in line:
                continue
            parts = line.split("~")
            if len(parts) > 32:
                code = parts[0]
                price = parts[3].strip()
                change = parts[32].strip() if len(parts) > 32 else "0"
                
                if "000001" in code and price and price not in ["0", ""]:
                    markets["上证指数"] = f"{price} ({change}%)"
                elif "399001" in code and price and price not in ["0", ""]:
                    markets["深证成指"] = f"{price} ({change}%)"
                elif "399006" in code and price and price not in ["0", ""]:
                    markets["创业板指"] = f"{price} ({change}%)"
    
    text = curl_get("https://qt.gtimg.cn/q=sh000016,sz399673,sz399550,hkHSI")
    if text:
        for line in text.split("\n"):
            if "~" not in line:
                continue
            parts = line.split("~")
            if len(parts) > 32:
                code = parts[0]
                price = parts[3].strip()
                change = parts[32].strip() if len(parts) > 32 else "0"
                
                if "000016" in code and price and price not in ["0", ""]:
                    markets["沪深300"] = f"{price} ({change}%)"
                elif "399673" in code and price and price not in ["0", ""]:
                    markets["中证500"] = f"{price} ({change}%)"
                elif "399550" in code and price and price not in ["0", ""]:
                    markets["中证1000"] = f"{price} ({change}%)"
                elif "HSI" in code and price and price not in ["0", ""]:
                    markets["恒生指数"] = f"{price} ({change}%)"
    
    return markets

def fetch_china_stocks():
    stocks_data = []
    
    for name, code in STOCKS.items():
        try:
            if code.startswith("6") or code.startswith("8") or code.startswith("9"):
                market = "sh"
            else:
                market = "sz"
            
            url = f"https://qt.gtimg.cn/q={market}{code}"
            text = curl_get(url)
            
            if text and "~" in text:
                parts = text.split("~")
                if len(parts) > 32:
                    price = parts[3].strip()
                    change_pct = parts[32].strip() if len(parts) > 32 else "0"
                    prev_close = parts[4].strip()
                    
                    if not change_pct or change_pct == "0":
                        if price and prev_close:
                            try:
                                pct = (float(price) - float(prev_close)) / float(prev_close) * 100
                                change_pct = f"{pct:.2f}"
                            except:
                                change_pct = "0"
                    
                    stocks_data.append({
                        "name": name,
                        "code": code,
                        "price": price,
                        "change": change_pct
                    })
                else:
                    stocks_data.append({"name": name, "code": code, "error": "数据格式错误"})
            else:
                stocks_data.append({"name": name, "code": code, "error": "数据获取失败"})
        except Exception as e:
            stocks_data.append({"name": name, "code": code, "error": str(e)})
    
    return stocks_data

def fetch_stock_news():
    news = []
    sources = [
        ("https://finance.sina.com.cn/stock/", ["A股", "大盘", "指数", "市场", "央行", "政策"]),
        ("https://wallstreetcn.com/", ["市场", "股市", "经济", "政策"]),
    ]
    
    for url, keywords in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            for item in soup.select("a[href]")[:30]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if not title or len(title) < 10:
                    continue
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://finance.sina.com.cn" + href
                for kw in keywords:
                    if kw in title and "http" in href:
                        news.append(f"• {title}\n  {href}")
                        break
        except:
            pass
    
    return "\n\n".join(news[:15]) if news else "暂无重大新闻"

def get_ai_analysis(markets, stocks, news):
    market_text = "\n".join([f"{k}: {v}" for k, v in markets.items()])
    stock_text = "\n".join([
        f"{s.get('name', 'N/A')}({s.get('code', 'N/A')}): {s.get('price', 'N/A')}元 ({s.get('change', '0')}%)"
        if 'price' in s else f"{s.get('name', 'N/A')}: {s.get('error', '错误')}"
        for s in stocks
    ])
    
    prompt = f"""请分析以下市场数据，生成简报：

【全球市场】
{market_text}

【自选股】
{stock_text}

【最新新闻】
{news}

请简要分析：
1. 今日市场整体走势
2. 重点关注板块/个股
3. 短期操作建议

中文回答，简洁专业，200字以内。"""

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data, timeout=60)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI分析失败: {str(e)}"
    return "AI分析不可用"

def send_daily_report():
    print("开始获取市场数据...")
    
    markets = fetch_global_markets()
    print(f"市场数据: {markets}")
    
    stocks = fetch_china_stocks()
    print(f"自选股: {stocks}")
    
    news = fetch_stock_news()
    
    ai_analysis = get_ai_analysis(markets, stocks, news)
    
    market_table = "\n".join([f"{k}: {v}" for k, v in markets.items()])
    
    stock_table = "\n".join([
        f"{s.get('name', 'N/A')}({s.get('code', 'N/A')}): {s.get('price', 'N/A')}元 ({s.get('change', 'N/A')}%)"
        if 'price' in s else f"{s.get('name', 'N/A')}({s.get('code', 'N/A')}): {s.get('error', '数据获取失败')}"
        for s in stocks
    ])
    
    subject = f"每日全球市场简报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    body = f"""每日全球市场简报
{'='*55}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【核心指标】
道琼斯指数: {markets.get('道琼斯指数', 'N/A')}
纳斯达克: {markets.get('纳斯达克', 'N/A')}
标普500: {markets.get('标普500', 'N/A')}

{'='*55}

【全球股指】
上证指数: {markets.get('上证指数', 'N/A')}
深证成指: {markets.get('深证成指', 'N/A')}
创业板指: {markets.get('创业板指', 'N/A')}

{'='*55}

【大宗商品】
现货黄金: {markets.get('现货黄金', 'N/A')}
WTI原油: {markets.get('WTI原油', 'N/A')}
布伦特原油: {markets.get('布伦特原油', 'N/A')}

{'='*55}

【自选股动态】
{stock_table}

{'='*55}

【AI简析】
{ai_analysis}

{'='*55}

【最新新闻】
{news}

{'='*55}

数据来源: 腾讯财经、新浪财经 | DeepSeek AI分析
免责声明: 本报告仅供参考，不构成投资建议
{'='*55}
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
    send_daily_report()
