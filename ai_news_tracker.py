# -*- coding: utf-8 -*-
import requests
import smtplib
import json
import xml.etree.ElementTree as ET
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ============================================================
# 配置
# ============================================================
SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

# ============================================================
# 工具函数
# ============================================================
def safe_request(url, headers=None, timeout=15):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        return r
    except Exception as e:
        print("  \u274c 请求失败: {} - {}".format(url, str(e)[:60]))
        return None

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:200]

# ============================================================
# 数据采集模块
# ============================================================

def fetch_qbitai():
    """量子位 - AI科技媒体"""
    print("  [1/6] 量子位...")
    news = []
    try:
        r = safe_request("https://www.qbitai.com/wp-json/wp/v2/posts?per_page=8")
        if r:
            for p in r.json()[:8]:
                title = p.get("title", {}).get("rendered", "")
                link = p.get("link", "")
                excerpt = clean_html(p.get("excerpt", {}).get("rendered", ""))
                date = p.get("date", "")[:10]
                categories = [c["name"] for c in p.get("_embedded", {}).get("wp:term", [[]])[0] if isinstance(c, dict)]
                tags = [t["name"] for t in p.get("tags", []) if isinstance(t, dict)]
                news.append({"title": title, "link": link, "excerpt": excerpt, "date": date, "source": "量子位", "category": categories})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_jiqizhixin():
    """机器之心 - AI专业媒体"""
    print("  [2/6] 机器之心...")
    news = []
    try:
        r = safe_request("https://www.jiqizhixin.com/api/v1/articles?limit=8")
        if r:
            for a in r.json()[:8]:
                title = a.get("title", "")
                link = "https://www.jiqizhixin.com/articles/{}".format(a.get("id", ""))
                excerpt = clean_html(a.get("description", ""))
                date = a.get("published_at", "")[:10] if a.get("published_at") else ""
                news.append({"title": title, "link": link, "excerpt": excerpt, "date": date, "source": "机器之心"})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_36kr():
    """36氪 RSS - 科技商业媒体"""
    print("  [3/6] 36氪...")
    news = []
    try:
        r = safe_request("https://www.36kr.com/feed", headers={"User-Agent": "Mozilla/5.0"})
        if r:
            root = ET.fromstring(r.content)
            ns = {"atom": "http://www.w3.org/2005/Atom", "": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)
            for item in items[:8]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = clean_html(item.findtext("description", ""))
                date = item.findtext("pubDate", "")[:16]
                news.append({"title": title, "link": link, "excerpt": desc, "date": date, "source": "36氪"})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_huggingface_papers():
    """HuggingFace每日论文 - 最新AI模型/论文"""
    print("  [4/6] HuggingFace每日论文...")
    news = []
    try:
        r = safe_request("https://huggingface.co/api/daily_papers")
        if r:
            for p in r.json()[:8]:
                title = p.get("title", "")
                paper_id = p.get("paper_id", "")
                link = "https://huggingface.co/papers/{}".format(paper_id)
                summary = p.get("summary", "")[:150]
                authors = ", ".join([a.get("name", "") for a in p.get("authors", [])[:3]])
                news.append({"title": title, "link": link, "excerpt": summary, "authors": authors, "source": "HuggingFace"})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_github_ai_projects():
    """GitHub热门AI开源项目"""
    print("  [5/6] GitHub AI项目...")
    news = []
    today = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    try:
        url = ("https://api.github.com/search/repositories"
               "?q=ai+llm+created:>{}&sort=stars&order=desc&per_page=10".format(today))
        r = safe_request(url, headers={"Accept": "application/vnd.github+json"})
        if r and r.status_code == 200:
            for item in r.json().get("items", [])[:10]:
                name = item.get("full_name", "")
                stars = item.get("stargazers_count", 0)
                desc = item.get("description", "") or ""
                lang = item.get("language", "") or ""
                url_html = item.get("html_url", "")
                news.append({"title": "[{} stars] {}".format(stars, name), "link": url_html,
                             "excerpt": desc[:150], "language": lang, "source": "GitHub"})
        else:
            # 备用：按stars搜索
            url2 = "https://api.github.com/search/repositories?q=ai+llm&sort=stars&order=desc&per_page=5"
            r2 = safe_request(url2, headers={"Accept": "application/vnd.github+json"})
            if r2 and r2.status_code == 200:
                for item in r2.json().get("items", [])[:5]:
                    name = item.get("full_name", "")
                    stars = item.get("stargazers_count", 0)
                    desc = item.get("description", "") or ""
                    url_html = item.get("html_url", "")
                    news.append({"title": "[{} stars] {}".format(stars, name), "link": url_html,
                                 "excerpt": desc[:150], "source": "GitHub"})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

