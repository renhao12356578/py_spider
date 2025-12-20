import pymysql
import pandas as pd
from typing import List, Dict, Optional, Tuple

# 数据库配置
DB_CONFIG = {
    'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    'port': 4000,
    'user': "48pvdQxqqjLneBr.root",
    'password': "o46hvbIhibN3tTPp",
    'database': "python_project",
    'ssl_ca': "C:/Users/xijun/tidb-ca.pem",
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}


def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


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
                OR business_area LIKE %s 
                OR community LIKE %s
                OR location LIKE %s
            )""")
            like_param = f"%{district}%"
            params.extend([like_param, like_param, like_param, like_param])

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
            if floor_pref == '中层':
                conditions.append("(floor LIKE '%中%' OR floor LIKE '%多层%')")
            elif floor_pref == '高层':
                conditions.append("floor LIKE '%高%'")
            elif floor_pref == '低层':
                conditions.append("floor LIKE '%低%'")

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
            if floor_pref == '中层':
                conditions.append("(floor LIKE '%中%' OR floor LIKE '%多层%')")
            elif floor_pref == '高层':
                conditions.append("floor LIKE '%高%'")
            elif floor_pref == '低层':
                conditions.append("floor LIKE '%低%'")

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



def get_area_statistics(area_name: str) -> Dict:
    """获取区域统计信息，包含建设年代分析
    result={
            'basic_stats': stats,
            'layout_distribution': layout_distribution,
            'year_distribution': year_distribution,
            'price_distribution': price_distribution,
            'elevator_stats': elevator_stats,
            'orientation_stats': orientation_stats
        }"""
    connection = get_db_connection()
    if not connection:
        return {}

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

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

        # 如果基础统计为空，直接返回
        if not stats or stats.get('total_listings', 0) == 0:
            print(f"⚠️ 未找到 {area_name} 的数据")
            cursor.close()
            connection.close()
            return {}

        # 2. 户型分布统计 - 修复GROUP BY问题
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

        # 3. 建设年代分布 - 修复GROUP BY问题
        build_year_query = f"""
        WITH year_categories AS (
            SELECT 
                build_year,
                CASE 
                    WHEN build_year IS NULL THEN '未知年代'
                    WHEN build_year < 1990 THEN '1990年以前'
                    WHEN build_year BETWEEN 1990 AND 1994 THEN '1990-1994年'
                    WHEN build_year BETWEEN 1995 AND 1999 THEN '1995-1999年'
                    WHEN build_year BETWEEN 2000 AND 2004 THEN '2000-2004年'
                    WHEN build_year BETWEEN 2005 AND 2009 THEN '2005-2009年'
                    WHEN build_year BETWEEN 2010 AND 2014 THEN '2010-2014年'
                    WHEN build_year BETWEEN 2015 AND 2019 THEN '2015-2019年'
                    WHEN build_year >= 2020 THEN '2020年以后'
                    ELSE '未知年代'
                END as build_period
            FROM beijing_house_info 
            WHERE 
                region LIKE '%{area_name}%' 
                OR business_area LIKE '%{area_name}%'
        )
        SELECT 
            build_period,
            COUNT(*) as count,
            ROUND(AVG(h.total_price), 2) as avg_total_price,
            ROUND(AVG(h.price_per_sqm), 2) as avg_unit_price,
            ROUND(AVG(h.area), 2) as avg_size
        FROM beijing_house_info h
        JOIN year_categories yc ON h.build_year = yc.build_year
        WHERE 
            h.region LIKE '%{area_name}%' 
            OR h.business_area LIKE '%{area_name}%'
        GROUP BY build_period
        ORDER BY 
            CASE 
                WHEN build_period = '未知年代' THEN 9999
                WHEN build_period = '1990年以前' THEN 1
                WHEN build_period = '1990-1994年' THEN 2
                WHEN build_period = '1995-1999年' THEN 3
                WHEN build_period = '2000-2004年' THEN 4
                WHEN build_period = '2005-2009年' THEN 5
                WHEN build_period = '2010-2014年' THEN 6
                WHEN build_period = '2015-2019年' THEN 7
                ELSE 8
            END
        """

        cursor.execute(build_year_query)
        year_distribution = cursor.fetchall()

        # 4. 价格段分布 - 修复ORDER BY问题
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
                  WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'), 2) as percentage,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price
        FROM beijing_house_info 
        WHERE region LIKE '%{area_name}%' OR business_area LIKE '%{area_name}%'
        GROUP BY 
            CASE 
                WHEN total_price < 200 THEN '200万以下'
                WHEN total_price < 400 THEN '200-400万'
                WHEN total_price < 600 THEN '400-600万'
                WHEN total_price < 800 THEN '600-800万'
                WHEN total_price < 1000 THEN '800-1000万'
                WHEN total_price < 1500 THEN '1000-1500万'
                WHEN total_price < 2000 THEN '1500-2000万'
                ELSE '2000万以上'
            END
        ORDER BY 
            MIN(total_price)
        """

        cursor.execute(price_dist_query)
        price_distribution = cursor.fetchall()

        # 5. 电梯情况统计
        elevator_query = f"""
        SELECT 
            IFNULL(has_elevator, '未知') as has_elevator,
            COUNT(*) as count,
            ROUND(AVG(total_price), 2) as avg_total_price,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price
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
            ROUND(AVG(total_price), 2) as avg_total_price,
            ROUND(AVG(price_per_sqm), 2) as avg_unit_price
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
            'basic_stats': stats,
            'layout_distribution': layout_distribution,
            'year_distribution': year_distribution,
            'price_distribution': price_distribution,
            'elevator_stats': elevator_stats,
            'orientation_stats': orientation_stats
        }

        print(f"✅ 统计查询完成")
        return result

    except Exception as e:
        print(f"❌ 统计查询失败: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return {}


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

        # 查询所有不同的区域
        query_regions = "SELECT DISTINCT region as 区域名称 FROM beijing_house_info WHERE region IS NOT NULL AND region != '' ORDER BY region"

        # 查询所有不同的商圈
        query_business_areas = "SELECT DISTINCT business_area as 商圈名称 FROM beijing_house_info WHERE business_area IS NOT NULL AND business_area != '' ORDER BY business_area"

        # 查询所有不同的小区
        query_communities = "SELECT DISTINCT community as 小区名称 FROM beijing_house_info WHERE community IS NOT NULL AND community != '' ORDER BY community"

        print(f"📝 执行区域查询...")
        cursor.execute(query_regions)
        regions = cursor.fetchall()

        print(f"📝 执行商圈查询...")
        cursor.execute(query_business_areas)
        business_areas = cursor.fetchall()

        print(f"📝 执行小区查询...")
        cursor.execute(query_communities)
        communities = cursor.fetchall()

        # 整合所有地点数据
        results = []

        # 添加区域
        for region in regions:
            results.append({
                '类型': '区域',
                '名称': region['区域名称']
            })

        # 添加商圈
        for area in business_areas:
            results.append({
                '类型': '商圈',
                '名称': area['商圈名称']
            })

        # 添加小区
        for community in communities:
            results.append({
                '类型': '小区',
                '名称': community['小区名称']
            })

        column_names = ['类型', '名称']

        print(f"✅ 查询结果: 找到 {len(regions)} 个区域, {len(business_areas)} 个商圈, {len(communities)} 个小区")

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



if __name__ == "__main__":
    a=query_house_data_by_area("海淀")
    print(a)