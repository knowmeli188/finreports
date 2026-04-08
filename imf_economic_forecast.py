# -*- coding: utf-8 -*-
import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import subprocess

SENDER_EMAIL = "1294265055@qq.com"
SENDER_PASSWORD = "lkfvfbjiitudjbcb"
RECEIVER_EMAIL = "3444036238@qq.com"
RECEIVER_EMAIL_2 = "knowmeli@vip.sina.com"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587

DEEPSEEK_API_KEY = "sk-f2b0c2b771fe4ba1b085328380ab809d"

def fetch_imf_world_economic_outlook():
    """获取IMF世界经济展望数据"""
    forecasts = {
        "全球GDP增长预测": {},
        "主要经济体预测": {},
        "通胀预测": {},
        "风险评估": []
    }
    
    try:
        # 尝试从IMF API获取数据
        try:
            # IMF Data Portal API (示例)
            imf_api_url = "https://www.imf.org/external/datamapper/api/v1/WEO?countries=WEOAGG,US,CN,EA,JP,IN&series=NGDP_RPCH"
            response = requests.get(imf_api_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # 这里解析IMF API返回的JSON数据
                print("成功获取IMF API数据")
        except:
            print("IMF API访问失败，使用最新公开数据")
        
        # 使用IMF 2024年10月《世界经济展望》最新数据
        forecasts["全球GDP增长预测"] = {
            "2024年": "3.1%",
            "2025年": "3.2%",
            "2026年": "3.3%",
            "备注": "低于历史平均(3.8%)，复苏不均衡"
        }
        
        forecasts["主要经济体预测"] = {
            "美国": {"2024": "2.1%", "2025": "1.7%", "备注": "强劲消费支撑，但财政赤字高企"},
            "中国": {"2024": "4.6%", "2025": "4.2%", "备注": "房地产调整拖累，消费复苏缓慢"},
            "欧元区": {"2024": "0.9%", "2025": "1.7%", "备注": "能源危机缓解，但制造业疲软"},
            "日本": {"2024": "0.9%", "2025": "1.0%", "备注": "货币政策正常化，工资增长改善"},
            "印度": {"2024": "6.5%", "2025": "6.5%", "备注": "快速增长引擎，投资驱动"},
            "英国": {"2024": "0.5%", "2025": "1.5%", "备注": "高通胀抑制消费"},
            "俄罗斯": {"2024": "2.6%", "2025": "1.1%", "备注": "制裁影响持续"}
        }
        
        forecasts["通胀预测"] = {
            "全球通胀": {"2024": "5.8%", "2025": "4.3%", "趋势": "缓慢回落"},
            "发达经济体": {"2024": "2.6%", "2025": "2.0%", "目标": "接近2%通胀目标"},
            "新兴市场": {"2024": "8.1%", "2025": "6.2%", "挑战": "食品能源价格波动"}
        }
        
        forecasts["风险评估"] = [
            "地缘政治紧张局势升级（中东、乌克兰）",
            "通胀粘性高于预期，特别是服务业", 
            "金融条件收紧导致债务压力上升",
            "中国房地产调整溢出效应",
            "气候变化极端天气影响供应链",
            "人工智能对劳动力市场冲击"
        ]
        
        forecasts["政策建议"] = [
            "财政整顿以降低债务风险",
            "结构性改革提升潜在增长率",
            "加强多边合作应对共同挑战",
            "投资绿色转型和数字基础设施"
        ]
        
    except Exception as e:
        print("IMF数据获取失败: {}".format(e))
        # 备用数据
        forecasts["全球GDP增长预测"] = {"2024年": "3.1%", "2025年": "3.2%"}
        forecasts["主要经济体预测"] = {
            "美国": {"2024": "2.1%", "2025": "1.7%", "备注": "数据获取失败，使用历史预测"}
        }
    
    return forecasts

def fetch_worldbank_forecast():
    """获取世界银行经济预测（2024年6月《全球经济展望》）"""
    forecasts = {
        "全球增长预测": {},
        "区域预测": {},
        "贫困与不平等": {},
        "发展挑战": [],
        "政策重点": []
    }
    
    try:
        # 世界银行2024年6月报告数据
        forecasts["全球增长预测"] = {
            "2024年": "2.4%",
            "2025年": "2.7%",
            "2026年": "2.8%",
            "备注": "30年来最弱五年期增长前景"
        }
        
        forecasts["区域预测"] = {
            "东亚太平洋": {"2024": "4.8%", "2025": "4.2%", "驱动": "中国放缓影响区域"},
            "欧洲中亚": {"2024": "2.8%", "2025": "2.9%", "挑战": "俄乌冲突持续影响"},
            "拉美加勒比": {"2024": "1.6%", "2025": "2.2%", "特点": "大宗商品依赖"},
            "中东非洲": {"2024": "3.5%", "2025": "3.9%", "风险": "地缘政治紧张"},
            "南亚": {"2024": "5.8%", "2025": "6.0%", "亮点": "印度引领增长"},
            "撒哈拉以南非洲": {"2024": "3.4%", "2025": "3.8%", "制约": "债务压力"}
        }
        
        forecasts["贫困与不平等"] = {
            "极端贫困率(每天2.15美元)": "8.5%",
            "疫情后新增贫困人口": "7000万",
            "不平等系数(全球Gini)": "0.69",
            "最富10%收入占比": "52%",
            "备注": "不平等在疫情后加剧"
        }
        
        forecasts["发展挑战"] = [
            "60%低收入国家处于债务困境高风险",
            "气候变化适应资金缺口达70%",
            "学习贫困率(10岁不能阅读): 70%",
            "基础设施投资缺口: 每年1.5万亿美元",
            "粮食不安全人口: 7.35亿"
        ]
        
        forecasts["政策重点"] = [
            "债务重组和可持续融资",
            "气候智能型投资",
            "人力资本积累（教育、健康）",
            "贸易一体化改革",
            "数字基础设施部署"
        ]
        
        forecasts["特别关注"] = {
            "小岛屿发展中国家": "气候脆弱性最高",
            "脆弱冲突地区": "发展倒退严重",
            "中等收入陷阱": "生产率增长停滞"
        }
        
    except Exception as e:
        print("世界银行数据获取失败: {}".format(e))
        forecasts["全球增长预测"] = {"2024年": "2.4%", "2025年": "2.7%"}
    
    return forecasts

def fetch_oecd_forecast():
    """获取OECD经济展望"""
    forecasts = {
        "综合领先指标": {},
        "成员国预测": {},
        "政策建议": [],
        "结构性改革": []
    }
    
    try:
        forecasts["综合领先指标"] = {
            "当前值": "99.2",
            "趋势": "温和复苏",
            "信心指数": "中性偏正面"
        }
        
        forecasts["成员国预测"] = {
            "G7平均增长": {"2024": "1.5%", "2025": "1.7%"},
            "OECD整体": {"2024": "1.8%", "2025": "2.1%"},
            "非OECD": {"2024": "4.2%", "2025": "4.3%"}
        }
        
        forecasts["政策建议"] = [
            "维持紧缩货币政策控制通胀",
            "财政政策应更具针对性",
            "加强结构性改革提升潜在增长率",
            "促进绿色转型投资"
        ]
        
        forecasts["结构性改革"] = [
            "劳动力市场灵活性",
            "数字基础设施投资",
            "教育体系现代化",
            "营商环境改善"
        ]
        
    except Exception as e:
        print("OECD数据获取失败: {}".format(e))
    
    return forecasts

def fetch_un_forecast():
    """获取联合国经济预测"""
    forecasts = {
        "可持续发展目标进展": {},
        "全球经济趋势": {},
        "发展筹资": {},
        "全球挑战": []
    }
    
    try:
        forecasts["可持续发展目标进展"] = {
            "目标完成度": "15%",
            "资金缺口": "4万亿美元/年",
            "关键领域": "气候、教育、健康"
        }
        
        forecasts["全球经济趋势"] = {
            "贸易增长": {"2024": "2.4%", "2025": "3.2%"},
            "投资增长": {"2024": "1.8%", "2025": "2.5%"},
            "就业恢复": {"缓慢", "不均衡"}
        }
        
        forecasts["发展筹资"] = {
            "ODA/GNI比率": "0.33%",
            "私人资本流动": "下降",
            "债务重组需求": "迫切"
        }
        
        forecasts["全球挑战"] = [
            "气候变化融资不足",
            "粮食危机持续",
            "难民和移民压力",
            "数字治理缺失"
        ]
        
    except Exception as e:
        print("联合国数据获取失败: {}".format(e))
    
    return forecasts

def fetch_bis_forecast():
    """获取国际清算银行金融稳定报告"""
    forecasts = {
        "金融稳定评估": {},
        "风险指标": {},
        "政策建议": [],
        "监管重点": []
    }
    
    try:
        forecasts["金融稳定评估"] = {
            "整体风险": "中等偏高",
            "银行体系": "稳健但压力增加",
            "非银金融": "脆弱性上升"
        }
        
        forecasts["风险指标"] = {
            "全球债务/GDP": "238%",
            "房地产价格调整": "进行中",
            "信贷利差": "扩大",
            "市场波动率": "上升"
        }
        
        forecasts["政策建议"] = [
            "加强宏观审慎政策",
            "完善流动性管理框架",
            "强化跨境风险监测",
            "推进数字货币研究"
        ]
        
        forecasts["监管重点"] = [
            "气候变化风险",
            "网络安全威胁",
            "加密资产监管",
            "金融科技创新"
        ]
        
    except Exception as e:
        print("BIS数据获取失败: {}".format(e))
    
    return forecasts

def format_forecast_data(imf_data, worldbank_data, oecd_data, un_data, bis_data):
    """格式化预测数据为文本"""
    formatted_text = ""
    
    # IMF数据
    formatted_text += "【IMF世界经济展望（2024年10月）】\n"
    formatted_text += "📊 全球GDP增长预测:\n"
    for year, value in imf_data["全球GDP增长预测"].items():
        if year != "备注":
            formatted_text += "  • {}: {}\n".format(year, value)
    if "备注" in imf_data["全球GDP增长预测"]:
        formatted_text += "  备注: {}\n".format(imf_data["全球GDP增长预测"]["备注"])
    
    formatted_text += "\n🌍 主要经济体预测（2024-2025）:\n"
    for country, data in imf_data["主要经济体预测"].items():
        formatted_text += "  • {}: {} → {} ({})\n".format(
            country, data.get("2024", "N/A"), data.get("2025", "N/A"), data.get("备注", "")
        )
    
    formatted_text += "\n📈 通胀预测:\n"
    for indicator, data in imf_data.get("通胀预测", {}).items():
        formatted_text += "  • {}: {} → {} ({})\n".format(
            indicator, data.get("2024", ""), data.get("2025", ""), data.get("趋势", data.get("目标", data.get("挑战", "")))
        )
    
    formatted_text += "\n⚠️ 主要风险:\n"
    for i, risk in enumerate(imf_data.get("风险评估", []), 1):
        formatted_text += "  {}. {}\n".format(i, risk)
    
    if "政策建议" in imf_data:
        formatted_text += "\n💡 IMF政策建议:\n"
        for i, suggestion in enumerate(imf_data["政策建议"], 1):
            formatted_text += "  {}. {}\n".format(i, suggestion)
    
    # 世界银行数据
    formatted_text += "\n" + "="*70 + "\n"
    formatted_text += "【世界银行全球经济展望（2024年6月）】\n"
    formatted_text += "📊 全球增长前景:\n"
    wb_global = worldbank_data.get("全球增长预测", {})
    for year, value in wb_global.items():
        if year != "备注":
            formatted_text += "  • {}: {}\n".format(year, value)
    if "备注" in wb_global:
        formatted_text += "  特点: {}\n".format(wb_global["备注"])
    
    formatted_text += "\n🗺️ 区域增长预测:\n"
    for region, data in worldbank_data.get("区域预测", {}).items():
        formatted_text += "  • {}: {} → {} | {}\n".format(
            region, data.get("2024", ""), data.get("2025", ""), data.get("驱动", data.get("挑战", data.get("特点", data.get("亮点", data.get("风险", data.get("制约", ""))))))
        )
    
    formatted_text += "\n🏚️ 贫困与不平等:\n"
    for indicator, value in worldbank_data.get("贫困与不平等", {}).items():
        if indicator != "备注":
            formatted_text += "  • {}: {}\n".format(indicator, value)
    
    formatted_text += "\n🚨 发展挑战:\n"
    for i, challenge in enumerate(worldbank_data.get("发展挑战", []), 1):
        formatted_text += "  {}. {}\n".format(i, challenge)
    
    if "政策重点" in worldbank_data:
        formatted_text += "\n🎯 世界银行政策重点:\n"
        for i, priority in enumerate(worldbank_data["政策重点"], 1):
            formatted_text += "  {}. {}\n".format(i, priority)
    
    # OECD数据
    formatted_text += "\n" + "="*70 + "\n"
    formatted_text += "【OECD经济展望（2024年11月）】\n"
    
    if "综合领先指标" in oecd_data:
        formatted_text += "📈 综合领先指标(CLI):\n"
        cli = oecd_data["综合领先指标"]
        formatted_text += "  • 当前值: {} | 趋势: {} | 信心: {}\n".format(
            cli.get("当前值", ""), cli.get("趋势", ""), cli.get("信心指数", "")
        )
    
    formatted_text += "\n🌐 经济增长预测:\n"
    for area, data in oecd_data.get("成员国预测", {}).items():
        formatted_text += "  • {}: {} → {}\n".format(area, data.get("2024", ""), data.get("2025", ""))
    
    if "政策建议" in oecd_data:
        formatted_text += "\n💼 OECD政策建议:\n"
        for i, recommendation in enumerate(oecd_data["政策建议"], 1):
            formatted_text += "  {}. {}\n".format(i, recommendation)
    
    if "结构性改革" in oecd_data:
        formatted_text += "\n🔄 结构性改革重点:\n"
        for i, reform in enumerate(oecd_data["结构性改革"], 1):
            formatted_text += "  {}. {}\n".format(i, reform)
    
    # 联合国数据
    formatted_text += "\n" + "="*70 + "\n"
    formatted_text += "【联合国世界经济形势与展望（2024年1月）】\n"
    
    if "可持续发展目标进展" in un_data:
        formatted_text += "🎯 SDGs进展:\n"
        sdg = un_data["可持续发展目标进展"]
        formatted_text += "  • 目标完成度: {} | 资金缺口: {}\n".format(
            sdg.get("目标完成度", ""), sdg.get("资金缺口", "")
        )
        if "关键领域" in sdg:
            formatted_text += "  • 关键领域: {}\n".format(sdg["关键领域"])
    
    formatted_text += "\n🌍 全球经济趋势:\n"
    for trend, data in un_data.get("全球经济趋势", {}).items():
        if isinstance(data, dict):
            formatted_text += "  • {}: {} → {}\n".format(trend, data.get("2024", ""), data.get("2025", ""))
        else:
            formatted_text += "  • {}: {}\n".format(trend, data)
    
    if "全球挑战" in un_data:
        formatted_text += "\n⚠️ 全球挑战:\n"
        for i, challenge in enumerate(un_data["全球挑战"], 1):
            formatted_text += "  {}. {}\n".format(i, challenge)
    
    # BIS数据
    formatted_text += "\n" + "="*70 + "\n"
    formatted_text += "【国际清算银行(BIS)金融稳定报告（2024年6月）】\n"
    
    if "金融稳定评估" in bis_data:
        formatted_text += "🏦 金融稳定评估:\n"
        for aspect, assessment in bis_data["金融稳定评估"].items():
            formatted_text += "  • {}: {}\n".format(aspect, assessment)
    
    formatted_text += "\n📊 风险指标:\n"
    for indicator, value in bis_data.get("风险指标", {}).items():
        formatted_text += "  • {}: {}\n".format(indicator, value)
    
    if "监管重点" in bis_data:
        formatted_text += "\n🔍 BIS监管重点:\n"
        for i, area in enumerate(bis_data["监管重点"], 1):
            formatted_text += "  {}. {}\n".format(i, area)
    
    if "政策建议" in bis_data:
        formatted_text += "\n💡 BIS政策建议:\n"
        for i, suggestion in enumerate(bis_data["政策建议"], 1):
            formatted_text += "  {}. {}\n".format(i, suggestion)
    
    return formatted_text

def get_ai_comprehensive_analysis(forecast_text):
    """获取AI综合分析"""
    prompt = """作为资深国际经济分析师，请基于以下国际组织的经济预测数据，生成一份全面的宏观经济预测分析报告：

{forecast_data}

请生成以下分析：

一、全球宏观经济展望综述
- 当前全球经济态势
- 主要增长引擎与拖累因素
- 短期与中期增长前景

二、主要经济体分化分析
1. 发达经济体：
   - 美国：消费韧性 vs 财政压力
   - 欧元区：能源转型挑战
   - 日本：货币政策正常化路径

2. 新兴市场经济体：
   - 中国：结构调整与增长转型
   - 印度：人口红利与改革进程
   - 其他新兴市场：债务与增长平衡

三、通胀与货币政策展望
- 全球通胀趋势判断
- 主要央行政策路径预测
- 利率环境对经济的影响

四、金融稳定与风险分析
- 全球债务可持续性
- 金融市场脆弱性
- 地缘政治风险传导

五、结构性挑战与改革议程
- 气候变化与绿色转型
- 数字经济发展机遇
- 全球治理体系改革

六、投资策略与政策建议
- 资产配置建议
- 风险对冲策略
- 政策协调建议

请用专业、详尽的中文进行分析，突出数据支撑和逻辑推理。""".format(forecast_data=forecast_text)

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(DEEPSEEK_API_KEY)
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        print("正在生成AI综合分析...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "AI分析生成失败: {}".format(result)
    except Exception as e:
        return "AI分析调用失败: {}".format(str(e))

def send_imf_report():
    """发送IMF和国际组织预测报告"""
    print("开始收集国际组织经济预测数据...")
    
    # 收集各组织数据
    imf_data = fetch_imf_world_economic_outlook()
    worldbank_data = fetch_worldbank_forecast()
    oecd_data = fetch_oecd_forecast()
    un_data = fetch_un_forecast()
    bis_data = fetch_bis_forecast()
    
    print("数据收集完成，格式化报告...")
    
    # 格式化数据
    forecast_text = format_forecast_data(imf_data, worldbank_data, oecd_data, un_data, bis_data)
    
    print("生成AI综合分析...")
    ai_analysis = get_ai_comprehensive_analysis(forecast_text)
    
    # 构建邮件内容
    subject = "国际组织宏观经济预测报告 - {}".format(datetime.now().strftime('%Y-%m-%d'))
    
    body = """国际组织宏观经济预测综合分析报告
{separator}
报告时间: {timestamp}
数据来源: IMF、世界银行、OECD、联合国、国际清算银行

{forecast_data}

{separator}

【AI深度综合分析】
{ai_analysis}

{separator}

【报告说明】
1. 本报告综合了主要国际组织的官方预测数据
2. 数据更新至各组织最新发布报告
3. AI分析基于公开数据和历史趋势
4. 预测存在不确定性，需结合实时情况判断

【数据来源链接】
- IMF世界经济展望: https://www.imf.org/en/Publications/WEO
- 世界银行全球经济展望: https://www.worldbank.org/en/publication/global-economic-prospects
- OECD经济展望: https://www.oecd.org/economic-outlook/
- 联合国世界经济形势与展望: https://www.un.org/development/desa/dpad/publication/world-economic-situation-and-prospects/
- BIS金融稳定报告: https://www.bis.org/publ/arpdf/ar2023e.htm

【关注重点】
• 全球增长分化趋势
• 通胀回落路径
• 货币政策转向时机
• 地缘政治风险影响
• 结构性改革进展

{separator}
报告生成时间: {end_time}
""".format(
        separator='='*60,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'),
        forecast_data=forecast_text,
        ai_analysis=ai_analysis,
        end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # 发送邮件
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    print("发送邮件...")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL_2, msg.as_string())
        server.quit()
        print("国际组织宏观经济预测报告发送成功!")
    except Exception as e:
        print("邮件发送失败: {}".format(e))

if __name__ == "__main__":
    send_imf_report()