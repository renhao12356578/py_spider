from flask import Blueprint, request, jsonify
import pymysql
import hashlib
import random
from config.db_config import get_db_connection

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def user_login(username: str, password: str) -> str:
    """
    实现POST /api/auth/login
    用户登录验证（使用用户基本信息表）
    :param username: 用户名
    :param password: 密码
    """
    if not username or not password:
        return json.dumps({
            "code": 400,
            "message": "用户名和密码不能为空",
            "data": {}
        }, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "message": "数据库连接失败",
            "data": {}
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 查询用户（注意：生产环境应使用密码加密存储，此处为演示）
        query = """
                SELECT id, username \
                FROM users
                WHERE username = %s \
                  AND password_hash = %s \
                """
        cursor.execute(query, (username.strip(), password.strip()))
        user = cursor.fetchone()

        if not user:
            return json.dumps({
                "code": 401,
                "message": "用户名或密码错误",
                "data": {}
            }, ensure_ascii=False)


        response = {
            "code": 200,
            "message": "登录成功",
            "data": {
                "user": {
                    "id": user['id'],
                    "username": user['username']
                }
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"登录失败: {e}")
        return json.dumps({
            "code": 500,
            "message": f"登录异常: {str(e)}",
            "data": {}
        }, ensure_ascii=False)

@auth_bp.route('/send-captcha', methods=['POST'])
def send_captcha():
    """发送验证码（模拟）"""
    data = request.get_json()
    
    if not data or 'phone' not in data:
        return jsonify({
            'code': 400,
            'message': '手机号不能为空',
            'data': None
        }), 400
    
    phone = data['phone']
    captcha_type = data.get('type', 'register')  # register | reset_password | login
    
    # 简单的手机号验证
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({
            'code': 400,
            'message': '手机号格式不正确',
            'data': None
        }), 400
    
    # 生成6位验证码（模拟）
    import random
    captcha = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    print(f"📱 [模拟] 向手机号 {phone} 发送验证码: {captcha} (类型: {captcha_type})")
    
    # 在实际项目中，这里应该调用短信服务
    # 模拟返回成功
    return jsonify({
        'code': 200,
        'message': '验证码已发送',
        'data': {
            'expires_in': 300,  # 5分钟过期
            'message': f'验证码已发送到 {phone[:3]}****{phone[-4:]}（模拟）'
        }
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['username', 'phone', 'password', 'captcha']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'code': 400,
                'message': f'{field} 不能为空',
                'data': None
            }), 400
    
    username = data['username']
    phone = data['phone']
    password = data['password']
    captcha = data['captcha']
    email = data.get('email', '')
    nickname = data.get('nickname', '')
    
    # 简单的验证码验证（模拟）
    if captcha != '123456':  # 模拟验证码
        return jsonify({
            'code': 400,
            'message': '验证码错误',
            'data': None
        }), 400
    
    # 验证用户名格式
    if not username.replace('_', '').isalnum():
        return jsonify({
            'code': 400,
            'message': '用户名只能包含字母、数字和下划线',
            'data': None
        }), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({
            'code': 400,
            'message': '用户名长度应为3-20个字符',
            'data': None
        }), 400
    
    # 验证手机号格式
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({
            'code': 400,
            'message': '手机号格式不正确（应为11位数字）',
            'data': None
        }), 400
    
    # 验证密码强度
    if len(password) < 6:
        return jsonify({
            'code': 400,
            'message': '密码长度不能少于6位',
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
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查用户名是否已存在
        check_username_query = "SELECT COUNT(*) as count FROM users WHERE username = %s"
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
        
        # 检查手机号是否已注册
        check_phone_query = "SELECT COUNT(*) as count FROM users WHERE phone = %s"
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
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if email:
            check_email_query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
            cursor.execute(check_email_query, (email,))
            email_result = cursor.fetchone()
            email_count = email_result['count'] if isinstance(email_result, dict) else email_result[0]
            
            if email_count > 0:
                cursor.close()
                connection.close()
                return jsonify({
                    'code': 400,
                    'message': '邮箱已存在',
                    'data': None
                }), 400
        
        # 生成默认昵称
        if not nickname:
            nickname = username
        
        # 生成头像URL
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
        
        # 简单密码哈希
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
        INSERT INTO users (id, username, phone, email, password_hash, nickname, avatar_url, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        cursor.execute(insert_query, (new_user_id, username, phone, email, password_hash, nickname, avatar_url))
        connection.commit()
        
        # 为用户创建默认通知设置（使用 try-except 避免表结构问题）
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
            VALUES (%s, %s, 1, 1, 0, 1, 0, 1, NOW())
            """
            cursor.execute(notification_insert_query, (notification_new_id, new_user_id))
            connection.commit()
            print(f"✅ 为用户 {new_user_id} 创建默认通知设置成功，新ID: {notification_new_id}")
        except Exception as e:
            print(f"⚠️ 创建默认通知设置失败，但用户注册成功: {e}")
            # 不回滚用户注册，只记录警告
            connection.rollback()  # 回滚 notification_settings 的插入
        
        # 生成登录token
        token = str(new_user_id)
        
        cursor.close()
        connection.close()
        
        print(f"✅ 新用户注册成功: {username} (ID: {new_user_id})")
        
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
                    'nickname': nickname
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

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """忘记密码（发送重置验证码）"""
    data = request.get_json()
    
    if not data or 'phone' not in data:
        return jsonify({
            'code': 400,
            'message': '手机号不能为空',
            'data': None
        }), 400
    
    phone = data['phone']
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败',
                'data': None
            }), 500
        
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        check_query = "SELECT COUNT(*) as count FROM users WHERE phone = %s"
        cursor.execute(check_query, (phone,))
        result = cursor.fetchone()
        
        # 处理返回结果类型
        if isinstance(result, dict):
            count = result.get('count', 0)
        else:
            count = result[0] if result else 0
        
        if count == 0:
            return jsonify({
                'code': 400,
                'message': '该手机号未注册',
                'data': None
            }), 400
        
        # 生成6位验证码（模拟）
        import random
        captcha = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        print(f"📱 [模拟] 向手机号 {phone} 发送重置密码验证码: {captcha}")
        
        return jsonify({
            'code': 200,
            'message': '验证码已发送',
            'data': {
                'expires_in': 300,  # 5分钟过期
                'message': f'验证码已发送到 {phone[:3]}****{phone[-4:]}（模拟）'
            }
        })
        
    except Exception as e:
        print(f"❌ 忘记密码请求失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        # 安全关闭数据库连接
        try:
            if cursor:
                cursor.close()
        except:
            pass
        try:
            if connection and not connection._closed:  # 检查连接是否已关闭
                connection.close()
        except:
            pass

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.get_json()
    
    required_fields = ['phone', 'captcha', 'new_password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'code': 400,
                'message': f'{field} 不能为空',
                'data': None
            }), 400
    
    phone = data['phone']
    captcha = data['captcha']
    new_password = data['new_password']
    
    # 简单的验证码验证（模拟）
    if captcha != '123456':  # 模拟验证码
        return jsonify({
            'code': 400,
            'message': '验证码错误',
            'data': None
        }), 400
    
    # 验证密码强度
    if len(new_password) < 6:
        return jsonify({
            'code': 400,
            'message': '密码长度不能少于6位',
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
        
        # 验证手机号是否存在
        check_query = "SELECT id FROM users WHERE phone = %s"
        cursor.execute(check_query, (phone,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({
                'code': 400,
                'message': '该手机号未注册',
                'data': None
            }), 400
        
        user_id = user[0] if isinstance(user, tuple) else user['id']
        
        # 更新密码
        import hashlib
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        update_query = "UPDATE users SET password_hash = %s WHERE phone = %s"
        cursor.execute(update_query, (new_password_hash, phone))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 密码重置成功")
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'code': 200,
            'message': '密码重置成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 密码重置失败: {e}")
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
            'message': '密码重置失败',
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
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        query = "SELECT COUNT(*) as count FROM users WHERE username = %s"
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

@auth_bp.route('/check-phone', methods=['GET'])
def check_phone():
    """检查手机号是否已注册"""
    phone = request.args.get('phone')
    if not phone:
        return jsonify({
            'code': 400,
            'message': '手机号不能为空',
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
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        query = "SELECT COUNT(*) as count FROM users WHERE phone = %s"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()
        
        registered = result['count'] > 0
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'registered': registered,
                'message': '手机号已注册' if registered else '手机号未注册'
            }
        })
        
    except Exception as e:
        print(f"检查手机号失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

#@auth_bp.route('/login', methods=['POST'])
#def login():
    """模拟登录接口（用于测试）"""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'code': 400,
            'message': '用户名或密码不能为空',
            'data': None
        }), 400
    
    # 简单模拟：用户名密码正确就返回token
    username = data['username']
    password = data['password']
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, username, nickname FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误',
                'data': None
            }), 401
        
        # 在实际项目中，这里应该验证密码哈希
        # 这里简单模拟：任何密码都可以登录
        
        # 生成token（实际应该用JWT）
        token = str(user['id'])  # 简单用用户ID作为token
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user.get('nickname', user['username'])
                }
            }
        })
        
    except Exception as e:
        print(f"登录失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()