def fetch_arxiv():
    """arXiv最新AI论文"""
    print("  [6/6] arXiv AI论文...")
    news = []
    try:
        # 搜索大模型/AI相关论文，按时间排序
        query = "all:(large language model OR AI OR deep learning) AND (training OR scaling OR algorithm)"
        r = safe_request("https://export.arxiv.org/api/query?search_query={}&start=0&max_results=8&sortBy=submittedDate&sortOrder=descending".format(
            requests.utils.quote(query)))
        if r:
            root = ET.fromstring(r.content)
            ns = {"http://www.w3.org/2005/Atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("http://www.w3.org/2005/Atom:entry", ns)[:8]:
                title = clean_html(entry.findtext("http://www.w3.org/2005/Atom:title", ""))
                link_tag = entry.find("http://www.w3.org/2005/Atom:id", ns)
                link = link_tag.text if link_tag is not None else ""
                summary = clean_html(entry.findtext("http://www.w3.org/2005/Atom:summary", ""))[:150]
                authors = [a.findtext("http://www.w3.org/2005/Atom:name", "") for a in entry.findall("http://www.w3.org/2005/Atom:author", ns)]
                news.append({"title": title, "link": link, "excerpt": summary,
                             "authors": ", ".join(authors[:3]), "source": "arXiv"})
    except Exception as e:
        print("    \u274c {}".format(str(e)[:50]))
    return news

# ============================================================
# AI分析模块
# ============================================================
def get_ai_summary(all_news):
    """DeepSeek API生成AI行业动态总结"""
    print("  生成AI综合解读...")
    cn_news = [n for n in all_news if n.get("source") in ["量子位", "机器之心", "36氪"]]
    global_news = [n for n in all_news if n.get("source") in ["HuggingFace", "GitHub", "arXiv"]]
    us_news = [n for n in global_news if n.get("source") in ["HuggingFace", "arXiv"]]
    eu_news = [n for n in all_news if n.get("source") in ["EU_AI"]]

    def format_news_list(news_list, max_count=6):
        text = ""
        for i, n in enumerate(news_list[:max_count], 1):
            text += "{}. [{}] {} - {}\n".format(i, n.get("source", ""), n.get("title", "")[:80], n.get("link", ""))
            if n.get("excerpt"):
                text += "   {}\n".format(n["excerpt"][:80])
        return text

    prompt = """作为AI行业分析师，请基于以下最新行业动态，生成一份中美欧AI发展动态综合分析报告：

【中国AI动态】
{cn_news}

【美国AI动态】
{us_news}

【欧洲AI动态】
{eu_news}

【全球AI开源项目】
{github}

请重点分析：
1. 中国AI在模型发布、产业应用方面的最新进展
2. 美国AI在基础研究、算力基建方面的领先动态
3. 欧洲AI在监管立法、隐私保护、开源社区方面的特色发展
4. 三方对比：中美欧在AI领域的差异化竞争格局""".format(
        cn_news=format_news_list(cn_news),
        us_news=format_news_list(us_news),
        eu_news=format_news_list(eu_news),
        github=format_news_list([n for n in all_news if n.get("source") == "GitHub"])
    )

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)}
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.7}
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "AI分析暂不可用"

def classify_news(all_news):
    """按主题分类"""
    topics = {"大模型/模型发布": [], "算力/基础设施": [], "算法/研究": [], "政策/产业": [], "开源项目": []}
    keywords = {
        "大模型/模型发布": ["模型", "GPT", "Llama", "Claude", "Gemini", "Qwen", "DeepSeek", "ChatGPT", "发布", "开源模型", "参数"],
        "算力/基础设施": ["算力", "GPU", "芯片", "数据中心", "H100", "A100", "训练", "集群", "算力基建", "服务器"],
        "算法/研究": ["算法", "论文", "训练方法", "注意力", "Transformer", "优化", "推理", "对齐", "微调"],
        "政策/产业": ["政策", "监管", "法案", "投资", "融资", "合作", "竞争", "出口管制", "制裁", "GDPR", "AI法案", "欧盟", "欧洲"],
    }
    for n in all_news:
        title = n.get("title", "")
        excerpt = n.get("excerpt", "")
        text = (title + " " + excerpt).lower()
        matched = False
        for topic, kws in keywords.items():
            if any(kw.lower() in text for kw in kws):
                topics[topic].append(n)
                matched = True
        if n.get("source") == "GitHub":
            topics["开源项目"].append(n)
        elif not matched:
            topics["算法/研究"].append(n)
    return topics

