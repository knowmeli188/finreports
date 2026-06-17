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

LEADERS = ["吴清", "潘功胜", "郑栅洁", "蓝佛安", "廖岷", "丁向群",
           "易会满", "郭树清", "刘鹤", "何立峰", "李强", "习近平",
           "刘昆", "易纲", "刘士余", "王建军"]

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

def ts_to_date(ts):
    try:
        ts_int = int(str(ts)[:10])
        return datetime.fromtimestamp(ts_int).strftime("%Y-%m-%d")
    except:
        return ""

# ============================================================
# 数据采集模块
# ============================================================

def fetch_sina_finance():
    print("  [1/9] 新浪财经新闻...")
    news = []
    urls = [
        "http://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&page=1",
        "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&page=1"
    ]
    for url in urls:
        r = safe_request(url)
        if r:
            try:
                data = r.json()
                for item in data.get("result", {}).get("data", [])[:50]:
                    news.append({
                        "title": item.get("title", ""), "link": item.get("url", ""),
                        "excerpt": clean_html(item.get("intro", "")),
                        "date": item.get("ctime", ""), "source": "新浪财经",
                        "leader": match_leader(item.get("title", ""))
                    })
                break
            except:
                continue
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_wallstreetcn():
    print("  [2/9] 华尔街见闻快讯...")
    news = []
    try:
        r = safe_request("https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30")
        if r:
            data = r.json()
            for item in data.get("data", {}).get("items", [])[:30]:
                title = item.get("title", "") or ""
                content = item.get("content_text", "") or ""
                display_time = ts_to_date(item.get("display_time", 0))
                news.append({
                    "title": title or content[:60], "link": "",
                    "excerpt": content[:200], "date": display_time,
                    "source": "华尔街见闻", "leader": match_leader(title + content)
                })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_yicai():
    print("  [3/9] 第一财经...")
    news = []
    try:
        r = safe_request("https://www.yicai.com/api/ajax/getlatest?type=1&page=1&pagesize=15")
        if r:
            for item in r.json()[:15]:
                news.append({
                    "title": item.get("NewsTitle", ""),
                    "link": "https://www.yicai.com/news/" + str(item.get("NewsID", "")),
                    "excerpt": clean_html(item.get("NewsNotes", "")),
                    "date": str(item.get("CreateDate", ""))[:10],
                    "source": "第一财经", "leader": match_leader(item.get("NewsTitle", ""))
                })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_people_rss():
    print("  [4/9] 人民网时政...")
    news = []
    try:
        r = safe_request("http://www.people.com.cn/rss/politics.xml")
        if r:
            root = ET.fromstring(r.content.encode('utf-8'))
            for item in root.findall(".//item")[:25]:
                title = item.findtext("title", "")
                desc = clean_html(item.findtext("description", ""))
                news.append({
                    "title": title, "link": item.findtext("link", ""),
                    "excerpt": desc, "date": str(item.findtext("pubDate", ""))[:16],
                    "source": "人民网", "leader": match_leader(title + desc)
                })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_eastmoney():
    print("  [5/9] 东方财富...")
    news = []
    try:
        r = safe_request("https://finance.eastmoney.com/a/czqyw.html", headers={"User-Agent": "Mozilla/5.0"})
        if r:
            r.encoding = "utf-8"
            for link, title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', r.text)[:30]:
                news.append({
                    "title": title, "link": link if link.startswith("http") else "https:" + link,
                    "excerpt": "", "date": "", "source": "东方财富", "leader": match_leader(title)
                })
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_csrc():
    print("  [6/9] 证监会官网...")
    news = []
    for base_url in ["http://www.csrc.gov.cn/csrc/", "http://www.csrc.gov.cn/pub/newsite/"]:
        try:
            r = safe_request(base_url, headers={"User-Agent": "Mozilla/5.0"}, encoding="utf-8")
            if r:
                for link, title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r.text)[:20]:
                    title = clean_html(title)
                    if len(title) < 5: continue
                    full_link = link if link.startswith("http") else "http://www.csrc.gov.cn" + ("/" if not link.startswith("/") else "") + link.lstrip("/")
                    news.append({"title": "[证监会] " + title, "link": full_link, "excerpt": "", "date": "", "source": "证监会", "leader": match_leader(title)})
                if news: break
        except: continue
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_pbc():
    print("  [7/9] 央行官网...")
    news = []
    for url in ["http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/index.html", "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html"]:
        try:
            r = safe_request(url, headers={"User-Agent": "Mozilla/5.0"})
            if r:
                r.encoding = "utf-8"
                for link, title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r.text)[:15]:
                    title = clean_html(title)
                    if len(title) < 5: continue
                    full_link = link if link.startswith("http") else "http://www.pbc.gov.cn" + link
                    news.append({"title": "[央行] " + title, "link": full_link, "excerpt": "", "date": "", "source": "央行", "leader": "潘功胜" if "潘功胜" in title else None})
                if news: break
        except: continue
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_ndrc():
    print("  [8/9] 发改委官网...")
    news = []
    try:
        r = safe_request("http://www.ndrc.gov.cn/xwdt/", headers={"User-Agent": "Mozilla/5.0"})
        if r:
            r.encoding = "utf-8"
            for link, title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r.text)[:20]:
                title = clean_html(title)
                if len(title) < 5: continue
                full_link = link if link.startswith("http") else "http://www.ndrc.gov.cn" + link
                news.append({"title": "[发改委] " + title, "link": full_link, "excerpt": "", "date": "", "source": "发改委", "leader": match_leader(title)})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    print("    \u2705 {} 条".format(len(news)))
    return news

