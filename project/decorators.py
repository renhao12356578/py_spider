from functools import wraps
from flask import request, jsonify

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
        
        # 在实际项目中，这里应该验证JWT token
        # 这里简单模拟：假设token就是user_id
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