# ============================================================
# 报告生成
# ============================================================
def generate_html_report(all_news, topics, ai_summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    week_num = (datetime.now().isocalendar()[1])
    period_end = datetime.now().strftime("%Y-%m-%d")
    period_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 960px; margin: auto; padding: 20px; background: #f0f4f8;">
<div style="background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%); color: white; padding: 25px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="margin:0;">\U0001f916 中美欧AI行业动态跟踪报告</h1>
    <div style="margin-top:8px; opacity:0.9; font-size:14px;">第{week}周 | {period_start} ~ {period_end}</div>
    <div style="margin-top:4px; opacity:0.7; font-size:12px;">大模型 · 算法 · 算力基建 · 开源 · 产业政策</div>
</div>
<div style="background: white; padding: 25px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
""".format(week=week_num, period_start=period_start, period_end=period_end)

    # 数据来源摘要
    source_count = {}
    for n in all_news:
        src = n.get("source", "其他")
        source_count[src] = source_count.get(src, 0) + 1
    src_summary = " | ".join(["{}: {}条".format(k, v) for k, v in sorted(source_count.items(), key=lambda x: -x[1])])

    html += '<div style="padding:10px 15px; background:#e3f2fd; border-radius:4px; margin-bottom:15px; font-size:13px; color:#1565c0;">'
    html += '<b>\U0001f4ca 数据概览</b> 共{}条动态 | {}'.format(len(all_news), src_summary)
    html += '</div>'

    # AI综合解读
    if ai_summary:
        html += '<h2 style="color:#0d47a1; border-bottom:2px solid #0d47a1; padding-bottom:6px;">\U0001f4ac 一、AI行业综合解读</h2>'
        html += '<div style="margin:12px 0; padding:15px; background:#f5f5f5; border-left:4px solid #0d47a1; border-radius:4px; line-height:1.9; font-size:13px;">'
        for line in ai_summary.split("\n"):
            if line.strip():
                html += '<div style="margin:6px 0;">{}</div>'.format(line.strip())
        html += '</div><br>'

    # 按主题分类展示
    html += '<h2 style="color:#0d47a1; border-bottom:2px solid #0d47a1; padding-bottom:6px;">\U0001f4ca 二、分类动态详情</h2>'

    order = ["大模型/模型发布", "算力/基础设施", "算法/研究", "开源项目", "政策/产业"]
    colors = ["#1565c0", "#2e7d32", "#e65100", "#6a1b9a", "#c62828"]
    icons = ["\U0001f9e0", "\U0001f4bb", "\U0001f52c", "\U0001f4e6", "\U0001f3db"]

    for idx, topic in enumerate(order):
        items = topics.get(topic, [])
        if not items:
            continue
        color = colors[idx % len(colors)]
        icon = icons[idx % len(icons)]
        html += '<h3 style="color:{}; margin:15px 0 8px 0;">{} {}（{}条）</h3>'.format(color, icon, topic, len(items))
        for n in items[:10]:
            title = n.get("title", "")
            link = n.get("link", "")
            excerpt = n.get("excerpt", "")
            date = n.get("date", "")
            source = n.get("source", "")
            excerpt_clean = clean_html(excerpt)[:100] if excerpt else ""

            html += '<div style="margin:6px 0; padding:8px 12px; background:#fafafa; border:1px solid #eee; border-radius:4px;">'
            html += '<div style="font-size:13px;"><b>'
            if link:
                html += '<a href="{}" style="color:#1565c0; text-decoration:none;" target="_blank">{}</a>'.format(link, title[:80])
            else:
                html += title[:80]
            html += '</b></div>'
            details = []
            if date:
                details.append(date)
            details.append(source)
            if details:
                html += '<div style="font-size:11px; color:#999; margin-top:3px;">{}</div>'.format(" | ".join(details))
            if excerpt_clean:
                html += '<div style="font-size:12px; color:#666; margin-top:3px;">{}</div>'.format(excerpt_clean)
            html += '</div>'

    # 中美欧对比分析
    cn_count = len([n for n in all_news if n.get("source") in ["量子位", "机器之心", "36氪"]])
    us_count = len([n for n in all_news if n.get("source") in ["HuggingFace", "arXiv", "GitHub"]])
    eu_count = len([n for n in all_news if n.get("source") == "EU_AI"])
    html += '<br><h2 style="color:#0d47a1; border-bottom:2px solid #0d47a1; padding-bottom:6px;">\U0001f30d 三、中美欧动态对比</h2>'
    html += '<div style="padding:15px; background:#f5f5f5; border-radius:4px; font-size:13px;">'
    html += '<div style="display:flex; justify-content:space-around; text-align:center;">'
    html += '<div style="flex:1; padding:15px; margin:5px; background:#e8eaf6; border-radius:8px;">'
    html += '<div style="font-size:36px; color:#c62828;">\U0001f1e8\U0001f1f3</div>'
    html += '<div style="font-size:24px; font-weight:bold; color:#1a237e;">{}条</div>'.format(cn_count)
    html += '<div style="font-size:12px; color:#666;">中国动态（媒体/产业）</div>'
    html += '</div>'
    html += '<div style="flex:1; padding:15px; margin:5px; background:#e3f2fd; border-radius:8px;">'
    html += '<div style="font-size:36px; color:#1565c0;">\U0001f1fa\U0001f1f8</div>'
    html += '<div style="font-size:24px; font-weight:bold; color:#01579b;">{}条</div>'.format(us_count)
    html += '<div style="font-size:12px; color:#666;">美国动态（论文/开源）</div>'
    html += '</div>'
    html += '<div style="flex:1; padding:15px; margin:5px; background:#fff3e0; border-radius:8px;">'
    html += '<div style="font-size:36px; color:#e65100;">\U0001f1ea\U0001f1fa</div>'
    html += '<div style="font-size:24px; font-weight:bold; color:#bf360c;">{}条</div>'.format(eu_count)
    html += '<div style="font-size:12px; color:#666;">欧洲动态（监管/开源）</div>'
    html += '</div>'
    html += '</div></div><br>'

    # 数据说明
    html += '<div style="padding:15px; background:#f5f5f5; border-radius:4px; font-size:11px; color:#999;">'
    html += '<b>\U0001f4d6 数据说明</b><br>'
    html += '<div style="margin-top:5px;">'
    for src, count in sorted(source_count.items(), key=lambda x: -x[1]):
        html += '<span style="display:inline-block; margin:2px 8px 2px 0; padding:2px 8px; background:#e0e0e0; border-radius:10px; font-size:11px;">{}: {}条</span>'.format(src, count)
    html += '</div>'
    html += '<div style="margin-top:8px;">\u2022 报告由自动化系统生成，数据来源为各平台公开API</div>'
    html += '<div>\u2022 不构成投资建议，仅供参考</div>'
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
    msg["Subject"] = "中美欧AI行业动态跟踪报告 - {}".format(datetime.now().strftime("%Y-%m-%d"))
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
    print("\U0001f916 中美欧AI行业动态跟踪系统 v1.0")
    print("="*60)
    print("报告周期: {}".format(datetime.now().strftime("%Y-%m-%d")))
    print("="*60)

    # 隔周二执行检查：用ISO周数判断奇偶数周
    # iso_week = datetime.now().isocalendar()[1]
    # if iso_week % 2 == 0:
    #     print("  本周为第{}周（偶数周），跳过执行（只在奇数周周二发送）".format(iso_week))
    #     print("  下次执行: 下周二")
    #     return
    # print("  本周为第{}周（奇数周），执行采集".format(iso_week))

    all_news = []
    all_news.extend(fetch_qbitai())
    time.sleep(0.5)
    all_news.extend(fetch_jiqizhixin())
    time.sleep(0.5)
    all_news.extend(fetch_36kr())
    time.sleep(0.5)
    all_news.extend(fetch_huggingface_papers())
    time.sleep(0.5)
    all_news.extend(fetch_github_ai_projects())
    time.sleep(0.5)
    all_news.extend(fetch_arxiv())

    print("\n\u2705 共获取 {} 条动态".format(len(all_news)))

    if not all_news:
        print("\u274c 无数据，终止")
        return

    print("\n分类整理...")
    topics = classify_news(all_news)

    print("生成AI综合解读...")
    ai_summary = get_ai_summary(all_news)

    print("生成报告...")
    html = generate_html_report(all_news, topics, ai_summary)

    print("发送邮件...")
    send_report(html)

    print("\n\u2705 完成!")

if __name__ == "__main__":
    main()