def fetch_economic_calendar():
    print("  [9/9] 经济数据日历...")
    events = []
    try:
        # 每经网财经日历
        r = safe_request("https://www.nbd.com.cn/", headers={"User-Agent": "Mozilla/5.0"})
        if r:
            r.encoding = "utf-8"
            for link, title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', r.text)[:30]:
                title = clean_html(title)
                if len(title) < 5: continue
                if any(kw in title for kw in ["数据", "发布", "公布", "会议", "讲话", "报告", "指数", "CPI", "PMI", "GDP"]):
                    events.append({"title": title, "link": link if link.startswith("http") else "https:" + link, "source": "每经日历"})
    except:
        pass
    print("    \u2705 {} 条日历事件".format(len(events)))
    return events

# ============================================================
# AI分析模块
# ============================================================
def get_ai_summary(all_news, economic_calendar):
    print("  生成AI综合分析...")
    by_dept = {}
    for n in all_news:
        src = n.get("source", "其他")
        by_dept.setdefault(src, []).append(n)

    def fmt(items):
        if not items: return "  无相关动态"
        return "\n".join(["  {}. {} - {}".format(i, n.get("title", "")[:80], n.get("link", "")) for i, n in enumerate(items[:8], 1)])

    cal_text = "\n".join(["  - {} ({})".format(e["title"], e["source"]) for e in economic_calendar[:8]]) if economic_calendar else "  暂无数据"

    prompt = """作为资深金融政策分析师，请基于以下本周动态生成一份综合分析报告：

【证监会/资本市场】
{csrc}

【央行/货币政策】
{pbc}

【发改委/产业政策】
{ndrc}

【财经媒体动态】
{media}

【下周经济数据日历】
{calendar}

请生成以下六部分分析（每部分3-5句话）：

一、本周政策要闻综述：概括最重要的政策信号和领导讲话要点。
二、资本市场政策分析：证监会涉及证券市场的政策解读，重点分析对A股的影响。
三、货币政策走向：央行降准降息预期及流动性管理。
四、产业与财政政策：发改委和财政部的最新政策动态。
五、下周关注重点：基于经济数据日历的关键事件提醒。
六、投资启示：综合以上，对资本市场的影响判断。""".format(
        csrc=fmt(by_dept.get("证监会", []) + by_dept.get("东方财富", [])),
        pbc=fmt(by_dept.get("央行", [])),
        ndrc=fmt(by_dept.get("发改委", [])),
        media=fmt(by_dept.get("新浪财经", []) + by_dept.get("华尔街见闻", []) + by_dept.get("第一财经", []) + by_dept.get("人民网", [])),
        calendar=cal_text
    )

    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2500, "temperature": 0.7},
            timeout=120)
        result = r.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "AI分析暂不可用: {}".format(str(e))
    return "AI分析暂不可用"

