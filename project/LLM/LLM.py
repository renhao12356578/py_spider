import _thread as thread
import base64
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket
from langchain.chains.question_answering.map_reduce_prompt import messages
from numpy.f2py.auxfuncs import throw_error
import sys
import sys
sys.path.append("..") #相对路径或绝对路径
from py_spider.project.LLM.use_data import query_house_data_by_area,get_area_statistics

# ================= 配置区域 =================
appid = "67e25832"
api_secret = "YTEwMTFjNTFiMTdjY2Q5ZTdhMDNkZmNj"
api_key = "32139567bbcfdbe2309c77f2403abd48"
domain = "spark-x"
Spark_url = "wss://spark-api.xf-yun.com/v1/x1"

# ================= 房源知识库 =================
result = query_house_data_by_area("海淀", 100)
if result and len(result) > 0:
    housing_data = "【房源库存清单】：" + (str(result[0]) if result[0] else "无数据")
else:
    throw_error("数据库访问失败")

# ================= 系统提示词 =================
recomandation_prompt = f"""
你是一位专业的资深房产顾问。你的任务是根据用户的需求，从【房源库存清单】中推荐最匹配的房子。

【房源库存清单】：
{housing_data}

你的工作准则：
1. **需求挖掘**：认真分析用户的每一句话。如果用户需求模糊（比如只说"我想买房"），你需要主动询问预算、区域、户型或购房目的（刚需/投资/学区）。
2. **记忆力**：你必须记住用户之前的对话。例如，如果用户之前说了"预算800万"，下一轮他说"还是太贵了"，你推荐的房子必须显著低于800万。
3. **严格匹配**：**只能推荐清单里有的房子**，严禁编造虚假房源。如果没有匹配的，请诚实告知并询问是否调整条件。
4. **回复风格**：专业、热情、有逻辑。推荐时请说明推荐理由（结合用户需求）。
"""

# ================= 全局变量 =================
answer = ""
conversation_history = []


# ================= WebSocket参数类 =================
class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'),
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.Spark_url + '?' + urlencode(v)
        return url


# ================= WebSocket回调函数 =================
def on_error(ws, error):
    print(f"\n❌ 连接错误: {error}")


def on_close(ws, one, two):
    pass


def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)


def on_message(ws, message):
    global answer
    data = json.loads(message)
    code = data['header']['code']

    if code != 0:
        print(f'\n请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0].get("content", "")

        if content:
            print(content, end="", flush=True)
            answer += content

        if status == 2:
            ws.close()


# ================= 参数生成函数 =================
def gen_params(appid, domain, question):
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


# ================= 对话历史管理 =================
def add_to_history(role, content):
    """添加消息到对话历史"""
    conversation_history.append({
        "role": role,
        "content": content
    })


def get_history_length():
    """计算对话历史的总字符数"""
    return sum(len(msg["content"]) for msg in conversation_history)


def trim_history():
    """裁剪对话历史，保持在token限制内"""
    # 星火API限制较严格，保留最近的对话
    while get_history_length() > 6000 and len(conversation_history) > 2:
        # 保留系统提示词（第一条），删除最早的用户-助手对话
        if len(conversation_history) > 1:
            del conversation_history[1]


def prepare_messages():
    """准备发送给API的消息列表"""
    trim_history()
    return conversation_history.copy()


# ================= 主对话函数 =================
def call_spark_api(user_input,max_tokens=2048):
    """调用星火API获取回复"""
    global answer
    answer = ""

    messages=user_input


    # 5. 创建连接
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()

    ws = websocket.WebSocketApp(wsUrl,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    ws.appid = appid
    ws.max_tokens = max_tokens  # 保存最大长度参数
    ws.question = messages  # 直接使用构建好的 messages
    ws.domain = domain
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    return answer


# ================= 主程序 =================
def chat_house_recommandation():
    print("=" * 60)
    print("🏡 星火AI房产推荐助手已启动")
    print("（输入 'quit' 或 'exit' 退出对话）")
    print("=" * 60)

    # 初始化：将系统提示词作为第一条消息
    add_to_history("system", recomandation_prompt)

    # 助手主动问候
    first_greeting = "您好！我是您的专属置业顾问。请问您想在哪个区域看房，或者您的购房预算大概是多少？"
    print(f"\nAssistant: {first_greeting}\n")
    add_to_history("assistant", first_greeting)

    while True:
        # 获取用户输入
        user_input = input("User: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\nAssistant: 感谢您的咨询，祝您早日买到心仪的房子，再见！")
            break

        # 添加用户输入到历史
        add_to_history("user", user_input)

        try:
            # 调用API获取回复
            print("\nAssistant: ", end="", flush=True)
            reply = call_spark_api(user_input)
            print()  # 换行

            # 添加助手回复到历史
            if reply:
                add_to_history("assistant", reply)
            else:
                print("\n⚠️ 未收到有效回复，请重试。")
                # 移除刚才添加的用户消息
                conversation_history.pop()

        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            # 出错时移除未完成的用户消息
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()


def generate_house_price_analysis(area_name):
    """
    专门生成房价分析报告的函数
    """
    analysis=get_area_statistics(area_name)
    analysis_prompt = f"""请为{area_name}生成一份详细的房价分析报告，包含以下部分：

## {area_name}房价分析报告
###该地的房价分析如下{analysis}

### 一、当前市场概况
1. 平均房价水平
2. 近期价格走势
3. 成交量分析

### 二、区域特征分析
1. 地理位置与交通
2. 教育资源分布
3. 商业配套设施
4. 环境与居住品质

### 三、政策影响分析
1. 限购限贷政策
2. 城市规划发展
3. 税收政策影响

### 四、投资价值评估
1. 租金收益率分析
2. 增值潜力评估
3. 风险因素提示

### 五、购房建议
1. 适合人群
2. 最佳入手时机
3. 推荐关注的小区


请确保分析基于最新市场数据，提供实用建议。"""

    # 这里你可以选择：
    # 1. 直接调用LLM
    # 2. 或者先调用你的call_spark_api函数
    # 取决于你的实现细节

    print("正在生成房价分析报告...")

    # 假设你的call_spark_api可以处理
    report = call_spark_api(analysis_prompt)

    return report


# 使用示例
def chat_house_price_analysis():
    """专门用于房价分析的对话"""
    print("=" * 60)
    print("📊 区域房价分析报告生成器")
    print("=" * 60)

    while True:
        area = input("\n请输入您想分析的区域（如'北京海淀区'、'上海浦东前滩'）：").strip()

        if area.lower() in ['quit', 'exit', '退出']:
            break

        print("\n正在分析中，请稍候...\n")
        report = generate_house_price_analysis(area)

        print("=" * 60)
        print(f"{area} 房价分析报告")
        print("=" * 60)
        print(report)
        print("=" * 60)

        # 询问是否需要保存或进一步分析
        choice = input("\n是否需要：\n1. 保存报告\n2. 分析其他区域\n3. 退出\n请选择(1/2/3): ").strip()

        if choice == "1":
            # 这里可以添加保存功能
            print("报告已保存（功能待实现）")
        elif choice == "3":
            break

