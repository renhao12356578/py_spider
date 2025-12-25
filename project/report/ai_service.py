# llm_service.py
import json
import threading
from typing import Dict, List, Optional
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLM.spark_client import SparkClient, call_spark_api

class LLMAIService:
    """统一的AI服务类，集成多种AI功能"""

    def __init__(self):
        # 使用统一的星火客户端
        self.spark_client = SparkClient()

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
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self._call_spark_api(prompt)
                
                # 解析响应，提取报告内容
                report_content = self._extract_report_from_response(response)
                
                # 验证内容
                is_valid, message = self.validate_report_content(report_content)
                if is_valid:
                    return report_content
                
                print(f"⚠️ 报告验证失败 (尝试 {attempt+1}/{max_retries}): {message}")
                last_error = message
                
            except Exception as e:
                print(f"❌ AI调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
                last_error = str(e)
        
        # 如果重试都失败了，返回备用内容
        return self._generate_fallback_content(area, report_type, last_error)

    def validate_report_content(self, content: str) -> tuple:
        """验证报告内容有效性"""
        if not content:
            return False, "内容为空"
            
        if len(content) < 300:
            return False, "报告内容过短"
        
        # 检查必须包含的关键词
        required_keywords = ['分析', '市场', '价格']
        missing = [k for k in required_keywords if k not in content]
        if len(missing) > 1:  # 允许缺失一个，太严可能会误杀
            return False, f"缺少关键内容: {', '.join(missing)}"
            
        # 检查是否包含拒绝生成的语句
        forbidden_phrases = ["我无法", "抱歉", "作为AI", "I cannot", "As an AI"]
        for phrase in forbidden_phrases:
            if phrase in content:
                return False, "报告包含拒绝生成或错误信息"
                
        return True, "验证通过"

    def _generate_fallback_content(self, area: str, report_type: str, error: str) -> str:
        """生成降级报告内容"""
        return f"""# {area}{report_type}报告

## ⚠️ 生成提示
由于系统繁忙或网络原因，暂时无法生成完整的详细分析报告。

## 区域概况
**{area}** 是一个受关注的区域。建议您稍后重试生成，或查看该区域的基础统计数据。

## 错误信息
{error}

## 建议
1. 检查网络连接
2. 稍后重试
3. 尝试生成其他区域的报告
"""

    def _create_report_prompt(self, area: str, statistics: Dict, report_type: str) -> str:
        """创建报告生成提示词 - 增强版"""
        
        # 检查数据可用性
        if not statistics.get('data_available', True):
            return self._create_fallback_prompt(area, report_type)
        
        # 提取关键数据
        data_source = statistics.get('data_source', 'beijing')
        
        # 构建数据摘要
        data_summary = self._format_statistics_summary(statistics)
        
        prompt = f"""
你是一位资深的房地产市场分析师，拥有10年以上的行业经验。请基于以下真实数据，撰写一份专业的{report_type}报告。

## 分析对象
区域：{area}
数据来源：{data_source}
数据时间：{statistics.get('query_time', '最新')}

## 核心数据
{data_summary}

## 报告撰写要求

### 1. 结构要求
- **标题**：{area}{report_type}报告（{datetime.now().strftime('%Y年%m月')}）
- **执行摘要**（200-300字）：提炼核心发现，包括市场定位、价格水平、供需状况
- **市场概况**：基于数据分析当前市场状态
- **价格分析**：详细解读价格分布、均价水平及价格区间
- **房源特征**：分析户型、建筑年代、配套设施等
- **市场趋势**：基于数据推断市场走向
- **投资建议**：针对不同需求群体提供建议
- **风险提示**：客观指出潜在风险

### 2. 数据使用规范
- 必须使用提供的真实数据，不得编造数据
- 数据引用时保留2位小数
- 涉及价格时明确单位（万元、元/㎡）
- 百分比数据保留1位小数

### 3. 分析深度
- 对比分析：与周边区域或市场均价对比
- 趋势判断：基于价格分布和房源特征推断
- 细分市场：针对不同价格段、户型的分析
- 实用建议：针对刚需、改善、投资等不同群体

### 4. 写作风格
- 专业严谨，使用行业术语
- 数据驱动，每个结论都有数据支撑
- 客观中立，避免过度乐观或悲观
- 逻辑清晰，层次分明
- 语言简洁，避免冗余

### 5. 格式规范
- 使用Markdown格式
- 标题层级清晰（# ## ###）
- 数据表格使用markdown表格
- 重要数据使用**加粗**
- 关键结论使用> 引用块

请严格按照以上要求，生成一份完整、专业、有价值的分析报告。
        """
        return prompt

    def _create_fallback_prompt(self, area: str, report_type: str) -> str:
        """创建备用提示词（无数据情况）"""
        return f"""
你是一位专业的房地产分析师。虽然目前暂时无法获取{area}的最新详细统计数据，但请根据你掌握的通用房地产知识和该区域的历史印象，撰写一份{report_type}框架性分析报告。

重点关注：
1. 区域宏观定位分析
2. 通用购房建议和注意事项
3. 市场风险提示
4. 如何考察该区域房产的建议

请注意：在报告开头明确标注"注：本报告基于通用市场分析，具体数据请以实际成交为准"。
        """

    def _format_statistics_summary(self, statistics: Dict) -> str:
        """格式化统计数据摘要"""
        summary = []
        
        # 基础数据
        basic = statistics.get('basic_stats', {})
        if basic:
            summary.append("### 基础数据")
            summary.append(f"- 房源数量：{basic.get('total_listings', 0)}")
            summary.append(f"- 平均总价：{basic.get('avg_total_price', 0)}万")
            summary.append(f"- 平均单价：{basic.get('avg_unit_price', 0)}元/㎡")
            summary.append(f"- 价格范围：{basic.get('min_price', 0)} - {basic.get('max_price', 0)}万")
            
        # 价格分布
        price_dist = statistics.get('price_distribution', [])
        if price_dist:
            summary.append("\n### 价格分布")
            for item in price_dist[:5]: # 取前5个
                if isinstance(item, dict):
                    # 适配不同的数据结构
                    range_name = item.get('price_range') or item.get('district_name')
                    count = item.get('count') or item.get('listing_count')
                    percent = item.get('percentage') or item.get('district_ratio')
                    if range_name:
                        summary.append(f"- {range_name}: {count}套 ({percent}%)")
                        
        # 户型分布
        layout_dist = statistics.get('layout_distribution', [])
        if layout_dist:
            summary.append("\n### 户型分布")
            for item in layout_dist[:5]:
                summary.append(f"- {item.get('layout')}: {item.get('count')}套 (均价{item.get('avg_price')}万)")
                
        return "\n".join(summary)

    def _call_spark_api(self, prompt: str) -> str:
        """调用星火大模型API"""
        return self.spark_client.chat(prompt)

    def _extract_report_from_response(self, response: str) -> str:
        """从API响应中提取报告内容 - 增强版"""
        if not response:
            return "报告生成失败，请稍后重试。"
            
        # 清理响应文本，移除可能的API格式信息
        lines = response.split('\n')
        cleaned_lines = []
        
        # 移除系统标记和无关内容
        skip_markers = ['[系统]', '[API]', '```json', '---', '```python', '助手：', 'Assistant:']

        for line in lines:
            # 跳过包含标记的行
            if any(marker in line for marker in skip_markers):
                continue
            # 跳过空行过多的情况
            if line.strip():
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1].strip():  # 保留单个空行
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines).strip()
        
        # 验证内容质量
        if len(content) < 200:
            return f"# 报告生成提示\n\n生成的内容过短，可能存在问题。原始内容：\n\n{content}"
            
        return content

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