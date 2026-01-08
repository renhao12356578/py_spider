import os
import json
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
from config import CONFIG

# 从环境变量读取讯飞星火图片生成配置
SPARK_IMAGE_APPID = CONFIG['spark_image']['appid']
SPARK_IMAGE_API_SECRET = CONFIG['spark_image']['api_secret']
SPARK_IMAGE_API_KEY = CONFIG['spark_image']['api_key']
SPARK_IMAGE_API_HOST = CONFIG['spark_image']['api_host']


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
            
            text = data["payload"]["choices"]["text"]
            image_content = text[0]
            image_base64 = image_content["content"]
            
            frontend_reports_path = os.path.join(os.path.dirname(__file__), '..', '..', 'project_web', 'reports')
            os.makedirs(frontend_reports_path, exist_ok=True)
            
            filename = f"spark_image_{int(time.time())}.png"
            filepath = os.path.join(frontend_reports_path, filename)
            
            try:
                image_data = base64.b64decode(image_base64)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                print(f'图片已保存到: {filepath}')
            except Exception as save_error:
                print(f'保存图片失败: {str(save_error)}')
                return None
            
            return f"reports/{filename}"
            
        else:
            print(f'请求失败,状态码: {response.status_code}')
            return None
            
    except Exception as e:
        print(f'生成图片异常: {str(e)}')
        return None


