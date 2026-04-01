# -*- coding: utf-8 -*-
import requests
import smtplib
import subprocess
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

def fetch_usd_index():
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", "https://api.exchangerate-api.com/v4/latest/USD"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            rates = data.get("rates", {})
            
            eur = rates.get("EUR", 0)
            jpy = rates.get("JPY", 0)
            gbp = rates.get("GBP", 0)
            cad = rates.get("CAD", 0)
            sek = rates.get("SEK", 0)
            chf = rates.get("CHF", 0)
            
            if eur > 0 and jpy > 0:
                usdx = 50.14348112 * (eur ** -0.576) * (jpy ** 0.136) * (gbp ** -0.119) * (cad ** 0.091) * (sek ** 0.042) * (chf ** 0.036)
                return "{:.2f} (基于主要货币汇率计算)".format(usdx)
    except Exception as e:
        print("Exchangerate API failed: {}".format(e))
    
    try:
        r = requests.get("https://stooq.com/q/d/l/?s=dxy", timeout=15)
        lines = r.text.strip().split("\n")
        if len(lines) >= 2:
            header = lines[0].split(",")
            close_idx = header.index("close") if "close" in header else 4
            
            last_line = lines[-1].split(",")
            prev_line = lines[-2].split(",") if len(lines) > 1 else last_line
            
            if len(last_line) > close_idx and len(prev_line) > close_idx:
                current = float(last_line[close_idx])
                prev = float(prev_line[close_idx])
                pct = (current - prev) / prev * 100
                return "{:.2f} (涨跌: {:.2f}%)".format(current, pct)
    except Exception as e:
        print("Stooq DXY failed: {}".format(e))
    
    try:
        response = requests.get("https://qt.gtimg.cn/q=USINDEX", headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=15)
        response.encoding = "gbk"
        data = response.text
        
        parts = data.split("~")
        if len(parts) > 32:
            price = parts[3]
            change_pct = parts[32] if len(parts) > 32 else "0"
            if price and price not in ["0", ""]:
                return "{} (涨跌: {}%)".format(price, change_pct)
    except Exception as e:
        print("获取美元指数失败: {}".format(e))
    
    return "数据获取中，请查看 https://finance.sina.com.cn/forex/"

def fetch_gold_price():
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", "https://qt.gtimg.cn/q=hf_XAU,hf_XAG"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            data = result.stdout
            results = []
            
            for line in data.split("\n"):
                if '="' not in line:
                    continue
                parts = line.split('="')[1].rstrip('";').split(",")
                if len(parts) >= 2:
                    if "hf_XAU" in line:
                        price = parts[0]
                        change = parts[1]
                        if price and price not in ["0", ""]:
                            results.append("现货黄金: ${}/盎司 (涨跌: {}%)".format(price, change))
                    elif "hf_XAG" in line:
                        price = parts[0]
                        change = parts[1]
                        if price and price not in ["0", ""]:
                            results.append("现货白银: ${}/盎司 (涨跌: {}%)".format(price, change))
            
            if results:
                return "\n".join(results)
    except Exception as e:
        print("获取贵金属价格失败: {}".format(e))
    
    # 新浪API返回空数据，已移除无效调用
    
    return "数据获取中，请查看 https://finance.sina.com.cn/money/metal/"

def send_usd_report():
    print("获取美元指数数据...")
    usd = fetch_usd_index()
    gold = fetch_gold_price()
    
    subject = "美元指数简报 - {}".format(datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    body = """美元指数与黄金实时报告
{}
{}

【美元指数】
{}

【贵金属价格】
{}

【美元指数走势分析】
美元指数反映美元相对于一篮子主要货币的强弱变化
- 指数 > 100：美元相对升值，可能导致黄金、大宗商品承压
- 指数 < 100：美元相对贬值，黄金、大宗商品通常受益
- 正常波动区间：95-115

【黄金走势分析】
黄金以美元计价，与美元指数呈负相关
- 美元走强 → 黄金承压
- 美元走弱 → 黄金受益
- 地缘政治风险上升 → 黄金避险需求增加

【影响因素】
1. 美联储货币政策（加息/降息预期）
2. 美国经济数据（GDP增长、CPI通胀、非农就业）
3. 地缘政治风险（海湾战争、俄乌冲突等）
4. 全球央行购金行为

【走势图链接】
- 新浪外汇: https://finance.sina.com.cn/forex/
- 东方财富外汇: https://data.eastmoney.com/forex/
- 黄金价格: https://finance.sina.com.cn/money/metal/
- 华尔街见闻: https://wallstreetcn.com/
- 金十数据: https://www.jin10.com/

{}
""".format('='*55, datetime.now().strftime('%Y-%m-%d %H:%M'), usd, gold, '='*55)
    
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
    send_usd_report()
