import pymysql
import pandas as pd
from typing import List, Dict, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import get_db_connection


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
        return results

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()
        return []


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


