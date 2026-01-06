import os
import json
import pymysql
import base64
import time
import requests
import hashlib
import hmac
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
from urllib.parse import urlencode
from typing import Dict, List, Optional, Tuple
from .ai_service import LLMAIService

# 使用系统连接池
from utils.database import get_db_connection
from tools.house_query import get_area_statistics

# ============ 讯飞星火图片生成配置 ============
# 请在此处填写您的鉴权信息
SPARK_IMAGE_APPID = '67e25832'  # 请填写您的APPID
SPARK_IMAGE_API_SECRET = 'YTEwMTFjNTFiMTdjY2Q5ZTdhMDNkZmNj'  # 请填写您的APISecret
SPARK_IMAGE_API_KEY = '32139567bbcfdbe2309c77f2403abd48'  # 请填写您的APIKey
SPARK_IMAGE_API_HOST = 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti'
# ============================================


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
    """生成鉴权URL"""
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
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }
    
    return request_url + "?" + urlencode(values)


def get_image_generation_body(appid, text):
    """生成图片请求体"""
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


def generate_image_with_spark(prompt_text, appid=SPARK_IMAGE_APPID, 
                              api_key=SPARK_IMAGE_API_KEY, 
                              api_secret=SPARK_IMAGE_API_SECRET):
    """调用讯飞星火API生成图片"""
    try:
        url = assemble_ws_auth_url(SPARK_IMAGE_API_HOST, method='POST', 
                                   api_key=api_key, api_secret=api_secret)
        content = get_image_generation_body(appid, prompt_text)
        
        response = requests.post(url, json=content, 
                               headers={'content-type': "application/json"}, 
                               timeout=30)
        
        
        if response.status_code == 200:
            data = response.json()
            code = data['header']['code']
            
            if code != 0:
                print(f'图片生成请求错误: {code}, {data}')
                return None
            
            # 提取base64图片数据
            text = data["payload"]["choices"]["text"]
            image_content = text[0]
            image_base64 = image_content["content"]
            
            # 更新存储路径到前端 reports 文件夹
            frontend_reports_path = os.path.join(os.path.dirname(__file__), '..', '..', 'project_web', 'reports')
            os.makedirs(frontend_reports_path, exist_ok=True)  # 确保路径存在
            
            # 生成唯一的文件名(使用时间戳)
            filename = f"spark_image_{int(time.time())}.png"
            filepath = os.path.join(frontend_reports_path, filename)
            
            # 解码base64并保存为图片文件
            try:
                image_data = base64.b64decode(image_base64)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                print(f'图片已保存到: {filepath}')
            except Exception as save_error:
                print(f'保存图片失败: {str(save_error)}')
                return None
            
            # 返回相对路径（从 project_web 开始）
            return f"reports/{filename}"
            
        else:
            print(f'请求失败,状态码: {response.status_code}')
            return None
            
    except Exception as e:
        print(f'生成图片异常: {str(e)}')
        return None


