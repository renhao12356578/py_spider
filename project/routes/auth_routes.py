from flask import Blueprint, request, jsonify, session
import hashlib
import random
import time
from utils import get_db_connection
import json

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 验证码过期时间（5分钟）- 保留用于未来可能的邮箱验证
CAPTCHA_EXPIRE_TIME = 300

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录验证 (支持用户名或邮箱)
    POST /api/auth/login
    请求体: {"username": "xxx", "password": "xxx"}
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必需字段
        if not data:
            return jsonify({
                "code": 400,
                "message": "请求体不能为空",
                "data": {}
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "用户名和密码不能为空",
                "data": {}
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                "code": 500,
                "message": "数据库连接失败",
                "data": {}
            }), 500
        
        try:
            cursor = connection.cursor()
            
            # 查询用户 - 支持用户名或邮箱登录
            query = """
            SELECT id, username, password_hash, email
            FROM users
            WHERE username = ? OR email = ?
            """
            cursor.execute(query, (username.strip(), username.strip()))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                connection.close()
                return jsonify({
                    "code": 401,
                    "message": "用户名或密码错误",
                    "data": {}
                }), 401
            
            # 验证密码
            import hashlib
            password_hash_input = hashlib.sha256(password.strip().encode()).hexdigest()
            
            if user['password_hash'] != password_hash_input:
                cursor.close()
                connection.close()
                return jsonify({
                    "code": 401,
                    "message": "用户名或密码错误",
                    "data": {}
                }), 401
            
            # 生成token（这里简单使用用户ID作为token，生产环境应该使用JWT）
            token = str(user['id'])
            
            response = {
                "code": 200,
                "message": "登录成功",
                "data": {
                    "token": token,
                    "user": {
                        "id": user['id'],
                        "username": user['username'],
                        "email": user.get('email', '')
                    }
                }
            }
            
            cursor.close()
            connection.close()
            return jsonify(response)
            
        except Exception as e:
            print(f"登录失败: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            try:
                if connection:
                    connection.close()
            except:
                pass
                
            return jsonify({
                "code": 500,
                "message": f"登录异常: {str(e)}",
                "data": {}
            }), 500
            
    except Exception as e:
        print(f"请求解析失败: {e}")
        return jsonify({
            "code": 500,
            "message": f"请求处理失败: {str(e)}",
            "data": {}
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册 (简化版 - 无需手机号和验证码)
    POST /api/auth/register
    请求体: {
        "username": "xxx",
        "password": "xxx",
        "email": "xxx@example.com",  // 必填
        "phone": "",  // 选填，保留向后兼容
        "nickname": ""  // 选填
    }
    """
    data = request.get_json()
    
    # 验证必需字段（简化版：只需用户名、密码、邮箱）
    required_fields = ['username', 'password', 'email']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'code': 400,
                'message': f'{field} 不能为空',
                'data': None
            }), 400
    
    username = data['username'].strip()
    password = data['password'].strip()
    email = data['email'].strip()
    phone = data.get('phone', '').strip()  # 选填
    nickname = data.get('nickname', '').strip()
    
    # 验证用户名格式
    if not username.replace('_', '').isalnum():
        return jsonify({
            'code': 400,
            'message': '用户名只能包含字母、数字和下划线',
            'data': None
        }), 400
    
    if len(username) < 4 or len(username) > 16:
        return jsonify({
            'code': 400,
            'message': '用户名长度应为4-16个字符',
            'data': None
        }), 400
    
    # 验证邮箱格式
    if '@' not in email or '.' not in email:
        return jsonify({
            'code': 400,
            'message': '邮箱格式不正确',
            'data': None
        }), 400
    
    # 验证密码强度
    if len(password) < 8:
        return jsonify({
            'code': 400,
            'message': '密码长度不能少于8位',
            'data': None
        }), 400
    
    # 验证手机号格式（如果提供）
    if phone and (not phone.isdigit() or len(phone) != 11):
        return jsonify({
            'code': 400,
            'message': '手机号格式不正确（应为11位数字）',
            'data': None
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        
        # 检查用户名是否已存在
        check_username_query = "SELECT COUNT(*) as count FROM users WHERE username = ?"
        cursor.execute(check_username_query, (username,))
        username_result = cursor.fetchone()
        username_count = username_result['count'] if isinstance(username_result, dict) else username_result[0]
        
        if username_count > 0:
            cursor.close()
            connection.close()
            return jsonify({
                'code': 400,
                'message': '用户名已存在',
                'data': None
            }), 400
        
        # 检查邮箱是否已存在
        check_email_query = "SELECT COUNT(*) as count FROM users WHERE email = ?"
        cursor.execute(check_email_query, (email,))
        email_result = cursor.fetchone()
        email_count = email_result['count'] if isinstance(email_result, dict) else email_result[0]
        
        if email_count > 0:
            cursor.close()
            connection.close()
            return jsonify({
                'code': 400,
                'message': '邮箱已被注册',
                'data': None
            }), 400
        
        # 检查手机号是否已注册（如果提供）
        if phone:
            check_phone_query = "SELECT COUNT(*) as count FROM users WHERE phone = ?"
            cursor.execute(check_phone_query, (phone,))
            phone_result = cursor.fetchone()
            phone_count = phone_result['count'] if isinstance(phone_result, dict) else phone_result[0]
            
            if phone_count > 0:
                cursor.close()
                connection.close()
                return jsonify({
                    'code': 400,
                    'message': '手机号已注册',
                    'data': None
                }), 400
        
        # 生成默认昵称
        if not nickname:
            nickname = username
        
        # 生成头像URL
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
        
        # 密码哈希 (SHA256)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 获取当前最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM users"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        
        # 处理最大ID结果
        if isinstance(max_id_result, dict):
            max_id = max_id_result.get('max_id', 0)
        else:
            max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0
        
        # 新ID为最大ID加1
        new_user_id = max_id + 1 if max_id else 1
        
        # 插入新用户
        insert_query = """
        INSERT INTO users (id, username, email, phone, password_hash, nickname, avatar_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """
        
        cursor.execute(insert_query, (new_user_id, username, email, phone or None, password_hash, nickname, avatar_url))
        connection.commit()
        
        # 为用户创建默认通知设置
        try:
            # 获取notification_settings表的最大ID
            notification_max_id_query = "SELECT MAX(id) as max_id FROM notification_settings"
            cursor.execute(notification_max_id_query)
            notification_max_id_result = cursor.fetchone()
            
            if isinstance(notification_max_id_result, dict):
                notification_max_id = notification_max_id_result.get('max_id', 0)
            else:
                notification_max_id = notification_max_id_result[0] if notification_max_id_result and notification_max_id_result[0] else 0
            
            notification_new_id = notification_max_id + 1 if notification_max_id else 1
            
            notification_insert_query = """
            INSERT INTO notification_settings 
            (id, user_id, price_alert, new_listing, market_report, system_notice, email_notify, sms_notify, created_at)
            VALUES (?, ?, 1, 1, 0, 1, 0, 0, datetime('now'))
            """
            cursor.execute(notification_insert_query, (notification_new_id, new_user_id))
            connection.commit()
            print(f"✅ 为用户 {new_user_id} 创建默认通知设置成功，新ID: {notification_new_id}")
        except Exception as e:
            print(f"⚠️ 创建默认通知设置失败，但用户注册成功: {e}")
            # 不回滚用户注册，只记录警告
        
        # 生成登录token
        token = str(new_user_id)
        
        cursor.close()
        connection.close()
        
        print(f"✅ 新用户注册成功: {username} (ID: {new_user_id}, Email: {email})")
        
        return jsonify({
            'code': 200,
            'message': '注册成功',
            'data': {
                'user_id': new_user_id,
                'username': username,
                'token': token,
                'user': {
                    'id': new_user_id,
                    'username': username,
                    'nickname': nickname,
                    'email': email
                }
            }
        })
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 用户注册失败: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            if cursor:
                cursor.close()
        except:
            pass
        try:
            if connection:
                connection.close()
        except:
            pass
            
        return jsonify({
            'code': 500,
            'message': f'注册失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/check-username', methods=['GET'])
def check_username():
    """检查用户名是否可用"""
    username = request.args.get('username')
    if not username:
        return jsonify({
            'code': 400,
            'message': '用户名不能为空',
            'data': None
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        query = "SELECT COUNT(*) as count FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        available = result['count'] == 0
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'available': available,
                'message': '用户名可用' if available else '用户名已存在'
            }
        })
        
    except Exception as e:
        print(f"检查用户名失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@auth_bp.route('/check-email', methods=['GET'])
def check_email():
    """检查邮箱是否已注册"""
    email = request.args.get('email')
    if not email:
        return jsonify({
            'code': 400,
            'message': '邮箱不能为空',
            'data': None
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        query = "SELECT COUNT(*) as count FROM users WHERE email = ?"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        registered = result['count'] > 0
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'registered': registered,
                'available': not registered,
                'message': '邮箱已注册' if registered else '邮箱可用'
            }
        })
        
    except Exception as e:
        print(f"检查邮箱失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户退出登录
    POST /api/auth/logout
    """
    # 清除session（如果使用了session）
    session.clear()
    
    return jsonify({
        'code': 200,
        'message': '已退出登录',
        'data': None
    })

# 清理过期验证码的定时任务（保留用于未来可能的邮箱验证）
def clean_expired_captchas():
    """清理过期的验证码"""
    try:
        current_time = time.time()
        keys_to_remove = []
        
        for key, value in session.items():
            if key.startswith('captcha_'):
                if 'expires' in value and current_time > value['expires']:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            session.pop(key, None)
        
        if keys_to_remove:
            print(f"🧹 清理了 {len(keys_to_remove)} 个过期验证码")
    except Exception as e:
        print(f"清理验证码失败: {e}")

# 在每次请求后清理过期验证码
@auth_bp.after_request
def after_request(response):
    clean_expired_captchas()
    return response
