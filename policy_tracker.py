# -*- coding: utf-8 -*-
import requests
import smtplib
import json
import re
import time
import xml.etree.ElementTree as ET
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

LEADERS = ["吴清", "潘功胜", "郑栅洁", "蓝佛安", "廖岷", "丁向群"]
KEYWORDS = ["资本市场", "证券市场", "货币政策", "财政政策", "降息", "降准",
            "注册制", "印花税", "IPO", "再融资", "退市", "中长期资金",
            "新质生产力", "高质量发展", "金融监管", "金融稳定"]

# ============================================================
# 工具函数
# ============================================================
def safe_request(url, headers=None, timeout=15, encoding=None):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if encoding:
            r.encoding = encoding
        return r
    except Exception as e:
        print("  \u274c 请求失败: {}".format(str(e)[:60]))
        return None

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:200]

def match_leader(text):
    for leader in LEADERS:
        if leader in text:
            return leader
    return None

def match_keyword(text):
    for kw in KEYWORDS:
        if kw in text:
            return True
    return False

BROAD_FINANCE_KEYWORDS = ["股市", "金融", "经济", "改革", "开放", "投资",
                          "证券", "银行", "贷款", "利率", "汇率", "储备",
                          "风险", "监管", "稳定", "增长", "发展"]

def is_finance_related(text):
    for kw in BROAD_FINANCE_KEYWORDS:
        if kw in text:
            return True
    return False

# ============================================================
# 数据采集模块
# ============================================================

