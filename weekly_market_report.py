import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, timedelta
import json

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

def get_week_date_range():
    today = datetime.now()
    days_since_saturday = (today.weekday() - 5) % 7
    last_saturday = today - timedelta(days=days_since_saturday if days_since_saturday > 0 else 7)
    start_date = (last_saturday - timedelta(days=6)).strftime("%Y%m%d")
    end_date = last_saturday.strftime("%Y%m%d")
    return start_date, end_date

def fetch_a_stock_history():
    indices = {
        "上证指数": "sh000001",
        "深证成指": "sz399001",
        "创业板指": "sz399006"
    }
    
    result = {}
    
    for name, symbol in indices.items():
        try:
            url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=5&datalen=10"
            response = requests.get(url, headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=10)
            data = response.json()
            
            if data and len(data) >= 2:
                first_day = data[0]
                last_day = data[-1]
                
                first_close = float(first_day["close"])
                last_close = float(last_day["close"])
                week_change = (last_close - first_close) / first_close * 100
                
                highs = [float(d["high"]) for d in data]
                lows = [float(d["low"]) for d in data]
                
                result[name] = {
                    "week_change": f"{week_change:+.2f}%",
                    "week_high": f"{max(highs):.2f}",
                    "week_low": f"{min(lows):.2f}",
                    "close": f"{last_close:.2f}",
                    "dates": len(data)
                }
        except Exception as e:
            print(f"获取{name}历史数据失败: {e}")
        
        time.sleep(0.3)
    
    return result

def fetch_us_index_history():
    indices = {
        "道琼斯": "^DJI",
        "纳斯达克": "^IXIC",
        "标普500": "^SPX"
    }
    
    start_date, end_date = get_week_date_range()
    start_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    end_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    
    result = {}
    
    for name, symbol in indices.items():
        try:
            url = f"https://stooq.com/q/d/l/?s={symbol}&d1={start_fmt.replace('-','')}&d2={end_fmt.replace('-','')}&i=d"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 and "Date" in response.text:
                lines = response.text.strip().split("\n")
                if len(lines) >= 3:
                    data = []
                    for line in lines[1:]:
                        parts = line.split(",")
                        if len(parts) >= 5:
                            data.append({
                                "close": float(parts[4]),
                                "high": float(parts[2]),
                                "low": float(parts[3])
                            })
                    
                    if len(data) >= 2:
                        first_close = data[0]["close"]
                        last_close = data[-1]["close"]
                        week_change = (last_close - first_close) / first_close * 100
                        
                        highs = [d["high"] for d in data]
                        lows = [d["low"] for d in data]
                        
                        result[name] = {
                            "week_change": f"{week_change:+.2f}%",
                            "week_high": f"{max(highs):.2f}",
                            "week_low": f"{min(lows):.2f}",
                            "close": f"{last_close:.2f}",
                            "dates": len(data)
                        }
        except Exception as e:
            print(f"获取{name}历史数据失败: {e}")
        
        time.sleep(0.3)
    
    return result

