import requests
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
    prices = {}
    
    try:
        response = requests.get("https://qt.gtimg.cn/q=hf_CL,hf_LCO,hf_XAU", headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=15)
        response.encoding = "gbk"
        data = response.text
        
        for line in data.split("\n"):
            parts = line.split("~")
            if len(parts) > 32:
                code = parts[0].split("_")[1] if "_" in parts[0] else ""
                if code == "CL":
                    price = parts[3]
                    change_pct = parts[32] if len(parts) > 32 else "0"
                    if price and price not in ["0", ""]:
                        prices["WTI纽约原油"] = {"price": f"${price}/桶", "change": change_pct}
                elif code == "LCO":
                    price = parts[3]
                    change_pct = parts[32] if len(parts) > 32 else "0"
                    if price and price not in ["0", ""]:
                        prices["布伦特原油"] = {"price": f"${price}/桶", "change": change_pct}
    except Exception as e:
        print(f"获取国际油价失败: {e}")
    
    try:
        response = requests.get("https://hq.sinajs.cn/list=nf_0#SC", headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=15)
        response.encoding = "utf-8"
        data = response.text
        if "nf_0" in data and "=" in data:
            parts = data.split("=")[1].split(",")
            if len(parts) > 4 and parts[1].strip():
                prices["SC上海原油"] = {"price": f"¥{parts[1].strip()}/桶", "change": parts[2].strip() if len(parts) > 2 else "0"}
    except Exception as e:
        print(f"获取国内油价失败: {e}")
    
    return prices

def get_oil_text_description(prices):
    if not prices:
        return "油价数据获取中，请查看链接了解详情"
    
    descriptions = []
    
    for name, data in prices.items():
        if isinstance(data, dict):
            price = data.get("price", "N/A")
            change = data.get("change", "0")
            try:
                change_float = float(change)
                if change_float > 0:
                    trend = "上涨"
                elif change_float < 0:
                    trend = "下跌"
                else:
                    trend = "持平"
            except:
                trend = "变化中"
                change_float = 0
            
            descriptions.append(f"{name}: {price}，今日{trend}{change}%")
        else:
            descriptions.append(f"{name}: {data}")
    
    return "\n".join(descriptions) if descriptions else "油价数据获取中，请查看链接了解详情"

def send_price_report():
    print("获取油价数据...")
    prices = fetch_oil_prices()
    oil_desc = get_oil_text_description(prices)
    
    subject = f"油价简报(12h) - {datetime.now().strftime('%m-%d %H:%M')}"
    
    body = f"""油价简报
{'='*55}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【全球油价实时报价】
{oil_desc}

【油价走势分析】
上海SC原油：国内原油期货主力合约，价格受国际油价及人民币汇率共同影响
美国纽约WTI：全球原油定价基准之一，反映北美市场供需状况
伦敦布伦特：国际原油市场最重要定价基准，覆盖欧洲及全球市场
迪拜阿曼：中东原油价格指标，反映波斯湾地区供应情况

【波斯湾局势影响】
- 霍尔木兹海峡运输受阻将影响油价
- 美伊冲突升级可能推高油价
- OPEC+产量决策影响供需平衡

【走势图链接】
- 新浪能源: https://finance.sina.com.cn/money/energy/
- 东方财富油服: https://data.eastmoney.com/industry/393d_0.html
- 腾讯能源: https://finance.qq.com/energy/
- 华尔街见闻: https://wallstreetcn.com/
- 金十数据: https://www.jin10.com/
- 英为财情: https://cn.investing.com/commodities/crude-oil

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
    send_price_report()
