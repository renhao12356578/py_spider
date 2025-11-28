"""
58同城爬虫配置文件
"""
import json
import os

# 北京市各区域配置（区域名称 -> 拼音）
BEIJING_DISTRICTS = {
    '朝阳': 'chaoyang',
    '海淀': 'haidian',
    '昌平': 'changping',
    '丰台': 'fengtai',
    '大兴': 'daxing',
    '通州': 'tongzhouqu',
    '房山': 'fangshan',
    '顺义': 'shunyi',
    '西城': 'xicheng',
    '东城': 'dongcheng',
    '密云': 'miyun',
    '石景山': 'shijingshan',
    '怀柔': 'huairou',
    '门头沟': 'mentougou',
    '延庆': 'yanqing',
    '平谷': 'pinggu',
}

# 价格区间配置
PRICE_RANGES = {
    '不限': '',
    '150万以下': 'i11292',
    '150-250万': 'i11293',
    '250-300万': 'i11294',
    '300-350万': 'i11295',
    '350-400万': 'i11296',
    '400-500万': 'i11297',
    '500-650万': 'i11298',
    '650-1000万': 'i11299',
    '1000万以上': 'i11300',
}

# 房型配置
ROOM_TYPES = {
    '不限': '',
    '一室': 'e15',
    '二室': 'e17',
    '三室': 'e23',
    '四室': 'e24',
    '五室': 'e25',
    '五室以上': 'e26',
}

# 面积配置
AREA_RANGES = {
    '不限': '',
    '60平米以下': 'k11888',
    '60-70平米': 'k11889',
    '70-80平米': 'k11890',
    '80-90平米': 'k11891',
    '90-110平米': 'k11893',
    '110-130平米': 'k11894',
    '130-160平米': 'k11895',
    '160-250平米': 'k11896',
    '250平米以上': 'k11897',
}

# 朝向配置
ORIENTATIONS = {
    '不限': '',
    '东': 'o1',
    '南': 'o2',
    '西': 'o3',
    '北': 'o4',
    '南北': 'o6',
    '东西': 'o5',
    '东南': 'o7',
    '西南': 'o8',
    '东北': 'o9',
    '西北': 'o10',
}

# 楼层配置
FLOOR_TYPES = {
    '不限': '',
    '底层': 'fl1',
    '低层': 'fl2',
    '中层': 'fl3',
    '高层': 'fl4',
    '顶层': 'fl5',
}

# 房龄配置
BUILDING_AGE = {
    '不限': '',
    '2年内': 'yy1',
    '2-5年': 'yy2',
    '5-10年': 'yy3',
    '10年以上': 'yy4',
}

# 装修配置
DECORATION_TYPES = {
    '不限': '',
    '毛坯': 'j1',
    '简单装修': 'j2',
    '精装修': 'j4',
    '豪华装修': 'j5',
}

# 爬虫配置
SPIDER_CONFIG = {
    'base_url': 'https://bj.58.com/',
    'ershoufang_path': 'ershoufang/',
    'max_retries': 10,
    'request_delay': (1, 3),
    'page_delay': (3, 6),
    'timeout': 10,
    'max_pages': 10,
}

# User-Agent列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# 商圈数据文件路径
AREAS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'areas.json')


def load_areas():
    """从JSON文件加载商圈数据"""
    if os.path.exists(AREAS_JSON_PATH):
        with open(AREAS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_areas(data):
    """保存商圈数据到JSON文件"""
    with open(AREAS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_district_areas(district_name):
    """获取指定区域的商圈列表"""
    areas = load_areas()
    return areas.get(district_name, {})

# 加载商圈数据（启动时自动加载）
DISTRICT_AREAS = load_areas()