class ReportDatabase:
    """报告数据库管理类"""

    def __init__(self, storage_path='reports_storage'):
        self.storage_path = storage_path
        frontend_reports_path = os.path.join(
                    os.path.dirname(__file__),  # 当前文件所在目录
                    '..',                        # 父目录
                    '..',                        # 祖父目录
                    'project_web',              # project_web 目录
                    'reports_storage'                   # reports 目录
                )
        self.txt_path = os.path.join(storage_path, 'texts')
        self.img_path = os.path.join(frontend_reports_path, 'images')

        # 初始化AI服务
        self.ai_service = LLMAIService()

        # 创建存储目录
        os.makedirs(self.txt_path, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)

    # ============ AI生成报告的核心方法 ============

    def generate_ai_report(self, area: str, report_type: str = "市场分析",
                           city: str = None, user_id: str = None) -> Dict:
        """
        使用AI生成区域分析报告

        Args:
            area: 区域名称
            report_type: 报告类型
            city: 城市
            user_id: 用户ID

        Returns:
            包含报告信息的字典
        """
        try:
            # 1. 获取区域统计信息
            area_statistics = get_area_statistics(area)

            # 2. 使用AI生成报告内容
            report_content = self.ai_service.generate_report_with_spark(
                area=area,
                area_statistics=area_statistics,
                report_type=report_type
            )

            # 3. 格式化报告内容
            formatted_content = self.ai_service.format_report_content(
                content=report_content,
                format_type="professional"
            )

            # 4. 生成报告标题和摘要
            title = f"{area}{report_type}报告"
            summary = self._generate_summary_from_content(formatted_content)

            # 5. 生成封面图片（使用新的讯飞星火方式）
            cover_image_filename = self._generate_and_save_image_spark(
                title=title,
                summary=summary,
                area=area
            )
            # 如果未生成封面图片，使用默认封面图片
            if not cover_image_filename:
                cover_image_filename ="reports_storage/images/default_report_cover.png"

            # 6. 保存报告到数据库
            result = self.create_report(
                title=title,
                summary=summary,
                content=formatted_content,
                cover_image_filename=cover_image_filename,
                report_type=report_type,
                city=city or area,
                user_id=user_id
            )

            # 7. 返回完整结果
            return {
                "report_id": result['report_id'],
                "title": title,
                "summary": summary,
                "content_preview": formatted_content[:200] + "...",
                "cover_image": cover_image_filename,
                "area": area,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "ai_generated": True
            }

        except Exception as e:
            raise Exception(f"AI生成报告失败: {str(e)}")

    def _generate_summary_from_content(self, content: str) -> str:
        """从报告内容中提取摘要"""
        if len(content) > 200:
            return content[:197] + "..."
        return content

    def _generate_and_save_image_spark(self, title: str, summary: str, area: str) -> str:
        """
        使用讯飞星火生成并保存封面图片
        
        Args:
            title: 报告标题
            summary: 报告摘要
            area: 区域名称
            
        Returns:
            图片文件名（相对路径 reports_storage/images/filename）
        """
        try:
            # 构建图片生成提示词
            prompt = f"生成一张专业的房地产市场报告封面图：{title}，展现{area}地区的城市景观和现代建筑，风格简约大气，商务风格"
            
            # 调用讯飞星火生成图片，传入保存路径
            filename = generate_image_with_spark(prompt, save_path=self.img_path)
            
            if filename:
                print(f"图片已生成: {filename}")
                # 返回相对路径（从 project_web 开始）
                return f"reports_storage/images/{filename}"
            else:
                print("图片生成失败，使用默认封面")
                return "reports_storage/images/default_report_cover.png"

        except Exception as e:
            print(f"生成图片失败: {e}")
            return "reports_storage/images/default_report_cover.png"


    # ============ 格式化现有内容的方法 ============

    def format_existing_report(self, content: str, format_type: str = "professional") -> str:
        """
        格式化现有报告内容

        Args:
            content: 原始报告内容
            format_type: 格式类型

        Returns:
            格式化后的内容
        """
        return self.ai_service.format_report_content(content, format_type)

    # ============ 批量AI生成方法 ============

    def batch_generate_ai_reports(self, areas: List[str], report_type: str = "市场分析",
                                  city: str = None, user_id: str = None) -> List[Dict]:
        """
        批量生成多个区域的AI报告

        Args:
            areas: 区域名称列表
            report_type: 报告类型
            city: 城市
            user_id: 用户ID

        Returns:
            报告生成结果列表
        """
        results = []

        for area in areas:
            try:
                result = self.generate_ai_report(
                    area=area,
                    report_type=report_type,
                    city=city,
                    user_id=user_id
                )
                result['status'] = 'success'
            except Exception as e:
                result = {
                    'area': area,
                    'status': 'failed',
                    'error': str(e)
                }

            results.append(result)

        return results

    def save_image_from_base64(self, image_data_b64: str, prefix: str = "report") -> str:
        """
        保存base64图片到本地

        Args:
            image_data_b64: base64编码的图片数据
            prefix: 文件名前缀

        Returns:
            图片文件名
        """
        try:
            # 生成唯一的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.png"
            filepath = os.path.join(self.img_path, filename)

            # 解码并保存图片
            image_data = base64.b64decode(image_data_b64)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            return filename

        except Exception as e:
            print(f"保存图片失败: {e}")
            return None

    def create_report(self, title: str, summary: str, content: str,
                     cover_image_filename: str = None, report_type: str = None,
                     city: str = None, user_id: str = None) -> Dict:
        """
        创建报告记录
        
        Args:
            title: 报告标题
            summary: 报告摘要
            content: 报告内容
            cover_image_filename: 封面图片文件名
            report_type: 报告类型
            city: 城市
            user_id: 用户ID
            
        Returns:
            创建结果
        """
        connection = get_db_connection()
        if not connection:
            return {"success": False, "error": "数据库连接失败"}

        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            # 生成文本文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_filename = f"report_{timestamp}.txt"
            txt_filepath = os.path.join(self.txt_path, txt_filename)

            # 保存文本内容
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            # 构建封面图片完整路径
            cover_image_path = None
            if cover_image_filename:
                cover_image_path = os.path.join(self.img_path, cover_image_filename)

            # 插入数据库记录
            insert_query = """
                INSERT INTO reports (
                    title, summary, txt_path, cover_image_path, 
                    type, city, user_id, 
                    created_at, updated_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'completed')
            """

            cursor.execute(insert_query, (
                title, summary, txt_filepath, cover_image_path,
                report_type, city, user_id
            ))

            report_id = cursor.lastrowid
            connection.commit()

            return {
                "success": True,
                "report_id": report_id,
                "txt_path": txt_filepath,
                "cover_image_path": cover_image_path,
                "message": "报告创建成功"
            }

        except Exception as e:
            connection.rollback()
            return {"success": False, "error": f"创建报告失败: {str(e)}"}

        finally:
            if connection:
                cursor.close()
                connection.close()

    def create_report_with_ai_support(self, title: str, summary: str, content: str,
                                      report_type: str = None, city: str = None,
                                      user_id: str = None, generate_image: bool = True) -> Dict:
        """
        创建报告，支持AI续写和图片生成（使用讯飞星火）

        Args:
            title: 报告标题
            summary: 报告摘要
            content: 报告内容
            report_type: 报告类型
            city: 城市
            user_id: 用户ID
            generate_image: 是否生成图片

        Returns:
            创建结果
        """
        connection = get_db_connection()
        if not connection:
            return {"success": False, "error": "数据库连接失败"}

        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            # 生成唯一的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_filename = f"report_{timestamp}.txt"
            txt_filepath = os.path.join(self.txt_path, txt_filename)

            # 保存文本内容
            try:
                with open(txt_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                return {"success": False, "error": f"保存文本文件失败: {e}"}

            # 生成并保存图片（使用讯飞星火）
            cover_image_path = None
            if generate_image and content:
                prompt = f"生成一张专业的{title}封面图，展现{city or '现代城市'}的建筑景观，商务风格，简约大气"
                image_base64 = generate_image_with_spark(prompt)
                
                if image_base64:
                    image_filename = self.save_image_from_base64(
                        image_base64,
                        prefix=f"cover_{timestamp}"
                    )
                    if image_filename:
                        cover_image_path ="reports_storage/images/default_report_cover.png"

            # 插入数据库记录
            insert_query = """
                INSERT INTO reports (
                    title, summary, txt_path, cover_image_path, 
                    type, city, user_id, 
                    created_at, updated_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'completed')
            """

            cursor.execute(insert_query, (
                title, summary, txt_filepath, cover_image_path,
                report_type, city, user_id
            ))

            report_id = cursor.lastrowid
            connection.commit()

            return {
                "success": True,
                "report_id": report_id,
                "txt_path": txt_filepath,
                "cover_image_path": cover_image_path,
                "has_image": cover_image_path is not None,
                "message": "报告创建成功"
            }

        except Exception as e:
            connection.rollback()
            return {"success": False, "error": f"创建报告失败: {str(e)}"}

        finally:
            if connection:
                cursor.close()
                connection.close()

    def continue_writing(self, report_id: int, current_content: str,
                         style: str = None, length: int = None) -> Dict:
        """
        AI续写报告内容

        Args:
            report_id: 报告ID
            current_content: 当前内容
            style: 续写风格
            length: 续写长度

        Returns:
            续写结果
        """
        try:
            # 调用AI服务续写
            result = self.ai_service.continue_writing(current_content, style, length)

            if result["success"]:
                # 更新报告内容
                update_success = self._update_report_content(report_id, result["full_content"])

                if update_success:
                    # 生成相关图片（使用讯飞星火）
                    image_result = self._generate_content_image_spark(report_id, result["continuation"])

                    return {
                        "success": True,
                        "continuation": result["continuation"],
                        "full_content": result["full_content"],
                        "image_generated": image_result["success"],
                        "image_info": image_result if image_result["success"] else None,
                        "similarity_score": result.get("similarity_score", 0),
                        "quality_score": result.get("quality_score", 0),
                        "tokens_used": result.get("tokens_used", 0)
                    }

            return {
                "success": False,
                "error": result.get("error", "续写失败"),
                "details": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"续写失败: {str(e)}"
            }

    def _update_report_content(self, report_id: int, new_content: str) -> bool:
        """更新报告内容"""
        connection = get_db_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # 获取原始文件路径
            cursor.execute("SELECT txt_path FROM reports WHERE id = %s", (report_id,))
            result = cursor.fetchone()

            if result and result[0]:
                # 写入新内容
                with open(result[0], 'w', encoding='utf-8') as f:
                    f.write(new_content)

                # 更新数据库记录
                cursor.execute("""
                    UPDATE reports 
                    SET updated_at = NOW()
                    WHERE id = %s
                """, (report_id,))

                connection.commit()
                return True

            return False

        except Exception as e:
            connection.rollback()
            print(f"更新内容失败: {e}")
            return False

        finally:
            if connection:
                cursor.close()
                connection.close()

    def _generate_content_image_spark(self, report_id: int, new_content: str) -> Dict:
        """使用讯飞星火为内容生成图片"""
        try:
            # 获取报告信息
            connection = get_db_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT title FROM reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()

            cursor.close()
            connection.close()

            # 构建图片提示词
            content_preview = new_content[:100] if len(new_content) > 100 else new_content
            prompt = f"根据以下内容生成配图：{content_preview}，风格专业，商务化"
            
            # 使用讯飞星火生成图片
            image_base64 = generate_image_with_spark(prompt)

            if image_base64:
                # 保存图片
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = self.save_image_from_base64(
                    image_base64,
                    prefix=f"content_{report_id}_{timestamp}"
                )

                if image_filename:
                    # 将图片关联到报告
                    self._associate_image_with_report(report_id, image_filename, "content")

                    return {
                        "success": True,
                        "image_filename": image_filename,
                        "prompt": prompt
                    }

            return {
                "success": False,
                "error": "图片生成失败"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"图片生成失败: {str(e)}"
            }

    def _generate_content_image(self, report_id: int, new_content: str) -> Dict:
        """【已弃用】旧的图片生成方法，保留以兼容"""
        return self._generate_content_image_spark(report_id, new_content)

    def _associate_image_with_report(self, report_id: int, image_filename: str, image_type: str):
        """将图片关联到报告"""
        connection = get_db_connection()
        if not connection:
            return

        try:
            cursor = connection.cursor()

            # 创建图片记录
            image_path = os.path.join(self.img_path, image_filename)

            cursor.execute("""
                INSERT INTO report_images (
                    report_id, image_path, image_type, created_at
                ) VALUES (%s, %s, %s, NOW())
            """, (report_id, image_path, image_type))

            connection.commit()

        except Exception as e:
            connection.rollback()
            print(f"关联图片失败: {e}")

        finally:
            if connection:
                cursor.close()
                connection.close()

    def _save_content_history(self, report_id: int, content: str, user_id: str):
        """保存内容历史记录"""
        connection = get_db_connection()
        if not connection:
            return

        try:
            cursor = connection.cursor()

            # 保存到内容历史表
            cursor.execute("""
                INSERT INTO report_content_history (
                    report_id, content, user_id, created_at
                ) VALUES (%s, %s, %s, NOW())
            """, (report_id, content, user_id))

            connection.commit()

        except Exception as e:
            connection.rollback()
            print(f"保存内容历史失败: {e}")

        finally:
            if connection:
                cursor.close()
                connection.close()

    def get_content_history(self, report_id: int) -> List[Dict]:
        """获取内容历史记录"""
        connection = get_db_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute("""
                SELECT id, content, user_id, created_at
                FROM report_content_history
                WHERE report_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (report_id,))

            history = cursor.fetchall()
            return history

        except Exception as e:
            print(f"获取内容历史失败: {e}")
            return []

        finally:
            if connection:
                cursor.close()
                connection.close()

    def get_report_types(self) -> List[Dict]:
        """获取报告类型列表"""
        return [
            {"id": "market_analysis", "name": "市场趋势报告", "description": "全国及重点城市房价趋势分析", "icon": "trending-up"},
            {"id": "district_analysis", "name": "城市分析报告", "description": "单一城市深度市场分析", "icon": "map-pin"},
            {"id": "comparison", "name": "城市对比报告", "description": "多城市横向对比分析", "icon": "git-compare"},
            {"id": "investment", "name": "投资价值报告", "description": "房产投资回报率分析", "icon": "dollar-sign"},
            {"id": "monthly", "name": "月度报告", "description": "月度市场动态总结", "icon": "calendar"},
            {"id": "quarterly", "name": "季度报告", "description": "季度市场趋势分析", "icon": "bar-chart-2"},
            {"id": "annual", "name": "年度报告", "description": "年度市场全景回顾", "icon": "file-bar-chart"}
        ]

    def get_report_detail(self, report_id: int) -> Dict:
        """获取报告详情"""
        connection = get_db_connection()
        if not connection:
            return None
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, title, summary, type, city, status,
                       created_at, updated_at, cover_image_path, txt_path
                FROM reports WHERE id = %s
            """, (report_id,))
            report = cursor.fetchone()
            if not report:
                return None
            content = ''
            txt_path = report.get('txt_path')
            if txt_path:
                if not os.path.isabs(txt_path):
                    txt_path = os.path.join(os.path.dirname(__file__), txt_path)
                if os.path.exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"读取报告文件失败: {e}")
            if not content:
                content = report.get('summary', '暂无内容')
            cursor.close()
            connection.close()
            return {
                "id": report['id'],
                "title": report['title'],
                "summary": report['summary'],
                "content": content,
                "type": report['type'],
                "city": report['city'],
                "status": report['status'] or 'completed',
                "created_at": report['created_at'].strftime('%Y-%m-%d %H:%M:%S') if report['created_at'] else None,
                "updated_at": report['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if report['updated_at'] else None,
                "cover_image": report['cover_image_path']
            }
        except Exception as e:
            print(f"获取报告详情失败: {e}")
            if connection:
                connection.close()
            return None

    def get_reports_list(self, report_type: str = None, city: str = None, page: int = 1, page_size: int = 10) -> Dict:
        """获取报告列表"""
        connection = get_db_connection()
        if not connection:
            return {"reports": [], "total": 0}
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            where_conditions = []
            params = []
            if report_type:
                where_conditions.append("type = %s")
                params.append(report_type)
            if city:
                where_conditions.append("city = %s")
                params.append(city)
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            cursor.execute(f"SELECT COUNT(*) as total FROM reports WHERE {where_clause}", params)
            total = cursor.fetchone()['total']
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT id, title, summary, type, city, status, created_at, updated_at, cover_image_path
                FROM reports WHERE {where_clause}
                ORDER BY created_at DESC LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            reports = cursor.fetchall()
            formatted_reports = []
            for report in reports:
                formatted_reports.append({
                    "id": report['id'],
                    "title": report['title'],
                    "summary": report['summary'],
                    "type": report['type'],
                    "city": report['city'],
                    "status": report['status'] or 'completed',
                    "ai_generated": False,
                    "created_at": report['created_at'].strftime('%Y-%m-%d %H:%M:%S') if report['created_at'] else None,
                    "updated_at": report['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if report['updated_at'] else None,
                    "cover_image": report['cover_image_path']
                })
            cursor.close()
            connection.close()
            return {"reports": formatted_reports, "total": total, "page": page, "page_size": page_size}
        except Exception as e:
            print(f"获取报告列表失败: {e}")
            if connection:
                connection.close()
            return {"reports": [], "total": 0}

    def create_custom_report(self, params: Dict) -> Dict:
        """创建自定义报告"""
        try:
            report_type = params.get('type', '自定义报告')
            city = params.get('city', '')
            user_id = params.get('user_id')
            title = f"{city}{report_type}"
            summary = f"本报告分析了{city}地区的房产市场数据"
            content = f"# {title}\n\n## 报告摘要\n{summary}\n\n## 结论\n\n根据以上数据分析，{city}地区房产市场呈现稳定发展态势。"
            result = self.create_report_with_ai_support(
                title=title,
                summary=summary,
                content=content,
                report_type=report_type,
                city=city,
                user_id=user_id,
                generate_image=True
            )
            if result.get('success'):
                return {'report_id': result['report_id'], 'title': title, 'status': 'completed', 'format': 'pdf'}
            else:
                raise Exception(result.get('error', '创建失败'))
        except Exception as e:
            raise Exception(f"创建自定义报告失败: {str(e)}")

    def get_user_reports(self, user_id: str, page: int = 1, page_size: int = 10) -> List[Dict]:
        """获取用户的报告列表"""
        connection = get_db_connection()
        if not connection:
            return []
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, title, summary, type, city, status, created_at, updated_at, cover_image_path
                FROM reports WHERE user_id = %s
                ORDER BY created_at DESC LIMIT %s OFFSET %s
            """, (user_id, page_size, offset))
            reports = cursor.fetchall()
            formatted_reports = []
            for report in reports:
                formatted_reports.append({
                    "id": report['id'],
                    "title": report['title'],
                    "summary": report['summary'],
                    "type": report['type'],
                    "city": report['city'],
                    "status": report['status'] or 'completed',
                    "created_at": report['created_at'].strftime('%Y-%m-%d %H:%M:%S') if report['created_at'] else None,
                    "updated_at": report['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if report['updated_at'] else None,
                    "cover_image": report['cover_image_path']
                })
            cursor.close()
            connection.close()
            return formatted_reports
        except Exception as e:
            print(f"获取用户报告失败: {e}")
            if connection:
                connection.close()
            return []