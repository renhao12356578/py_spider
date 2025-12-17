# llm_service.py
import json
import base64
import hashlib
import hmac
import ssl
import websocket
import threading
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlencode
from typing import Dict, List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os


class LLMAIService:
    """统一的AI服务类，集成多种AI功能"""

    def __init__(self):
        # 星火大模型配置
        self.spark_appid = "67e25832"
        self.spark_api_secret = "YTEwMTFjNTFiMTdjY2Q5ZTdhMDNkZmNj"
        self.spark_api_key = "32139567bbcfdbe2309c77f2403abd48"
        self.spark_domain = "spark-x"
        self.spark_url = "wss://spark-api.xf-yun.com/v1/x1"

        # 图片生成API配置（可以使用不同的服务）
        self.image_api_url = "https://api.openai.com/v1/images/generations"
        self.image_api_key = "your-image-api-key"  # 替换为实际的API密钥

        # 对话历史
        self.conversation_history = []

    # ================= 星火大模型相关方法 =================

    def generate_report_with_spark(self, area: str, area_statistics: Dict,
                                   report_type: str = "市场分析") -> str:
        """
        使用星火大模型根据区域统计信息生成报告

        Args:
            area: 区域名称
            area_statistics: 区域统计信息
            report_type: 报告类型

        Returns:
            生成的报告内容
        """
        # 准备提示词
        prompt = self._create_report_prompt(area, area_statistics, report_type)

        # 调用星火大模型
        response = self._call_spark_api(prompt)

        # 解析响应，提取报告内容
        report_content = self._extract_report_from_response(response)

        return report_content

    def _create_report_prompt(self, area: str, statistics: Dict, report_type: str) -> str:
        """创建报告生成提示词"""
        prompt = f"""
        你是一位专业的房地产数据分析师。请根据以下区域统计信息，生成一份专业的{report_type}报告。

        【分析区域】：{area}

        【区域统计信息】：
        {json.dumps(statistics, ensure_ascii=False, indent=2)}

        【报告要求】：
        1. 报告标题：清晰明确，突出区域和分析主题
        2. 执行摘要：概括核心发现和结论
        3. 详细分析：包括市场现状、发展趋势、机会与挑战
        4. 数据解读：对关键统计数据进行专业解读
        5. 建议部分：提供针对性的市场策略或投资建议
        6. 展望：对未来3-6个月的市场趋势进行预测

        【报告格式】：
        使用标准的商业报告格式，包括：
        - 标题
        - 报告日期
        - 执行摘要
        - 正文（分章节）
        - 数据表格（用markdown格式）
        - 结论与建议
        - 附录（如有）

        【报告风格】：
        专业、客观、数据驱动，避免主观臆断。

        请生成一份完整、专业的报告。
        """
        return prompt

    def _call_spark_api(self, prompt: str) -> str:
        """调用星火大模型API"""

        class Ws_Param:
            def __init__(self, APPID, APIKey, APISecret, Spark_url):
                self.APPID = APPID
                self.APIKey = APIKey
                self.APISecret = APISecret
                self.host = urlparse(Spark_url).netloc
                self.path = urlparse(Spark_url).path
                self.Spark_url = Spark_url

            def create_url(self):
                now = datetime.now()
                date = self._format_date_time(mktime(now.timetuple()))

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

            def _format_date_time(self, timestamp):
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

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

        answer = ""

        def on_message(ws, message):
            nonlocal answer
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
                    answer += content

                if status == 2:
                    ws.close()

        def on_error(ws, error):
            print(f"\n❌ 连接错误: {error}")

        def on_close(ws, one, two):
            pass

        def on_open(ws):
            def run(*args):
                data = json.dumps(gen_params(
                    appid=ws.appid,
                    domain=ws.domain,
                    question=ws.question
                ))
                ws.send(data)

            threading.Thread(target=run).start()

        # 创建WebSocket连接
        ws_param = Ws_Param(
            self.spark_appid,
            self.spark_api_key,
            self.spark_api_secret,
            self.spark_url
        )

        websocket.enableTrace(False)
        ws_url = ws_param.create_url()

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        ws.appid = self.spark_appid
        ws.question = [{"role": "user", "content": prompt}]
        ws.domain = self.spark_domain

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return answer

    def _extract_report_from_response(self, response: str) -> str:
        """从API响应中提取报告内容"""
        # 清理响应文本，移除可能的API格式信息
        lines = response.split('\n')
        cleaned_lines = []

        for line in lines:
            # 移除一些常见的API响应格式
            if not any(marker in line for marker in ['[系统]', '[API]', '```json', '---']):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    # ================= 图片生成方法 =================

    def generate_report_image(self, report_title: str, report_summary: str,
                              area: str = None) -> Optional[bytes]:
        """
        为报告生成封面图片

        Args:
            report_title: 报告标题
            report_summary: 报告摘要
            area: 区域名称

        Returns:
            图片的字节数据，如果生成失败返回None
        """
        try:
            # 方法1：使用AI图片生成API
            image_bytes = self._generate_image_with_api(report_title, report_summary, area)
            if image_bytes:
                return image_bytes

            # 方法2：回退到本地生成简单图片
            image_bytes = self._generate_simple_image(report_title, report_summary, area)
            return image_bytes

        except Exception as e:
            print(f"生成报告图片失败: {str(e)}")
            return None

    def _generate_image_with_api(self, title: str, summary: str, area: str) -> Optional[bytes]:
        """使用AI图片生成API"""
        try:
            prompt = f"""
            为房地产分析报告生成专业封面图片：

            报告标题：{title}
            区域：{area if area else "未指定"}
            主题：{summary[:100]}...

            要求：
            1. 专业、商务风格
            2. 房地产相关元素（建筑、图表、地图等）
            3. 蓝色、金色、白色等商务配色
            4. 包含标题文字但不要遮挡主要视觉元素
            5. 简洁、现代的设计
            """

            headers = {
                "Authorization": f"Bearer {self.image_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "prompt": prompt,
                "size": "1200x800",
                "quality": "standard",
                "n": 1
            }

            response = requests.post(
                self.image_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    image_url = data['data'][0].get('url')
                    if image_url:
                        # 下载图片
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            return img_response.content

            return None

        except Exception as e:
            print(f"API图片生成失败: {str(e)}")
            return None

    def _generate_simple_image(self, title: str, summary: str, area: str) -> bytes:
        """生成简单的本地图片"""
        # 创建画布
        width, height = 1200, 800
        img = Image.new('RGB', (width, height), color='#1a237e')
        draw = ImageDraw.Draw(img)

        try:
            # 尝试加载字体
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_medium = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            # 使用默认字体
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 绘制标题
        title_lines = self._wrap_text(title, font_large, width - 200)
        title_y = 200
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, title_y), line, fill='white', font=font_large)
            title_y += 70

        # 绘制区域信息
        if area:
            area_text = f"分析区域：{area}"
            bbox = draw.textbbox((0, 0), area_text, font=font_medium)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, title_y + 40), area_text, fill='#bbdefb', font=font_medium)

        # 绘制摘要（截断）
        if summary:
            summary_short = summary[:100] + "..." if len(summary) > 100 else summary
            summary_lines = self._wrap_text(summary_short, font_small, width - 300)
            summary_y = height - 200
            for line in summary_lines:
                bbox = draw.textbbox((0, 0), line, font=font_small)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2
                draw.text((text_x, summary_y), line, fill='#e8eaf6', font=font_small)
                summary_y += 30

        # 绘制装饰线
        draw.line([(100, 150), (width - 100, 150)], fill='#3949ab', width=3)
        draw.line([(100, height - 100), (width - 100, height - 100)], fill='#3949ab', width=3)

        # 保存到字节流
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """将文本按宽度换行"""
        lines = []
        words = text.split()

        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line) if hasattr(font, 'getbbox') else (0, 0, len(test_line) * 10, 20)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    # ================= 格式化工具方法 =================

    def format_report_content(self, content: str, format_type: str = "professional") -> str:
        """
        格式化报告内容

        Args:
            content: 原始报告内容
            format_type: 格式类型（professional, academic, summary等）

        Returns:
            格式化后的报告内容
        """
        formats = {
            "professional": self._format_professional,
            "academic": self._format_academic,
            "summary": self._format_summary,
            "markdown": self._format_markdown
        }

        formatter = formats.get(format_type, self._format_professional)
        return formatter(content)

    def _format_professional(self, content: str) -> str:
        """专业商业报告格式"""
        lines = content.split('\n')
        formatted = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # 检测标题
                if line.endswith('报告') or '分析' in line or '研究' in line:
                    formatted.append(f"# {line}")
                elif '摘要' in line or '概述' in line:
                    formatted.append(f"## {line}")
                elif any(keyword in line for keyword in ['结论', '建议', '展望', '数据']):
                    formatted.append(f"### {line}")
                else:
                    formatted.append(line)

        return '\n'.join(formatted)

    def _format_academic(self, content: str) -> str:
        """学术论文格式"""
        # 这里可以添加更复杂的学术格式逻辑
        return f"**学术报告格式**\n\n{content}"

    def _format_summary(self, content: str) -> str:
        """摘要格式"""
        # 提取关键信息生成摘要
        return f"**执行摘要**\n\n{content[:500]}..."

    def _format_markdown(self, content: str) -> str:
        """Markdown格式"""
        lines = content.split('\n')
        formatted = []

        for line in lines:
            line = line.strip()
            if line:
                # 添加适当的Markdown标记
                if len(line) < 50 and not line.endswith('。'):
                    formatted.append(f"## {line}")
                else:
                    formatted.append(line)

        return '\n'.join(formatted)