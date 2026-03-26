import requests
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

def fetch_news():
    sources = [
        ("华尔街见闻", "https://wallstreetcn.com/", ["海湾", "伊朗", "霍尔木兹", "沙特", "油", "中东", "OPEC", "美伊", "制裁", "波斯湾"]),
        ("新浪财经", "https://finance.sina.com.cn/money/energy/", ["海湾", "伊朗", "石油", "沙特", "OPEC", "中东"]),
        ("金十数据", "https://www.jin10.com/", ["海湾", "伊朗", "原油", "石油", "中东"]),
    ]
    
    all_news = []
    
    for source_name, url, keywords in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=8)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            for item in soup.select("a[href]")[:40]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                
                if not title or len(title) < 8:
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
                
                if not href.startswith("http"):
                    continue
                
                for kw in keywords:
                    if kw in title:
                        news_item = f"[{source_name}]\n• {title}\n  {href}"
                        if news_item not in str(all_news):
                            all_news.append(news_item)
                        break
        except Exception as e:
            print(f"获取{source_name}失败: {e}")
    
    return all_news[:25]

def fetch_oil_prices():
    prices = []
    
    try:
        response = requests.get(
            "https://qt.gtimg.cn/q=hf_CL,hf_LCO,hf_XAU",
            headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.encoding = "gbk"
        data = response.text
        
        for line in data.split("\n"):
            if "=" not in line:
                continue
            
            code = line.split("=")[0].strip()
            
            if "hf_CL" in code and '"' in line:
                parts = line.split('="')[1].split(",")
                price = parts[0] if len(parts) > 0 else ""
                change = parts[1] if len(parts) > 1 else "0"
                if price and price not in ["0", ""]:
                    prices.append("WTI纽约原油: $" + price + "/桶 (" + change + "%)")
            elif "hf_LCO" in code and '"' in line:
                parts = line.split('="')[1].split(",")
                price = parts[0] if len(parts) > 0 else ""
                change = parts[1] if len(parts) > 1 else "0"
                if price and price not in ["0", ""]:
                    prices.append("布伦特原油: $" + price + "/桶 (" + change + "%)")
            elif "hf_XAU" in code and '"' in line:
                parts = line.split('="')[1].split(",")
                price = parts[0] if len(parts) > 0 else ""
                change = parts[1] if len(parts) > 1 else "0"
                if price and price not in ["0", ""]:
                    prices.append("现货黄金: $" + price + "/盎司 (" + change + "%)")
    except Exception as e:
        print("获取油价数据失败: " + str(e))
    
    return "\n".join(prices) if prices else "油价数据获取中"

def send_report():
    print("获取国际媒体海湾新闻...")
    news = fetch_news()
    oil_prices = fetch_oil_prices()
    
    news_text = "\n\n".join(news) if news else "暂无相关新闻"
    
    subject = f"国际媒体海湾战况报道 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    body = f"""国际媒体海湾战况报道
{'='*60}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【实时油价】
{oil_prices}

{'='*60}

【国际媒体报道】
{news_text}

{'='*60}

【相关链接】
- 华尔街见闻: https://wallstreetcn.com/
- 金十数据: https://www.jin10.com/
- 新浪能源: https://finance.sina.com.cn/money/energy/

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
    
    print(f"发送给 {RECEIVER_EMAIL}...")
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    
    print(f"发送给 {RECEIVER_EMAIL_2}...")
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL_2, msg.as_string())
    
    server.quit()
    print("发送成功!")

if __name__ == "__main__":
    send_report()
