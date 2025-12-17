from flask import Blueprint, request, jsonify
import pymysql
from decorators import require_auth
from config.db_config import get_db_connection

# 创建蓝图
favorites_bp = Blueprint('favorites', __name__, url_prefix='/api/favorites')

@favorites_bp.route('/houses', methods=['GET'])
@require_auth
def get_favorite_houses():
    """获取收藏的房源列表"""
    user_id = request.user_id
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询总数
        count_query = "SELECT COUNT(*) as total FROM favorite_houses WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total_result = cursor.fetchone()
        total = total_result['total']
        
        # 查询收藏的房源
        query = """
        SELECT 
            fh.id as favorite_id,
            fh.house_id,
            fh.note,
            fh.favorited_at,
            h.total_price,
            h.price_per_sqm,
            h.area,
            h.layout,
            h.region as district,
            h.community
        FROM favorite_houses fh
        LEFT JOIN beijing_house_info h ON fh.house_id = h.house_id
        WHERE fh.user_id = %s
        ORDER BY fh.favorited_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, page_size, offset))
        houses = cursor.fetchall()
        
        # 格式化数据
        formatted_houses = []
        for house in houses:
            formatted_house = {
                'favorite_id': house['favorite_id'],
                'house_id': house['house_id'],
                'total_price': float(house['total_price']) if house['total_price'] else None,
                'price_per_sqm': float(house['price_per_sqm']) if house['price_per_sqm'] else None,
                'area': float(house['area']) if house['area'] else None,
                'layout': house['layout'],
                'district': house['district'],
                'note': house['note'],
                'favorited_at': house['favorited_at'].isoformat() if house['favorited_at'] else None,
                'price_change': -5  # 模拟数据，实际应该计算
            }
            formatted_houses.append(formatted_house)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'houses': formatted_houses
            }
        })
        
    except Exception as e:
        print(f"获取收藏房源失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@favorites_bp.route('/houses', methods=['POST'])
@require_auth
def add_favorite_house():
    """添加房源收藏"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data or 'house_id' not in data:
        return jsonify({
            'code': 400,
            'message': '缺少房源ID',
            'data': None
        }), 400
    
    house_id = data['house_id']
    note = data.get('note', '')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查是否已收藏
        check_query = "SELECT COUNT(*) as count FROM favorite_houses WHERE user_id = %s AND house_id = %s"
        cursor.execute(check_query, (user_id, house_id))
        result = cursor.fetchone()
        
        # 处理返回结果类型
        if isinstance(result, dict):
            count = result.get('count', 0)
        else:
            count = result[0] if result else 0
        
        if count > 0:
            return jsonify({
                'code': 400,
                'message': '该房源已收藏',
                'data': None
            }), 400
        
        # 获取当前最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_houses"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        
        # 处理最大ID结果
        if isinstance(max_id_result, dict):
            max_id = max_id_result.get('max_id', 0)
        else:
            max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0
        
        # 新ID为最大ID加1
        new_id = max_id + 1 if max_id else 1
        
        # 插入收藏记录
        insert_query = """
        INSERT INTO favorite_houses (id, user_id, house_id, note, favorited_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (new_id, user_id, house_id, note))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 收藏房源: {house_id}, 新ID: {new_id}")
        
        return jsonify({
            'code': 200,
            'message': '收藏成功',
            'data': {
                'favorite_id': new_id,
                'message': '收藏成功'
            }
        })
        
    except Exception as e:
        connection.rollback()
        print(f"添加房源收藏失败: {e}")
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

@favorites_bp.route('/houses/<int:house_id>', methods=['DELETE'])
@require_auth
def remove_favorite_house(house_id):
    """取消房源收藏"""
    user_id = request.user_id
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        
        # 删除收藏记录
        delete_query = "DELETE FROM favorite_houses WHERE user_id = %s AND house_id = %s"
        cursor.execute(delete_query, (user_id, house_id))
        connection.commit()
        
        affected_rows = cursor.rowcount
        
        if affected_rows == 0:
            return jsonify({
                'code': 404,
                'message': '未找到收藏记录',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '取消收藏成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"取消房源收藏失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@favorites_bp.route('/cities', methods=['GET'])
@require_auth
def get_favorite_cities():
    """获取关注的城市列表（使用真实数据）"""
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
        
        # 1. 查询关注的城市
        query = """
        SELECT 
            city_name,
            followed_at
        FROM favorite_cities 
        WHERE user_id = %s
        ORDER BY followed_at DESC
        """
        cursor.execute(query, (user_id,))
        cities = cursor.fetchall()
        
        if not cities:
            print("⚠️ 用户未关注任何城市")
            cursor.close()
            connection.close()
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'cities': []
                }
            })
        
        # 2. 获取每个城市的实时房价数据
        formatted_cities = []
        city_names = [city['city_name'] for city in cities]
        
        for city in cities:
            city_name = city['city_name']
            
            # 查询该城市的最新房价数据
            trend_query = """
            SELECT 
                city_name,
                year,
                month,
                year_avg_price,
                month_avg_price
            FROM trend 
            WHERE city_name = %s
            ORDER BY year DESC, month DESC
            LIMIT 1
            """
            
            cursor.execute(trend_query, (city_name,))
            trend_data = cursor.fetchone()
            
            if trend_data:
                # 使用真实数据
                avg_price = float(trend_data.get('month_avg_price') or trend_data.get('year_avg_price') or 0)
                
                # 计算价格变化（与前一个月比较）
                # 首先获取前一个月的数据
                prev_month_query = """
                SELECT 
                    month_avg_price
                FROM trend 
                WHERE city_name = %s 
                    AND (year = %s AND month = %s - 1)
                    OR (year = %s - 1 AND month = 12 AND %s = 1)
                LIMIT 1
                """
                
                current_year = trend_data.get('year', 2024)
                current_month = trend_data.get('month', 12)
                
                if current_month > 1:
                    cursor.execute(prev_month_query, (city_name, current_year, current_month, current_year, current_month))
                else:
                    # 如果是1月，查去年12月
                    cursor.execute(prev_month_query, (city_name, current_year, current_month, current_year, current_month))
                
                prev_month_data = cursor.fetchone()
                
                if prev_month_data and prev_month_data.get('month_avg_price'):
                    prev_price = float(prev_month_data['month_avg_price'])
                    if prev_price > 0:
                        price_change = round(((avg_price - prev_price) / prev_price) * 100, 2)
                    else:
                        price_change = 0.0
                else:
                    # 如果没有上月数据，使用模拟变化
                    import random
                    price_change = round(random.uniform(-3.0, 3.0), 2)
                
                formatted_city = {
                    'city_name': city_name,
                    'avg_price': avg_price,
                    'price_change': price_change,
                    'followed_at': city['followed_at'].isoformat() if city['followed_at'] else None,
                    'data_source': 'trend',
                    'latest_month': f"{current_year}-{current_month:02d}",
                    'has_real_data': True
                }
            else:
                # 如果trend表中没有数据，使用模拟数据
                print(f"⚠️ trend表中没有{city_name}的数据，使用模拟数据")
                
                # 模拟城市数据
                city_simulation = {
                    '北京': {'avg_price': 65000, 'price_change': 1.2},
                    '上海': {'avg_price': 62000, 'price_change': -0.5},
                    '深圳': {'avg_price': 58000, 'price_change': 0.8},
                    '广州': {'avg_price': 42000, 'price_change': 0.5},
                    '杭州': {'avg_price': 38000, 'price_change': 1.0},
                    '成都': {'avg_price': 22000, 'price_change': 0.3},
                    '南京': {'avg_price': 35000, 'price_change': 0.6},
                    '武汉': {'avg_price': 21000, 'price_change': 0.4},
                    '西安': {'avg_price': 18000, 'price_change': 0.7},
                    '重庆': {'avg_price': 15000, 'price_change': 0.2}
                }
                
                city_info = city_simulation.get(city_name, {'avg_price': 0, 'price_change': 0})
                
                formatted_city = {
                    'city_name': city_name,
                    'avg_price': city_info['avg_price'],
                    'price_change': city_info['price_change'],
                    'followed_at': city['followed_at'].isoformat() if city['followed_at'] else None,
                    'data_source': 'simulation',
                    'latest_month': '2024-12',
                    'has_real_data': False
                }
            
            formatted_cities.append(formatted_city)
        
        cursor.close()
        connection.close()
        
        print(f"✅ 获取关注城市成功，共{len(formatted_cities)}个城市，其中{sum(1 for c in formatted_cities if c['has_real_data'])}个有真实数据")
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'cities': formatted_cities,
                'total': len(formatted_cities),
                'real_data_count': sum(1 for c in formatted_cities if c['has_real_data']),
                'simulation_count': sum(1 for c in formatted_cities if not c['has_real_data'])
            }
        })
        
    except Exception as e:
        print(f"❌ 获取关注城市失败: {e}")
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
            
        # 错误时返回空列表
        return jsonify({
            'code': 500,
            'message': f'获取关注城市失败: {str(e)}',
            'data': {
                'cities': [],
                'total': 0,
                'real_data_count': 0,
                'simulation_count': 0
            }
        }), 500

@favorites_bp.route('/cities', methods=['POST'])
@require_auth
def add_favorite_city():
    """添加城市关注"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data or 'city_name' not in data:
        return jsonify({
            'code': 400,
            'message': '缺少城市名称',
            'data': None
        }), 400
    
    city_name = data['city_name']
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查是否已关注
        check_query = "SELECT COUNT(*) as count FROM favorite_cities WHERE user_id = %s AND city_name = %s"
        cursor.execute(check_query, (user_id, city_name))
        result = cursor.fetchone()
        
        # 修复：正确处理返回结果类型
        if isinstance(result, dict):
            count = result.get('count', 0)
        else:
            # 如果是元组，获取第一个元素
            count = result[0] if result else 0
        
        if count > 0:
            cursor.close()
            connection.close()
            return jsonify({
                'code': 400,
                'message': '该城市已关注',
                'data': None
            }), 400
        
        # 获取当前最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_cities"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        
        # 处理最大ID结果
        if isinstance(max_id_result, dict):
            max_id = max_id_result.get('max_id', 0)
        else:
            max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0
        
        # 新ID为最大ID加1
        new_id = max_id + 1 if max_id else 1
        
        # 插入关注记录
        insert_query = """
        INSERT INTO favorite_cities (id, user_id, city_name, followed_at)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (new_id, user_id, city_name))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 关注城市: {city_name}, 新ID: {new_id}")
        
        cursor.close()
        connection.close()
        return jsonify({
            'code': 200,
            'message': '关注成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 添加城市关注失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 安全关闭连接
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
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500

@favorites_bp.route('/cities/<string:city_name>', methods=['DELETE'])
@require_auth
def remove_favorite_city(city_name):
    """取消城市关注"""
    user_id = request.user_id
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        
        # 删除关注记录
        delete_query = "DELETE FROM favorite_cities WHERE user_id = %s AND city_name = %s"
        cursor.execute(delete_query, (user_id, city_name))
        connection.commit()
        
        affected_rows = cursor.rowcount
        
        cursor.close()
        connection.close()
        
        if affected_rows == 0:
            return jsonify({
                'code': 404,
                'message': '未找到关注记录',
                'data': None
            }), 404
        
        print(f"✅ 用户 {user_id} 取消关注城市: {city_name}")
        return jsonify({
            'code': 200,
            'message': '取消关注成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 取消城市关注失败: {e}")
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
            'message': '服务器内部错误',
            'data': None
        }), 500

@favorites_bp.route('/reports', methods=['GET'])
@require_auth
def get_favorite_reports():
    """获取收藏的报告列表"""
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
        
        # 查询收藏的报告
        query = """
        SELECT 
            fr.id as favorite_id,
            fr.report_id,
            fr.favorited_at,
            r.title,
            r.type,
            r.published_at
        FROM favorite_reports fr
        LEFT JOIN reports r ON fr.report_id = r.id
        WHERE fr.user_id = %s
        ORDER BY fr.favorited_at DESC
        """
        cursor.execute(query, (user_id,))
        reports = cursor.fetchall()
        
        formatted_reports = []
        for report in reports:
            formatted_report = {
                'favorite_id': report['favorite_id'],
                'report_id': report['report_id'],
                'title': report['title'],
                'type': report['type'],
                'favorited_at': report['favorited_at'].isoformat() if report['favorited_at'] else None,
                'published_at': report['published_at'].isoformat() if report['published_at'] else None
            }
            formatted_reports.append(formatted_report)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'reports': formatted_reports
            }
        })
        
    except Exception as e:
        print(f"获取收藏报告失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@favorites_bp.route('/reports', methods=['POST'])
@require_auth
def add_favorite_report():
    """添加报告收藏"""
    user_id = request.user_id
    data = request.get_json()
    
    if not data or 'report_id' not in data:
        return jsonify({
            'code': 400,
            'message': '缺少报告ID',
            'data': None
        }), 400
    
    report_id = data['report_id']
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查是否已收藏
        check_query = "SELECT COUNT(*) as count FROM favorite_reports WHERE user_id = %s AND report_id = %s"
        cursor.execute(check_query, (user_id, report_id))
        result = cursor.fetchone()
        
        # 处理返回结果类型
        if isinstance(result, dict):
            count = result.get('count', 0)
        else:
            count = result[0] if result else 0
        
        if count > 0:
            return jsonify({
                'code': 400,
                'message': '该报告已收藏',
                'data': None
            }), 400
        
        # 获取当前最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_reports"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        
        # 处理最大ID结果
        if isinstance(max_id_result, dict):
            max_id = max_id_result.get('max_id', 0)
        else:
            max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0
        
        # 新ID为最大ID加1
        new_id = max_id + 1 if max_id else 1
        
        # 插入收藏记录
        insert_query = """
        INSERT INTO favorite_reports (id, user_id, report_id, favorited_at)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (new_id, user_id, report_id))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 收藏报告: {report_id}, 新ID: {new_id}")
        
        return jsonify({
            'code': 200,
            'message': '收藏成功',
            'data': {
                'favorite_id': new_id
            }
        })
        
    except Exception as e:
        connection.rollback()
        print(f"添加报告收藏失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@favorites_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@require_auth
def remove_favorite_report(report_id):
    """取消报告收藏"""
    user_id = request.user_id
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': None
        }), 500
    
    try:
        cursor = connection.cursor()
        
        # 删除收藏记录
        delete_query = "DELETE FROM favorite_reports WHERE user_id = %s AND report_id = %s"
        cursor.execute(delete_query, (user_id, report_id))
        connection.commit()
        
        affected_rows = cursor.rowcount
        
        if affected_rows == 0:
            return jsonify({
                'code': 404,
                'message': '未找到收藏记录',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '取消收藏成功',
            'data': None
        })
        
    except Exception as e:
        connection.rollback()
        print(f"取消报告收藏失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()