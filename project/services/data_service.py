"""
数据服务层
提供房产数据的查询和分析服务
使用数据库连接池提升性能
"""
import pymysql
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from utils import get_db_connection  # 使用连接池


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


def get_national_overview() -> str:
    """
    实现GET /api/national/overview
    获取全国房价概览（使用current_price表）- 优化为单次查询
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

        # 合并为单次查询（优化性能）
        query = """
        SELECT 
            ROUND(AVG(city_avg_price), 0) as national_avg_price,
            SUM(listing_count) as total_listings,
            COUNT(DISTINCT city_name) as total_cities,
            MAX(city_avg_price) as max_price,
            MIN(CASE WHEN city_avg_price > 0 THEN city_avg_price END) as min_price
        FROM (
            SELECT DISTINCT city_name, city_avg_price, listing_count
            FROM current_price
        ) AS city_data
        """
        cursor.execute(query)
        stats = cursor.fetchone()

        # 获取最高/最低价格城市名称
        cursor.execute("""
            SELECT city_name, city_avg_price FROM current_price 
            WHERE city_avg_price = %s LIMIT 1
        """, (stats['max_price'],))
        highest_city = cursor.fetchone() or {'city_name': '未知', 'city_avg_price': 0}

        cursor.execute("""
            SELECT city_name, city_avg_price FROM current_price 
            WHERE city_avg_price = %s LIMIT 1
        """, (stats['min_price'],))
        lowest_city = cursor.fetchone() or {'city_name': '未知', 'city_avg_price': 0}

        response = {
            "code": 200,
            "data": {
                "national_avg_price": int(stats['national_avg_price'] or 0),
                "highest_city": {
                    "name": highest_city['city_name'],
                    "price": int(highest_city['city_avg_price'])
                },
                "lowest_city": {
                    "name": lowest_city['city_name'],
                    "price": int(lowest_city['city_avg_price'])
                },
                "total_listings": int(stats['total_listings'] or 0),
                "total_cities": int(stats['total_cities'] or 0)
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
    获取城市房价及区县数据（使用current_price表）
    :param province: 筛选省份（可选，如果为空则返回全国数据）
    :param min_price: 最低城市均价（可选）
    :param max_price: 最高城市均价（可选）
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
        
        print(f"🔍 [DEBUG] 开始查询城市房价数据:")
        print(f"    省份: {province if province and province.strip() else '全国'}")
        print(f"    最低价: {min_price}")
        print(f"    最高价: {max_price}")

        # 构建查询条件（使用参数化查询）
        where_conditions = []
        query_params = []
        
        if province and province.strip():
            where_conditions.append("province_name LIKE %s")
            query_params.append(f"%{province.strip()}%")
        
        if min_price is not None and min_price > 0:
            where_conditions.append("city_avg_price >= %s")
            query_params.append(min_price)
        if max_price is not None and max_price > 0:
            where_conditions.append("city_avg_price <= %s")
            query_params.append(max_price)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        print(f"🔍 [DEBUG] SQL WHERE子句: {where_clause}")
        print(f"🔍 [DEBUG] 查询参数: {query_params}")

        # 一次性查询所有数据（优化N+1查询问题）
        query = f"""
        SELECT 
            province_name,
            city_name,
            city_avg_price,
            city_avg_total_price,
            price_rent_ratio,
            listing_count,
            district_name,
            district_avg_price,
            district_ratio
        FROM current_price
        {where_clause}
        ORDER BY city_avg_price DESC, district_avg_price DESC
        """
        
        cursor.execute(query, tuple(query_params))
        all_data = cursor.fetchall()
        
        print(f"🔍 [DEBUG] 查询到 {len(all_data)} 条记录")

        # 在代码中分组处理
        city_map = {}
        for row in all_data:
            city_key = (row['province_name'], row['city_name'])
            
            if city_key not in city_map:
                city_map[city_key] = {
                    "province_name": row['province_name'],
                    "city_name": row['city_name'],
                    "city_avg_price": int(row['city_avg_price']) if row['city_avg_price'] else 0,
                    "city_avg_total_price": int(row['city_avg_total_price']) if row['city_avg_total_price'] else 0,
                    "price_rent_ratio": int(row['price_rent_ratio']) if row['price_rent_ratio'] else 0,
                    "listing_count": int(row['listing_count']) if row['listing_count'] else 0,
                    "districts": []
                }
            
            if row['district_name']:
                city_map[city_key]['districts'].append({
                    "district_name": row['district_name'],
                    "district_avg_price": int(row['district_avg_price']) if row['district_avg_price'] else 0,
                    "district_ratio": round(float(row['district_ratio']), 1) if row['district_ratio'] else 0.0
                })
        
        result_cities = list(city_map.values())
        
        print(f"✅ [DEBUG] 成功处理 {len(result_cities)} 个城市的数据")
        
        # 如果没有查询到数据，返回空数组
        if not result_cities:
            response = {
                "code": 200,
                "data": {"cities": []}
            }
        else:
            response = {
                "code": 200,
                "data": {"cities": result_cities}
            }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"❌ [DEBUG] 城市房价查询失败: {e}")
        import traceback
        traceback.print_exc()
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

        # 构建查询
        if rank_type == "change":
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
        else:
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

        # 使用参数化查询，避免SQL注入
        query = """
        SELECT DISTINCT
            city_name,
            province_name,
            city_avg_price
        FROM current_price
        WHERE 
            city_name LIKE %s 
            OR province_name LIKE %s
        ORDER BY city_avg_price DESC
        LIMIT 20
        """
        
        # 构建LIKE模式的参数
        like_pattern = f"%{keyword.strip()}%"
        cursor.execute(query, (like_pattern, like_pattern))
        results = cursor.fetchall()

        # 格式化结果
        formatted_results = []
        for item in results:
            formatted_results.append({
                "city_name": item['city_name'],
                "province_name": item['province_name'],
                "city_avg_price": int(item['city_avg_price']) if item['city_avg_price'] is not None else 0
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
        import traceback
        traceback.print_exc()
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_price_trend(city: str, year: Optional[int] = None) -> str:
    """
    实现GET /api/national/trend
    获取城市价格趋势（使用trend表）
    :param city: 城市名（可选，为空时返回全国平均趋势）
    :param year: 年份（可选，默认返回2023-2025年数据）
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

        # 构建年份条件
        year_condition = ""
        if year and year >= 2017 and year <= 2025:
            year_condition = f"AND year = {year}"
        else:
            year_condition = ""

        # 根据是否有city参数决定查询方式
        if city and city.strip():
            # 查询指定城市
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
        else:
            # 查询全国平均
            query = f"""
            SELECT
                year,
                month,
                ROUND(AVG(month_avg_price), 0) as avg_price
            FROM trend
            WHERE 1=1 {year_condition}
            GROUP BY year, month
            ORDER BY year ASC, month ASC
            """
        cursor.execute(query)
        trends = cursor.fetchall()

        # 预测数据查询（仅2026年时查询）
        predicts = []
        if year == 2026 and city and city.strip():
            p_query = f"""
            SELECT
                year,
                month,
                predicted_price as avg_price,
                method
            FROM predict1
            WHERE city LIKE '%{city.strip()}%'
            ORDER BY year ASC, month ASC
            """
            cursor.execute(p_query)
            predicts = cursor.fetchall()

        # 格式化结果
        formatted_trends = []
        for trend in trends:
            formatted_trends.append({
                "year": trend['year'],
                "month": trend['month'],
                "avg_price": int(trend['avg_price']),
                "predict": 'exist'
            })

        formatted_predicts = []
        for predict in predicts:
            formatted_predicts.append({
                "year": predict['year'],
                "month": predict['month'],
                "avg_price": int(predict['avg_price']),
                "predict": predict['method']
            })

        response = {
            "code": 200,
            "data": {
                "city_name": city.strip(),
                "trends": formatted_trends+formatted_predicts
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
    返回行政区单价排名（全部）
    """
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"})

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        query = """
        SELECT region as district, 
               ROUND(AVG(price_per_sqm), 0) as avg_price,
               COUNT(*) as count
        FROM beijing_house_info
        WHERE region IS NOT NULL AND region != ''
        GROUP BY region
        ORDER BY avg_price DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "district": item['district'],
                "avg_price": int(item['avg_price']) if item['avg_price'] else 0,
                "count": item['count']
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
                  AND orientation != '南北'
                  AND orientation != '东西'  
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
    :param district: 筛选区域（可选，如果为空则查询所有区域）
    """
    if not district or not district.strip():
        # 查询所有区域的数据
        # 这里使用一个简单的查询，获取每个区域的统计信息
        connection = get_db_connection()
        if not connection:
            return json.dumps({"code": 500, "msg": "数据库连接失败"}, ensure_ascii=False)
        
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 简化查询：直接使用原始列名，不使用别名price
            query_all_districts = """
            SELECT 
                region as district,
                MIN(price_per_sqm) as min,
                AVG(price_per_sqm) as median,
                MAX(price_per_sqm) as max
            FROM beijing_house_info 
            WHERE price_per_sqm IS NOT NULL
            GROUP BY region
            HAVING COUNT(*) > 0
            ORDER BY region
            """
            
            cursor.execute(query_all_districts)
            stats_list = cursor.fetchall()
            
            if not stats_list:
                return json.dumps({
                    "code": 200,
                    "msg": "成功",
                    "data": {"boxplot": []}
                }, ensure_ascii=False)
            
            # 格式化结果
            boxplot = []
            for stats in stats_list:
                def format_val(val):
                    return int(val) if val is not None else 0
                
                # 简化计算：使用平均值作为中位数，计算粗略的四分位数
                min_val = format_val(stats['min'])
                max_val = format_val(stats['max'])
                median_val = format_val(stats['median'])
                
                # 估算四分位数
                q1 = format_val(min_val + (median_val - min_val) * 0.25)
                q3 = format_val(median_val + (max_val - median_val) * 0.25)
                
                boxplot.append({
                    "district": stats['district'],
                    "min": min_val,
                    "q1": q1,
                    "median": median_val,
                    "q3": q3,
                    "max": max_val
                })
            
            response = {
                "code": 200,
                "msg": "成功",
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
    
    # 原有代码（指定区域的查询）
    connection = get_db_connection()
    if not connection:
        return json.dumps({"code": 500, "msg": "数据库连接失败"}, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 修正原始查询中的列名问题
        query = f"""
        SELECT
            MIN(price) as min,
            MAX(CASE WHEN rn = q1_pos THEN price END) as q1,
            MAX(CASE WHEN rn = median_pos THEN price END) as median,
            MAX(CASE WHEN rn = q3_pos THEN price END) as q3,
            MAX(price) as max
        FROM (
            SELECT 
                price_per_sqm as price,
                @row_num := @row_num + 1 as rn,
                (SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) as total_cnt,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.25) as q1_pos,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.5) as median_pos,
                FLOOR((SELECT COUNT(*) FROM beijing_house_info WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL) * 0.75) as q3_pos
            FROM beijing_house_info,
                 (SELECT @row_num := 0) as init
            WHERE region LIKE '%{district.strip()}%' AND price_per_sqm IS NOT NULL
            ORDER BY price_per_sqm ASC
        ) as ranked_prices
        GROUP BY total_cnt, q1_pos, median_pos, q3_pos
        """
        
        cursor.execute(query)
        stats = cursor.fetchone()

        if not stats or stats['min'] is None:
            return json.dumps({
                "code": 200,
                "msg": "成功",
                "data": {"boxplot": []}
            }, ensure_ascii=False)

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
            "msg": "成功",
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

def get_city_clustering() -> str:
    """
    方案C：城市分级气泡图数据
    按均价和挂牌量将城市分为一二三四线城市
    返回：城市名、均价、总价、挂牌量、租售比、城市等级
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
        SELECT 
            city_name,
            city_avg_price,
            city_avg_total_price,
            listing_count,
            price_rent_ratio,
            city_tier
        FROM (
            SELECT DISTINCT
                city_name,
                city_avg_price,
                city_avg_total_price,
                listing_count,
                price_rent_ratio,
                CASE
                    WHEN city_avg_price >= 30000 THEN '一线城市'
                    WHEN city_avg_price >= 15000 THEN '二线城市'
                    WHEN city_avg_price >= 8000 THEN '三线城市'
                    ELSE '四线城市'
                END as city_tier
            FROM current_price
            WHERE city_avg_price IS NOT NULL AND listing_count IS NOT NULL
        ) AS city_data
        ORDER BY city_avg_price DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        cities = []
        for item in results:
            cities.append({
                "city_name": item['city_name'],
                "city_avg_price": int(item['city_avg_price']) if item['city_avg_price'] else 0,
                "city_avg_total_price": int(item['city_avg_total_price']) if item['city_avg_total_price'] else 0,
                "listing_count": int(item['listing_count']) if item['listing_count'] else 0,
                "price_rent_ratio": int(item['price_rent_ratio']) if item['price_rent_ratio'] else 0,
                "city_tier": item['city_tier']
            })

        response = {
            "code": 200,
            "data": {"cities": cities}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"城市分级查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_district_change_heatmap(city: Optional[str] = None) -> str:
    """
    方案C：区县涨跌比热力图数据
    展示各城市区县的涨跌情况
    :param city: 指定城市（可选，为空则返回全国数据）
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

        where_conditions = ["district_ratio IS NOT NULL", "district_avg_price > 0"]
        if city and city.strip():
            where_conditions.append(f"city_name LIKE '%{city.strip()}%'")
        where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
        SELECT
            city_name,
            district_name,
            district_avg_price,
            district_ratio
        FROM current_price
        {where_clause}
        ORDER BY ABS(district_ratio) DESC
        LIMIT 300
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        heatmap_data = []
        for item in results:
            heatmap_data.append({
                "city_name": item['city_name'],
                "district_name": item['district_name'],
                "district_avg_price": int(item['district_avg_price']) if item['district_avg_price'] else 0,
                "district_ratio": round(float(item['district_ratio']), 1) if item['district_ratio'] else 0.0
            })

        response = {
            "code": 200,
            "data": {"heatmap": heatmap_data}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"涨跌比热力图查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_listing_top_ranking(limit: int = 20) -> str:
    """
    方案C：挂牌量TOP排行
    展示房源供应最多的城市
    :param limit: 返回数量（默认20）
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
        limit = max(1, min(limit, 50))

        query = f"""
        SELECT 
            city_name,
            MAX(listing_count) as listing_count,
            MAX(city_avg_price) as city_avg_price
        FROM current_price
        WHERE listing_count IS NOT NULL AND listing_count > 0
        GROUP BY city_name
        ORDER BY listing_count DESC
        LIMIT {limit}
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "city_name": item['city_name'],
                "listing_count": int(item['listing_count']) if item['listing_count'] else 0,
                "city_avg_price": int(item['city_avg_price']) if item['city_avg_price'] else 0
            })

        response = {
            "code": 200,
            "data": {"ranking": ranking}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"挂牌量排行查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_district_price_ranking(limit: int = 50, city: Optional[str] = None) -> str:
    """
    方案D：区县价格排行
    全国所有区县的房价排名
    :param limit: 返回数量（默认50）
    :param city: 指定城市（可选）
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
        limit = max(1, min(limit, 100))

        where_conditions = ["district_avg_price IS NOT NULL", "district_avg_price > 0"]
        if city and city.strip():
            where_conditions.append(f"city_name LIKE '%{city.strip()}%'")
        where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
        SELECT
            city_name,
            district_name,
            district_avg_price,
            district_ratio
        FROM current_price
        {where_clause}
        ORDER BY district_avg_price DESC
        LIMIT {limit}
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "city_name": item['city_name'],
                "district_name": item['district_name'],
                "district_avg_price": int(item['district_avg_price']) if item['district_avg_price'] else 0,
                "district_ratio": round(float(item['district_ratio']), 1) if item['district_ratio'] else 0.0
            })

        response = {
            "code": 200,
            "data": {"ranking": ranking}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"区县价格排行查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_city_districts_comparison(city: str) -> str:
    """
    方案D：同城区县对比
    选定城市后，展示其各区县的价格差异
    :param city: 城市名称（必填）
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

        query = f"""
        SELECT
            district_name,
            district_avg_price,
            district_ratio
        FROM current_price
        WHERE city_name LIKE '%{city.strip()}%'
            AND district_avg_price IS NOT NULL
            AND district_avg_price > 0
        ORDER BY district_avg_price DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return json.dumps({
                "code": 404,
                "data": {},
                "message": f"未找到城市 {city} 的区县数据"
            }, ensure_ascii=False)

        districts = []
        for item in results:
            districts.append({
                "district_name": item['district_name'],
                "district_avg_price": int(item['district_avg_price']) if item['district_avg_price'] else 0,
                "district_ratio": round(float(item['district_ratio']), 1) if item['district_ratio'] else 0.0
            })

        response = {
            "code": 200,
            "data": {
                "city_name": city.strip(),
                "districts": districts
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"同城区县对比查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


def get_district_change_ranking(limit: int = 30, order: str = "desc") -> str:
    """
    方案D：区县涨跌榜
    按district_ratio排序展示涨跌幅最大的区县
    :param limit: 返回数量（默认30）
    :param order: 排序方式 (desc/asc，默认desc)
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
        limit = max(1, min(limit, 100))
        order = order.upper() if order.lower() in ['desc', 'asc'] else 'DESC'

        query = f"""
        SELECT
            city_name,
            district_name,
            district_avg_price,
            district_ratio
        FROM current_price
        WHERE district_ratio IS NOT NULL
        ORDER BY district_ratio {order}
        LIMIT {limit}
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        ranking = []
        for idx, item in enumerate(results, 1):
            ranking.append({
                "rank": idx,
                "city_name": item['city_name'],
                "district_name": item['district_name'],
                "district_avg_price": int(item['district_avg_price']) if item['district_avg_price'] else 0,
                "district_ratio": round(float(item['district_ratio']), 1) if item['district_ratio'] else 0.0
            })

        response = {
            "code": 200,
            "data": {"ranking": ranking}
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"区县涨跌榜查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
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