class ReportDatabase:
    """报告数据库管理类 - SQLite版本"""

    def __init__(self, storage_path='reports_storage'):
        self.storage_path = storage_path
        frontend_reports_path = os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    '..',
                    'project_web',
                    'reports_storage'
                )
        self.txt_path = os.path.join(storage_path, 'texts')
        self.img_path = os.path.join(frontend_reports_path, 'images')

        self.ai_service = LLMAIService()

        os.makedirs(self.txt_path, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)

    def generate_ai_report(self, area: str, report_type: str = "市场分析",
                           city: str = None, user_id: str = None) -> Dict:
        """使用AI生成区域分析报告"""
        try:
            area_statistics = get_area_statistics(area)
            report_content = self.ai_service.generate_report_with_spark(
                area=area,
                area_statistics=area_statistics,
                report_type=report_type
            )
            formatted_content = self.ai_service.format_report_content(
                content=report_content,
                format_type="professional"
            )
            title = f"{area}{report_type}报告"
            summary = self._generate_summary_from_content(formatted_content)
            
            result = self.create_report(
                title=title,
                summary=summary,
                content=formatted_content,
                report_type=report_type,
                city=city or area,
                user_id=user_id
            )

            return {
                "report_id": result.get("report_id"),
                "title": title,
                "summary": summary,
                "content_preview": formatted_content[:200] + "...",
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

    def format_existing_report(self, content: str, format_type: str = "professional") -> str:
        """格式化现有报告内容"""
        return self.ai_service.format_report_content(content, format_type)

    def batch_generate_ai_reports(self, areas: List[str], report_type: str = "市场分析",
                                  city: str = None, user_id: str = None) -> List[Dict]:
        """批量生成多个区域的AI报告"""
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
        """保存base64图片到本地"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.png"
            filepath = os.path.join(self.img_path, filename)

            image_data = base64.b64decode(image_data_b64)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            return filename

        except Exception as e:
            print(f"保存图片失败: {e}")
            return None

    def create_report(self, title: str, summary: str, content: str,
                     report_type: str = None, city: str = None, user_id: str = None) -> Dict:
        """创建报告记录 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return {"success": False, "error": "数据库连接失败"}

        try:
            cursor = connection.cursor()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_filename = f"report_{timestamp}.txt"
            txt_filepath = os.path.join(self.txt_path, txt_filename)

            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            insert_query = """
                INSERT INTO reports (
                    title, summary, txt_path, 
                    type, city, user_id, 
                    created_at, updated_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'completed')
            """

            cursor.execute(insert_query, (
                title, summary, txt_filepath,
                report_type, city, user_id
            ))

            report_id = cursor.lastrowid
            connection.commit()

            return {
                "success": True,
                "report_id": report_id,
                "txt_path": txt_filepath,
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
                                      user_id: str = None, generate_image: bool = False) -> Dict:
        """创建报告，支持AI续写 - SQLite版本（已禁用图片生成）"""
        connection = get_db_connection()
        if not connection:
            return {"success": False, "error": "数据库连接失败"}

        try:
            cursor = connection.cursor()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_filename = f"report_{timestamp}.txt"
            txt_filepath = os.path.join(self.txt_path, txt_filename)

            try:
                with open(txt_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                return {"success": False, "error": f"保存文本文件失败: {e}"}

            insert_query = """
                INSERT INTO reports (
                    title, summary, txt_path, 
                    type, city, user_id, 
                    created_at, updated_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'completed')
            """

            cursor.execute(insert_query, (
                title, summary, txt_filepath,
                report_type, city, user_id
            ))

            report_id = cursor.lastrowid
            connection.commit()

            return {
                "success": True,
                "report_id": report_id,
                "txt_path": txt_filepath,
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
        """AI续写报告内容"""
        try:
            result = self.ai_service.continue_writing(current_content, style, length)

            if result["success"]:
                update_success = self._update_report_content(report_id, result["full_content"])

                if update_success:
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
        """更新报告内容 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            cursor.execute("SELECT txt_path FROM reports WHERE id = ?", (report_id,))
            result = cursor.fetchone()

            if result and result[0]:
                with open(result[0], 'w', encoding='utf-8') as f:
                    f.write(new_content)

                cursor.execute("""
                    UPDATE reports 
                    SET updated_at = datetime('now')
                    WHERE id = ?
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
        """使用讯飞星火为内容生成图片 - SQLite版本"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT txt_path FROM reports WHERE id = ?", (report_id,))
            report = cursor.fetchone()

            cursor.close()
            connection.close()

            content_preview = new_content[:100] if len(new_content) > 100 else new_content
            prompt = f"根据以下内容生成配图：{content_preview}，风格专业，商务化"
            
            image_base64 = generate_image_with_spark(prompt)

            if image_base64:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = self.save_image_from_base64(
                    image_base64,
                    prefix=f"content_{report_id}_{timestamp}"
                )

                if image_filename:
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

    def _associate_image_with_report(self, report_id: int, image_filename: str, image_type: str):
        """将图片关联到报告 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return

        try:
            cursor = connection.cursor()

            image_path = os.path.join(self.img_path, image_filename)

            cursor.execute("""
                INSERT INTO report_images (
                    report_id, image_path, image_type, created_at
                ) VALUES (?, ?, ?, datetime('now'))
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
        """保存内容历史记录 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return

        try:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO report_content_history (
                    report_id, content, user_id, created_at
                ) VALUES (?, ?, ?, datetime('now'))
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
        """获取内容历史记录 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT id, content, user_id, created_at
                FROM report_content_history
                WHERE report_id = ?
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
        """获取报告详情 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return None
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, title, summary, type, city, status,
                       created_at, updated_at, txt_path
                FROM reports WHERE id = ?
            """, (report_id,))
            report = cursor.fetchone()
            if not report:
                return None
            
            content = ''
            txt_path = report[8] if len(report) > 8 else None
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
                content = report[2] or '暂无内容'
            
            cursor.close()
            connection.close()
            
            return {
                "id": report[0],
                "title": report[1],
                "summary": report[2],
                "content": content,
                "type": report[3],
                "city": report[4],
                "status": report[5] or 'completed',
                "created_at": report[6],
                "updated_at": report[7]
            }
        except Exception as e:
            print(f"获取报告详情失败: {e}")
            if connection:
                connection.close()
            return None

    def get_reports_list(self, report_type: str = None, city: str = None, page: int = 1, page_size: int = 10) -> Dict:
        """获取报告列表 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return {"reports": [], "total": 0}
        try:
            cursor = connection.cursor()
            where_conditions = []
            params = []
            if report_type:
                where_conditions.append("type = ?")
                params.append(report_type)
            if city:
                where_conditions.append("city = ?")
                params.append(city)
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            cursor.execute(f"SELECT COUNT(*) as total FROM reports WHERE {where_clause}", params)
            result = cursor.fetchone()
            total = result[0]
            
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT id, title, summary, type, city, status, created_at, updated_at
                FROM reports WHERE {where_clause}
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, params + [page_size, offset])
            reports = cursor.fetchall()
            
            formatted_reports = []
            for report in reports:
                formatted_reports.append({
                    "id": report[0],
                    "title": report[1],
                    "summary": report[2],
                    "type": report[3],
                    "city": report[4],
                    "status": report[5] or 'completed',
                    "ai_generated": False,
                    "created_at": report[6],
                    "updated_at": report[7]
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
                generate_image=False
            )
            if result.get('success'):
                return {'report_id': result['report_id'], 'title': title, 'status': 'completed', 'format': 'pdf'}
            else:
                raise Exception(result.get('error', '创建失败'))
        except Exception as e:
            raise Exception(f"创建自定义报告失败: {str(e)}")

    def get_user_reports(self, user_id: str, page: int = 1, page_size: int = 10) -> List[Dict]:
        """获取用户的报告列表 - SQLite版本"""
        connection = get_db_connection()
        if not connection:
            return []
        try:
            cursor = connection.cursor()
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, title, summary, type, city, status, created_at, updated_at
                FROM reports WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, (user_id, page_size, offset))
            reports = cursor.fetchall()
            
            formatted_reports = []
            for report in reports:
                formatted_reports.append({
                    "id": report[0],
                    "title": report[1],
                    "summary": report[2],
                    "type": report[3],
                    "city": report[4],
                    "status": report[5] or 'completed',
                    "created_at": report[6],
                    "updated_at": report[7]
                })
            
            cursor.close()
            connection.close()
            return formatted_reports
        except Exception as e:
            print(f"获取用户报告失败: {e}")
            if connection:
                connection.close()
            return []
