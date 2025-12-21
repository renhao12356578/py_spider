"""
公共函数模块
提供各个蓝图公用的数据库连接和装饰器
"""
import pymysql
from functools import wraps
from flask import request, jsonify
import os
import traceback

# 数据库配置（所有蓝图共享）
DB_CONFIG = {
    'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    'port': 4000,
    'user': "48pvdQxqqjLneBr.root",
    'password': "o46hvbIhibN3tTPp",
    'database': "python_project",
    'ssl_ca': "tidb-ca.pem",
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}

def get_db_connection():
    """获取数据库连接"""
    try:
        # 检查证书文件是否存在
        cert_file = DB_CONFIG['ssl_ca']
        if not os.path.exists(cert_file):
            print(f"⚠️ SSL证书文件不存在: {cert_file}")
            # 尝试不使用SSL连接
            return get_db_connection_no_ssl()
            
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def get_db_connection_no_ssl():
    """不使用SSL连接数据库（备用方案）"""
    try:
        config_no_ssl = DB_CONFIG.copy()
        config_no_ssl.pop('ssl_ca', None)
        config_no_ssl.pop('ssl_verify_cert', None)
        config_no_ssl.pop('ssl_verify_identity', None)
        
        connection = pymysql.connect(**config_no_ssl)
        print("⚠️ 使用无SSL连接成功")
        return connection
    except Exception as e:
        print(f"❌ 无SSL连接也失败: {e}")
        return None

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证令牌',
                'data': None
            }), 401
        
        # 提取token（去掉Bearer前缀）
        token = auth_header.replace('Bearer ', '').strip()
        
        try:
            user_id = int(token)
        except:
            return jsonify({
                'code': 401,
                'message': '无效的认证令牌',
                'data': None
            }), 401
        
        # 将user_id添加到请求上下文中
        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function