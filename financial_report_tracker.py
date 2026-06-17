# -*- coding: utf-8 -*-
import requests
import smtplib
import json
import math
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ============================================================
# 配置
# ============================================================
SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "1294265055@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

FINANCIAL_INDUSTRIES = ["银行", "保险", "证券", "多元金融"]

# ============================================================
# 工具函数
# ============================================================
def curl_get(url):
    r = requests.get(url, headers={
        "Referer": "https://quote.eastmoney.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }, timeout=15)
    text = r.text
    if text.startswith("jQuery"):
        text = text[text.index("(")+1:text.rindex(")")]
    return json.loads(text)

def format_wan(val):
    if val is None or val == 0:
        return "N/A"
    return "{:.2f}亿".format(val / 1e8)

def format_pct(val):
    if val is None:
        return "N/A"
    v = float(val)
    return "{:.2f}%".format(v)

def format_num(val, decimals=2):
    if val is None or val == 0:
        return "N/A"
    return "{:.{}f}".format(float(val), decimals)

def safe_float(val, default=0):
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except:
        return default

# ============================================================
# 一、数据获取层
# ============================================================
def fetch_all_stocks():
    print("[1/6] 获取全A股财报数据...")
    url = ("https://push2.eastmoney.com/api/qt/clist/get"
           "?pn=1&pz=5000&po=1&np=1"
           "&ut=bd1d9ddb04089700cf9c27f6f7426281"
           "&fltt=2&invt=2&fid=f46"
           "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
           "&fields=f2,f9,f12,f14,f20,f23,f37,f45,f46,f48,f50,f57,f69,f75,f85,f100,f115")
    try:
        data = curl_get(url)
        stocks = data.get("data", {}).get("diff", [])
        print("  成功获取 {} 只股票数据".format(len(stocks)))
        return stocks
    except Exception as e:
        print("  获取失败: {}".format(e))
        return []

# ============================================================
# 二、数据分类与排名
# ============================================================
def classify_stocks(stocks):
    print("[2/6] 数据分类...")
    financial = []
    non_financial = []
    for s in stocks:
        industry = s.get("f100", "")
        if industry in FINANCIAL_INDUSTRIES:
            financial.append(s)
        else:
            non_financial.append(s)
    print("  非金融 {} 只 | 金融 {} 只".format(len(non_financial), len(financial)))
    return non_financial, financial

def calc_composite_score(s):
    np_yoy = min(safe_float(s.get("f46", 0)), 500)
    rev_yoy = max(min(safe_float(s.get("f57", 0)), 500), -100)
    roe = max(min(safe_float(s.get("f75", 0)), 100), -100)
    eps = max(safe_float(s.get("f48", 0)), 0)
    mcap = safe_float(s.get("f20", 0))
    mcap_score = min(math.log(mcap / 1e8 + 1) / 5, 1) if mcap > 0 else 0
    return np_yoy * 0.4 + rev_yoy * 0.2 + roe * 0.2 + eps * 0.1 + mcap_score * 10

def get_top_20(stocks):
    sorted_stocks = sorted(stocks, key=calc_composite_score, reverse=True)
    return sorted_stocks[:20]

def get_bottom_10(stocks):
    sorted_stocks = sorted(stocks, key=lambda s: safe_float(s.get("f46", 0)))
    return sorted_stocks[:10]

def get_financial_top(financial):
    sorted_stocks = sorted(financial, key=calc_composite_score, reverse=True)
    return sorted_stocks[:10]

def get_report_period():
    month = datetime.now().month
    year = datetime.now().year
    if 1 <= month <= 4:
        return "{}年年报 + {}年一季报".format(year-1, year)
    elif 5 <= month <= 8:
        return "{}年半年报".format(year)
    elif 9 <= month <= 10:
        return "{}年三季报".format(year)
    else:
        return "{}年年报（预告）".format(year)

# ============================================================
# 三、特殊事项公告获取
# ============================================================
def fetch_special_announcements(stock_codes):
    print("[4/6] 获取特殊事项公告... {} 只股票".format(len(stock_codes)))
    result = {
        "common": {"title": "定增/再融资", "items": []},
        "lawsuit": {"title": "诉讼仲裁", "items": []},
        "pledge": {"title": "股权质押/担保", "items": []},
        "related": {"title": "关联交易", "items": []},
        "risk": {"title": "风险提示/ST", "items": []},
        "restruct": {"title": "资产重组", "items": []}
    }
    category_map = {
        "common": ("1", "010004"),
        "lawsuit": ("1", "010101"),
        "pledge": ("1", "010005"),
        "related": ("1", "010006"),
        "risk": ("4", "0"),
        "restruct": ("5", "0")
    }
    since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    total = 0
    for code in stock_codes[:30]:
        time.sleep(0.3)
        for key, (f_node, s_node) in category_map.items():
            url = ("https://np-anotice-stock.eastmoney.com/api/security/ann"
                   "?sr=-1&page_size=3&page_index=1&ann_type=A"
                   "&stock_list={}&f_node={}&s_node={}&client_source=web"
                   .format(code, f_node, s_node))
            try:
                data = curl_get(url)
                items = data.get("data", {}).get("list", [])
                for item in items:
                    title = item.get("title_ch", "")
                    notice_date = item.get("display_time", "")[:10]
                    if notice_date >= since_date:
                        result[key]["items"].append("[{}] {}".format(notice_date[:10], title))
                        total += 1
            except:
                pass
    for key in result:
        result[key]["items"] = result[key]["items"][:5]
    print("  共获取 {} 条特殊事项公告".format(total))
    return result

# ============================================================
# 四、报告生成层
# ============================================================
def generate_html_report(top_20, bottom_10, financial_top, special_events):
    period = get_report_period()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 960px; margin: auto; padding: 20px; background: #f5f7fa;">
<div style="background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%); color: white; padding: 25px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="margin:0;">\U0001f4ca 上市公司财报业绩跟踪分析报告</h1>
    <div style="margin-top:8px; opacity:0.9; font-size:14px;">报告期间: {period} | 数据截至: {now}</div>
</div>
<div style="background: white; padding: 25px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
""".format(period=period, now=now)

    # TOP 20
    html += '<h2 style="color:#27ae60; border-bottom:2px solid #27ae60; padding-bottom:6px;">\U0001f4c8 一、业绩TOP 20排行榜（非金融类）</h2>'
    html += '<table style="width:100%; border-collapse:collapse; font-size:12px; margin:10px 0;">'
    html += '<tr style="background:#1a5276; color:white; font-weight:bold; text-align:center;">'
    for h in ["#", "名称", "营收(亿)", "营收%", "净利(亿)", "净利%", "EPS", "ROE", "PE-TTM", "PE-静态", "毛利率", "PB", "市值(亿)", "行业"]:
        html += "<td style='padding:8px 4px;'>{}</td>".format(h)
    html += '</tr>'
    for i, s in enumerate(top_20[:20], 1):
        bg = "#f6fdf6" if i % 2 == 0 else "#ffffff"
        np_yoy = safe_float(s.get("f46", 0))
        np_color = "color:red;" if np_yoy < 0 else "color:green;"
        html += '<tr style="background:{}; text-align:center;">'.format(bg)
        html += "<td style='padding:6px 4px;'><b>{}</b></td>".format(i)
        html += "<td style='padding:6px 4px;'><b>{}</b><br><small style='color:#999;'>{}</small></td>".format(
            s.get("f14", ""), s.get("f12", ""))
        html += "<td>{}</td>".format(format_wan(s.get("f50", 0)))
        html += "<td style='{}'>{}</td>".format(np_color, format_pct(s.get("f57", 0)))
        html += "<td>{}</td>".format(format_wan(s.get("f45", 0)))
        html += "<td style='{}'><b>{}</b></td>".format(np_color, format_pct(s.get("f46", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f48", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f75", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f9", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f115", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f69", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f23", 0)))
        html += "<td>{}</td>".format(format_wan(s.get("f20", 0)))
        html += "<td>{}</td>".format(s.get("f100", ""))
        html += '</tr>'
    html += '</table><br>'

    # BOTTOM 10
    html += '<h2 style="color:#e74c3c; border-bottom:2px solid #e74c3c; padding-bottom:6px;">\u26a0\ufe0f 二、业绩BOTTOM 10排行榜</h2>'
    html += '<table style="width:100%; border-collapse:collapse; font-size:12px; margin:10px 0;">'
    html += '<tr style="background:#c0392b; color:white; font-weight:bold; text-align:center;">'
    for h in ["#", "名称", "营收(亿)", "营收%", "净利(亿)", "净利%", "EPS", "ROE", "PE-TTM", "行业"]:
        html += "<td style='padding:8px 4px;'>{}</td>".format(h)
    html += '</tr>'
    for i, s in enumerate(bottom_10[:10], 1):
        bg = "#fff5f5" if i % 2 == 0 else "#ffffff"
        html += '<tr style="background:{}; text-align:center;">'.format(bg)
        html += "<td style='padding:6px 4px;'><b>{}</b></td>".format(i)
        html += "<td><b>{}</b><br><small style='color:#999;'>{}</small></td>".format(s.get("f14",""), s.get("f12",""))
        html += "<td>{}</td>".format(format_wan(s.get("f50", 0)))
        html += "<td style='color:#c0392b;'>{}</td>".format(format_pct(s.get("f57", 0)))
        html += "<td>{}</td>".format(format_wan(s.get("f45", 0)))
        html += "<td style='color:#c0392b;'><b>{}</b></td>".format(format_pct(s.get("f46", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f48", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f75", 0)))
        html += "<td>{}</td>".format(format_num(s.get("f9", 0)))
        html += "<td>{}</td>".format(s.get("f100", ""))
        html += '</tr>'
    html += '</table><br>'

    # 金融类 TOP 10
    if financial_top:
        html += '<h2 style="color:#2980b9; border-bottom:2px solid #2980b9; padding-bottom:6px;">\U0001f3e6 三、金融类业绩TOP 10</h2>'
        html += '<table style="width:100%; border-collapse:collapse; font-size:12px; margin:10px 0;">'
        html += '<tr style="background:#2980b9; color:white; font-weight:bold; text-align:center;">'
        for h in ["#", "名称", "净利(亿)", "净利%", "营收%", "EPS", "ROE", "PE-TTM", "PB", "行业"]:
            html += "<td style='padding:8px 4px;'>{}</td>".format(h)
        html += '</tr>'
        for i, s in enumerate(financial_top[:10], 1):
            bg = "#f0f9ff" if i % 2 == 0 else "#ffffff"
            html += '<tr style="background:{}; text-align:center;">'.format(bg)
            html += "<td style='padding:6px 4px;'><b>{}</b></td>".format(i)
            html += "<td><b>{}</b><br><small style='color:#999;'>{}</small></td>".format(s.get("f14",""), s.get("f12",""))
            html += "<td>{}</td>".format(format_wan(s.get("f45", 0)))
            html += "<td style='{}'>{}</td>".format("color:green;" if safe_float(s.get("f46",0))>=0 else "color:red;", format_pct(s.get("f46",0)))
            html += "<td>{}</td>".format(format_pct(s.get("f57", 0)))
            html += "<td>{}</td>".format(format_num(s.get("f48", 0)))
            html += "<td>{}</td>".format(format_num(s.get("f75", 0)))
            html += "<td>{}</td>".format(format_num(s.get("f9", 0)))
            html += "<td>{}</td>".format(format_num(s.get("f23", 0)))
            html += "<td>{}</td>".format(s.get("f100", ""))
            html += '</tr>'
        html += '</table><br>'

    # 特殊事项
    html += '<h2 style="color:#e67e22; border-bottom:2px solid #e67e22; padding-bottom:6px;">\U0001f514 四、特殊事项通告</h2>'
    icon_map = {"定增/再融资": "\U0001f4cc", "诉讼仲裁": "\u2696\ufe0f", "股权质押/担保": "\U0001f512",
                "关联交易": "\U0001f504", "风险提示/ST": "\u26a0\ufe0f", "资产重组": "\U0001f3d7\ufe0f"}
    any_items = False
    for key, data in special_events.items():
        if data["items"]:
            any_items = True
            icon = icon_map.get(data["title"], "")
            html += '<div style="margin:10px 0; padding:12px; background:#fffbe6; border-left:5px solid #e67e22; border-radius:4px;">'
            html += '<b style="font-size:14px;">{} {} ({})</b><br>'.format(icon, data["title"], len(data["items"]))
            for item in data["items"]:
                html += '<div style="margin:4px 0; padding:4px 0; border-bottom:1px dashed #eee; font-size:12px;">\u2022 {}</div>'.format(item)
            html += '</div>'
    if not any_items:
        html += '<div style="padding:12px; background:#eef; border-radius:4px;">近30天无特殊事项公告</div>'
    else:
        html += '<div style="margin-top:8px; font-size:11px; color:#999;">以上仅列出TOP 20和BOTTOM 10股票近30天公告</div>'
    html += '<br>'

    # 行业集中度
    industry_count = {}
    for s in top_20[:20]:
        ind = s.get("f100", "未知")
        industry_count[ind] = industry_count.get(ind, 0) + 1
    sorted_industries = sorted(industry_count.items(), key=lambda x: x[1], reverse=True)
    html += '<h2 style="color:#8e44ad; border-bottom:2px solid #8e44ad; padding-bottom:6px;">\U0001f4ca 五、行业集中度分析</h2>'
    html += '<div style="padding:12px; background:#f9f0ff; border-radius:4px;">'
    html += '<b>TOP 20行业分布：</b><br>'
    for ind, cnt in sorted_industries:
        bar_width = cnt * 20
        html += '<div style="margin:4px 0; font-size:13px;">{}（{}家）：</div>'.format(ind, cnt)
        html += '<div style="background:#eee; height:18px; border-radius:4px; margin:2px 0 8px 0;">'
        html += '<div style="background:#8e44ad; height:18px; border-radius:4px; width:{}px; text-align:center; color:white; font-size:11px; line-height:18px;"></div>'.format(bar_width)
        html += '</div>'
    html += '</div>'

    return html

# ============================================================
# 五、AI深度分析
# ============================================================
def get_ai_analysis(top_20, bottom_10, financial_top, special_events):
    print("[5/6] 生成AI分析...")
    top_summary = ""
    for i, s in enumerate(top_20[:10], 1):
        top_summary += "{}. {} 营收{} 净利同比{} ROE{} 行业{}\n".format(
            i, s.get("f14",""), format_pct(s.get("f57",0)), format_pct(s.get("f46",0)),
            format_pct(s.get("f75",0)), s.get("f100",""))
    bottom_summary = ""
    for i, s in enumerate(bottom_10[:5], 1):
        bottom_summary += "{}. {} 营收{} 净利同比{} 行业{}\n".format(
            i, s.get("f14",""), format_pct(s.get("f57",0)), format_pct(s.get("f46",0)), s.get("f100",""))
    fin_summary = ""
    for i, s in enumerate(financial_top[:5], 1):
        fin_summary += "{}. {} 净利同比{} ROE{}\n".format(i, s.get("f14",""), format_pct(s.get("f46",0)), format_pct(s.get("f75",0)))
    special_summary = ""
    for key, data in special_events.items():
        if data["items"]:
            special_summary += "{}类{}条: {}\n".format(data["title"], len(data["items"]), data["items"][0][:50] if data["items"] else "")

    prompt = """作为资深A股财报分析师，请基于以下数据生成一份综合分析报告：

【业绩TOP 10（非金融类）】
{top_summary}

【业绩BOTTOM 5（非金融类）】
{bottom_summary}

【金融类TOP 5】
{fin_summary}

【最近30天特殊事项汇总】
{special_summary}

请输出以下四个部分，每部分3-5句话：

一、TOP 20整体特征：总结增长最快的公司的共同特征、行业分布、增长驱动因素。
二、BOTTOM 10风险提示：分析业绩最差公司的共性问题和潜在风险。
三、特殊事项影响：分析定增、诉讼、质押等事件对相关公司的影响。
四、投资建议：基于以上分析给出关注方向和建议。""".format(
        top_summary=top_summary, bottom_summary=bottom_summary,
        fin_summary=fin_summary, special_summary=special_summary)

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.7}
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            text = result["choices"][0]["message"]["content"]
            sections = text.split("\n")
            html = '<h2 style="color:#2c3e50; border-bottom:2px solid #2c3e50; padding-bottom:6px;">\U0001f50d 六、AI深度分析</h2>'
            current_section = ""
            for line in sections:
                if line.startswith("一、") or line.startswith("二、") or line.startswith("三、") or line.startswith("四、"):
                    if current_section:
                        html += '<div style="margin:12px 0; padding:12px; background:#f8f9fa; border-left:4px solid #2c3e50; border-radius:4px;">'
                        html += '<b style="font-size:14px;">{}</b><br>'.format(current_title)
                        html += '<div style="font-size:13px; line-height:1.8;">{}</div>'.format(current_content)
                        html += '</div>'
                    current_title = line
                    current_content = ""
                else:
                    if line.strip():
                        current_content += line.strip() + "<br>"
            if current_content:
                html += '<div style="margin:12px 0; padding:12px; background:#f8f9fa; border-left:4px solid #2c3e50; border-radius:4px;">'
                html += '<b style="font-size:14px;">{}</b><br>'.format(current_title)
                html += '<div style="font-size:13px; line-height:1.8;">{}</div>'.format(current_content)
                html += '</div>'
            return html
    except Exception as e:
        return '<h2 style="color:#2c3e50;">\U0001f50d AI深度分析</h2><div style="padding:12px; background:#fff3cd; border-radius:4px;">AI分析暂不可用: {}</div>'.format(str(e))

# ============================================================
# 六、邮件发送
# ============================================================
def send_report(html_body, ai_html):
    print("[6/6] 发送邮件...")
    body = """<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{} {} </body></html>""".format(html_body, ai_html)
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    period = get_report_period()
    msg["Subject"] = "上市公司财报业绩跟踪分析报告 - {} - {}".format(period, datetime.now().strftime("%Y-%m-%d"))
    msg.attach(MIMEText(body, "html", "utf-8"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL_2, msg.as_string())
        server.quit()
        print("  \u2705 发送成功! 收件人: {}, {}".format(RECEIVER_EMAIL, RECEIVER_EMAIL_2))
        return True
    except Exception as e:
        print("  \u274c 发送失败: {}".format(e))
        return False

# ============================================================
# 七、主流程
# ============================================================
def main():
    print("上市公司财报业绩跟踪分析系统 v1.0")
    print("="*60)
    period = get_report_period()
    print("报告期间: {}".format(period))
    print("数据截至: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("="*60)

    all_stocks = fetch_all_stocks()
    if not all_stocks:
        print("\u274c 数据获取失败，终止")
        return

    non_financial, financial = classify_stocks(all_stocks)

    print("[3/6] 综合评分排名...")
    top_20 = get_top_20(non_financial)
    bottom_10 = get_bottom_10(non_financial)
    financial_top = get_financial_top(financial)
    if top_20:
        print("  TOP 1: {} 综合评分 {:.1f}".format(top_20[0].get("f14",""), calc_composite_score(top_20[0])))
    if bottom_10:
        print("  BOTTOM 1: {} 净利同比 {}".format(bottom_10[0].get("f14",""), format_pct(bottom_10[0].get("f46",0))))

    all_codes = [s.get("f12","") for s in (top_20 + bottom_10) if s.get("f12")]
    special_events = fetch_special_announcements(all_codes)

    print("[5/6] 生成报告...")
    html_body = generate_html_report(top_20, bottom_10, financial_top, special_events)
    ai_html = get_ai_analysis(top_20, bottom_10, financial_top, special_events)
    print("  报告生成完成")

    send_report(html_body, ai_html)

if __name__ == "__main__":
    main()