# ============================================================
# 报告生成
# ============================================================
def generate_html_report(all_news, ai_summary, economic_calendar):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    period_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    period_end = datetime.now().strftime("%Y-%m-%d")

    bg_colors = {"证监会": "#e3f2fd", "央行": "#e8f5e9", "发改委": "#f3e5f5",
                 "新浪财经": "#e0f7fa", "人民网": "#f1f8e9", "东方财富": "#fce4ec",
                 "华尔街见闻": "#fff8e1", "第一财经": "#e0f2f1"}
    dept_icons = {"证监会": "\U0001f3e6", "央行": "\U0001f4b0", "发改委": "\U0001f3ed",
                  "新浪财经": "\U0001f4f0", "人民网": "\U0001f4f0", "东方财富": "\U0001f4f0",
                  "华尔街见闻": "\u26a1", "第一财经": "\U0001f4ca"}
    dept_labels = {"证监会": "证监会（资本市场）", "央行": "央行（货币政策）", "发改委": "发改委（产业政策）",
                   "新浪财经": "新浪财经", "人民网": "人民网时政", "东方财富": "东方财富",
                   "华尔街见闻": "华尔街见闻快讯", "第一财经": "第一财经"}
    dept_colors = {"证监会": "#1565c0", "央行": "#2e7d32", "发改委": "#6a1b9a",
                   "新浪财经": "#00838f", "人民网": "#558b2f", "东方财富": "#c62828",
                   "华尔街见闻": "#e65100", "第一财经": "#004d40"}

    dept_count = {}
    leader_count = {}
    for n in all_news:
        src = n.get("source", "其他")
        dept_count[src] = dept_count.get(src, 0) + 1
        ldr = n.get("leader")
        if ldr: leader_count[ldr] = leader_count.get(ldr, 0) + 1
    leader_summary = " | ".join(["{}: {}条".format(k, v) for k, v in sorted(leader_count.items(), key=lambda x: -x[1])])
    src_summary = " | ".join(["{}: {}条".format(k, v) for k, v in sorted(dept_count.items(), key=lambda x: -x[1])])
    total = len(all_news)

    # 构建索引目录
    index_items = []
    index_items.append("\U0001f4ac AI综合解读")
    if dept_count:
        by_dept_sorted = sorted(dept_count.items(), key=lambda x: -x[1])
        for d, c in by_dept_sorted[:6]:
            label = dept_labels.get(d, d)
            index_items.append("{} {}（{}条）".format(dept_icons.get(d, "\U0001f4cb"), label, c))
    index_items.append("\U0001f4c5 下周经济数据日历")
    index_items.append("\U0001f4ca 本周数据统计")
    index_html = " · ".join(index_items)

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 980px; margin: auto; padding: 20px; background: #f5f5f5;">
<div style="background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 25px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="margin:0;">\U0001f3db 中国金融政策动态周报</h1>
    <div style="margin-top:8px; opacity:0.9; font-size:14px;">{period_start} ~ {period_end} | 共{total}条动态</div>
    <div style="margin-top:4px; opacity:0.7; font-size:12px;">{index_html}</div>
