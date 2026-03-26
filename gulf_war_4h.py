# -*- coding: utf-8 -*-
import requests
import subprocess
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

def fetch_oil_prices():
    prices = []
    
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", "https://qt.gtimg.cn/q=hf_CL,hf_LCO,hf_XAU"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            data = result.stdout
            print(f"Raw data: {data[:200]}")
            for line in data.split("\n"):
                if '="' not in line:
                    continue
                parts = line.split('="')[1].rstrip('";\n').split(",")
                if len(parts) >= 2:
                    price = parts[0].strip()
                    change = parts[1].strip()
                    if "hf_CL" in line and price and price not in ["0", ""]:
                        prices.append(f"WTI纽约原油: ${price}/桶 ({change}%)")
                    elif "hf_LCO" in line and price and price not in ["0", ""]:
                        prices.append(f"布伦特原油: ${price}/桶 ({change}%)")
                    elif "hf_XAU" in line and price and price not in ["0", ""]:
                        prices.append(f"现货黄金: ${price}/盎司 ({change}%)")
            print(f"Prices found: {prices}")
    except Exception as e:
        print(f"获取油价数据失败: {e}")
    
    return "\n".join(prices) if prices else "油价数据获取中，请查看链接 https://finance.sina.com.cn/money/metal/"

def fetch_gulf_news():
    all_news = []
    sources = [
        ("华尔街见闻", "https://wallstreetcn.com/", ["海湾", "伊朗", "霍尔木兹", "沙特", "原油", "中东", "OPEC", "美伊", "制裁", "波斯湾", "油轮", "油价"]),
        ("金十数据", "https://www.jin10.com/", ["海湾", "伊朗", "原油", "石油", "中东", "霍尔木兹", "美伊", "战"]),
        ("新浪财经", "https://finance.sina.com.cn/money/energy/", ["海湾", "伊朗", "石油", "原油", "沙特", "OPEC", "中东", "霍尔木兹"]),
    ]
    
    for source_name, url, keywords in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            for item in soup.select("a[href]")[:50]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                
                if not title or len(title) < 10:
                    continue
                
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    if "wallstreetcn" in url:
                        href = "https://wallstreetcn.com" + href
                    elif "jin10" in url:
                        href = "https://www.jin10.com" + href
                    else:
                        href = "https://finance.sina.com.cn" + href
                
                if not href or not href.startswith("http"):
                    continue
                
                for kw in keywords:
                    if kw in title:
                        news_item = f"[{source_name}]\n• {title}\n  {href}"
                        if news_item not in str(all_news):
                            all_news.append(news_item)
                        break
        except Exception as e:
            print(f"获取{source_name}失败: {e}")
    
    return "\n\n".join(all_news[:20]) if all_news else "暂无相关新闻"

def send_war_report():
    print("获取波斯湾战况...")
    news = fetch_gulf_news()
    oil_prices = fetch_oil_prices()
    
    subject = f"波斯湾战况简报(4h) - {datetime.now().strftime('%m-%d %H:%M')}"
    
    body = f"""波斯湾战况简报
{'='*50}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【实时油价】
{oil_prices}

{'='*50}

【波斯湾相关报道】
{news}

{'='*50}

【相关链接】
- 华尔街见闻: https://wallstreetcn.com/
- 金十数据: https://www.jin10.com/
- 新浪能源: https://finance.sina.com.cn/money/energy/
- 东方财富油服: https://data.eastmoney.com/industry/393d_0.html

【实时油价走势】
- 新浪贵金属: https://finance.sina.com.cn/money/metal/
- 腾讯能源: https://finance.qq.com/energy/
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
    send_war_report()
