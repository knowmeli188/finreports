# -*- coding: utf-8 -*-
import requests
import json
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import sys
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
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", "-H", "Referer: https://finance.qq.com", url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except:
        pass
    return None

def fetch_hot_sectors():
    sectors = []
    
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!50&fields=f12,f14,f3,f6,f8"
        text = curl_get(url)
        
        if text:
            data = json.loads(text)
            diff = data.get("data", {}).get("diff", [])
            
            for item in diff[:5]:
                sectors.append({
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "change_pct": item.get("f3", 0),
                    "amount": item.get("f6", 0),
                    "pe": item.get("f8", 0)
                })
    except Exception as e:
        print(f"获取板块失败: {e}")
    
    return sectors

def fetch_sector_stocks(sector_code):
    stocks = []
    
    try:
        url = f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f3&fs=b:{sector_code}+f:!50&fields=f2,f3,f4,f5,f6,f12,f14,f8"
        text = curl_get(url)
        
        if text:
            data = json.loads(text)
            diff = data.get("data", {}).get("diff", [])
            
            for item in diff[:5]:
                stocks.append({
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0),
                    "change_pct": item.get("f3", 0),
                    "volume": item.get("f5", 0),
                    "amount": item.get("f6", 0),
                    "turnover": item.get("f8", 0)
                })
    except Exception as e:
        print(f"获取个股失败: {e}")
    
    return stocks

def analyze_with_ai(sectors_data, all_stocks_data):
    sector_text = "\n".join([
        f"{i+1}. **{s['name']}**（代码:{s['code']}）\n   涨幅:{s['change_pct']}% | 成交额:{s['amount']/100000000:.2f}亿"
        for i, s in enumerate(sectors_data)
    ])
    
    stocks_text = ""
    for sector in all_stocks_data:
        stocks_text += f"\n\n=== 【{sector['name']}板块 TOP3】===\n"
        for stock in sector['stocks'][:3]:
            stocks_text += f"  {stock['name']}({stock['code']}): 现价{stock['price']}元 | {stock['change_pct']}% | 换手{stock['turnover']}%\n"

    prompt = f"""请分析以下A股热门板块的投资价值：

【今日涨幅前五热门板块】
{sector_text}

【板块内代表性个股】
{stocks_text}

请从以下维度进行深度分析：

## 1. 基本面分析
板块上涨的宏观逻辑、行业景气度和政策支持情况

## 2. 技术面分析
当前走势特征、量价配合、短期支撑压力位

## 3. 资金面分析
资金流入情况、板块轮动持续性

## 4. 个股重点关注
2-3只重点关注个股及其上涨逻辑

## 5. 投资建议
短期操作建议和风险提示

请用专业客观风格，中文，600-1000字。"""

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        print("调用AI分析...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return f"AI分析失败"
    except Exception as e:
        return f"AI分析失败: {str(e)}"

def send_sector_report():
    print("获取热门板块...")
    sectors = fetch_hot_sectors()
    
    if not sectors:
        print("未获取到数据，请检查网络")
        return
    
    print(f"获取到 {len(sectors)} 个板块")
    
    all_stocks = []
    for s in sectors:
        print(f"获取 {s['name']} 个股...")
        stocks = fetch_sector_stocks(s["code"])
        s["stocks"] = stocks
        all_stocks.append(s)
        time.sleep(0.3)
    
    print("生成AI分析...")
    ai_analysis = analyze_with_ai(sectors, all_stocks)
    
    sector_table = "\n".join([
        f"{i+1}. {s['name']} 涨幅:{s['change_pct']}% 成交额:{s['amount']/100000000:.2f}亿"
        for i, s in enumerate(sectors)
    ])
    
    stocks_detail = ""
    for s in all_stocks:
        stocks_detail += f"\n【{s['name']} TOP5】\n"
        for st in s['stocks']:
            stocks_detail += f"  {st['name']}({st['code']}): {st['price']}元 {st['change_pct']}%\n"
    
    subject = f"每日热门板块深度分析 - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = f"""每日热门板块深度分析
{'='*60}
{datetime.now().strftime('%Y-%m-%d %H:%M')}

【今日涨幅前五板块】
{sector_table}

【板块内个股】
{stocks_detail}

{'='*60}

【AI深度分析】
{ai_analysis}

{'='*60}
数据来源: 东方财富 | DeepSeek AI分析
免责声明: 本报告仅供参考，不构成投资建议
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
    send_sector_report()