</div>
<div style="background: white; padding: 25px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
""".format(period_start=period_start, period_end=period_end, total=total, index_html=index_html)

    # AI综合解读
    if ai_summary:
        html += '<h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ac 一、本周政策深度解读</h2>'
        html += '<div style="margin:12px 0; padding:15px; background:#f5f5f5; border-left:4px solid #1a237e; border-radius:4px; line-height:1.9; font-size:13px;">'
        for line in ai_summary.split("\n"):
            line = line.strip()
            if not line: continue
            if re.match(r'^[一二三四五六]、', line) or re.match(r'^\d+[\.\、]', line):
                html += '<div style="margin:10px 0 4px 0; font-weight:bold; color:#1a237e;">{}</div>'.format(line)
            else:
                html += '<div style="margin:4px 0;">{}</div>'.format(line)
        html += '</div><br>'

    # 政策动态详情
    html += '<h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ca 二、政策动态详情</h2>'
    displayed = set()
    for dept in ["证监会", "央行", "发改委", "新浪财经", "华尔街见闻", "第一财经", "人民网", "东方财富"]:
        items = [n for n in all_news if n.get("source") == dept]
        if not items: continue
        color = dept_colors.get(dept, "#333")
        label = dept_labels.get(dept, dept)
        icon = dept_icons.get(dept, "")
        bg = bg_colors.get(dept, "#f5f5f5")
        html += '<h3 style="color:{}; margin:15px 0 8px 0;">{} {}（{}条）</h3>'.format(color, icon, label, len(items))
        for n in items[:8]:
            title = n.get("title", "")
            link = n.get("link", "")
            excerpt = n.get("excerpt", "")
            leader = n.get("leader", "")
            if title in displayed: continue
            displayed.add(title)
            html += '<div style="margin:6px 0; padding:8px 12px; background:{}; border-left:3px solid {}; border-radius:4px;">'.format(bg, color)
            html += '<div style="font-size:13px;"><b>'
            if link: html += '<a href="{}" style="color:#333; text-decoration:none;" target="_blank">{}</a>'.format(link, title[:100])
            else: html += title[:100]
            html += '</b></div>'
            if leader: html += '<span style="display:inline-block; margin-top:3px; padding:1px 6px; background:#ffcdd2; border-radius:3px; font-size:11px; color:#b71c1c;">涉及: {}</span>'.format(leader)
            if excerpt: html += '<div style="font-size:12px; color:#666; margin-top:3px;">{}</div>'.format(excerpt)
            html += '</div>'

    # 下周经济数据日历
    html += '<br><h2 style="color:#e65100; border-bottom:2px solid #e65100; padding-bottom:6px;">\U0001f4c5 三、下周经济数据日历</h2>'
    if economic_calendar:
        for e in economic_calendar[:10]:
            html += '<div style="margin:4px 0; padding:6px 12px; background:#fff8e1; border-left:3px solid #e65100; border-radius:4px; font-size:12px;">'
            html += '\u2022 {}'.format(e["title"])
            if e.get("link"): html += ' <a href="{}" style="color:#1565c0; font-size:11px;" target="_blank">[详情]</a>'.format(e["link"])
            html += '</div>'
    else:
        html += '<div style="padding:10px; background:#f5f5f5; border-radius:4px; font-size:12px; color:#999;">暂无下周经济数据日历</div>'
    html += '<br>'

    # 本周数据统计
    html += '<h2 style="color:#1a237e; border-bottom:2px solid #1a237e; padding-bottom:6px;">\U0001f4ca 四、本周数据统计</h2>'
    html += '<div style="padding:15px; background:#f5f5f5; border-radius:4px;">'
    html += '<div style="display:flex; flex-wrap:wrap;">'
    for dept, count in sorted(dept_count.items(), key=lambda x: -x[1]):
        html += '<div style="flex:1; min-width:110px; padding:10px; margin:3px; background:{}; border-radius:8px; text-align:center;">'.format(bg_colors.get(dept, "#e0e0e0"))
        html += '<div style="font-size:20px; font-weight:bold;">{}条</div>'.format(count)
        html += '<div style="font-size:10px; color:#666;">{}</div>'.format(dept)
        html += '</div>'
    if leader_count:
        html += '</div><div style="margin-top:10px; font-size:12px;">\U0001f464 涉及领导: '
        html += " ".join(['<span style="display:inline-block; margin:2px; padding:2px 8px; background:#ffcdd2; border-radius:10px; font-size:11px;">{}: {}条</span>'.format(k,v) for k,v in sorted(leader_count.items(), key=lambda x: -x[1])])
        html += '</div>'
    html += '</div><br>'

    # 数据说明
    html += '<div style="padding:12px; background:#f5f5f5; border-radius:4px; font-size:11px; color:#999;">'
    html += '<b>\U0001f4d6 数据说明</b><br>'
    html += '\u2022 数据来源: 新浪财经API、华尔街见闻API、第一财经API、人民网RSS、东方财富、证监会官网、央行官网、发改委官网、每经网日历<br>'
    html += '\u2022 覆盖领导: {}</span><br>'.format("、".join(LEADERS))
    html += '\u2022 经济数据日历来自公开财经信息，具体发布以官方通知为准<br>'
    html += '\u2022 报告自动生成，仅供参考，不构成投资建议'
    html += '</div>'

    html += '<hr style="margin:20px 0; border:0; border-top:1px solid #ddd;">'
    html += '<div style="text-align:center; font-size:11px; color:#999;">报告生成: {}<br>\u00a9 2026 自动化金融报告系统</div>'.format(now)
    html += '</div></body></html>'
    return html

# ============================================================
# 邮件发送
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

# ============================================================
# 主流程
# ============================================================
def main():
    print("="*60)
    print("\U0001f3db 中国金融政策动态追踪系统 v2.0")
    print("="*60)
    print("报告周期: {}".format(datetime.now().strftime("%Y-%m-%d")))
    print("="*60)

    all_news = []
    for fn in [fetch_sina_finance, fetch_wallstreetcn, fetch_yicai, fetch_people_rss,
               fetch_eastmoney, fetch_csrc, fetch_pbc, fetch_ndrc]:
        all_news.extend(fn())
        time.sleep(0.5)

    economic_calendar = fetch_economic_calendar()

    seen = set()
    unique_news = []
    for n in all_news:
        title = n.get("title", "")
        if title and title not in seen:
            seen.add(title)
            unique_news.append(n)
    all_news = unique_news

    print("\n\u2705 共获取 {} 条政策动态".format(len(all_news)))
    if not all_news:
        print("\u274c 无数据，终止")
        return

    print("生成AI综合分析...")
    ai_summary = get_ai_summary(all_news, economic_calendar)

    print("生成报告...")
    html = generate_html_report(all_news, ai_summary, economic_calendar)

    print("发送邮件...")
    send_report(html)
    print("\n\u2705 完成!")

if __name__ == "__main__":
    main()
