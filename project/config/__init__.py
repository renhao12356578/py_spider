"""
配置模块初始化文件
"""
from .db_config import get_db_connection, execute_query, execute_update, DB_CONFIG

__all__ = ['get_db_connection', 'execute_query', 'execute_update', 'DB_CONFIG']
