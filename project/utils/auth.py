"""
认证相关工具函数
提供API请求的认证装饰器
"""
from functools import wraps
from flask import request, jsonify


def require_auth(f):
    """
    认证装饰器
    验证请求头中的 Authorization token
    
    使用方式:
        @require_auth
        def my_route():
            user_id = request.user_id
            ...
    """
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
            # 简单token验证（生产环境应使用JWT）
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

