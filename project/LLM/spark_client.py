"""
星火大模型API客户端 - 统一的WebSocket接口封装
"""
import _thread as thread
import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time

import websocket


# ================= 默认配置 =================
DEFAULT_CONFIG = {
    "appid": "67e25832",
    "api_secret": "YTEwMTFjNTFiMTdjY2Q5ZTdhMDNkZmNj",
    "api_key": "32139567bbcfdbe2309c77f2403abd48",
    "domain": "spark-x",
    "spark_url": "wss://spark-api.xf-yun.com/v1/x1"
}


class SparkClient:
    """星火大模型客户端"""

    def __init__(self, appid=None, api_key=None, api_secret=None, 
                 domain=None, spark_url=None):
        self.appid = appid or DEFAULT_CONFIG["appid"]
        self.api_key = api_key or DEFAULT_CONFIG["api_key"]
        self.api_secret = api_secret or DEFAULT_CONFIG["api_secret"]
        self.domain = domain or DEFAULT_CONFIG["domain"]
        self.spark_url = spark_url or DEFAULT_CONFIG["spark_url"]

    def _create_url(self):
        """生成WebSocket认证URL"""
        host = urlparse(self.spark_url).netloc
        path = urlparse(self.spark_url).path

        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"

        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')

        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode('utf-8')
        ).decode('utf-8')

        url = self.spark_url + '?' + urlencode({
            "authorization": authorization,
            "date": date,
            "host": host
        })
        return url

    def _gen_params(self, messages, max_tokens=9198, temperature=0.7):
        """生成API请求参数"""
        return {
            "header": {
                "app_id": self.appid,
                "uid": "1234",
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            },
            "payload": {
                "message": {
                    "text": messages if isinstance(messages, list) else [
                        {"role": "user", "content": messages}
                    ]
                }
            }
        }

    def chat(self, messages, max_tokens=20000, temperature=0.7, stream_print=False):
        """
        调用星火API进行对话
        
        Args:
            messages: 消息内容，可以是字符串或消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            stream_print: 是否流式打印输出
            
        Returns:
            AI回复内容
        """
        answer = ""

        def on_message(ws, message):
            nonlocal answer
            data = json.loads(message)
            code = data['header']['code']

            if code != 0:
                print(f'\n[ERROR] 请求错误: {code}, {data}', flush=True)
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0].get("content", "")

                if content:
                    if stream_print:
                        print(content, end="", flush=True)
                    answer += content

                if status == 2:
                    ws.close()

        def on_error(ws, error):
            print(f"\n[ERROR] 连接错误: {error}", flush=True)

        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            def run(*args):
                data = json.dumps(self._gen_params(
                    ws.messages, ws.max_tokens, ws.temperature
                ))
                ws.send(data)
            thread.start_new_thread(run, ())

        websocket.enableTrace(False)
        ws_url = self._create_url()

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        ws.messages = messages
        ws.max_tokens = max_tokens
        ws.temperature = temperature

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return answer


# ================= 便捷函数（兼容旧接口） =================
_default_client = None


def get_default_client():
    """获取默认客户端实例"""
    global _default_client
    if _default_client is None:
        _default_client = SparkClient()
    return _default_client


def call_spark_api(messages, max_tokens=4096, temperature=0.7, stream_print=False):
    """
    便捷函数：调用星火API
    
    Args:
        messages: 消息内容
        max_tokens: 最大token数
        temperature: 温度
        stream_print: 是否流式打印
        
    Returns:
        AI回复
    """
    return get_default_client().chat(
        messages, max_tokens, temperature, stream_print
    )
