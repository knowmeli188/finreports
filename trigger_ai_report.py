# -*- coding: utf-8 -*-
"""临时触发脚本：跳过隔周检查，立即发送一份报告样本"""
import ai_news_tracker as ai
import time

print("="*60)
print("中美欧AI行业动态跟踪报告 - 手动触发样本")
print("="*60)
print("报告周期: {}".format(ai.datetime.now().strftime("%Y-%m-%d")))
print("="*60)

all_news = []
all_news.extend(ai.fetch_qbitai())
time.sleep(0.5)
all_news.extend(ai.fetch_jiqizhixin())
time.sleep(0.5)
all_news.extend(ai.fetch_36kr())
time.sleep(0.5)
all_news.extend(ai.fetch_huggingface_papers())
time.sleep(0.5)
all_news.extend(ai.fetch_github_ai_projects())
time.sleep(0.5)
all_news.extend(ai.fetch_arxiv())

print("\n共获取 {} 条动态".format(len(all_news)))

if not all_news:
    print("无数据，终止")
else:
    print("\n分类整理...")
    topics = ai.classify_news(all_news)
    for k, v in topics.items():
        print("  {}: {}条".format(k, len(v)))

    print("生成AI综合解读...")
    ai_summary = ai.get_ai_summary(all_news)

    print("生成报告...")
    html = ai.generate_html_report(all_news, topics, ai_summary)

    print("发送邮件...")
    ai.send_report(html)

    print("完成!")
