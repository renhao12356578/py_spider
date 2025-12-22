import pymysql
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from config.db_config import get_db_connection


def get_national_overview() -> str:
    """
    实现GET /api/national/overview
    获取全国房价概览（使用current_price表）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 1. 全国平均房价（按城市去重计算）
        national_avg_query = """
                             SELECT ROUND(AVG(DISTINCT city_avg_price), 0) as national_avg_price
                             FROM current_price \
                             """
        cursor.execute(national_avg_query)
        national_avg = cursor.fetchone()['national_avg_price'] or 0

        # 2. 房价最高的城市
        highest_city_query = """
                             SELECT city_name, city_avg_price
                             FROM current_price
                             GROUP BY city_name, city_avg_price
                             ORDER BY city_avg_price DESC LIMIT 1 \
                             """
        cursor.execute(highest_city_query)
        highest_city = cursor.fetchone() or {"name": "未知", "price": 0}

        # 3. 房价最低的城市
        lowest_city_query = """
                            SELECT city_name, city_avg_price
                            FROM current_price
                            WHERE city_avg_price > 0
                            GROUP BY city_name, city_avg_price
                            ORDER BY city_avg_price ASC LIMIT 1 \
                            """
        cursor.execute(lowest_city_query)
        lowest_city = cursor.fetchone() or {"name": "未知", "price": 0}

        # 4. 总挂牌量（所有城市挂牌量之和）
        total_listings_query = """
                               SELECT SUM(DISTINCT listing_count) as total_listings
                               FROM current_price \
                               """
        cursor.execute(total_listings_query)
        total_listings = cursor.fetchone()['total_listings'] or 0

        # 5. 总城市数（去重）
        total_cities_query = """
                             SELECT COUNT(DISTINCT city_name) as total_cities
                             FROM current_price \
                             """
        cursor.execute(total_cities_query)
        total_cities = cursor.fetchone()['total_cities'] or 0

        response = {
            "code": 200,
            "data": {
                "national_avg_price": int(national_avg),
                "highest_city": {
                    "name": highest_city['city_name'],
                    "price": int(highest_city['city_avg_price'])
                },
                "lowest_city": {
                    "name": lowest_city['city_name'],
                    "price": int(lowest_city['city_avg_price'])
                },
                "total_listings": int(total_listings),
                "total_cities": int(total_cities)
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"全国概览查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_city_prices(province: str, min_price: Optional[int] = None, max_price: Optional[int] = None) -> str:
    """
    实现GET /api/national/city-prices
    获取指定省份的城市房价及区县数据（使用current_price表）
    :param province: 筛选省份（必填）
    :param min_price: 最低城市均价（可选）
    :param max_price: 最高城市均价（可选）
    """
    if not province or not province.strip():
        return json.dumps({
            "code": 400,
            "data": {},
            "message": "province参数为必填项"
        }, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建查询条件
        where_conditions = [f"province_name LIKE '%{province.strip()}%'"]
        if min_price is not None and min_price > 0:
            where_conditions.append(f"city_avg_price >= {min_price}")
        if max_price is not None and max_price > 0:
            where_conditions.append(f"city_avg_price <= {max_price}")
        where_clause = "WHERE " + " AND ".join(where_conditions)

        # 1. 查询城市列表（去重）
        city_query = f"""
        SELECT DISTINCT
            province_name,
            city_name,
            city_avg_price,
            city_avg_total_price,
            price_rent_ratio,
            listing_count
        FROM current_price
        {where_clause}
        ORDER BY city_avg_price DESC
        """
        cursor.execute(city_query)
        cities = cursor.fetchall()

        # 2. 为每个城市查询对应的区县数据
        result_cities = []
        for city in cities:
            city_name = city['city_name']
            # 查询该城市的区县数据
            district_query = f"""
            SELECT
                district_name,
                district_avg_price,
                district_ratio
            FROM current_price
            WHERE city_name = %s
            ORDER BY district_avg_price DESC
            """
            cursor.execute(district_query, (city_name,))
            districts = cursor.fetchall()

            # 格式化区县数据
            formatted_districts = []
            for district in districts:
                formatted_districts.append({
                    "district_name": district['district_name'],
                    "district_avg_price": int(district['district_avg_price']),
                    "district_ratio": round(district['district_ratio'], 1) if district['district_ratio'] else 0.0
                })

            # 格式化城市数据
            result_cities.append({
                "province_name": city['province_name'],
                "city_name": city['city_name'],
                "city_avg_price": int(city['city_avg_price']),
                "city_avg_total_price": int(city['city_avg_total_price']),
                "price_rent_ratio": int(city['price_rent_ratio']),
                "listing_count": int(city['listing_count']),
                "districts": formatted_districts
            })

        response = {
            "code": 200,
            "data": {"cities": result_cities}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"城市房价查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_province_list() -> str:
    """
    实现GET /api/national/provinces
    获取所有省份列表（使用current_price表）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
                SELECT DISTINCT province_name
                FROM current_price
                WHERE province_name IS NOT NULL \
                  AND province_name != ''
                ORDER BY province_name ASC \
                """
        cursor.execute(query)
        provinces = [item['province_name'] for item in cursor.fetchall()]

        response = {
            "code": 200,
            "data": {"provinces": provinces}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"省份列表查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_city_ranking(rank_type: str, limit: int = 10, order: str = "desc") -> str:
    """
    实现GET /api/national/ranking
    获取城市排行榜（使用current_price表）
    :param rank_type: 排行类型 (price/change/rent_ratio)
    :param limit: 返回数量（默认10）
    :param order: 排序方式 (desc/asc，默认desc)
    """
    # 验证参数
    valid_types = ["price", "change", "rent_ratio"]
    if rank_type not in valid_types:
        return json.dumps({
            "code": 400,
            "data": {},
            "message": f"rank_type必须是{valid_types}中的一种"
        }, ensure_ascii=False)

    valid_orders = ["desc", "asc"]
    if order not in valid_orders:
        order = "desc"  # 默认降序

    limit = max(1, min(limit, 50))  # 限制返回数量1-50之间

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 映射排行类型到数据库字段
        type_field_map = {
            "price": "city_avg_price",  # 房价排行
            "change": "district_ratio",  # 涨跌比排行（取城市平均涨跌比）
            "rent_ratio": "price_rent_ratio"  # 租售比排行
        }
        field = type_field_map[rank_type]
        #print(f"🏆 获取城市排行榜: 类型={rank_type}, 字段={field}, 限制={limit}, 顺序={order}")
        # 构建查询
        if rank_type == "price" or rank_type == "rent_ratio":
            # 其他类型直接取城市去重数据
            query = f"""
            SELECT DISTINCT
                city_name,
                {field} as value
            FROM current_price
            WHERE {field} IS NOT NULL AND {field} > 0
            ORDER BY {field} {order.upper()}
            LIMIT {limit}
            """
        
        elif rank_type == "change":
            # 涨跌比取城市下所有区县的平均值
            query = f"""
            SELECT 
                city_name,
                ROUND(AVG(district_ratio), 1) as value
            FROM current_price
            GROUP BY city_name
            HAVING value IS NOT NULL
            ORDER BY value {order.upper()}
            LIMIT {limit}
            """
        

        cursor.execute(query)
        results = cursor.fetchall()

        # 生成排名
        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "city_name": item['city_name'],
                "value": int(item['value']) if rank_type != "change" else round(item['value'], 1)
            })

        response = {
            "code": 200,
            "data": {
                "type": rank_type,
                "ranking": ranking
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"城市排行榜查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def search_city(keyword: str) -> str:
    """
    实现GET /api/national/search
    城市搜索（使用current_price表）
    :param keyword: 搜索关键词（必填）
    """
    if not keyword or not keyword.strip():
        return json.dumps({
            "code": 400,
            "data": {},
            "message": "keyword参数为必填项"
        }, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = f"""
        SELECT DISTINCT
            city_name,
            province_name,
            city_avg_price
        FROM current_price
        WHERE 
            city_name LIKE '%{keyword.strip()}%' 
            OR province_name LIKE '%{keyword.strip()}%'
        ORDER BY city_avg_price DESC
        LIMIT 20
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # 格式化结果
        formatted_results = []
        for item in results:
            formatted_results.append({
                "city_name": item['city_name'],
                "province_name": item['province_name'],
                "city_avg_price": int(item['city_avg_price'])
            })

        response = {
            "code": 200,
            "data": {"results": formatted_results}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"城市搜索失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_price_trend(city: str, year: Optional[int] = None) -> str:
    """
    实现GET /api/national/trend
    获取城市价格趋势（使用trend表）
    :param city: 城市名（必填）
    :param year: 年份（可选，默认返回2023-2025年数据）
    """
    if not city or not city.strip():
        return json.dumps({
            "code": 400,
            "data": {},
            "message": "city参数为必填项"
        }, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

    
        year_condition = ""
        if year:
            year_condition = f"AND year = {year}"
        else:
            year_condition = "AND year = 2025"

        query = f"""
        SELECT
            year,
            month,
            month_avg_price as avg_price
        FROM trend
        WHERE city_name LIKE '%{city.strip()}%'
        {year_condition}
        ORDER BY year ASC, month ASC
        """
        cursor.execute(query)
        trends = cursor.fetchall()

        # 格式化结果
        formatted_trends = []
        for trend in trends:
            formatted_trends.append({
                "year": trend['year'],
                "month": trend['month'],
                "avg_price": int(trend['avg_price'])
            })

        response = {
            "code": 200,
            "data": {
                "city_name": city.strip(),
                "trends": formatted_trends
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"价格趋势查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_beijing_overview() -> str:
    """
    实现GET /api/beijing/overview
    返回北京房产概览信息
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 1. 基础统计（平均单价、平均总价、总记录数）
        basic_query = """
                      SELECT ROUND(AVG(price_per_sqm), 0) as avg_price, \
                             ROUND(AVG(total_price), 0)   as avg_total_price, \
                             COUNT(*)                     as total_listings
                      FROM beijing_house_info \
                      """
        cursor.execute(basic_query)
        basic_stats = cursor.fetchone()

        # 2. 热门区域（记录数占比最高的三个区）
        hot_districts_query = """
                              SELECT region as district, COUNT(*) as count
                              FROM beijing_house_info
                              WHERE region IS NOT NULL AND region != ''
                              GROUP BY region
                              ORDER BY count DESC
                                  LIMIT 3 \
                              """
        cursor.execute(hot_districts_query)
        hot_districts = [item['district'] for item in cursor.fetchall()]

        # 构造响应数据
        response = {
            "code": 200,
            "data": {
                "avg_price": int(basic_stats['avg_price']) if basic_stats['avg_price'] else 0,
                "avg_total_price": int(basic_stats['avg_total_price']) if basic_stats['avg_total_price'] else 0,
                "total_listings": basic_stats['total_listings'],
                "hot_districts": hot_districts
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"概览查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def get_district_ranking() -> str:
    """
    实现GET /api/beijing/district-ranking
    返回行政区单价排名（前3）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
                SELECT region                       as district, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price
                FROM beijing_house_info
                WHERE region IS NOT NULL \
                  AND region != ''
                GROUP BY region
                ORDER BY avg_price DESC
                    LIMIT 3 \
                """
        cursor.execute(query)
        results = cursor.fetchall()

        # 添加排名字段
        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "district": item['district'],
                "avg_price": int(item['avg_price']) if item['avg_price'] else 0
            })

        response = {
            "code": 200,
            "data": {"ranking": ranking}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"区域排名查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def get_district_prices() -> str:
    """
    实现GET /api/beijing/district-prices
    返回所有行政区的平均单价及记录数（地图用）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
                SELECT region                       as name, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price, \
                       COUNT(*) as count
                FROM beijing_house_info
                WHERE region IS NOT NULL AND region != ''
                GROUP BY region
                ORDER BY name ASC \
                """
        cursor.execute(query)
        districts = []
        for item in cursor.fetchall():
            districts.append({
                "name": item['name'],
                "avg_price": int(item['avg_price']) if item['avg_price'] else 0,
                "count": item['count']
            })

        response = {
            "code": 200,
            "data": {"districts": districts}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"区域房价查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def analysis_floor() -> str:
    """
    实现GET /api/beijing/analysis/floor
    楼层特征分析（低/中/高楼层分类）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 先获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM beijing_house_info WHERE floor IS NOT NULL")
        total = cursor.fetchone()['total']
        if total == 0:
            return json.dumps({
                "code": 200,
                "data": {"floor_analysis": []}
            })

        # 楼层分类查询
        query = """
                SELECT CASE \
                           WHEN floor BETWEEN 1 AND 6 THEN '低楼层(1-6)' \
                           WHEN floor BETWEEN 7 AND 15 THEN '中楼层(7-15)' \
                           WHEN floor >= 16 THEN '高楼层(16+)' \
                           ELSE '未知楼层' \
                           END                      as category, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price, \
                       COUNT(*) as count
                FROM beijing_house_info
                WHERE floor IS NOT NULL
                GROUP BY category
                ORDER BY
                    CASE
                    WHEN category = '低楼层(1-6)' THEN 1
                    WHEN category = '中楼层(7-15)' THEN 2
                    WHEN category = '高楼层(16+)' THEN 3
                    ELSE 4
                END \
                """
        cursor.execute(query)
        results = cursor.fetchall()

        # 计算占比百分比
        floor_analysis = []
        for item in results:
            percentage = round((item['count'] / total) * 100, 1)
            floor_analysis.append({
                "category": item['category'],
                "avg_price": int(item['avg_price']) if item['avg_price'] else 0,
                "count": item['count'],
                "percentage": percentage
            })

        response = {
            "code": 200,
            "data": {"floor_analysis": floor_analysis}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"楼层分析查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def analysis_layout() -> str:
    """
    北京房产户型特征分析 - 彻底修复重复户型问题，每种户型仅返回一条记录
    采用子查询先转换户型，再外层分组聚合，避免字段歧义
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 核心修改：子查询先统一户型分类，外层再按统一户型分组聚合
        query = """
                SELECT unified_layout               as layout, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price, \
                       ROUND(AVG(total_price), 0)   as avg_total, \
                       COUNT(*) as count
                FROM (
                    -- 子查询：将原始细分户型转换为统一户型（1室/2室/3室/4室+/未知）
                    SELECT
                    price_per_sqm, total_price, CASE
                    WHEN layout REGEXP '^1室' THEN '1室'
                    WHEN layout REGEXP '^2室' THEN '2室'
                    WHEN layout REGEXP '^3室' THEN '3室'
                    WHEN layout REGEXP '^4室|^5室|^6室' THEN '4室+'
                    ELSE '未知'
                    END as unified_layout
                    FROM beijing_house_info
                    WHERE layout IS NOT NULL
                    ) as converted_houses
                -- 外层按统一户型分组，确保每种户型仅一条记录
                GROUP BY unified_layout
                -- 按记录数降序排序，便于前端展示
                ORDER BY count DESC \
                """

        cursor.execute(query)
        layout_stats = cursor.fetchall()

        # 格式化结果（确保字段类型统一，无冗余数据）
        layout_analysis = []
        for stats in layout_stats:
            layout_analysis.append({
                "layout": stats['layout'],
                "avg_price": int(stats['avg_price']) if stats['avg_price'] else 0,
                "avg_total": int(stats['avg_total']) if stats['avg_total'] else 0,
                "count": int(stats['count']) if stats['count'] else 0
            })

        response = {
            "code": 200,
            "data": {
                "layout_analysis": layout_analysis
            },
            "message": "户型特征分析查询成功"
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"户型特征分析查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"户型特征分析异常: {str(e)}"
        }, ensure_ascii=False)


def analysis_orientation() -> str:
    """
    北京房产朝向特征分析 - 仅保留1-2个汉字的朝向数据，过滤超长朝向
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 核心修改：1. 先分组聚合 2. 筛选CHAR_LENGTH(orientation) <= 2 3. 过滤空字符串
        query = """
                SELECT orientation, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price, \
                       COUNT(*) as count
                FROM beijing_house_info
                WHERE
                    orientation IS NOT NULL
                  AND orientation != ''              -- 过滤空字符串
                  AND CHAR_LENGTH (orientation) <= 2 -- 仅保留1-2个汉字的朝向
                GROUP BY orientation -- 确保每种有效朝向仅一条记录
                ORDER BY count DESC -- 按房源数量降序排序 \
                """

        cursor.execute(query)
        orientation_stats = cursor.fetchall()

        # 格式化结果
        orientation_analysis = []
        for stats in orientation_stats:
            orientation_analysis.append({
                "orientation": stats['orientation'],
                "avg_price": int(stats['avg_price']) if stats['avg_price'] else 0,
                "count": int(stats['count']) if stats['count'] else 0
            })

        response = {
            "code": 200,
            "data": {
                "orientation_analysis": orientation_analysis
            },
            "message": "朝向特征分析查询成功（仅保留1-2个汉字的朝向）"
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"朝向特征分析查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"朝向特征分析异常: {str(e)}"
        }, ensure_ascii=False)

def analysis_elevator() -> str:
    """
    实现GET /api/beijing/analysis/elevator
    电梯特征分析
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
                SELECT IFNULL(has_elevator, '未知') as has_elevator, \
                       ROUND(AVG(price_per_sqm), 0) as avg_price, \
                       COUNT(*) as count
                FROM beijing_house_info
                GROUP BY IFNULL(has_elevator, '未知') \
                """
        cursor.execute(query)
        results = cursor.fetchall()

        # 格式化电梯状态为布尔值（按API要求）
        elevator_analysis = []
        for item in results:
            has_elevator = item['has_elevator']
            # 转换为布尔值："有电梯"->True，其他->False
            is_elevator = True if has_elevator == "有电梯" else False
            elevator_analysis.append({
                "has_elevator": is_elevator,
                "avg_price": int(item['avg_price']) if item['avg_price'] else 0,
                "count": item['count']
            })

        response = {
            "code": 200,
            "data": {"elevator_analysis": elevator_analysis}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"电梯分析查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def get_scatter_data(district: Optional[str] = None, limit: int = 1000) -> str:
    """
    实现GET /api/beijing/chart/scatter
    获取面积-价格散点图数据
    :param district: 筛选区域（可选）
    :param limit: 数据点数量（默认1000）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建查询条件
        where_clause = ""
        if district and district.strip():
            where_clause = f"WHERE region LIKE '%{district.strip()}%'"

        query = f"""
        SELECT
            area,
            total_price,
            price_per_sqm,
            region as district
        FROM beijing_house_info
        {where_clause}
        ORDER BY RAND()
        LIMIT {min(limit, 5000)}  # 限制最大5000个数据点，避免数据过大
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # 格式化结果（保留一位小数）
        points = []
        for item in results:
            points.append({
                "area": round(item['area'], 1) if item['area'] else 0.0,
                "total_price": round(item['total_price'], 1) if item['total_price'] else 0.0,
                "price_per_sqm": int(item['price_per_sqm']) if item['price_per_sqm'] else 0,
                "district": item['district'] or "未知区域"
            })

        response = {
            "code": 200,
            "data": {"points": points}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"散点图数据查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


def get_boxplot_data(district: str) -> str:
    """
    实现GET /api/beijing/chart/boxplot
    获取指定区域的单价箱线图数据（5个统计量）- 彻底解决only_full_group_by问题
    改用子查询手动计算四分位数，避免PERCENTILE函数的语法兼容问题
    :param district: 筛选区域（必填）
    """
    if not district or not district.strip():
        return json.dumps({"code": 400, "msg": "district参数为必填项"}, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"}, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 核心修正：用子查询+行号计算四分位数，完全兼容only_full_group_by
        query = f"""
        SELECT
            MIN(price) as min,
            MAX(CASE WHEN rn = q1_pos THEN price END) as q1,  -- 下四分位数（25%）
            MAX(CASE WHEN rn = median_pos THEN price END) as median,  -- 中位数（50%）
            MAX(CASE WHEN rn = q3_pos THEN price END) as q3,  -- 上四分位数（75%）
            MAX(price) as max
        FROM (
            -- 子查询1：获取符合条件的单价，排序并添加行号
            SELECT 
                price_per_sqm as price,
                @row_num := @row_num + 1 as rn,
                -- 子查询2：计算总记录数和四分位数对应的行号
                (SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) as total_cnt,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.25) as q1_pos,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.5) as median_pos,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.75) as q3_pos
            FROM beijing_house_info,
                 (SELECT @row_num := 0) as init  -- 初始化行号变量
            WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL
            ORDER BY price_per_sqm ASC
        ) as ranked_prices
        -- 全局聚合，无实际分组，兼容only_full_group_by
        GROUP BY total_cnt, q1_pos, median_pos, q3_pos
        """
        cursor.execute(query)
        stats = cursor.fetchone()

        # 处理无数据场景
        if not stats or stats['min'] is None:
            return json.dumps({
                "code": 200,
                "data": {"boxplot": []}
            }, ensure_ascii=False)

        # 格式化结果（处理可能的NULL分位数，取整）
        def format_val(val):
            return int(val) if val is not None else 0

        boxplot = [{
            "district": district.strip(),
            "min": format_val(stats['min']),
            "q1": format_val(stats['q1']),
            "median": format_val(stats['median']),
            "q3": format_val(stats['q3']),
            "max": format_val(stats['max'])
        }]

        response = {
            "code": 200,
            "data": {"boxplot": boxplot}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        error_msg = f"箱线图查询失败: {str(e)}"
        print(error_msg)
        return json.dumps({
            "code": 500,
            "msg": error_msg
        }, ensure_ascii=False)

def query_houses_list(
        district: Optional[str] = None,
        layout: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
) -> str:
    """
    实现GET /api/beijing/houses
    房源列表查询（支持多条件筛选和分页）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建查询条件
        where_conditions = []
        if district and district.strip():
            where_conditions.append(f"region LIKE '%{district.strip()}%'")
        if layout and layout.strip():
            where_conditions.append(f"layout LIKE '%{layout.strip()}%'")
        if min_price is not None and min_price > 0:
            where_conditions.append(f"total_price >= {min_price}")
        if max_price is not None and max_price > 0:
            where_conditions.append(f"total_price <= {max_price}")
        if min_area is not None and min_area > 0:
            where_conditions.append(f"area >= {min_area}")
        if max_area is not None and max_area > 0:
            where_conditions.append(f"area <= {max_area}")

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # 1. 查询总记录数
        count_query = f"SELECT COUNT(*) as total FROM beijing_house_info {where_clause}"
        cursor.execute(count_query)
        total = cursor.fetchone()['total']

        # 2. 计算分页参数
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # 限制每页最大100条
        offset = (page - 1) * page_size

        # 3. 查询房源数据
        data_query = f"""
        SELECT
            house_id,
            total_price,
            price_per_sqm,
            area,
            layout,
            orientation,
            floor,
            has_elevator,
            region,
            tags
        FROM beijing_house_info
        {where_clause}
        ORDER BY house_id ASC
        LIMIT {offset}, {page_size}
        """
        cursor.execute(data_query)
        houses = cursor.fetchall()

        # 格式化结果
        formatted_houses = []
        for house in houses:
            formatted_houses.append({
                "house_id": house['house_id'],
                "total_price": round(house['total_price'], 2) if house['total_price'] else 0.00,
                "price_per_sqm": int(house['price_per_sqm']) if house['price_per_sqm'] else 0,
                "area": round(house['area'], 2) if house['area'] else 0.00,
                "layout": house['layout'] or "未知",
                "orientation": house['orientation'] or "未知",
                "floor": house['floor'] or 0,
                "has_elevator": house['has_elevator'] or "未知",
                "region": house['region'] or "未知",
                "tags": house['tags'] or ""
            })

        response = {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "houses": formatted_houses
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"房源列表查询失败: {e}")
        return json.dumps({"code": 500, "msg": f"查询失败: {str(e)}"})


