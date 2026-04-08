# -*- coding: utf-8 -*-
import requests
# from bs4 import BeautifulSoup  # 暂时注释掉
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

def fetch_china_market():
    markets = {}
    
    try:
        response = requests.get(
            "https://qt.gtimg.cn/q=s_sh000001,s_sz399001,s_usDJI,s_usIXIC,s_usINX",
            headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.encoding = "gbk"
        data = response.text
        
        for line in data.split("\n"):
            parts = line.split("~")
            if len(parts) > 5:
                code = parts[0]
                price = parts[3]
                change = parts[5] if len(parts) > 5 else "0"
                
                if "sh000001" in code and price and price not in ["0", ""]:
                    markets["上证指数"] = "{} ({}%)".format(price, change)
                elif "sz399001" in code and price and price not in ["0", ""]:
                    markets["深证成指"] = "{} ({}%)".format(price, change)
                elif "usDJI" in code and price and price not in ["0", ""]:
                    markets["道琼斯"] = "{} ({}%)".format(price, change)
                elif "usIXIC" in code and price and price not in ["0", ""]:
                    markets["纳斯达克"] = "{} ({}%)".format(price, change)
                elif "usINX" in code and price and price not in ["0", ""]:
                    markets["标普500"] = "{} ({}%)".format(price, change)
    except Exception as e:
        print("腾讯财经数据获取失败: {}".format(e))
    
    if not markets:
        try:
            response = requests.get("https://hq.sinajs.cn/list=s_sh000001,s_sz399001", headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            data = response.text
            if "sh000001" in data:
                parts = data.split("sh000001")[1].split("=")[1].split(",")
                if len(parts) > 2:
                    markets["上证指数"] = "{} ({}%)".format(parts[1], parts[2])
            if "sz399001" in data:
                parts = data.split("sz399001")[1].split("=")[1].split(",")
                if len(parts) > 2:
                    markets["深证成指"] = "{} ({}%)".format(parts[1], parts[2])
        except:
            pass
    
    return markets

def fetch_oil_price():
    try:
        response = requests.get(
            "https://qt.gtimg.cn/q=hf_CL,hf_LCO",
            headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.encoding = "gbk"
        data = response.text
        
        for line in data.split("\n"):
            parts = line.split("~")
            if len(parts) > 5:
                code = parts[0].split("_")[1] if "_" in parts[0] else ""
                price = parts[3]
                change = parts[5] if len(parts) > 5 else "0"
                
                if code == "CL" and price and price not in ["0", ""]:
                    return "${}/桶 ({}%)".format(price, change)
                elif code == "LCO" and price and price not in ["0", ""]:
                    return "${}/桶 ({}%)".format(price, change)
    except Exception as e:
        print("获取油价失败: {}".format(e))
    
    try:
        response = requests.get("https://hq.sinajs.cn/list=nf_CL", headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        data = response.text
        if "=" in data:
            parts = data.split("=")[1].split(",")
            if len(parts) > 2:
                return "${}".format(parts[1])
    except:
        pass
    
    return "数据获取中"

def fetch_usd_index():
    try:
        response = requests.get(
            "https://qt.gtimg.cn/q=USINDEX",
            headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.encoding = "gbk"
        data = response.text
        
        parts = data.split("~")
        if len(parts) > 5:
            price = parts[3]
            change = parts[5] if len(parts) > 5 else "0"
            if price and price not in ["0", ""]:
                return "{} ({}%)".format(price, change)
    except Exception as e:
        print("获取美元指数失败: {}".format(e))
    
    try:
        response = requests.get("https://hq.sinajs.cn/list=fx_usdindex", headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        data = response.text
        if "=" in data:
            parts = data.split("=")[1].split(",")
            if len(parts) > 0:
                return parts[0].strip('"')
    except:
        pass
    
    return "数据获取中"

def fetch_china_news():
    # 暂时跳过新闻抓取，避免BeautifulSoup依赖
    return "新闻抓取功能暂时禁用（需要BeautifulSoup）"

def get_ai_analysis(markets, oil_price, usd_index, news):
    prompt = """请作为资深A股市场分析师，为我生成一份全面的A股走势分析报告：

【A股主要指数】
{markets}

【国际油价】
WTI原油: {oil_price}

【美元指数】
{usd_index}

【国内新闻】
{news}

请生成以下分析：

一、A股市场走势分析
- 今日盘面表现
- 成交量能分析
- 板块轮动情况

二、影响因素分析
国内因素：
- 宏观经济政策（财政、货币）
- 监管政策变化
- 产业政策导向
- IPO与再融资情况

国际因素：
- 美联储货币政策
- 中美关系动态
- 全球供应链变化
- 国际资金流向

三、海湾战争影响分析
- 油价波动对A股能源板块影响
- 地缘政治风险偏好变化
- 输入性通胀压力
- 航运与物流板块

四、资金面分析
- 北向资金流向
- 两融数据变化
- 主力资金动向

五、后市展望与投资建议
- 短期走势预判
- 重点关注板块
- 风险提示

请用专业详尽的中文进行分析。""".format(markets=markets, oil_price=oil_price, usd_index=usd_index, news=news)

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        print("正在调用AI分析...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "AI分析生成失败: {}".format(result)
    except Exception as e:
        return "AI分析调用失败: {}".format(str(e))

def send_report():
    print("获取A股数据...")
    markets = fetch_china_market()
    oil_price = fetch_oil_price()
    usd_index = fetch_usd_index()
    news = fetch_china_news()
    
    market_text = "\n".join(["{}: {}".format(k, v) for k, v in markets.items()])
    
    print("生成AI分析...")
    ai_analysis = get_ai_analysis(markets, oil_price, usd_index, news)
    
    subject = "A股走势分析报告 - {}".format(datetime.now().strftime('%Y-%m-%d'))
    
    body = """A股市场走势分析报告
{separator}
{timestamp}

【A股核心指数】
{market_text}

【美股参考】
{market_text}

【国际联动】
WTI原油: {oil_price}（海湾局势影响）
布伦特原油: 参考WTI
美元指数: {usd_index}

{separator}

【AI深度分析】
{ai_analysis}

{separator}

【国内财经新闻】
{news}

{separator}

【行情图表链接】
上证指数: https://finance.sina.com.cn/stock/
深证成指: https://finance.sina.com.cn/stock/
创业板指: https://finance.sina.com.cn/stock/
恒生指数: https://finance.sina.com.cn/stock/

【板块行情】
新能源: https://finance.sina.com.cn/stock/
AI人工智能: https://finance.sina.com.cn/stock/
半导体: https://finance.sina.com.cn/stock/

【资金流向】
北向资金: https://data.eastmoney.com/hsgt/
融资融券: https://data.eastmoney.com/rzrq/

【综合分析平台】
新浪财经: https://finance.sina.com.cn/stock/
东方财富: https://www.eastmoney.com/
同花顺: https://www.10jqka.com.cn/
Wind: https://www.wind.com.cn/

{separator}
报告生成时间: {end_time}
""".format(
        separator='='*60,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'),
        market_text=market_text,
        oil_price=oil_price,
        usd_index=usd_index,
        ai_analysis=ai_analysis,
        news=news,
        end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
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
    send_report()
