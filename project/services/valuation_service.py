"""
房屋估价服务
提供房屋价值评估和市场分析功能
"""
import re
from typing import Dict, Optional
from tools.house_query import query_house_by_id, get_area_average_price


def calculate_house_valuation(house_id) -> Dict:
    """计算房屋估价"""
    house_info = query_house_by_id(house_id)

    if not house_info:
        raise ValueError(f"未找到房源 ID: {house_id}")

    # 提取关键信息
    region = house_info.get('region', '')
    unit_price = house_info.get('price_per_sqm', 0)
    total_price = house_info.get('total_price', 0)
    area = house_info.get('area', 0)
    floor_info = house_info.get('floor', '')
    direction = house_info.get('orientation', '')
    construction_year = house_info.get('bulid_year', 0)

    # 获取区域均价
    area_avg_price = get_area_average_price(region)

    # 评分计算
    location_score = _calculate_location_score(unit_price, area_avg_price)
    traffic_score = _calculate_traffic_score(floor_info)
    school_score = _calculate_school_score(region)
    quality_score = _calculate_quality_score(construction_year, direction)
    environment_score = _calculate_environment_score(total_price)

    # 构建评分因素
    factors = [
        {"name": "地理位置", "score": location_score, "weight": 30},
        {"name": "交通便利", "score": traffic_score, "weight": 25},
        {"name": "学区资源", "score": school_score, "weight": 20},
        {"name": "房屋品质", "score": quality_score, "weight": 15},
        {"name": "社区环境", "score": environment_score, "weight": 10}
    ]

    # 计算加权得分
    weighted_score = sum(f["score"] * f["weight"] / 100 for f in factors)

    # 估价计算
    estimated_price = _calculate_estimated_price(
        total_price, area, area_avg_price, weighted_score
    )

    price_range = {
        "min": int(estimated_price * 0.92),
        "max": int(estimated_price * 1.08)
    }

    # 市场判断和建议
    market_sentiment = _get_market_sentiment(weighted_score)
    advice, advice_detail = _get_purchase_advice(weighted_score)

    return {
        "estimated_price": estimated_price,
        "price_range": price_range,
        "factors": factors,
        "market_sentiment": market_sentiment,
        "advice": advice,
        "advice_detail": advice_detail,
        "house_info": {
            "community": house_info.get('community'),
            "region": region,
            "layout": house_info.get('layout'),
            "area": area,
            "total_price": total_price,
            "unit_price": unit_price
        }
    }


def _calculate_location_score(unit_price: float, area_avg_price: Optional[float]) -> int:
    """计算地理位置评分"""
    if not area_avg_price or unit_price <= 0:
        return 75

    price_ratio = unit_price / area_avg_price
    if price_ratio >= 1.2:
        return 90
    elif price_ratio >= 1.0:
        return 80
    elif price_ratio >= 0.8:
        return 70
    return 60


def _calculate_traffic_score(floor_info: str) -> int:
    """计算交通便利评分"""
    if not floor_info:
        return 75

    floor_match = re.search(r'(\d+)', floor_info)
    if floor_match:
        floor_num = int(floor_match.group(1))
        if floor_num <= 6:
            return 85
        elif floor_num <= 15:
            return 80
    return 75


def _calculate_school_score(region: str) -> int:
    """计算学区资源评分"""
    good_school_areas = ['海淀', '西城', '东城']
    if any(area in region for area in good_school_areas):
        return 85
    elif region in ['朝阳', '丰台']:
        return 75
    return 70


def _calculate_quality_score(construction_year: int, direction: str) -> int:
    """计算房屋品质评分"""
    current_year = 2024
    score = 70

    if construction_year and construction_year > 0:
        house_age = current_year - construction_year
        if house_age <= 5:
            score = 90
        elif house_age <= 10:
            score = 80
        elif house_age <= 20:
            score = 70
        else:
            score = 60

    if '南' in direction:
        score = min(95, score + 10)

    return score


def _calculate_environment_score(total_price: float) -> int:
    """计算社区环境评分"""
    if total_price >= 1000:
        return 85
    elif total_price >= 500:
        return 80
    elif total_price >= 300:
        return 75
    return 70


def _calculate_estimated_price(
    total_price: float,
    area: float,
    area_avg_price: Optional[float],
    weighted_score: float
) -> int:
    """计算估算价格"""
    if total_price and total_price > 0:
        adjustment_factor = weighted_score / 80
        return int(total_price * adjustment_factor)

    if area_avg_price and area:
        return int((area_avg_price * area / 10000) * (weighted_score / 80))

    return int(400 * (weighted_score / 80))


def _get_market_sentiment(weighted_score: float) -> str:
    """获取市场情绪判断"""
    if weighted_score >= 85:
        return "卖方市场"
    elif weighted_score <= 70:
        return "买方市场"
    return "均衡市场"


def _get_purchase_advice(weighted_score: float) -> tuple:
    """获取购买建议"""
    if weighted_score < 70:
        return "议价空间较大", "综合评分偏低，建议协商8-12%议价空间。"
    elif weighted_score < 80:
        return "议价空间一般", "性价比一般，建议协商5-8%议价空间。"
    elif weighted_score < 90:
        return "价格合理", "性价比较高，议价空间约3-5%。"
    return "优质房源", "综合素质优秀，议价空间有限（2-3%）。"
