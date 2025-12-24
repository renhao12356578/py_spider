"""
房源查询工具库
提供智能房源查询、区域统计等功能
使用数据库连接池
"""
import pymysql
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sys
import os

# 添加父目录到路径以便导入 utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_db_connection


def query_houses_by_requirements(requirements: dict, limit: int = 20) -> List[Dict]:
    """
    根据用户需求查询符合条件的房源（随机返回）

    Args:
        requirements: 查询条件字典
            - budget_min: 最低预算（万元）
            - budget_max: 最高预算（万元）
            - district: 区域名称
            - layout: 户型（如 "2室"）
            - area_min: 最小面积（平米）
            - area_max: 最大面积（平米）
            - floor_pref: 楼层偏好（如 "中层"、"高层"、"低层"）
        limit: 返回数量限制

    Returns:
        房源数据列表
    """
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建WHERE条件
        conditions = []
        params = []

        # 1. 区域条件
        if requirements.get('district'):
            district = requirements['district']
            conditions.append("""(
                region LIKE %s 
            )""")
            like_param = f"%{district}%"
            params.extend([like_param])

        # 2. 预算条件（总价）
        if requirements.get('budget_min') is not None:
            conditions.append("total_price >= %s")
            params.append(requirements['budget_min'])

        if requirements.get('budget_max') is not None:
            conditions.append("total_price <= %s")
            params.append(requirements['budget_max'])

        # 3. 面积条件
        if requirements.get('area_min') is not None:
            conditions.append("area >= %s")
            params.append(requirements['area_min'])

        if requirements.get('area_max') is not None:
            conditions.append("area <= %s")
            params.append(requirements['area_max'])

        # 4. 户型条件
        if requirements.get('layout'):
            conditions.append("layout LIKE %s")
            params.append(f"%{requirements['layout']}%")

        # 5. 楼层偏好（可选，根据你的数据库字段调整）
        if requirements.get('floor_pref'):
            floor_pref = requirements['floor_pref']
            if floor_pref == '低层':
                conditions.append("floor < %s")
                params.append(6)
            elif floor_pref == '中层':
                conditions.append("(floor >= %s AND floor <= %s)")
                params.extend([6, 12])
            elif floor_pref == '高层':
                conditions.append("floor > %s")
                params.append(12)

        # 构建完整SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        SELECT * FROM beijing_house_info 
        WHERE {where_clause}
        ORDER BY RAND()
        LIMIT %s
        """

        params.append(limit)

        print(f"📝 执行查询SQL:")
        print(f"   条件数: {len(conditions)}")
        print(f"   WHERE: {where_clause}")
        print(f"   参数: {params}")

        # 执行查询
        cursor.execute(query, params)
        results = cursor.fetchall()

        print(f"✅ 查询结果: 找到 {len(results)} 条数据")

        cursor.close()
        connection.close()

        return results

    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.close()
        return []


def count_matched_houses(requirements: dict) -> int:
    """
    统计符合条件的房源总数（不限制返回数量）
    用于返回 total_matched 字段
    """
    connection = get_db_connection()
    if not connection:
        return 0

    try:
        cursor = connection.cursor()

        # 构建WHERE条件（与上面相同）
        conditions = []
        params = []

        if requirements.get('district'):
            district = requirements['district']
            conditions.append("""(
                region LIKE %s 
                OR business_area LIKE %s 
                OR community LIKE %s
                OR location LIKE %s
            )""")
            like_param = f"%{district}%"
            params.extend([like_param, like_param, like_param, like_param])

        if requirements.get('budget_min') is not None:
            conditions.append("total_price >= %s")
            params.append(requirements['budget_min'])

        if requirements.get('budget_max') is not None:
            conditions.append("total_price <= %s")
            params.append(requirements['budget_max'])

        if requirements.get('area_min') is not None:
            conditions.append("area >= %s")
            params.append(requirements['area_min'])

        if requirements.get('area_max') is not None:
            conditions.append("area <= %s")
            params.append(requirements['area_max'])

        if requirements.get('layout'):
            conditions.append("layout LIKE %s")
            params.append(f"%{requirements['layout']}%")

        if requirements.get('floor_pref'):
            floor_pref = requirements['floor_pref']
            if floor_pref == '低层':
                conditions.append("floor < %s")
                params.append(6)
            elif floor_pref == '中层':
                conditions.append("(floor >= %s AND floor <= %s)")
                params.extend([6, 12])
            elif floor_pref == '高层':
                conditions.append("floor > %s")
                params.append(12)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"SELECT COUNT(*) as total FROM beijing_house_info WHERE {where_clause}"

        cursor.execute(query, params)
        result = cursor.fetchone()
        total = result[0] if result else 0

        cursor.close()
        connection.close()

        return total

    except Exception as e:
        print(f"❌ 统计查询失败: {e}")
        if connection:
            connection.close()
        return 0


def query_house_data_by_area(area_name: str, limit: int = 20) -> Tuple[List[Dict], List[str]]:
    """
    根据区域名称查询房产数据
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 首先获取表结构 - 使用SHOW COLUMNS替代DESCRIBE
        cursor.execute("SHOW COLUMNS FROM beijing_house_info")
        columns_info = cursor.fetchall()

        # 打印调试信息，查看实际返回的数据结构
        print(f"🔍 表结构查询结果类型: {type(columns_info)}")
        if columns_info:
            print(f"🔍 第一条表结构记录: {columns_info[0]}")
            print(f"🔍 表结构记录的键: {columns_info[0].keys()}")

        # 从字典中提取字段名
        column_names = []
        for col in columns_info:
            # 尝试不同的键名，因为不同数据库可能有不同的键名
            if 'Field' in col:
                column_names.append(col['Field'])
            elif 'field' in col:
                column_names.append(col['field'])
            elif 'COLUMN_NAME' in col:
                column_names.append(col['COLUMN_NAME'])
            elif 'column_name' in col:
                column_names.append(col['column_name'])
            else:
                # 如果都不匹配，使用第一个键
                first_key = list(col.keys())[0]
                column_names.append(col[first_key])

        print(f"🔍 提取的字段列表: {column_names}")

        # 根据你的数据库结构，我们使用联合查询来搜索多个字段
        query = f"""
        SELECT * FROM beijing_house_info 
        WHERE 
            region LIKE '%{area_name}%' 
            OR business_area LIKE '%{area_name}%' 
            OR community LIKE '%{area_name}%'
            OR location LIKE '%{area_name}%'
        ORDER BY RAND()
        LIMIT {limit}
        """

        print(f"📝 执行查询: {query[:100]}...")  # 只打印前100个字符

        cursor.execute(query)
        results = cursor.fetchall()

        print(f"✅ 查询结果: 找到 {len(results)} 条数据")
        if results:
            print(f"✅ 第一条结果: {results[0]}")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_all_distinct_locations() -> Tuple[List[Dict], List[str]]:
    """
    查询所有不同的地点信息（区域、商圈、小区）
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 使用UNION ALL合并三个查询为一次
        query = """
        SELECT '区域' as type, region as name FROM beijing_house_info 
        WHERE region IS NOT NULL AND region != '' GROUP BY region
        UNION ALL
        SELECT '商圈' as type, business_area as name FROM beijing_house_info 
        WHERE business_area IS NOT NULL AND business_area != '' GROUP BY business_area
        UNION ALL
        SELECT '小区' as type, community as name FROM beijing_house_info 
        WHERE community IS NOT NULL AND community != '' GROUP BY community
        ORDER BY type, name
        """

        print(f"📝 执行地点查询（优化版）...")
        cursor.execute(query)
        all_locations = cursor.fetchall()

        # 整合所有地点数据
        results = []
        for loc in all_locations:
            results.append({
                '类型': loc['type'],
                '名称': loc['name']
            })

        column_names = ['类型', '名称']

        print(f"✅ 查询结果: 找到 {len(results)} 条地点数据")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_all_distinct_regions() -> Tuple[List[Dict], List[str]]:
    """
    查询所有不同的区域名称
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = "SELECT DISTINCT region as 区域名称 FROM beijing_house_info WHERE region IS NOT NULL AND region != '' ORDER BY region"

        print(f"📝 执行查询...")
        cursor.execute(query)
        results = cursor.fetchall()

        column_names = ['区域名称']

        print(f"✅ 查询结果: 找到 {len(results)} 个不同的区域")
        if results:
            print(f"✅ 前5个区域: {[r['区域名称'] for r in results[:5]]}")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_all_distinct_business_areas() -> Tuple[List[Dict], List[str]]:
    """
    查询所有不同的商圈名称
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = "SELECT DISTINCT business_area as 商圈名称 FROM beijing_house_info WHERE business_area IS NOT NULL AND business_area != '' ORDER BY business_area"

        print(f"📝 执行查询...")
        cursor.execute(query)
        results = cursor.fetchall()

        column_names = ['商圈名称']

        print(f"✅ 查询结果: 找到 {len(results)} 个不同的商圈")
        if results:
            print(f"✅ 前5个商圈: {[r['商圈名称'] for r in results[:5]]}")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_all_distinct_communities() -> Tuple[List[Dict], List[str]]:
    """
    查询所有不同的小区名称
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = "SELECT DISTINCT community as 小区名称 FROM beijing_house_info WHERE community IS NOT NULL AND community != ''"

        print(f"📝 执行查询...")
        cursor.execute(query)
        results = cursor.fetchall()

        column_names = ['小区名称']

        print(f"✅ 查询结果: 找到 {len(results)} 个不同的小区")
        if results:
            print(f"✅ 前5个小区: {[r['小区名称'] for r in results[:5]]}")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_houses_by_business_area(business_area: str, limit: int = 50) -> Tuple[List[Dict], List[str]]:
    """
    根据商圈查询房屋信息
    返回: (数据列表, 表头字段名)
    """
    connection = get_db_connection()
    if not connection:
        return [], []

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 首先获取表结构
        cursor.execute("SHOW COLUMNS FROM beijing_house_info")
        columns_info = cursor.fetchall()

        # 提取字段名
        column_names = []
        for col in columns_info:
            if 'Field' in col:
                column_names.append(col['Field'])
            elif 'field' in col:
                column_names.append(col['field'])
            elif 'COLUMN_NAME' in col:
                column_names.append(col['COLUMN_NAME'])
            elif 'column_name' in col:
                column_names.append(col['column_name'])
            else:
                first_key = list(col.keys())[0]
                column_names.append(col[first_key])

        # 查询指定商圈的房屋信息
        query = f"""
        SELECT * FROM beijing_house_info 
        WHERE business_area LIKE '%{business_area}%'
        ORDER BY 
            CASE 
                WHEN room_type LIKE '%室%厅%' THEN 1
                WHEN room_type LIKE '%室%' THEN 2
                ELSE 3
            END,
            price ASC,
            area DESC
        LIMIT {limit}
        """

        print(f"📝 执行查询: {query[:100]}...")
        cursor.execute(query)
        results = cursor.fetchall()

        print(f"✅ 查询结果: 在商圈 '{business_area}' 中找到 {len(results)} 条数据")

        cursor.close()
        connection.close()
        return results, column_names

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return [], []


