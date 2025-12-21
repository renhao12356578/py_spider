"""
数据库配置文件 - 统一管理所有数据库连接配置
"""
import pymysql
import os

# 数据库配置
DB_CONFIG = {
    'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    'port': 4000,
    'user': "48pvdQxqqjLneBr.root",
    'password': "o46hvbIhibN3tTPp",
    'database': "python_project",
    'ssl_ca': os.path.join(os.path.dirname(__file__), "..", "tidb-ca.pem"),
    'ssl_verify_cert': True,
    'ssl_verify_identity': True,
    'charset': 'utf8mb4',
}


def get_db_connection():
    """
    获取数据库连接的统一方法
    Returns:
        connection: pymysql连接对象，失败返回None
    """
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


def execute_query(query, params=None, fetch_one=False):
    """
    执行查询的通用方法
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_one: 是否只返回一条记录
    Returns:
        查询结果或None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    except Exception as e:
        print(f"查询执行失败: {e}")
        return None
    finally:
        connection.close()


def execute_update(query, params=None):
    """
    执行更新操作的通用方法
    Args:
        query: SQL更新语句
        params: 更新参数
    Returns:
        影响的行数或None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(query, params or ())
            connection.commit()
            return affected_rows
    except Exception as e:
        print(f"更新执行失败: {e}")
        connection.rollback()
        return None
    finally:
        connection.close()
get_db_connection()