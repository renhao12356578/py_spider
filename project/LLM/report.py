import pymysql
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import os


class ReportDatabase:
    """报告数据库操作类"""

    def __init__(self):
        self.db_config = {
            'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
            'port': 4000,
            'user': "48pvdQxqqjLneBr.root",
            'password': "o46hvbIhibN3tTPp",
            'database': "python_project",
            'ssl_ca': "C:/Users/xijun/tidb-ca.pem",
            'ssl_verify_cert': True,
            'ssl_verify_identity': True,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**self.db_config)
            return connection
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    # ============ 报告类型操作 ============

    def get_report_types(self) -> List[Dict]:
        """获取报告类型列表"""
        report_types = [
            {"id": "monthly", "name": "月度报告", "description": "每月市场分析"},
            {"id": "quarterly", "name": "季度报告", "description": "季度深度分析"},
            {"id": "annual", "name": "年度报告", "description": "年度全面总结"},
            {"id": "district", "name": "区域报告", "description": "特定区域分析"},
            {"id": "custom", "name": "自定义报告", "description": "根据需求定制"}
        ]
        return report_types

    # ============ 报告列表操作 ============

    def get_reports_list(
            self,
            report_type: Optional[str] = None,
            city: Optional[str] = None,
            page: int = 1,
            page_size: int = 10
    ) -> Dict[str, Any]:
        """获取报告列表（带分页）"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 构建WHERE条件
                conditions = []
                params = []

                if report_type:
                    conditions.append("type = %s")
                    params.append(report_type)

                if city:
                    conditions.append("city = %s")
                    params.append(city)

                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)

                # 查询总数
                count_query = f"SELECT COUNT(*) as total FROM reports {where_clause}"
                cursor.execute(count_query, params)
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0

                # 查询数据（带分页）
                offset = (page - 1) * page_size
                query = f"""
                    SELECT 
                        id as report_id,
                        title,
                        type,
                        city,
                        cover_image,
                        summary,
                        author,
                        published_at,
                        views,
                        download_count,
                        status,
                        is_favorited
                    FROM reports 
                    {where_clause}
                    ORDER BY published_at DESC
                    LIMIT %s OFFSET %s
                """

                params.extend([page_size, offset])
                cursor.execute(query, params)
                reports = cursor.fetchall()

                # 转换时间格式
                for report in reports:
                    if report['published_at']:
                        report['published_at'] = report['published_at'].isoformat() + 'Z'
                    # 如果没有is_favorited字段，添加默认值
                    if 'is_favorited' not in report:
                        report['is_favorited'] = False

                return {
                    "total": total,
                    "page": page,
                    "reports": reports
                }

        except Exception as e:
            print(f"获取报告列表失败: {e}")
            raise
        finally:
            connection.close()

    # ============ 报告详情操作 ============

    def get_report_detail(self, report_id: int) -> Optional[Dict]:
        """获取报告详情"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 查询报告基本信息
                query = """
                    SELECT 
                        id as report_id,
                        title,
                        type,
                        city,
                        content,
                        summary,
                        author,
                        published_at,
                        views,
                        highlights,
                        charts_data
                    FROM reports 
                    WHERE id = %s
                """
                cursor.execute(query, (report_id,))
                report = cursor.fetchone()

                if not report:
                    return None

                # 增加浏览量
                self.increment_view_count(report_id)

                # 转换时间格式
                if report['published_at']:
                    report['published_at'] = report['published_at'].isoformat() + 'Z'

                # 解析JSON字段
                if report.get('highlights'):
                    try:
                        report['highlights'] = json.loads(report['highlights'])
                    except:
                        report['highlights'] = []

                if report.get('charts_data'):
                    try:
                        report['charts_data'] = json.loads(report['charts_data'])
                    except:
                        report['charts_data'] = {}

                # 读取本地文件内容（如果content是文件路径）
                if report.get('content') and os.path.exists(report['content']):
                    try:
                        with open(report['content'], 'r', encoding='utf-8') as f:
                            report['content'] = f.read()
                    except Exception as e:
                        print(f"读取文件内容失败: {e}")
                        report['content'] = "<p>无法加载报告内容</p>"

                return report

        except Exception as e:
            print(f"获取报告详情失败: {e}")
            raise
        finally:
            connection.close()

    def increment_view_count(self, report_id: int):
        """增加报告浏览量"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                update_query = "UPDATE reports SET views = views + 1 WHERE id = %s"
                cursor.execute(update_query, (report_id,))
                connection.commit()
        except Exception as e:
            print(f"更新浏览量失败: {e}")
        finally:
            connection.close()

    # ============ 自定义报告生成操作 ============

    def create_custom_report(self, report_data: Dict) -> Dict:
        """创建自定义报告记录"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 生成报告标题
                title = self._generate_report_title(report_data)

                # 插入报告记录
                query = """
                    INSERT INTO reports (
                        title, type, city, status, 
                        created_at, user_id, report_params
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                params = (
                    title,
                    report_data.get('type', 'custom'),
                    report_data.get('city', ''),
                    'generating',  # 初始状态
                    datetime.now(),
                    report_data.get('user_id'),  # 从认证中获取
                    json.dumps(report_data)  # 保存请求参数
                )

                cursor.execute(query, params)
                report_id = cursor.lastrowid
                connection.commit()

                return {
                    "report_id": report_id,
                    "title": title,
                    "status": "generating",
                    "estimated_time": 30
                }

        except Exception as e:
            print(f"创建自定义报告失败: {e}")
            raise
        finally:
            connection.close()

    def _generate_report_title(self, report_data: Dict) -> str:
        """生成报告标题"""
        city = report_data.get('city', '')
        districts = report_data.get('districts', [])

        if districts:
            districts_str = '、'.join(districts[:3])  # 最多显示3个区域
            if len(districts) > 3:
                districts_str += '等'
            title = f"自定义报告 - {city}{districts_str}"
        else:
            title = f"自定义报告 - {city}"

        return title

    # ============ 我的报告操作 ============

    def get_user_reports(self, user_id: int) -> List[Dict]:
        """获取用户的报告"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT 
                        id as report_id,
                        title,
                        type,
                        status,
                        created_at,
                        content as download_url,
                        progress
                    FROM reports 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """
                cursor.execute(query, (user_id,))
                reports = cursor.fetchall()

                # 转换时间格式和内容处理
                for report in reports:
                    if report['created_at']:
                        report['created_at'] = report['created_at'].isoformat() + 'Z'

                    # 根据状态设置下载URL
                    if report['status'] == 'completed' and report['download_url']:
                        # 如果是文件路径，转换为可下载的URL
                        if os.path.exists(report['download_url']):
                            filename = os.path.basename(report['download_url'])
                            report['download_url'] = f"/api/reports/download/{filename}"
                        else:
                            report['download_url'] = None
                    else:
                        report['download_url'] = None

                return reports

        except Exception as e:
            print(f"获取用户报告失败: {e}")
            raise
        finally:
            connection.close()

    # ============ 工具方法 ============

    def update_report_status(self, report_id: int, status: str, content_path: str = None):
        """更新报告状态和内容"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                if content_path:
                    query = "UPDATE reports SET status = %s, content = %s WHERE id = %s"
                    cursor.execute(query, (status, content_path, report_id))
                else:
                    query = "UPDATE reports SET status = %s WHERE id = %s"
                    cursor.execute(query, (status, report_id))
                connection.commit()
        except Exception as e:
            print(f"更新报告状态失败: {e}")
            raise
        finally:
            connection.close()