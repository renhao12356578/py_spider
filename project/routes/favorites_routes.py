"""
收藏相关路由
包括房源收藏、城市关注、报告收藏
"""
from flask import Blueprint, request, jsonify
import pymysql
from utils import get_db_connection, require_auth

# 创建蓝图
favorites_bp = Blueprint('favorites', __name__, url_prefix='/api/favorites')

@favorites_bp.route('/houses', methods=['GET'])
@require_auth
def get_favorite_houses():
    """获取收藏的房源列表"""
    user_id = request.user_id
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    
    print(f"🔍 获取收藏房源 - 用户ID: {user_id}, page: {page}, limit: {limit}")
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': {'list': []}
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询总数
        count_query = "SELECT COUNT(*) as total FROM favorite_houses WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
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
            h.floor,
            h.orientation,
            h.region as district,
            h.community,
            h.tags
        FROM favorite_houses fh
        LEFT JOIN beijing_house_info h ON fh.house_id = h.house_id
        WHERE fh.user_id = %s
        ORDER BY fh.favorited_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, limit, offset))
        houses = cursor.fetchall()
        
        # 格式化数据
        formatted_list = []
        for house in houses:
            formatted_item = {
                'id': house['favorite_id'],
                'favorite_id': house['favorite_id'],
                'house_id': house['house_id'],
                'title': f"{house['district']} · {house['layout']}",
                'district': house['district'],
                'layout': house['layout'],
                'area': float(house['area']) if house['area'] else 0,
                'floor': house.get('floor', '未知'),
                'orientation': house.get('orientation', '未知'),
                'total_price': float(house['total_price']) if house['total_price'] else 0,
                'price_per_sqm': float(house['price_per_sqm']) if house['price_per_sqm'] else 0,
                'community': house.get('community', ''),
                'tags': house.get('tags', ''),
                'note': house.get('note', ''),
                'favorited_at': house['favorited_at'].isoformat() if house['favorited_at'] else None,
                'price_change': -5
            }
            formatted_list.append(formatted_item)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': formatted_list,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
        
    except Exception as e:
        print(f"❌ 获取收藏房源失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': {'list': []}
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
        
        count = result['count'] if isinstance(result, dict) else result[0]
        
        if count > 0:
            return jsonify({
                'code': 400,
                'message': '该房源已收藏',
                'data': None
            }), 400
        
        # 获取最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_houses"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        max_id = max_id_result['max_id'] if isinstance(max_id_result, dict) else max_id_result[0]
        new_id = (max_id or 0) + 1
        
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
        print(f"❌ 添加房源收藏失败: {e}")
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

@favorites_bp.route('/houses/<int:favorite_id>', methods=['DELETE'])
@require_auth
def remove_favorite_house(favorite_id):
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
        delete_query = "DELETE FROM favorite_houses WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (favorite_id, user_id))
        connection.commit()
        
        affected_rows = cursor.rowcount
        
        if affected_rows == 0:
            return jsonify({
                'code': 404,
                'message': '未找到收藏记录',
                'data': None
            }), 404
        
        print(f"✅ 取消收藏成功 - 删除 {affected_rows} 条记录")
        
        return jsonify({
            'code': 200,
            'message': '取消收藏成功',
            'data': None
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ 取消房源收藏失败: {e}")
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

@favorites_bp.route('/cities', methods=['GET'])
@require_auth
def get_favorite_cities():
    """获取关注的城市列表"""
    user_id = request.user_id
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': []
        }), 500
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户关注的城市列表
        favorite_query = """
        SELECT DISTINCT city_name as name, followed_at
        FROM favorite_cities 
        WHERE user_id = %s
        ORDER BY followed_at DESC
        """
        
        cursor.execute(favorite_query, (user_id,))
        favorite_cities = cursor.fetchall()
        
        if not favorite_cities:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': []
            })
        
        # 提取城市名称
        city_names = [city['name'] for city in favorite_cities]
        
        # 从current_price表获取城市数据
        placeholders = ', '.join(['%s'] * len(city_names))
        price_query = f"""
        SELECT 
            city_name,
            AVG(city_avg_price) as city_avg_price,
            AVG(city_avg_total_price) as city_avg_total_price,
            AVG(price_rent_ratio) as price_rent_ratio,
            SUM(listing_count) as listing_count,
            AVG(district_ratio) as avg_district_ratio
        FROM current_price 
        WHERE city_name IN ({placeholders})
        GROUP BY city_name
        """
        
        cursor.execute(price_query, city_names)
        price_data = cursor.fetchall()
        
        # 创建价格数据映射
        price_map = {item['city_name']: item for item in price_data}
        
        # 合并数据
        formatted_cities = []
        for favorite in favorite_cities:
            city_name = favorite['name']
            price_info = price_map.get(city_name)
            
            if price_info:
                formatted_city = {
                    'name': city_name,
                    'city_name': city_name,
                    'avg_price': float(price_info['city_avg_price']) if price_info['city_avg_price'] else 0,
                    'change': round(float(price_info['avg_district_ratio'] or 0), 2),
                    'price_change': round(float(price_info['avg_district_ratio'] or 0), 2),
                    'avg_total_price': float(price_info['city_avg_total_price']) if price_info['city_avg_total_price'] else 0,
                    'price_rent_ratio': int(price_info['price_rent_ratio']) if price_info['price_rent_ratio'] else 0,
                    'listing_count': int(price_info['listing_count']) if price_info['listing_count'] else 0,
                    'followed_at': favorite['followed_at'].isoformat() if favorite['followed_at'] else None,
                    'has_real_data': True
                }
            else:
                formatted_city = {
                    'name': city_name,
                    'city_name': city_name,
                    'avg_price': 0,
                    'change': 0,
                    'price_change': 0,
                    'avg_total_price': 0,
                    'price_rent_ratio': 0,
                    'listing_count': 0,
                    'followed_at': favorite['followed_at'].isoformat() if favorite['followed_at'] else None,
                    'has_real_data': False
                }
            
            formatted_cities.append(formatted_city)
        
        print(f"✅ 获取关注城市成功，返回 {len(formatted_cities)} 个城市")
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': formatted_cities
        })
        
    except Exception as e:
        print(f"❌ 获取关注城市失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': []
        })
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

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
        
        count = result['count'] if isinstance(result, dict) else result[0]
        
        if count > 0:
            return jsonify({
                'code': 400,
                'message': '该城市已关注',
                'data': None
            }), 400
        
        # 获取最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_cities"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        max_id = max_id_result['max_id'] if isinstance(max_id_result, dict) else max_id_result[0]
        new_id = (max_id or 0) + 1
        
        # 插入关注记录
        insert_query = """
        INSERT INTO favorite_cities (id, user_id, city_name, followed_at)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (new_id, user_id, city_name))
        connection.commit()
        
        print(f"✅ 用户 {user_id} 关注城市: {city_name}, 新ID: {new_id}")
        
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
        
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

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

@favorites_bp.route('/reports', methods=['GET'])
@require_auth
def get_favorite_reports():
    """获取收藏的报告列表"""
    import datetime
    user_id = request.user_id
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'code': 500,
            'message': '数据库连接失败',
            'data': {'list': []}
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
            r.created_at as published_at,
            r.summary as description
        FROM favorite_reports fr
        LEFT JOIN reports r ON fr.report_id = r.id
        WHERE fr.user_id = %s
        ORDER BY fr.favorited_at DESC
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (user_id, limit, offset))
        reports = cursor.fetchall()
        
        # 查询总数
        count_query = "SELECT COUNT(*) as total FROM favorite_reports WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
        # 格式化数据
        formatted_reports = []
        for report in reports:
            formatted_report = {
                'id': report.get('favorite_id'),
                'favorite_id': report.get('favorite_id'),
                'report_id': report.get('report_id'),
                'title': report.get('title', '未知标题'),
                'description': report.get('description', ''),
                'created_at': report.get('favorited_at').isoformat() if report.get('favorited_at') else None,
                'type': report.get('type', 'unknown')
            }
            
            if report.get('published_at'):
                formatted_report['published_at'] = report['published_at'].isoformat()
                
            formatted_reports.append(formatted_report)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': formatted_reports,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
        
    except Exception as e:
        print(f"❌ 获取收藏报告失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [],
                'total': 0,
                'page': page,
                'limit': limit
            }
        })
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
        
        count = result['count'] if isinstance(result, dict) else result[0]
        
        if count > 0:
            return jsonify({
                'code': 400,
                'message': '该报告已收藏',
                'data': None
            }), 400
        
        # 获取最大ID
        max_id_query = "SELECT MAX(id) as max_id FROM favorite_reports"
        cursor.execute(max_id_query)
        max_id_result = cursor.fetchone()
        max_id = max_id_result['max_id'] if isinstance(max_id_result, dict) else max_id_result[0]
        new_id = (max_id or 0) + 1
        
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
        print(f"❌ 添加报告收藏失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

@favorites_bp.route('/reports/<int:favorite_id>', methods=['DELETE'])
@require_auth
def remove_favorite_report(favorite_id):
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
        delete_query = "DELETE FROM favorite_reports WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (favorite_id, user_id))
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
        print(f"❌ 取消报告收藏失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    finally:
        if connection:
            connection.close()

