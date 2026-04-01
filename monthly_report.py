# -*- coding: utf-8 -*-
import requests
import json
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import os

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-f2b0c2b771fe4ba1b085328380ab809d")

def curl_get(url):
    try:
        process = subprocess.Popen(
            ["curl", "-s", "--max-time", "15", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0 and stdout:
            return stdout
    except:
        pass
    return None

def fetch_us_indices():
    data = {}
    try:
        url = "https://qt.gtimg.cn/q=usDJI,usIXIC,usSPX"
        text = curl_get(url)
        if text:
            for line in text.split("\n"):
                if "none_match" in line or "~" not in line:
                    continue
                parts = line.split("~")
                if len(parts) > 32:
                    code = parts[0].split("_")[1] if "_" in parts[0] else ""
                    price = parts[3]
                    change = parts[32]
                    if not change or change == "0":
                        change = parts[4]
                        if price and change:
                            try:
                                pct = (float(price) - float(change)) / float(change) * 100
                                change = f"{pct:.2f}"
                            except:
                                change = "0"
                    if code == "DJI":
                        data["道指"] = {"price": price, "change": change}
                    elif code == "IXIC":
                        data["纳指"] = {"price": price, "change": change}
                    elif code == "SPX":
                        data["标普500"] = {"price": price, "change": change}
    except Exception as e:
        print(f"获取美股指数失败: {e}")
    return data

def fetch_sp500_history():
    try:
        url = "https://stooq.com/q/d/l/?s=spx.us&i=d&d1=20260201&d2=20260228"
        text = curl_get(url)
        if text and "No data" not in text:
            lines = text.strip().split("\n")
            if len(lines) > 2:
                return lines[-1]
    except:
        pass
    return None

def fetch_oil_prices():
    data = {}
    try:
        url = "https://qt.gtimg.cn/q=hf_CL,hf_LCO"
        text = curl_get(url)
        if text:
            for line in text.split("\n"):
                if '=",' not in line:
                    continue
                parts = line.split('="')[1].rstrip('";\n').split(",")
                if len(parts) >= 2:
                    price = parts[0].strip()
                    change = parts[1].strip()
                    if "hf_CL" in line:
                        data["WTI"] = {"price": price, "change": change}
                    elif "hf_LCO" in line:
                        data["布伦特"] = {"price": price, "change": change}
    except Exception as e:
        print(f"获取油价失败: {e}")
    return data

def fetch_gold_price():
    try:
        url = "https://qt.gtimg.cn/q=hf_XAU,hf_XAG"
        text = curl_get(url)
        if text:
            for line in text.split("\n"):
                if '=",' not in line:
                    continue
                parts = line.split('="')[1].rstrip('";\n').split(",")
                if len(parts) >= 2 and "hf_XAU" in line:
                    return {"price": parts[0].strip(), "change": parts[1].strip()}
    except:
        pass
    return None

def fetch_usd_index():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        text = curl_get(url)
        if text:
            data = json.loads(text)
            rates = data.get("rates", {})
            eur = rates.get("EUR", 0)
            jpy = rates.get("JPY", 0)
            if eur > 0 and jpy > 0:
                usdx = 50.14348112 * (eur ** -0.576) * (jpy ** 0.136)
                return round(usdx, 2)
    except:
        pass
    return None

def fetch_china_indices():
    data = {}
    try:
        url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
        text = curl_get(url)
        if text:
            for line in text.split("\n"):
                if "~" not in line:
                    continue
                parts = line.split("~")
                if len(parts) > 32:
                    code = parts[0].split("_")[1] if "_" in parts[0] else ""
                    price = parts[3]
                    change_pct = parts[32]
                    if code == "000001":
                        data["上证指数"] = {"price": price, "change": change_pct}
                    elif code == "399001":
                        data["深证成指"] = {"price": price, "change": change_pct}
                    elif code == "399006":
                        data["创业板"] = {"price": price, "change": change_pct}
    except:
        pass
    return data

def fetch_europe_indices():
    try:
        url = "https://qt.gtimg.cn/q=hf_FTSE,hf_GDAXI,hf_CAC40"
        text = curl_get(url)
        if text:
            data = {}
            for line in text.split("\n"):
                if '=",' not in line:
                    continue
                parts = line.split('="')[1].rstrip('";\n').split(",")
                if len(parts) >= 2:
                    price = parts[0].strip()
                    change = parts[1].strip()
                    if "FTSE" in line:
                        data["富时100"] = {"price": price, "change": change}
                    elif "GDAXI" in line:
                        data["德国DAX"] = {"price": price, "change": change}
                    elif "CAC40" in line:
                        data["法国CAC"] = {"price": price, "change": change}
            return data
    except:
        pass
    return {}

def fetch_news_summary():
    keywords = ["特朗普", "伊朗", "油价", "美联储", "中美", "关税", "市场", "经济"]
    news = []
    sources = [
        ("华尔街见闻", "https://wallstreetcn.com/"),
        ("新浪财经", "https://finance.sina.com.cn/"),
    ]
    
    for name, url in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            
            for item in soup.select("a[href]")[:30]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if not title or len(title) < 10:
                    continue
                for kw in keywords:
                    if kw in title:
                        news.append(f"• {title}")
                        break
        except:
            pass
    
    return "\n".join(news[:10]) if news else "暂无重大新闻"

def generate_monthly_report(market_data, news):
    prompt = f"""请根据以下市场数据，生成一份月度资本市场分析报告，严格按照以下格式，字数控制在8000-10000字：

【报告格式要求】

1. 开篇：用一个重大的市场事件作为引子，描述该事件对全球金融市场的冲击
   例如：特朗普宣布XX政策/消息，触发全球金融市场剧烈震荡。油价XX%，黄金XX%，美股XX%。

2. 分市场详细分析：
   - 美股：三大指数表现、涨跌幅、具体点位、行业板块表现（科技股、金融股、能源股等）
   - 欧股：主要股指表现、德法英意西等国股指
   - A股：上证、深证、创业板表现
   - 美债：10年期、2年期国债收益率变化
   - 欧债：德法英等国国债收益率
   - 原油：WTI和布伦特价格、涨跌幅
   - 黄金白银：价格走势
   - 外汇：美元指数、主要货币汇率（欧元、日元、英镑、人民币）

3. 资金流向分析：
   - 资金从哪些市场流出
   - 资金流入哪些避风港
   - 板块轮动特征

4. 政策面分析：
   - 美联储政策动向
   - 全球主要央行政策
   - 地缘政治影响

5. 技术面分析：
   - 主要指数技术位置
   - 关键支撑压力位

6. 后市展望：
   - 短期走势预判
   - 风险因素提示
   - 投资建议

【市场数据】
{datetime.now().strftime('%Y年%m月%d日')}

美股：
{json.dumps(market_data.get('us_indices', {}), ensure_ascii=False, indent=2)}

A股：
{json.dumps(market_data.get('china_indices', {}), ensure_ascii=False, indent=2)}

欧股：
{json.dumps(market_data.get('europe_indices', {}), ensure_ascii=False, indent=2)}

原油：
{json.dumps(market_data.get('oil', {}), ensure_ascii=False, indent=2)}

黄金：{market_data.get('gold', '暂无数据')}

美元指数：{market_data.get('usd_index', '暂无数据')}

【近期重大新闻】
{news}

请严格按照上述格式生成报告，中文，8000-10000字，专业客观。"""

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000,
            "temperature": 0.7
        }
        
        print("生成月度分析报告...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return "报告生成失败"
    except Exception as e:
        return f"报告生成失败: {str(e)}"

def send_monthly_report():
    print("开始收集月度市场数据...")
    
    market_data = {
        "us_indices": fetch_us_indices(),
        "china_indices": fetch_china_indices(),
        "europe_indices": fetch_europe_indices(),
        "oil": fetch_oil_prices(),
        "gold": fetch_gold_price(),
        "usd_index": fetch_usd_index()
    }
    
    print(f"美股: {market_data['us_indices']}")
    print(f"A股: {market_data['china_indices']}")
    print(f"欧股: {market_data['europe_indices']}")
    print(f"原油: {market_data['oil']}")
    print(f"黄金: {market_data['gold']}")
    print(f"美元指数: {market_data['usd_index']}")
    
    print("获取新闻摘要...")
    news = fetch_news_summary()
    
    print("生成AI分析报告...")
    report = generate_monthly_report(market_data, news)
    
    subject = f"【月度资本市场深度分析】{datetime.now().strftime('%Y年%m月')}"
    
    summary = f"""数据概要：
美股：道指 {market_data['us_indices'].get('道指', {}).get('price', 'N/A')} ({market_data['us_indices'].get('道指', {}).get('change', 'N/A')}%)
     纳指 {market_data['us_indices'].get('纳指', {}).get('price', 'N/A')} ({market_data['us_indices'].get('纳指', {}).get('change', 'N/A')}%)
     标普500 {market_data['us_indices'].get('标普500', {}).get('price', 'N/A')} ({market_data['us_indices'].get('标普500', {}).get('change', 'N/A')}%)
     
原油：WTI ${market_data['oil'].get('WTI', {}).get('price', 'N/A')}/桶 ({market_data['oil'].get('WTI', {}).get('change', 'N/A')}%)
     布伦特 ${market_data['oil'].get('布伦特', {}).get('price', 'N/A')}/桶 ({market_data['oil'].get('布伦特', {}).get('change', 'N/A')}%)
     
黄金：${market_data['gold'].get('price', 'N/A')}/盎司 ({market_data['gold'].get('change', 'N/A')}%)

美元指数：{market_data['usd_index']}
"""
    
    body = f"""{'='*60}
月度资本市场深度分析报告
{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
{'='*60}

【市场数据概要】
{summary}

{'='*60}

【深度分析正文】
{report}

{'='*60}
数据来源：东方财富、腾讯财经、新浪财经
分析工具：DeepSeek AI
免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。
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
    print("月度报告发送成功!")

if __name__ == "__main__":
    send_monthly_report()