def query_house_by_id(house_id):
    """
    根据房屋ID查询房屋详细信息

    Args:
        house_id: 房屋ID

    Returns:
        房屋信息字典，如果未找到返回None
    """
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = "SELECT * FROM beijing_house_info WHERE house_id = %s"
        cursor.execute(query, (house_id,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return result

    except Exception as e:
        print(f"❌ 查询房屋信息失败: {e}")
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return None


def get_area_average_price(region):
    """
    获取区域平均房价

    Args:
        region: 区域名称

    Returns:
        区域平均单价（元/㎡）
    """
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
        SELECT AVG(unit_price) as avg_price 
        FROM beijing_house_info 
        WHERE region LIKE %s AND unit_price > 0
        """
        cursor.execute(query, (f'%{region}%',))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return result['avg_price'] if result and result['avg_price'] else None

    except Exception as e:
        print(f"❌ 查询区域均价失败: {e}")
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return None


def get_area_statistics(area_name: str, city: str = None) -> Dict:
    """获取区域统计信息，支持全国城市数据查询
    
    Args:
        area_name: 区域名称（如：海淀、朝阳等）
        city: 城市名称（可选，如：北京、上海等）
    
    Returns:
        统计信息字典，包含:
        - basic_stats: 基础统计
        - layout_distribution: 户型分布
        - year_distribution: 建设年代分布
        - price_distribution: 价格段分布
        - elevator_stats: 电梯情况统计
        - orientation_stats: 朝向分布
        - data_source: 数据来源标识
    """
    connection = get_db_connection()
    if not connection:
        return {
            'error': '数据库连接失败',
            'data_available': False
        }

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 判断数据来源：优先查询北京数据，如果没有则查询全国数据
        data_source = 'beijing'

        # 1. 基础统计
        stats_query = f"""
        SELECT 
            COUNT(*) as total_listings,
            ROUND(AVG(total_price), 2) as avg_total_price,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price,
            MIN(total_price) as min_price,
            MAX(total_price) as max_price,
            ROUND(AVG(area), 2) as avg_size,
            COUNT(DISTINCT community) as distinct_communities
        FROM beijing_house_info 
        WHERE 
            region LIKE '%{area_name}%' 
            OR business_area LIKE '%{area_name}%'
            OR community LIKE '%{area_name}%'
        """

        print(f"📊 执行基础统计查询...")
        cursor.execute(stats_query)
        stats = cursor.fetchone()
        print(f"📊 基础统计结果: {stats}")

        # 如果北京数据为空，尝试查询全国数据
        if not stats or stats.get('total_listings', 0) == 0:
            print(f"⚠️ 北京数据库未找到 {area_name} 的数据，尝试查询全国数据...")
            
            # 查询全国数据（current_price表）
            national_stats = _get_national_area_statistics(cursor, area_name, city)
            
            if national_stats and national_stats.get('data_available'):
                cursor.close()
                connection.close()
                return national_stats
            
            # 如果全国数据也没有，返回空结果
            print(f"⚠️ 未找到 {area_name} 的任何数据")
            cursor.close()
            connection.close()
            return {
                'error': f'未找到区域 {area_name} 的数据',
                'data_available': False,
                'area_name': area_name,
                'city': city
            }

        # 2. 户型分布统计
        layout_query = f"""
        SELECT 
            IFNULL(layout, '未知') as layout,
            COUNT(*) as count,
            ROUND(AVG(total_price), 2) as avg_price,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price,
            ROUND(AVG(area), 2) as avg_size
        FROM beijing_house_info 
        WHERE 
            (region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%')
        GROUP BY IFNULL(layout, '未知')
        ORDER BY count DESC
        LIMIT 10
        """

        cursor.execute(layout_query)
        layout_distribution = cursor.fetchall()

        # 3. 建设年代分布
        build_year_query = f"""
        SELECT 
            CASE 
                WHEN build_year IS NULL THEN '未知年代'
                WHEN build_year < 1990 THEN '1990年以前'
                WHEN build_year BETWEEN 1990 AND 1999 THEN '1990-1999年'
                WHEN build_year BETWEEN 2000 AND 2009 THEN '2000-2009年'
                WHEN build_year BETWEEN 2010 AND 2019 THEN '2010-2019年'
                WHEN build_year >= 2020 THEN '2020年以后'
                ELSE '未知年代'
            END as build_period,
            COUNT(*) as count,
            ROUND(AVG(total_price), 2) as avg_total_price,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price
        FROM beijing_house_info 
        WHERE 
            region LIKE '%{area_name}%' 
            OR business_area LIKE '%{area_name}%'
        GROUP BY build_period
        ORDER BY 
            CASE 
                WHEN build_period = '未知年代' THEN 9999
                WHEN build_period = '1990年以前' THEN 1
                WHEN build_period = '1990-1999年' THEN 2
                WHEN build_period = '2000-2009年' THEN 3
                WHEN build_period = '2010-2019年' THEN 4
                ELSE 5
            END
        """

        cursor.execute(build_year_query)
        year_distribution = cursor.fetchall()

        # 4. 价格段分布
        price_dist_query = f"""
        SELECT 
            CASE 
                WHEN total_price < 200 THEN '200万以下'
                WHEN total_price < 400 THEN '200-400万'
                WHEN total_price < 600 THEN '400-600万'
                WHEN total_price < 800 THEN '600-800万'
                WHEN total_price < 1000 THEN '800-1000万'
                WHEN total_price < 1500 THEN '1000-1500万'
                WHEN total_price < 2000 THEN '1500-2000万'
                ELSE '2000万以上'
            END as price_range,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM beijing_house_info 
                  WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'), 2) as percentage
        FROM beijing_house_info 
        WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'
        GROUP BY price_range
        ORDER BY MIN(total_price)
        """

        cursor.execute(price_dist_query)
        price_distribution = cursor.fetchall()

        # 5. 电梯情况统计
        elevator_query = f"""
        SELECT 
            IFNULL(has_elevator, '未知') as has_elevator,
            COUNT(*) as count,
            ROUND(AVG(total_price), 2) as avg_total_price
        FROM beijing_house_info 
        WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'
        GROUP BY IFNULL(has_elevator, '未知')
        ORDER BY count DESC
        """

        cursor.execute(elevator_query)
        elevator_stats = cursor.fetchall()

        # 6. 朝向分布
        orientation_query = f"""
        SELECT 
            IFNULL(orientation, '未知') as orientation,
            COUNT(*) as count,
            ROUND(AVG(total_price), 2) as avg_total_price
        FROM beijing_house_info 
        WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'
        GROUP BY IFNULL(orientation, '未知')
        ORDER BY count DESC
        LIMIT 8
        """

        cursor.execute(orientation_query)
        orientation_stats = cursor.fetchall()

        cursor.close()
        connection.close()

        result = {
            'data_available': True,
            'data_source': data_source,
            'area_name': area_name,
            'city': city or '北京',
            'basic_stats': stats,
            'layout_distribution': layout_distribution,
            'year_distribution': year_distribution,
            'price_distribution': price_distribution,
            'elevator_stats': elevator_stats,
            'orientation_stats': orientation_stats,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"✅ 统计查询完成，数据来源: {data_source}")
        return result

    except Exception as e:
        print(f"❌ 统计查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return {
            'error': f'查询失败: {str(e)}',
            'data_available': False,
            'area_name': area_name
        }


def _get_national_area_statistics(cursor, area_name: str, city: str = None) -> Dict:
    """查询全国数据库的区域统计信息（current_price表）"""
    try:
        # 构建查询条件
        where_conditions = []
        if city:
            where_conditions.append(f"city_name LIKE '%{city}%'")
        where_conditions.append(f"(district_name LIKE '%{area_name}%' OR city_name LIKE '%{area_name}%')")
        where_clause = " AND ".join(where_conditions)
        
        # 基础统计
        stats_query = f"""
        SELECT 
            COUNT(DISTINCT city_name) as total_cities,
            COUNT(DISTINCT district_name) as total_districts,
            ROUND(AVG(district_avg_price), 2) as avg_unit_price,
            MIN(district_avg_price) as min_price,
            MAX(district_avg_price) as max_price,
            SUM(listing_count) as total_listings
        FROM current_price 
        WHERE {where_clause}
        """
        
        cursor.execute(stats_query)
        stats = cursor.fetchone()
        
        if not stats or stats.get('total_listings', 0) == 0:
            return {'data_available': False}
        
        # 价格分布
        price_dist_query = f"""
        SELECT 
            district_name,
            district_avg_price,
            listing_count,
            district_ratio
        FROM current_price 
        WHERE {where_clause}
        ORDER BY district_avg_price DESC
        LIMIT 20
        """
        
        cursor.execute(price_dist_query)
        price_distribution = cursor.fetchall()
        
        return {
            'data_available': True,
            'data_source': 'national',
            'area_name': area_name,
            'city': city,
            'basic_stats': {
                'total_listings': int(stats['total_listings'] or 0),
                'avg_unit_price': float(stats['avg_unit_price'] or 0),
                'min_price': float(stats['min_price'] or 0),
                'max_price': float(stats['max_price'] or 0),
                'total_cities': int(stats['total_cities'] or 0),
                'total_districts': int(stats['total_districts'] or 0)
            },
            'price_distribution': price_distribution,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"❌ 全国数据查询失败: {e}")
        return {'data_available': False}


if __name__ == "__main__":
    # 测试代码
    print("Testing Beijing area...")
    result_bj = get_area_statistics("海淀")
    print(f"Beijing Result keys: {result_bj.keys()}")
    
    print("\nTesting National area...")
    result_national = get_area_statistics("浦东", city="上海")
    print(f"National Result: {result_national.get('data_source')} - {result_national.get('area_name')}")