def fetch_realtime_prices():
    data = {}
    
    try:
        response = requests.get(
            "https://qt.gtimg.cn/q=hf_XAU,hf_XAG,hf_CL,hf_LCO,USINDEX",
            headers={"Referer": "https://finance.qq.com", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.encoding = "gbk"
        raw = response.text
        
        for line in raw.split("\n"):
            parts = line.split("~")
            if len(parts) > 32:
                code = parts[0].split("_")[1] if "_" in parts[0] else ""
                price = parts[3]
                change = parts[32]
                
                if code == "XAU" and price not in ["0", ""]:
                    data["黄金"] = f"${price}/盎司 ({change}%)"
                elif code == "XAG" and price not in ["0", ""]:
                    data["白银"] = f"${price}/盎司 ({change}%)"
                elif code == "CL" and price not in ["0", ""]:
                    data["WTI原油"] = f"${price}/桶 ({change}%)"
                elif code == "LCO" and price not in ["0", ""]:
                    data["布伦特原油"] = f"${price}/桶 ({change}%)"
                elif code == "USINDEX":
                    data["美元指数"] = f"{price} ({change}%)"
    except Exception as e:
        print(f"获取实时数据失败: {e}")
    
    return data

def fetch_news():
    url = "https://finance.sina.com.cn/stock/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    news_items = []
    keywords = ["A股", "美股", "股市", "政策", "美联储", "降息", "加息", "关税", "IPO", "科创板", "创业板", "AI", "芯片", "新能源", "房地产", "经济"]
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        for item in soup.select("h2 a, .news-item a")[:20]:
            title = item.get_text(strip=True)
            href = item.get("href", "")
            if title and href and "http" in href:
                for kw in keywords:
                    if kw in title:
                        news_items.append(f"• {title}\n  {href}")
                        break
    except:
        pass
    
    return "\n\n".join(news_items[:15]) if news_items else "暂无相关新闻"

def get_ai_analysis(a_week, us_week, global_data, news):
    prompt = f"""请作为资深金融市场分析师，基于以下数据生成A股和美股的周总结分析报告：

【A股本周数据】
{a_week}

【美股本周数据】
{us_week}

【大宗商品与外汇（实时）】
{global_data}

【最新财经新闻】
{news}

请生成以下分析：

一、A股市场周总结
- 本周走势回顾（涨跌幅、震幅）
- 板块轮动与热点板块
- 量能变化分析
- 北向资金动向

二、美股市场周总结
- 三大指数周表现
- 科技股与成长股
- 美联储政策影响
- 与A股联动性

三、大宗商品周总结
- 黄金白银走势
- 原油价格波动
- 美元指数变化
- 对全球市场影响

四、下周市场展望
- A股预判与操作建议
- 美股趋势判断
- 重点关注事件
- 风险提示

请用专业详尽的中文进行分析。"""

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        print("正在调用AI分析...")
        response = requests.post(url, headers=headers, json=data, timeout=180)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"AI分析生成失败: {result}"
    except Exception as e:
        return f"AI分析调用失败: {str(e)}"

def format_a_stock_data(data):
    if not data:
        return "数据获取中"
    
    lines = []
    for name, info in data.items():
        lines.append(f"{name}: 收盘{info['close']} | 周涨跌幅{info['week_change']} | 周最高{info['week_high']} | 周最低{info['week_low']} | 交易{info['dates']}天")
    return "\n".join(lines)

def format_us_data(data):
    if not data:
        return "数据获取中"
    
    lines = []
    for name, info in data.items():
        lines.append(f"{name}: 收盘{info['close']} | 周涨跌幅{info['week_change']} | 周最高{info['week_high']} | 周最低{info['week_low']} | 交易{info['dates']}天")
    return "\n".join(lines)

def send_report():
    print("获取市场数据...")
    
    start_date, end_date = get_week_date_range()
    print(f"查询周期: {start_date} 至 {end_date}")
    
    a_stock = fetch_a_stock_history()
    us_index = fetch_us_index_history()
    realtime = fetch_realtime_prices()
    news = fetch_news()
    
    a_text = format_a_stock_data(a_stock)
    us_text = format_us_data(us_index)
    global_text = "\n".join([f"{k}: {v}" for k, v in realtime.items()]) if realtime else "数据获取中"
    
    print("生成AI分析...")
    ai_analysis = get_ai_analysis(a_text, us_text, global_text, news)
    
    subject = f"A股美股周报({start_date}~{end_date}) - {datetime.now().strftime('%m-%d')}"
    
    body = f"""A股与美股周总结报告
{'='*60}
报告周期: {start_date} 至 {end_date}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

【A股本周数据】
{a_text}

【美股本周数据】
{us_text}

{'='*60}

【大宗商品与外汇（实时）】
{global_text}

{'='*60}

【AI周深度分析】
{ai_analysis}

{'='*60}

【财经新闻】
{news}

{'='*60}

【行情链接】
A股:
- 上证指数: https://finance.sina.com.cn/stock/
- 深证成指: https://finance.sina.com.cn/stock/
- 东方财富: https://data.eastmoney.com/

美股:
- 新浪财经: https://finance.sina.com.cn/stock/
- 腾讯财经: https://stockapp.finance.qq.com/mstats/search?type=USAll

大宗商品:
- 金十数据: https://www.jin10.com/
- 华尔街见闻: https://wallstreetcn.com/

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