def fetch_sina_finance():
    """新浪财经新闻API（推荐首选）"""
    print("  [1/6] 新浪财经新闻...")
    news = []
    try:
        r = safe_request("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&page=1")
        if r:
            data = r.json()
            for item in data.get("result", {}).get("data", [])[:30]:
                title = item.get("title", "")
                link = item.get("url", "")
                intro = clean_html(item.get("intro", ""))
                ctime = item.get("ctime", "")
                keywords = item.get("keywords", "")
                matched = match_leader(title) or match_keyword(title + intro)
                if matched or is_finance_related(title + intro):
                    news.append({
                        "title": title, "link": link, "excerpt": intro,
                        "date": ctime, "source": "新浪财经",
                        "leader": match_leader(title) if matched else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_people_rss():
    """人民网时政RSS"""
    print("  [2/6] 人民网时政...")
    news = []
    try:
        r = safe_request("http://www.people.com.cn/rss/politics.xml")
        if r:
            root = ET.fromstring(r.content.encode('utf-8'))
            ns = {"": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//entry", ns)
            for item in items[:20]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = clean_html(item.findtext("description", ""))
                date = item.findtext("pubDate", "")[:16]
                matched = match_leader(title + desc) or match_keyword(title + desc)
                if matched or is_finance_related(title + desc):
                    news.append({
                        "title": title, "link": link, "excerpt": desc,
                        "date": date, "source": "人民网",
                        "leader": match_leader(title + desc) if matched else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_eastmoney():
    """东方财富财经新闻"""
    print("  [3/6] 东方财富...")
    news = []
    try:
        r = safe_request("https://finance.eastmoney.com/a/czqyw.html", headers={
            "User-Agent": "Mozilla/5.0"
        })
        if r:
            r.encoding = "utf-8"
            html = r.text
            items = re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', html)[:20]
            for link, title in items:
                matched = match_leader(title) or match_keyword(title)
                if matched or is_finance_related(title):
                    news.append({
                        "title": title, "link": link if link.startswith("http") else "https:" + link,
                        "excerpt": "", "date": "", "source": "东方财富",
                        "leader": match_leader(title) if matched else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_csrc():
    """证监会官网 - 要闻"""
    print("  [4/6] 证监会官网...")
    news = []
    try:
        r = safe_request("http://www.csrc.gov.cn/csrc/", headers={"User-Agent": "Mozilla/5.0"}, encoding="utf-8")
        if r:
            html = r.text
            items = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)[:15]
            for link, title in items:
                title = clean_html(title)
                if not title or len(title) < 5:
                    continue
                matched = match_leader(title) or match_keyword(title)
                if matched or is_finance_related(title):
                    full_link = link if link.startswith("http") else "http://www.csrc.gov.cn" + link
                    news.append({
                        "title": "[证监会] " + title, "link": full_link,
                        "excerpt": "", "date": "", "source": "证监会",
                        "leader": match_leader(title) if matched else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_pbc():
    """央行官网 - 货币政策"""
    print("  [5/6] 央行官网...")
    news = []
    try:
        r = safe_request("http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/index.html",
                         headers={"User-Agent": "Mozilla/5.0"})
        if r:
            r.encoding = "utf-8"
            html = r.text
            items = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)[:10]
            for link, title in items:
                title = clean_html(title)
                if not title or len(title) < 5:
                    continue
                matched = match_keyword(title) or "央行" in title or "潘功胜" in title
                if matched or is_finance_related(title):
                    full_link = link if link.startswith("http") else "http://www.pbc.gov.cn" + link
                    news.append({
                        "title": "[央行] " + title, "link": full_link,
                        "excerpt": "", "date": "", "source": "央行",
                        "leader": "潘功胜" if "潘功胜" in title else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_ndrc():
    """发改委官网"""
    print("  [6/6] 发改委官网...")
    news = []
    try:
        r = safe_request("http://www.ndrc.gov.cn/", headers={"User-Agent": "Mozilla/5.0"})
        if r:
            r.encoding = "utf-8"
            html = r.text
            items = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)[:20]
            for link, title in items:
                title = clean_html(title)
                if not title or len(title) < 5:
                    continue
                matched = match_leader(title) or match_keyword(title)
                if matched or is_finance_related(title):
                    full_link = link if link.startswith("http") else "http://www.ndrc.gov.cn" + link
                    news.append({
                        "title": "[发改委] " + title, "link": full_link,
                        "excerpt": "", "date": "", "source": "发改委",
                        "leader": match_leader(title) if matched else None
                    })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

# ============================================================
# AI分析模块
# ============================================================
def get_ai_summary(all_news):
    """DeepSeek API生成政策影响分析"""
    print("  生成AI综合分析...")

    dept_order = ["证监会", "央行", "财政部", "发改委"]
    by_dept = {d: [] for d in dept_order}
    by_dept["其他"] = []
    for n in all_news:
        src = n.get("source", "")
        if src in by_dept:
            by_dept[src].append(n)
        else:
            by_dept["其他"].append(n)

    def format_dept(dept, items):
        if not items:
            return "  无相关动态"
        text = ""
        for i, n in enumerate(items[:8], 1):
            title = n.get("title", "")
            leader = n.get("leader", "")
            leader_str = " (涉及: {})".format(leader) if leader else ""
            text += "  {}. {} {} - {}\n".format(i, title[:80], leader_str, n.get("link", ""))
        return text

    prompt = """作为资深金融政策分析师，请基于以下本周中国金融监管政策动态，生成一份综合分析报告：

【证监会】
{csrc}

【央行】
{pbc}

【财政部与发改委】
{finance}

【其他来源】
{other}

请生成以下分析（每部分3-5句话）：

一、本周政策要闻综述：概括最重要的政策信号和领导讲话要点。
二、资本市场政策分析：证监会、交易所等涉及证券市场的政策解读，重点分析对A股的影响。
三、货币政策走向：央行降准降息预期及流动性管理，对市场利率的影响。
四、财政与产业政策：财政部和发改委的政策动态，对实体经济的影响。
五、下周关注重点：关键事件提醒和政策预期。
六、投资启示：综合以上，对资本市场的影响判断。""".format(
        csrc=format_dept("证监会", by_dept["证监会"]),
        pbc=format_dept("央行", by_dept["央行"]),
        finance=format_dept("财政部", by_dept["财政部"]) + "\n" + format_dept("发改委", by_dept["发改委"]),
        other=format_dept("其他", by_dept["其他"])
    )

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2500, "temperature": 0.7}
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "AI分析暂不可用: {}".format(str(e))
    return "AI分析暂不可用"

# ============================================================
# 报告生成
# ============================================================
def generate_html_report(all_news, ai_summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    period_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    period_end = datetime.now().strftime("%Y-%m-%d")

    bg_colors = {
        "证监会": "#e3f2fd",
        "央行": "#e8f5e9",
        "财政部": "#fff3e0",
        "发改委": "#f3e5f5",
        "东方财富": "#fce4ec",
        "新浪财经": "#e0f7fa",
        "人民网": "#f1f8e9",
    }
    dept_icons = {
        "证监会": "\U0001f3e6",
        "央行": "\U0001f4b0",
        "财政部": "\U0001f4b5",
        "发改委": "\U0001f3ed",
        "新浪财经": "\U0001f4f0",
        "人民网": "\U0001f4f0",
        "东方财富": "\U0001f4f0",
    }

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 960px; margin: auto; padding: 20px; background: #f5f5f5;">
<div style="background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 25px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="margin:0;">\U0001f3db 中国金融政策动态周报</h1>
    <div style="margin-top:8px; opacity:0.9; font-size:14px;">{period_start} ~ {period_end}</div>
    <div style="margin-top:4px; opacity:0.7; font-size:12px;">证监会 · 央行 · 财政部 · 发改委 · 领导讲话 · 政策解读</div>
</div>
<div style="background: white; padding: 25px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
""".format(period_start=period_start, period_end=period_end)

    # 数据概览
    dept_count = {}
    leader_count = {}
    for n in all_news:
        src = n.get("source", "其他")
        dept_count[src] = dept_count.get(src, 0) + 1
        leader = n.get("leader")
        if leader:
            leader_count[leader] = leader_count.get(leader, 0) + 1

    leader_summary = " | ".join(["{}: {}条".format(k, v) for k, v in sorted(leader_count.items(), key=lambda x: -x[1])])
    src_summary = " | ".join(["{}: {}条".format(k, v) for k, v in sorted(dept_count.items(), key=lambda x: -x[1])])

    html += '<div style="padding:10px 15px; background:#e8eaf6; border-radius:4px; margin-bottom:15px; font-size:13px; color:#1a237e;">'
    html += '<b>\U0001f4ca 数据概览</b> 共{}条动态 | {}<br>'.format(len(all_news), src_summary)
    if leader_summary:
        html += '<b>\U0001f464 涉及领导</b> {}'.format(leader_summary)
    html += '</div>'

    # AI综合解读
    if ai_summary:
        html += '<h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ac 一、本周政策深度解读</h2>'
        html += '<div style="margin:12px 0; padding:15px; background:#f5f5f5; border-left:4px solid #1a237e; border-radius:4px; line-height:1.9; font-size:13px;">'
        for line in ai_summary.split("\n"):
            if line.strip():
                if line[0].isdigit() or line.startswith("一") or line.startswith("二") or line.startswith("三") or line.startswith("四") or line.startswith("五") or line.startswith("六"):
                    html += '<div style="margin:10px 0 4px 0; font-weight:bold;">{}</div>'.format(line.strip())
                else:
                    html += '<div style="margin:4px 0;">{}</div>'.format(line.strip())
        html += '</div><br>'

    # 按部门分类展示
    html += '<h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ca 二、政策动态详情</h2>'

    dept_order = ["证监会", "央行", "财政部", "发改委", "新浪财经", "人民网", "东方财富"]
    dept_labels = ["证监会（资本市场）", "央行（货币政策）", "财政部（财政政策）", "发改委（产业政策）", "新浪财经", "人民网时政", "东方财富"]
    dept_colors = ["#1565c0", "#2e7d32", "#e65100", "#6a1b9a", "#00838f", "#558b2f", "#c62828"]

    for idx, dept in enumerate(dept_order):
        items = [n for n in all_news if n.get("source") == dept]
        if not items:
            continue
        color = dept_colors[idx]
        label = dept_labels[idx]
        icon = dept_icons.get(dept, "")
        bg = bg_colors.get(dept, "#f5f5f5")

        html += '<h3 style="color:{}; margin:15px 0 8px 0;">{} {}（{}条）</h3>'.format(color, icon, label, len(items))
        for n in items[:8]:
            title = n.get("title", "")
            link = n.get("link", "")
            excerpt = n.get("excerpt", "")
            leader = n.get("leader", "")

            html += '<div style="margin:6px 0; padding:8px 12px; background:{}; border-left:3px solid {}; border-radius:4px;">'.format(bg, color)
            html += '<div style="font-size:13px;"><b>'
            if link:
                html += '<a href="{}" style="color:#333; text-decoration:none;" target="_blank">{}</a>'.format(link, title[:100])
            else:
                html += title[:100]
            html += '</b></div>'
            if leader:
                html += '<span style="display:inline-block; margin-top:3px; padding:1px 6px; background:#ffcdd2; border-radius:3px; font-size:11px; color:#b71c1c;">涉及: {}</span>'.format(leader)
            if excerpt:
                html += '<div style="font-size:12px; color:#666; margin-top:3px;">{}</div>'.format(excerpt)
            html += '</div>'

    # 统计信息
    html += '<br><h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ca 三、本周数据统计</h2>'
    html += '<div style="padding:15px; background:#f5f5f5; border-radius:4px;">'
    html += '<div style="display:flex; flex-wrap:wrap;">'

    for dept, count in sorted(dept_count.items(), key=lambda x: -x[1]):
        bg = bg_colors.get(dept, "#e0e0e0")
        html += '<div style="flex:1; min-width:120px; padding:12px; margin:4px; background:{}; border-radius:8px; text-align:center;">'.format(bg)
        html += '<div style="font-size:24px; font-weight:bold;">{}条</div>'.format(count)
        html += '<div style="font-size:11px; color:#666;">{}</div>'.format(dept)
        html += '</div>'

    html += '</div></div><br>'

    # 数据说明
    html += '<div style="padding:12px; background:#f5f5f5; border-radius:4px; font-size:11px; color:#999;">'
    html += '<b>\U0001f4d6 数据说明</b><br>'
    html += '\u2022 数据来源: 证监会官网、央行官网、发改委官网、新浪财经API、人民网RSS、东方财富<br>'
    html += '\u2022 覆盖领导: {}</span><br>'.format("、".join(LEADERS))
    html += '\u2022 关键词过滤: 资本市场、货币政策、降息降准、注册制、IPO、金融监管等<br>'
    html += '\u2022 报告自动生成，仅供参考，不构成投资建议'
    html += '</div>'

    # 页脚
    html += '<hr style="margin:20px 0; border:0; border-top:1px solid #ddd;">'
    html += '<div style="text-align:center; font-size:11px; color:#999;">'
    html += '报告生成: {}<br>'.format(now)
    html += '\u00a9 2026 自动化金融报告系统'
    html += '</div>'

    html += '</div></body></html>'
    return html

# ============================================================
# 主流程
# ============================================================
def send_report(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "中国金融政策动态周报 - {}".format(datetime.now().strftime("%Y-%m-%d"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL_2, msg.as_string())
        server.quit()
        print("  \u2705 发送成功!")
        return True
    except Exception as e:
        print("  \u274c 发送失败: {}".format(e))
        return False

def main():
    print("="*60)
    print("\U0001f3db 中国金融政策动态追踪系统 v1.0")
    print("="*60)
    print("报告周期: {}".format(datetime.now().strftime("%Y-%m-%d")))
    print("="*60)

    all_news = []
    all_news.extend(fetch_sina_finance())
    time.sleep(0.5)
    all_news.extend(fetch_people_rss())
    time.sleep(0.5)
    all_news.extend(fetch_eastmoney())
    time.sleep(0.5)
    all_news.extend(fetch_csrc())
    time.sleep(0.5)
    all_news.extend(fetch_pbc())
    time.sleep(0.5)
    all_news.extend(fetch_ndrc())

    # 去重（按标题去重）
    seen = set()
    unique_news = []
    for n in all_news:
        title = n.get("title", "")
        if title not in seen:
            seen.add(title)
            unique_news.append(n)
    all_news = unique_news

    print("\n\u2705 共获取 {} 条政策动态".format(len(all_news)))

    if not all_news:
        print("\u274c 无数据，终止")
        return

    print("生成AI综合分析...")
    ai_summary = get_ai_summary(all_news)

    print("生成报告...")
    html = generate_html_report(all_news, ai_summary)

    print("发送邮件...")
    send_report(html)

    print("\n\u2705 完成!")

if __name__ == "__main__":
    main()
