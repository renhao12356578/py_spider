from flask import Blueprint, request, jsonify
import pymysql
import hashlib
from decorators import require_auth
from config.db_config import get_db_connection

# 创建蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """获取用户信息"""
    user_id = request.user_id
    
    print(f"🔍 [DEBUG] 获取用户信息，用户ID: {user_id}")
    
    connection = get_db_connection()
    if not connection:
        print("❌ [DEBUG] 数据库连接失败")
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 先检查用户是否存在
        check_query = "SELECT COUNT(*) as count FROM users WHERE id = %s"
        cursor.execute(check_query, (user_id,))
        count_result = cursor.fetchone()
        print(f"🔍 [DEBUG] 用户存在检查结果: {count_result}")
        
        if not count_result or count_result['count'] == 0:
            print(f"❌ [DEBUG] 用户不存在，ID: {user_id}")
            cursor.close()
            connection.close()
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 获取用户详细信息
        query = """
        SELECT 
            id, username, phone, email, 
            COALESCE(nickname, username) as nickname,
            COALESCE(avatar_url, '') as avatar_url,
            created_at
        FROM users WHERE id = %s
        """
        
        print(f"🔍 [DEBUG] 执行用户查询: {query}")
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        
        print(f"🔍 [DEBUG] 查询结果类型: {type(user)}")
        print(f"🔍 [DEBUG] 查询结果: {user}")
        
        if not user:
            print(f"❌ [DEBUG] 查询返回None")
            cursor.close()
            connection.close()
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 检查user是否是字典
        if not isinstance(user, dict):
            print(f"❌ [DEBUG] user不是字典，而是: {type(user)}")
            cursor.close()
            connection.close()
            return jsonify({
                'code': 500,
                'message': f'数据库查询结果格式错误，期望字典但得到 {type(user)}',
                'data': None
            }), 500
        
        # 处理 datetime 对象
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
        
        # 隐藏敏感信息
        if user.get('phone'):
            phone = user['phone']
            if len(phone) >= 11:
                user['phone'] = phone[:3] + '****' + phone[-4:]
        
        if user.get('email'):
            email = user['email']
            parts = email.split('@')
            if len(parts) == 2:
                username_part = parts[0]
                if len(username_part) > 2:
                    user['email'] = username_part[0] + '***' + username_part[-1] + '@' + parts[1]
                else:
                    user['email'] = '*' * len(username_part) + '@' + parts[1]
        
        # 添加虚拟VIP信息
        user['vip_level'] = 1
        user['vip_expire'] = '2025-01-01'
        
        print(f"✅ [DEBUG] 成功获取用户信息: {user.get('username', '未知用户')}")
        
        cursor.close()
        connection.close()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': user
        })
        
    except Exception as e:
        print(f"❌ [DEBUG] 获取用户信息异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500

@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_user_profile():
    """更新用户信息"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空',
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
        
        # 构建更新字段
        update_fields = []
        update_values = []
        
        if 'nickname' in data:
            update_fields.append("nickname = %s")
            update_values.append(data['nickname'])
        
        if 'email' in data:
            # 验证邮箱格式（简单验证）
            if '@' not in data['email']:
                return jsonify({
                    'code': 400,
                    'message': '邮箱格式不正确',
                    'data': None
                }), 400
            update_fields.append("email = %s")
            update_values.append(data['email'])
        if 'phone' in data:
            # 简单的手机号验证（11位数字）
            if not str(data['phone']).isdigit() or len(str(data['phone'])) != 11:
                return jsonify({
                    'code': 400,
                    'message': '手机号格式不正确（应为11位数字）',
                    'data': None
                }), 400
            update_fields.append("phone = %s")
            update_values.append(str(data['phone']))  # 确保是字符串
        
        if 'username' in data:
            # 检查用户名是否已存在（排除当前用户）
            check_query = "SELECT COUNT(*) as count FROM users WHERE username = %s AND id != %s"
            cursor.execute(check_query, (data['username'], user_id))
            check_result = cursor.fetchone()
            
            if isinstance(check_result, tuple):
                count = check_result[0]
            else:
                count = check_result.get('count', 0)
            
            if count > 0:
                return jsonify({
                    'code': 400,
                    'message': '用户名已存在',
                    'data': None
                }), 400
            
            update_fields.append("username = %s")
            update_values.append(data['username'])
            
        if not update_fields:
            return jsonify({
                'code': 400,
                'message': '没有可更新的字段',
                'data': None
            }), 400
        
        update_values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, tuple(update_values))
        connection.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"更新用户信息失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@user_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """修改密码"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data or 'old_password' not in data or 'new_password' not in data:
        return jsonify({
            'code': 400,
            'message': '请提供旧密码和新密码',
            'data': None
        }), 400
    
    old_password = data['old_password']
    new_password = data['new_password']
    
    if len(new_password) < 6:
        return jsonify({
            'code': 400,
            'message': '新密码长度不能少于6位',
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
        
        # 获取当前用户的密码哈希
        query = "SELECT password_hash FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 验证旧密码（简单比较，实际应该使用哈希比较）
        # 这里假设password_hash存储的是明文密码（仅用于演示）
        if user['password_hash'] != old_password:
            return jsonify({
                'code': 400,
                'message': '旧密码不正确',
                'data': None
            }), 400
        
        # 更新密码
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
        cursor.execute(update_query, (new_password, user_id))
        connection.commit()
        
        return jsonify({
            'code': 200,
            'message': '密码修改成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"修改密码失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@user_bp.route('/notifications/settings', methods=['GET'])
@require_auth
def get_notification_settings():
    """获取通知设置"""
    user_id = request.user_id
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT 
            price_alert, new_listing, market_report,
            system_notice, email_notify, sms_notify
        FROM notification_settings 
        WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        settings = cursor.fetchone()
        
        if not settings:
            # 如果没有设置，创建默认设置
            default_settings = {
                'price_alert': 1,
                'new_listing': 1,
                'market_report': 0,
                'system_notice': 1,
                'email_notify': 0,
                'sms_notify': 1
            }
            insert_query = """
            INSERT INTO notification_settings 
            (user_id, price_alert, new_listing, market_report, 
             system_notice, email_notify, sms_notify, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (user_id, *default_settings.values()))
            connection.commit()
            settings = default_settings
        else:
            # 将数据库中的0/1转换为布尔值
            settings = {k: bool(v) for k, v in settings.items()}
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': settings
        })
        
    except Exception as e:
        print(f"获取通知设置失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@user_bp.route('/notifications/settings', methods=['PUT'])
@require_auth
def update_notification_settings():
    """更新通知设置"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空',
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
        
        # 检查是否已有设置
        check_query = "SELECT COUNT(*) as count FROM notification_settings WHERE user_id = %s"
        cursor.execute(check_query, (user_id,))
        result = cursor.fetchone()
        
        # 处理返回结果类型
        if isinstance(result, tuple):
            count = result[0]
        else:
            count = result.get('count', 0)
        
        if count > 0:
            # 更新现有设置
            update_fields = []
            update_values = []
            
            for field in ['price_alert', 'new_listing', 'market_report', 
                          'system_notice', 'email_notify', 'sms_notify']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(1 if data[field] else 0)
            
            if update_fields:
                update_values.append(user_id)
                query = f"""
                UPDATE notification_settings 
                SET {', '.join(update_fields)} 
                WHERE user_id = %s
                """
                cursor.execute(query, tuple(update_values))
        else:
            # 插入新设置
            insert_query = """
            INSERT INTO notification_settings 
            (user_id, price_alert, new_listing, market_report, 
             system_notice, email_notify, sms_notify, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            default_values = [
                1 if data.get('price_alert', True) else 0,
                1 if data.get('new_listing', True) else 0,
                1 if data.get('market_report', False) else 0,
                1 if data.get('system_notice', True) else 0,
                1 if data.get('email_notify', False) else 0,
                1 if data.get('sms_notify', True) else 0
            ]
            cursor.execute(insert_query, (user_id, *default_values))
        
        connection.commit()
        
        return jsonify({
            'code': 200,
            'message': '设置已保存',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"更新通知设置失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 确保cursor和connection正确关闭
        try:
            cursor.close()
        except:
            pass
        try:
            connection.close()
        except:
            pass
            
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500