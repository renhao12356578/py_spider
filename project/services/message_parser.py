"""
消息解析与格式化服务
提取用户消息中的需求信息，格式化房源数据
"""
import re
from typing import Dict, List, Optional


# 北京区域列表
BEIJING_DISTRICTS = [
    '东城', '西城', '朝阳', '海淀', '丰台', '石景山',
    '通州', '顺义', '昌平', '大兴', '房山', '门头沟',
    '平谷', '怀柔', '密云', '延庆'
]

# 户型关键词映射
LAYOUT_KEYWORDS = {
    '一居': 1, '1居': 1, '单间': 1,
    '两居': 2, '2居': 2, '二居': 2,
    '三居': 3, '3居': 3,
    '四居': 4, '4居': 4,
    '五居': 5, '5居': 5
}


def extract_district_from_message(message: str) -> Optional[str]:
    """从消息中提取区域"""
    for district in BEIJING_DISTRICTS:
        if district in message:
            return district
    return None


def extract_requirements_from_message(message: str) -> Dict:
    """从消息中提取购房需求"""
    requirements = {
        'budget': None,
        'layout': None,
        'district': None
    }

    # 提取预算（万元）
    budget_patterns = [
        r'(\d+)万',
        r'预算\s*[:：]?\s*(\d+)',
        r'(\d+)w'
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, message)
        if match:
            requirements['budget'] = int(match.group(1))
            break

    # 提取户型
    for keyword, rooms in LAYOUT_KEYWORDS.items():
        if keyword in message:
            requirements['layout'] = f'{rooms}室'
            break

    # 提取区域
    requirements['district'] = extract_district_from_message(message)

    return requirements


def format_house_for_prompt(house: Dict) -> str:
    """将房源格式化为简洁的提示词格式"""
    return (
        f"ID:{house.get('house_id')} "
        f"{house.get('region', '未知区')} {house.get('community', '未知小区')} "
        f"{house.get('layout', '未知户型')} {house.get('area', 0)}㎡ "
        f"总价{house.get('total_price', 0)}万 "
        f"单价{house.get('price_per_sqm', 0)}元/㎡"
    )


def filter_houses_by_requirements(houses: List[Dict], requirements: Dict) -> List[Dict]:
    """根据需求过滤房源"""
    filtered = []

    for house in houses:
        # 预算过滤
        if requirements.get('budget'):
            total_price = house.get('total_price', 0)
            if total_price > requirements['budget'] * 1.2:  # 超预算20%以上跳过
                continue

        # 户型过滤
        if requirements.get('layout'):
            layout = house.get('layout', '')
            if requirements['layout'] not in layout:
                continue

        filtered.append(house)

    return filtered


def format_house_inventory_compact(houses: List[Dict], requirements: Dict = None) -> str:
    """格式化房源清单为紧凑格式"""
    if not houses:
        return "暂无房源"

    # 如果有需求，先过滤
    if requirements:
        houses = filter_houses_by_requirements(houses, requirements)

    # 限制数量，最多返回20条
    houses = houses[:20]

    if not houses:
        return "暂无符合条件的房源"

    inventory = "【房源列表】\n"
    for idx, house in enumerate(houses, 1):
        inventory += f"{idx}. {format_house_for_prompt(house)}\n"

    return inventory
