from flask import Blueprint, request, jsonify
import pymysql
import hashlib
from utils import get_db_connection, require_auth

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
    
    print(f"🔍 [DEBUG] 收到更新用户信息请求，用户ID: {user_id}")
    print(f"🔍 [DEBUG] 请求数据: {data}")
    
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
    
    cursor = None
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 首先获取用户当前信息
        current_user_query = """
        SELECT username, nickname, email, phone 
        FROM users WHERE id = %s
        """
        cursor.execute(current_user_query, (user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            return jsonify({
                'code': 404,
                'message': '用户不存在',
                'data': None
            }), 404
        
        print(f"🔍 [DEBUG] 用户当前信息: {current_user}")
        
        # 使用字典来存储需要更新的字段和值
        updates = {}
        
        # 检查昵称更新
        if 'nickname' in data:
            new_nickname = data['nickname'].strip() if data['nickname'] is not None else ''
            current_nickname = current_user.get('nickname') or current_user.get('username', '')
            
            # 如果昵称有变化或者前端明确发送了空字符串（允许清空昵称）
            if new_nickname != current_nickname:
                updates['nickname'] = new_nickname if new_nickname else None
                print(f"🔍 [DEBUG] 更新昵称: {current_nickname} -> {new_nickname if new_nickname else 'NULL'}")
        
        # 检查邮箱更新
        if 'email' in data:
            new_email = data['email'].strip() if data['email'] is not None else ''
            current_email = current_user.get('email', '')
            
            # 如果邮箱有变化
            if new_email != current_email:
                if new_email:  # 新邮箱不为空，验证格式
                    if '@' not in new_email:
                        return jsonify({
                            'code': 400,
                            'message': '邮箱格式不正确',
                            'data': None
                        }), 400
                    updates['email'] = new_email
                    print(f"🔍 [DEBUG] 更新邮箱: {current_email} -> {new_email}")
                else:  # 清空邮箱
                    updates['email'] = None
                    print(f"🔍 [DEBUG] 清空邮箱")
        
        # 检查手机号更新
        if 'phone' in data:
            new_phone = str(data['phone']).strip() if data['phone'] is not None else ''
            current_phone = current_user.get('phone', '')
            
            # 如果手机号有变化
            if new_phone != current_phone:
                if new_phone:  # 新手机号不为空，验证格式
                    if not new_phone.isdigit() or len(new_phone) != 11:
                        return jsonify({
                            'code': 400,
                            'message': '手机号格式不正确（应为11位数字）',
                            'data': None
                        }), 400
                    updates['phone'] = new_phone
                    print(f"🔍 [DEBUG] 更新手机号: {current_phone} -> {new_phone}")
                else:  # 清空手机号
                    updates['phone'] = None
                    print(f"🔍 [DEBUG] 清空手机号")
        
        # 检查用户名更新
        if 'username' in data and data['username'] is not None:
            new_username = data['username'].strip()
            current_username = current_user.get('username', '')
            
            # 如果用户名有变化
            if new_username != current_username:
                if new_username:  # 新用户名不为空
                    # 检查用户名是否已存在（排除当前用户）
                    check_query = "SELECT COUNT(*) as count FROM users WHERE username = %s AND id != %s"
                    cursor.execute(check_query, (new_username, user_id))
                    check_result = cursor.fetchone()
                    
                    count = 0
                    if check_result:
                        if isinstance(check_result, dict) and 'count' in check_result:
                            count = check_result['count']
                        elif isinstance(check_result, tuple) and len(check_result) > 0:
                            count = check_result[0]
                    
                    if count > 0:
                        return jsonify({
                            'code': 400,
                            'message': '用户名已存在',
                            'data': None
                        }), 400
                    
                    # 验证用户名格式
                    if not new_username.replace('_', '').isalnum():
                        return jsonify({
                            'code': 400,
                            'message': '用户名只能包含字母、数字和下划线',
                            'data': None
                        }), 400
                    
                    if len(new_username) < 3 or len(new_username) > 20:
                        return jsonify({
                            'code': 400,
                            'message': '用户名长度应为3-20个字符',
                            'data': None
                        }), 400
                    
                    updates['username'] = new_username
                    print(f"🔍 [DEBUG] 更新用户名: {current_username} -> {new_username}")
                else:  # 用户名不能为空
                    return jsonify({
                        'code': 400,
                        'message': '用户名不能为空',
                        'data': None
                    }), 400
        
        if not updates:
            print(f"⚠️ [DEBUG] 没有检测到需要更新的字段")
            return jsonify({
                'code': 200,
                'message': '没有检测到需要更新的内容',
                'data': None
            }), 200
        
        print(f"🔍 [DEBUG] 需要更新的字段: {updates}")
        
        # 构建SQL查询和参数
        sql_fields = []
        sql_values = []
        
        for field, value in updates.items():
            if value is None:
                sql_fields.append(f"{field} = NULL")
            else:
                sql_fields.append(f"{field} = %s")
                sql_values.append(value)
        
        # 添加更新时间
        sql_fields.append("updated_at = NOW()")
        
        # 构建完整的SQL查询
        query = f"UPDATE users SET {', '.join(sql_fields)} WHERE id = %s"
        sql_values.append(user_id)
        
        print(f"🔍 [DEBUG] 执行更新查询: {query}")
        print(f"🔍 [DEBUG] 查询参数: {sql_values}")
        
        cursor.execute(query, tuple(sql_values))
        connection.commit()
        
        # 获取更新后的用户信息
        select_query = """
        SELECT id, username, phone, email, 
               COALESCE(nickname, username) as nickname,
               COALESCE(avatar_url, '') as avatar_url,
               created_at, updated_at
        FROM users WHERE id = %s
        """
        cursor.execute(select_query, (user_id,))
        updated_user = cursor.fetchone()
        
        if updated_user:
            # 处理 datetime 对象
            if updated_user.get('created_at'):
                updated_user['created_at'] = updated_user['created_at'].isoformat()
            if updated_user.get('updated_at'):
                updated_user['updated_at'] = updated_user['updated_at'].isoformat()
            
            # 隐藏敏感信息
            if updated_user.get('phone'):
                phone = updated_user['phone']
                if len(phone) >= 11:
                    updated_user['phone'] = phone[:3] + '****' + phone[-4:]
            
            if updated_user.get('email'):
                email = updated_user['email']
                parts = email.split('@')
                if len(parts) == 2:
                    username_part = parts[0]
                    if len(username_part) > 2:
                        updated_user['email'] = username_part[0] + '***' + username_part[-1] + '@' + parts[1]
                    else:
                        updated_user['email'] = '*' * len(username_part) + '@' + parts[1]
        
        print(f"✅ [DEBUG] 用户信息更新成功: 用户ID {user_id}")
        print(f"✅ [DEBUG] 更新后的用户信息: {updated_user}")
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': updated_user
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ [DEBUG] 更新用户信息失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回更详细的错误信息用于调试
        error_message = str(e)
        if "NoneType" in error_message:
            error_message = "数据库查询结果为空，请检查数据库连接或表结构"
        
        return jsonify({
            'code': 500,
            'message': f'更新失败: {error_message}',
            'data': None
        }), 500
    finally:
        # 确保正确关闭数据库连接
        try:
            if cursor:
                cursor.close()
        except Exception as e:
            print(f"⚠️ 关闭游标时出错: {e}")
        
        try:
            if connection and not connection._closed:
                connection.close()
        except Exception as e:
            print(f"⚠️ 关闭连接时出错: {e}")

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
    
    old_password = data['old_password'].strip()
    new_password = data['new_password'].strip()
    
    # 验证新密码强度
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
        
        # 验证旧密码：使用SHA256哈希后比较
        old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
        
        if user['password_hash'] != old_password_hash:
            return jsonify({
                'code': 400,
                'message': '旧密码不正确',
                'data': None
            }), 400
        
        # 检查新密码是否与旧密码相同
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        if user['password_hash'] == new_password_hash:
            return jsonify({
                'code': 400,
                'message': '新密码不能与旧密码相同',
                'data': None
            }), 400
        
        # 更新密码（使用SHA256哈希）
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
        cursor.execute(update_query, (new_password_hash, user_id))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 修改密码成功")
        
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
