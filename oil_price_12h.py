# -*- coding: utf-8 -*-
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
            if not line.strip() or "=" not in line:
                continue
                
            code_part, value_part = line.split("=", 1)
            if not value_part or '"' not in value_part:
                continue
                
            values = value_part.strip('";').split(",")
            if len(values) < 2:
                continue
            
            price = values[0].strip()
            change = values[1].strip()
            
            if "hf_CL" in line and price and price not in ["0", ""]:
                prices["WTI纽约原油"] = {"price": "${}/桶".format(price), "change": change}
            elif "hf_LCO" in line and price and price not in ["0", ""]:
                prices["布伦特原油"] = {"price": "${}/桶".format(price), "change": change}
            elif "hf_XAU" in line and price and price not in ["0", ""]:
                prices["现货黄金"] = {"price": "${}/盎司".format(price), "change": change}
            elif "hf_XAG" in line and price and price not in ["0", ""]:
                prices["现货白银"] = {"price": "${}/盎司".format(price), "change": change}
    except Exception as e:
        print("获取国际油价失败: {}".format(e))
    
    try:
        response = requests.get("https://hq.sinajs.cn/list=nf_SC0", headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=15)
        response.encoding = "gbk"
        data = response.text
        if "nf_SC0" in data and "=" in data:
            values = data.split("=")[1].strip('";').split(",")
            if len(values) > 9:
                price = values[2].strip()  # 最新价
                prev_close = values[5].strip() if len(values) > 5 else price  # 昨结算价
                if price and price not in ["0", ""]:
                    try:
                        price_float = float(price)
                        prev_float = float(prev_close)
                        if prev_float != 0:
                            change_pct = ((price_float - prev_float) / prev_float * 100)
                            change_str = "{:.2f}".format(change_pct)
                        else:
                            change_str = "0"
                    except:
                        change_str = "0"
                    prices["SC上海原油"] = {"price": "¥{}/桶".format(price), "change": change_str}
    except Exception as e:
        print("获取国内油价失败: {}".format(e))
    
    # 尝试获取迪拜现货油价
    dubai_found = False
    dubai_codes = ["hf_DUBAI", "hf_OMAN", "hf_DU", "hf_DB", "hf_MID"]
    for code in dubai_codes:
        try:
            response = requests.get("https://qt.gtimg.cn/q={}".format(code), headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=10)
            response.encoding = "gbk"
            data = response.text
            if '="' in data and "none_match" not in data:
                values = data.split('="')[1].strip('";').split(",")
                if len(values) >= 2:
                    price = values[0].strip()
                    change = values[1].strip()
                    if price and price not in ["0", ""]:
                        prices["迪拜现货原油"] = {"price": "${}/桶".format(price), "change": change}
                        dubai_found = True
                        break
        except:
            continue
    
    if not dubai_found:
        prices["迪拜现货原油"] = {"price": "数据获取中", "change": "0"}
    
    return prices

def get_oil_text_description(prices):
    if not prices:
        return "油价数据获取中，请查看链接了解详情"
    
    descriptions = []
    
    for name, data in prices.items():
        if isinstance(data, dict):
            price = data.get("price", "N/A")
            change = data.get("change", "0")
            
            if price == "数据获取中":
                descriptions.append("{}: {}".format(name, price))
                continue
                
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
            
            descriptions.append("{}: {}，今日{}{}%".format(name, price, trend, change))
        else:
            descriptions.append("{}: {}".format(name, data))
    
    return "\n".join(descriptions) if descriptions else "油价数据获取中，请查看链接了解详情"

def send_price_report():
    print("获取油价数据...")
    prices = fetch_oil_prices()
    oil_desc = get_oil_text_description(prices)
    
    subject = "大宗商品简报(12h) - {}".format(datetime.now().strftime('%m-%d %H:%M'))
    
    body = """大宗商品简报
{}
{}

【大宗商品实时报价】
{}

【油价走势分析】
上海SC原油：国内原油期货主力合约，价格受国际油价及人民币汇率共同影响
美国纽约WTI：全球原油定价基准之一，反映北美市场供需状况
伦敦布伦特：国际原油市场最重要定价基准，覆盖欧洲及全球市场
迪拜阿曼：中东原油价格指标，反映波斯湾地区供应情况

【贵金属走势分析】
现货黄金：全球避险资产，与美元指数负相关，地缘政治风险上升时需求增加
现货白银：工业属性强，波动性高于黄金，受工业需求和通胀预期影响

【波斯湾局势影响】
- 霍尔木兹海峡运输受阻将影响油价
- 美伊冲突升级可能推高油价
- OPEC+产量决策影响供需平衡

【走势图链接】
- 新浪能源: https://finance.sina.com.cn/money/energy/
- 东方财富油服: https://data.eastmoney.com/industry/393d_0.html
- 腾讯能源: https://finance.qq.com/energy/
- 黄金价格: https://finance.sina.com.cn/money/metal/
- 华尔街见闻: https://wallstreetcn.com/
- 金十数据: https://www.jin10.com/
- 英为财情: https://cn.investing.com/commodities/crude-oil

{}
""".format('='*55, datetime.now().strftime('%Y-%m-%d %H:%M'), oil_desc, '='*55)
    
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
