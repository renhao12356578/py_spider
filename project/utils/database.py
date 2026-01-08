"""
数据库连接池管理模块
提供数据库连接的创建、复用和管理
支持SQLite和MySQL数据库
"""
import sqlite3
import os
import traceback

# 数据库配置
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_CURRENT_DIR)

# 使用SQLite本地数据库
DB_TYPE = 'sqlite'
DB_CONFIG = {
    'database': os.path.join(_PROJECT_DIR, 'house_data.sqlite')
}


def init_db_pool():
    """
    初始化数据库连接池
    SQLite不需要连接池，此函数保留用于兼容性
    """
    db_path = DB_CONFIG['database']
    if os.path.exists(db_path):
        print(f"[SUCCESS] SQLite database found: {db_path}")
    else:
        print(f"[WARNING] SQLite database not found: {db_path}")
    return


def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        connection: sqlite3连接对象
    """
    return _get_direct_connection()


def _get_direct_connection():
    """
    直接创建SQLite数据库连接
    
    Returns:
        connection: sqlite3连接对象或None
    """
    try:
        db_path = DB_CONFIG['database']
        if not os.path.exists(db_path):
            print(f"[ERROR] Database file not found: {db_path}")
            return None
        
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None


def close_db_pool():
    """
    关闭数据库连接池
    SQLite不需要连接池管理，此函数保留用于兼容性
    """
    print("[INFO] SQLite connections are closed automatically")
