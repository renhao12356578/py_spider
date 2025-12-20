# encoding: UTF-8
import time
import requests
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import os


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema


def sha256base64(data):
    """计算sha256并编码为base64"""
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(request_url):
    """解析URL"""
    stidx = request_url.index("://")
    host = request_url[stidx + 3:]
    schema = request_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(request_url, method="GET", api_key="", api_secret=""):
    """生成鉴权url"""
    u = parse_url(request_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }
    
    return request_url + "?" + urlencode(values)


def getBody(appid, text):
    """生成请求body"""
    body = {
        "header": {
            "app_id": appid,
            "uid": "123456789"
        },
        "parameter": {
            "chat": {
                "domain": "general",
                "temperature": 0.5,
                "max_tokens": 4096
            }
        },
        "payload": {
            "message": {
                "text": [
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            }
        }
    }
    return body


def generate_and_save_image(message, save_dir="./generated_images"):
    """
    根据message生成图片并保存
    
    参数:
        message: 图片描述文本
        save_dir: 保存目录，默认为当前目录下的generated_images文件夹
    
    返回:
        str: 图片的相对路径，失败返回None
    """
    try:
        # 确保保存目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 构建请求URL
        host = 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti'
        url = assemble_ws_auth_url(host, method='POST', api_key=APIKEY, api_secret=APISECRET)
        
        # 构建请求body
        content = getBody(APPID, message)
        
        # 发起请求
        print(f"正在生成图片: {message}")
        response = requests.post(url, json=content, headers={'content-type': "application/json"}).text
        
        # 解析响应
        data = json.loads(response)
        code = data['header']['code']
        
        if code != 0:
            print(f'请求错误: {code}, {data}')
            return None
        
        # 提取图片数据
        text = data["payload"]["choices"]["text"]
        imageContent = text[0]
        imageBase = imageContent["content"]
        imageName = data['header']['sid']
        
        # 保存图片
        img_data = base64.b64decode(imageBase)
        image_filename = f"{imageName}.png"
        image_path = os.path.join(save_dir, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(img_data)
        
        # 返回相对路径
        relative_path = os.path.relpath('/LLM',image_path)
        print(f"图片已保存: {relative_path}")
        return relative_path
        
    except Exception as e:
        print(f"生成图片时出错: {str(e)}")
        return None


# 全局配置 - 请在这里配置你的讯飞API凭证
APPID = '67e25832'
APIKEY = 'YTEwMTFjNTFiMTdjY2Q5ZTdhMDNkZmNj'
APISECRET = '32139567bbcfdbe2309c77f2403abd48'