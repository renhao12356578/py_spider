"""
认证相关路由
"""
from flask import Blueprint, request, jsonify
import data_process as dp

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    result = dp.user_login(username, password)
    return jsonify(eval(result))
