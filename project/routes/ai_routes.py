"""
AI聊天相关路由
"""
from flask import Blueprint, request, jsonify
import uuid
import re
from datetime import datetime
from pathlib import Path
import sys
sys.path.append("..") #相对路径或绝对路径
from py_spider.project.LLM.LLM import recomandation_prompt, get_area_statistics, call_spark_api

'''ai_bp = Blueprint('ai', __name__, url_prefix='/api/beijing/ai')

# 会话存储目录
SESSION_DIR = Path(__file__).parent.parent / 'LLM' / 'chat_sessions'
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# 会话存储（生产环境建议使用Redis等持久化存储）
session_storage = {}


def save_session_to_file(session_id):
    """将会话保存到文件"""
    try:
        if session_id not in session_storage:
            return

        file_path = SESSION_DIR / f"{session_id}.txt"
        session_data = session_storage[session_id]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 会话ID: {session_id} ===\n")
            f.write(f"创建时间: {session_data.get('created_at', 'N/A')}\n")
            f.write(f"最后更新: {datetime.now().isoformat()}\n")
            f.write(f"消息总数: {len(session_data['history'])}\n")
            f.write("=" * 60 + "\n\n")

            for msg in session_data['history']:
                role = msg['role']
                content = msg['content']
                timestamp = msg.get('timestamp', 'N/A')

                if role == 'system':
                    f.write(f"[系统提示词] {timestamp}\n")
                    f.write(f"{content}\n")
                elif role == 'user':
                    f.write(f"[用户] {timestamp}\n")
                    f.write(f"{content}\n")
                elif role == 'assistant':
                    f.write(f"[助手] {timestamp}\n")
                    f.write(f"{content}\n")

                f.write("-" * 60 + "\n\n")

        print(f"✓ 会话 {session_id} 已保存到文件")

    except Exception as e:
        print(f"✗ 保存会话文件失败: {e}")


def load_session_from_file(session_id):
    """从文件加载会话"""
    try:
        file_path = SESSION_DIR / f"{session_id}.txt"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        history = []
        current_role = None
        current_content = []
        current_timestamp = None

        for line in content.split('\n'):
            line = line.strip()

            if line.startswith('=') or line.startswith('-') or not line:
                continue

            if line.startswith('[系统提示词]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'system'
                current_timestamp = line.replace('[系统提示词]', '').strip()
                current_content = []
            elif line.startswith('[用户]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'user'
                current_timestamp = line.replace('[用户]', '').strip()
                current_content = []
            elif line.startswith('[助手]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'assistant'
                current_timestamp = line.replace('[助手]', '').strip()
                current_content = []
            elif line.startswith('创建时间:'):
                created_at = line.replace('创建时间:', '').strip()
            else:
                if current_role:
                    current_content.append(line)

        if current_role and current_content:
            history.append({
                'role': current_role,
                'content': '\n'.join(current_content).strip(),
                'timestamp': current_timestamp
            })

        session_data = {
            'history': history,
            'created_at': created_at if 'created_at' in locals() else datetime.now().isoformat()
        }

        print(f"✓ 从文件加载会话 {session_id}，共 {len(history)} 条消息")
        return session_data

    except Exception as e:
        print(f"✗ 加载会话文件失败: {e}")
        return None


def load_all_sessions():
    """启动时加载所有会话文件"""
    try:
        session_files = list(SESSION_DIR.glob("*.txt"))
        loaded_count = 0

        for file_path in session_files:
            session_id = file_path.stem
            session_data = load_session_from_file(session_id)

            if session_data:
                session_storage[session_id] = session_data
                loaded_count += 1

        print(f"✓ 启动时加载了 {loaded_count} 个会话")

    except Exception as e:
        print(f"✗ 加载会话文件失败: {e}")


def extract_district_from_message(message):
    """从用户消息中提取区域信息"""
    districts = ['东城', '西城', '朝阳', '海淀', '丰台', '石景山',
                 '通州', '顺义', '昌平', '大兴', '房山', '门头沟',
                 '平谷', '怀柔', '密云', '延庆']

    for district in districts:
        if district in message:
            return district
    return None


def extract_price_from_reply(reply):
    """从回复中提取价格信息（简单正则匹配）"""
    pattern = r'(\d{1,3}(?:,\d{3})*|\d+)(?:元|万)'
    matches = re.findall(pattern, reply)

    if matches:
        price_str = matches[0].replace(',', '')
        try:
            return int(price_str)
        except:
            return None
    return None


def get_session_history(session_id):
    """获取会话历史"""
    if session_id not in session_storage:
        loaded_data = load_session_from_file(session_id)
        if loaded_data:
            session_storage[session_id] = loaded_data
        else:
            session_storage[session_id] = {
                'history': [],
                'created_at': datetime.now().isoformat()
            }

    return session_storage[session_id]['history']


def add_to_session(session_id, role, content):
    """添加消息到会话历史"""
    history = get_session_history(session_id)
    history.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })

    if len(history) > 20:
        session_storage[session_id]['history'] = history[-20:]

    save_session_to_file(session_id)


@ai_bp.route('/chat', methods=['POST'])
def ai_chat():
    """北京房产AI聊天接口"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'code': 400,
                'message': '请求体不能为空'
            }), 400

        message = data.get('message', '').strip()
        session_id = data.get('session_id', '')

        if not message:
            return jsonify({
                'code': 400,
                'message': 'message字段不能为空'
            }), 400

        if not session_id:
            session_id = str(uuid.uuid4())

        history = get_session_history(session_id)

        if len(history) == 0:
            add_to_session(session_id, 'system', recomandation_prompt)

        add_to_session(session_id, 'user', message)

        district = extract_district_from_message(message)

        enhanced_message = message
        if district and ('均价' in message or '房价' in message or '价格' in message):
            try:
                area_stats = get_area_statistics(f"{district}")
                print("区域数据正确")
                enhanced_message = f"{message}\n\n参考数据：{area_stats}"
            except Exception as e:
                print(f"获取区域统计数据失败: {e}")
        print(enhanced_message)
        reply = call_spark_api(enhanced_message)

        if not reply:
            return jsonify({
                'code': 500,
                'message': 'LLM服务暂时不可用，请稍后重试'
            }), 500

        add_to_session(session_id, 'assistant', reply)

        related_data = {}

        if district:
            related_data['district'] = district

            avg_price = extract_price_from_reply(reply)
            if avg_price:
                related_data['avg_price'] = avg_price

        response = {
            'code': 200,
            'data': {
                'reply': reply,
                'session_id': session_id,
                'related_data': related_data if related_data else None
            }
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"处理请求时发生错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """获取会话历史记录"""
    session_id = request.args.get('session_id', '')

    if not session_id:
        return jsonify({
            'code': 400,
            'message': 'session_id参数不能为空'
        }), 400

    if session_id not in session_storage:
        return jsonify({
            'code': 404,
            'message': '会话不存在或已过期'
        }), 404

    history = session_storage[session_id]['history']
    filtered_history = [
        {
            'role': msg['role'],
            'content': msg['content'],
            'timestamp': msg['timestamp']
        }
        for msg in history
        if msg['role'] != 'system'
    ]

    return jsonify({
        'code': 200,
        'data': {
            'history': filtered_history,
            'session_id': session_id,
            'total_messages': len(filtered_history)
        }
    }), 200


@ai_bp.route('/sessions/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """清除会话历史"""
    if session_id in session_storage:
        del session_storage[session_id]

    try:
        file_path = SESSION_DIR / f"{session_id}.txt"
        if file_path.exists():
            file_path.unlink()
            print(f"✓ 已删除会话文件: {session_id}")
    except Exception as e:
        print(f"✗ 删除会话文件失败: {e}")

    return jsonify({
        'code': 200,
        'message': '会话已清除'
    }), 200'''
from flask import Flask, request, jsonify,Blueprint
from pathlib import Path
from datetime import datetime
import uuid
import re
from py_spider.project.LLM.use_data import get_area_statistics, query_house_data_by_area, query_house_by_id, get_area_average_price
from py_spider.project.LLM.LLM import call_spark_api

# ============================================
# Flask应用初始化
# ============================================

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# 会话存储目录
SESSION_DIR = Path('chat_sessions')
SESSION_DIR.mkdir(exist_ok=True)

# 会话存储
session_storage = {}

# ============================================
# 工具函数
# ============================================


def extract_district_from_message(message):
    """从消息中提取区域"""
    districts = ['东城', '西城', '朝阳', '海淀', '丰台', '石景山',
                 '通州', '顺义', '昌平', '大兴', '房山', '门头沟',
                 '平谷', '怀柔', '密云', '延庆']

    for district in districts:
        if district in message:
            return district
    return None


def extract_requirements_from_message(message):
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
    layout_keywords = {
        '一居': 1, '1居': 1, '单间': 1,
        '两居': 2, '2居': 2, '二居': 2,
        '三居': 3, '3居': 3,
        '四居': 4, '4居': 4,
        '五居': 5, '5居': 5
    }
    for keyword, rooms in layout_keywords.items():
        if keyword in message:
            requirements['layout'] = f'{rooms}室'
            break

    # 提取区域
    requirements['district'] = extract_district_from_message(message)

    return requirements


def format_house_for_prompt(house):
    """将房源格式化为简洁的提示词格式"""
    return (
        f"ID:{house.get('house_id')} "
        f"{house.get('region', '未知区')} {house.get('community', '未知小区')} "
        f"{house.get('layout', '未知户型')} {house.get('area', 0)}㎡ "
        f"总价{house.get('total_price', 0)}万 "
        f"单价{house.get('price_per_sqm', 0)}元/㎡"
    )


def filter_houses_by_requirements(houses, requirements):
    """根据需求过滤房源"""
    filtered = []

    for house in houses:
        # 预算过滤
        if requirements['budget']:
            total_price = house.get('total_price', 0)
            if total_price > requirements['budget'] * 1.2:  # 超预算20%以上跳过
                continue

        # 户型过滤
        if requirements['layout']:
            layout = house.get('layout', '')
            if requirements['layout'] not in layout:
                continue

        filtered.append(house)

    return filtered


def format_house_inventory_compact(houses, requirements=None):
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


def calculate_house_valuation(house_id):
    """计算房屋估价"""
    try:
        # ============ 调试信息：查询房源 ============
        print("\n" + "=" * 80)
        print("🏠 开始房屋估价")
        print("=" * 80)
        print(f"房源ID: {house_id}")
        print("-" * 80)

        house_info = query_house_by_id(house_id)

        if not house_info:
            raise ValueError(f"未找到房源 ID: {house_id}")

        print(f"✓ 查询到房屋信息:")
        print(f"  - 小区: {house_info.get('community', 'N/A')}")
        print(f"  - 区域: {house_info.get('region', 'N/A')}")
        print(f"  - 户型: {house_info.get('layout', 'N/A')}")
        print(f"  - 面积: {house_info.get('area', 0)}㎡")
        print(f"  - 总价: {house_info.get('total_price', 0)}万")
        print(f"  - 单价: {house_info.get('price_per_sqm', 0)}元/㎡")
        print("-" * 80)

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
        print(f"\n📊 区域参考数据:")
        print(f"  - 区域: {region}")
        print(f"  - 区域均价: {area_avg_price}元/㎡" if area_avg_price else "  - 区域均价: 暂无数据")
        print("-" * 80)

        # ============ 评分计算过程 ============
        print(f"\n🔍 开始评分计算...")

        # 评分计算
        location_score = 75
        if area_avg_price and unit_price > 0:
            price_ratio = unit_price / area_avg_price
            if price_ratio >= 1.2:
                location_score = 90
            elif price_ratio >= 1.0:
                location_score = 80
            elif price_ratio >= 0.8:
                location_score = 70
            else:
                location_score = 60

        print(
            f"  ✓ 地理位置评分: {location_score} (单价/均价比: {price_ratio:.2f})" if area_avg_price and unit_price > 0 else f"  ✓ 地理位置评分: {location_score} (默认)")

        traffic_score = 75
        if floor_info:
            floor_match = re.search(r'(\d+)', floor_info)
            if floor_match:
                floor_num = int(floor_match.group(1))
                if floor_num <= 6:
                    traffic_score = 85
                elif floor_num <= 15:
                    traffic_score = 80

        print(f"  ✓ 交通便利评分: {traffic_score} (楼层: {floor_info})")

        school_score = 70
        good_school_areas = ['海淀', '西城', '东城']
        if any(area in region for area in good_school_areas):
            school_score = 85
        elif region in ['朝阳', '丰台']:
            school_score = 75

        print(f"  ✓ 学区资源评分: {school_score} (区域: {region})")

        quality_score = 70
        current_year = 2024
        if construction_year and construction_year > 0:
            house_age = current_year - construction_year
            if house_age <= 5:
                quality_score = 90
            elif house_age <= 10:
                quality_score = 80
            elif house_age <= 20:
                quality_score = 70
            else:
                quality_score = 60

        if '南' in direction:
            quality_score = min(95, quality_score + 10)

        print(
            f"  ✓ 房屋品质评分: {quality_score} (房龄: {current_year - construction_year if construction_year else '未知'}年, 朝向: {direction})")

        environment_score = 70
        if total_price >= 1000:
            environment_score = 85
        elif total_price >= 500:
            environment_score = 80
        elif total_price >= 300:
            environment_score = 75

        print(f"  ✓ 社区环境评分: {environment_score} (总价: {total_price}万)")
        print("-" * 80)

        # 计算加权得分
        factors = [
            {"name": "地理位置", "score": location_score, "weight": 30},
            {"name": "交通便利", "score": traffic_score, "weight": 25},
            {"name": "学区资源", "score": school_score, "weight": 20},
            {"name": "房屋品质", "score": quality_score, "weight": 15},
            {"name": "社区环境", "score": environment_score, "weight": 10}
        ]

        weighted_score = sum(f["score"] * f["weight"] / 100 for f in factors)

        print(f"\n📈 综合评分:")
        print(f"  - 加权总分: {weighted_score:.1f}")
        for factor in factors:
            print(f"  - {factor['name']}: {factor['score']}分 (权重{factor['weight']}%)")
        print("-" * 80)

        # 估价计算
        if total_price and total_price > 0:
            adjustment_factor = weighted_score / 80
            estimated_price = int(total_price * adjustment_factor)
            print(f"\n💰 估价计算:")
            print(f"  - 原始总价: {total_price}万")
            print(f"  - 调整系数: {adjustment_factor:.2f}")
            print(f"  - 估算总价: {estimated_price}万")
        else:
            if area_avg_price and area:
                estimated_price = int((area_avg_price * area / 10000) * (weighted_score / 80))
                print(f"\n💰 估价计算 (基于均价):")
                print(f"  - 区域均价: {area_avg_price}元/㎡")
                print(f"  - 房屋面积: {area}㎡")
                print(f"  - 估算总价: {estimated_price}万")
            else:
                estimated_price = int(400 * (weighted_score / 80))
                print(f"\n💰 估价计算 (默认):")
                print(f"  - 估算总价: {estimated_price}万")

        price_range = {
            "min": int(estimated_price * 0.92),
            "max": int(estimated_price * 1.08)
        }

        market_sentiment = "均衡市场"
        if weighted_score >= 85:
            market_sentiment = "卖方市场"
        elif weighted_score <= 70:
            market_sentiment = "买方市场"

        if weighted_score < 70:
            advice = "议价空间较大"
            advice_detail = "综合评分偏低，建议协商8-12%议价空间。"
        elif weighted_score < 80:
            advice = "议价空间一般"
            advice_detail = "性价比一般，建议协商5-8%议价空间。"
        elif weighted_score < 90:
            advice = "价格合理"
            advice_detail = "性价比较高，议价空间约3-5%。"
        else:
            advice = "优质房源"
            advice_detail = "综合素质优秀，议价空间有限（2-3%）。"

        print(f"✓ 估价完成: {estimated_price}万元 (评分: {weighted_score:.1f})")

        return {
            "estimated_price": estimated_price,
            "price_range": price_range,
            "factors": factors,
            "market_sentiment": market_sentiment,
            "advice": advice,
            "advice_detail": advice_detail
        }

    except Exception as e:
        print(f"✗ 估价失败: {e}")
        import traceback
        traceback.print_exc()
        raise


# ============================================
# 会话管理
# ============================================

def save_session_to_file(session_id):
    """保存会话到文件"""
    try:
        if session_id not in session_storage:
            return

        file_path = SESSION_DIR / f"{session_id}.txt"
        session_data = session_storage[session_id]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 会话ID: {session_id} ===\n")
            f.write(f"类型: {session_data.get('chat_type', 'unknown')}\n")
            f.write(f"创建: {session_data.get('created_at', 'N/A')}\n")
            f.write(f"更新: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            for msg in session_data['history']:
                role_map = {'system': '[系统]', 'user': '[用户]', 'assistant': '[助手]'}
                role = role_map.get(msg['role'], '[未知]')
                f.write(f"{role} {msg.get('timestamp', '')}\n")
                f.write(f"{msg['content']}\n")
                f.write("-" * 60 + "\n\n")

        print(f"✓ 会话已保存: {session_id}")

    except Exception as e:
        print(f"✗ 保存会话失败: {e}")


def load_session_from_file(session_id):
    """从文件加载会话"""
    try:
        file_path = SESSION_DIR / f"{session_id}.txt"
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        history = []
        current_role = None
        current_content = []
        current_timestamp = None
        chat_type = 'consultation'
        created_at = None

        for line in content.split('\n'):
            line = line.strip()

            if line.startswith('类型:'):
                chat_type = line.replace('类型:', '').strip()
            elif line.startswith('创建:'):
                created_at = line.replace('创建:', '').strip()
            elif line.startswith('[系统]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'system'
                current_timestamp = line.replace('[系统]', '').strip()
                current_content = []
            elif line.startswith('[用户]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'user'
                current_timestamp = line.replace('[用户]', '').strip()
                current_content = []
            elif line.startswith('[助手]'):
                if current_role and current_content:
                    history.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': current_timestamp
                    })
                current_role = 'assistant'
                current_timestamp = line.replace('[助手]', '').strip()
                current_content = []
            elif line and not line.startswith('=') and not line.startswith('-'):
                if current_role:
                    current_content.append(line)

        if current_role and current_content:
            history.append({
                'role': current_role,
                'content': '\n'.join(current_content).strip(),
                'timestamp': current_timestamp
            })

        return {
            'history': history,
            'chat_type': chat_type,
            'created_at': created_at or datetime.now().isoformat()
        }

    except Exception as e:
        print(f"✗ 加载会话失败: {e}")
        return None


def get_session_history(session_id):
    """获取会话历史"""
    if session_id not in session_storage:
        loaded_data = load_session_from_file(session_id)
        if loaded_data:
            session_storage[session_id] = loaded_data
        else:
            session_storage[session_id] = {
                'history': [],
                'chat_type': 'consultation',
                'created_at': datetime.now().isoformat()
            }

    return session_storage[session_id]['history']


def add_to_session(session_id, role, content, chat_type='consultation'):
    """添加消息到会话"""
    if session_id not in session_storage:
        session_storage[session_id] = {
            'history': [],
            'chat_type': chat_type,
            'created_at': datetime.now().isoformat()
        }

    history = session_storage[session_id]['history']
    history.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })

    # 限制历史长度
    if len(history) > 20:
        session_storage[session_id]['history'] = history[-20:]

    save_session_to_file(session_id)

def load_all_sessions():
    """启动时加载所有会话文件"""
    try:
        session_files = list(SESSION_DIR.glob("*.txt"))
        loaded_count = 0

        for file_path in session_files:
            session_id = file_path.stem
            session_data = load_session_from_file(session_id)

            if session_data:
                session_storage[session_id] = session_data
                loaded_count += 1

        print(f"✓ 启动时加载了 {loaded_count} 个会话")

    except Exception as e:
        print(f"✗ 加载会话文件失败: {e}")

# ============================================
# AI服务类
# ============================================

class AIService:
    """统一AI服务"""

    # 精简的系统提示词
    PROMPTS = {
        'consultation': """你是北京房产顾问。职责：
1. 基于提供数据回答房价问题
2. 记住对话历史，理解上下文
3. 价格用"XX元/㎡"格式
4. 回答简洁（100字内）
5. 直接给答案，不输出思考过程""",

        'recommendation': """你是房产推荐顾问。规则：
1. 仅推荐清单中的房源，严禁编造
2. 需求不明确时主动询问
3. 记住用户预算等要求
4. 推荐时说明理由（30字内）
5. 直接给结果，不输出思考

{house_inventory}""",

        'valuation': """你是房产估价顾问。任务：
基于提供的估价数据，用50字左右总结要点。
包括：估价、评分亮点、购买建议。
语气专业、简洁。"""
    }

    def __init__(self):
        pass

    def create_or_get_session(self, session_id=None, chat_type='consultation'):
        """创建或获取会话"""
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"✓ 新会话: {session_id} ({chat_type})")

        history = get_session_history(session_id)
        if len(history) == 0:
            system_prompt = self.PROMPTS.get(chat_type, self.PROMPTS['consultation'])
            add_to_session(session_id, 'system', system_prompt, chat_type)

        return session_id

    def build_messages(self, session_id):
        """构建消息列表"""
        history = get_session_history(session_id)
        messages = []
        for msg in history:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        return messages

    def call_ai(self, session_id, user_message, enhanced_context=None):
        """调用AI"""
        try:
            # 构建最终消息
            final_message = user_message
            if enhanced_context:
                final_message = f"{user_message}\n\n[数据]\n{enhanced_context}"

            # 保存用户消息
            add_to_session(session_id, 'user', user_message)

            # 构建完整消息列表
            messages = self.build_messages(session_id)

            # 如果有增强上下文，修改最后一条消息
            if enhanced_context and messages:
                messages[-1]['content'] = final_message

            # ============ 详细调试信息 ============
            print("\n" + "=" * 80)
            print("📤 发送给AI的完整消息列表")
            print("=" * 80)
            print(f"会话ID: {session_id}")
            print(f"消息总数: {len(messages)}")
            print("-" * 80)

            for idx, msg in enumerate(messages, 1):
                role_emoji = {'system': '🔧', 'user': '👤', 'assistant': '🤖'}
                emoji = role_emoji.get(msg['role'], '❓')
                print(f"\n{emoji} 消息 {idx} - 角色: {msg['role'].upper()}")
                print(f"内容长度: {len(msg['content'])} 字符")
                print("-" * 40)
                # 完整打印内容
                print(msg['content'])
                print("-" * 40)
            # 调用AI
            reply = call_spark_api(messages)

            # ============ AI回复调试信息 ============
            print("\n" + "=" * 80)
            print("📥 收到AI的回复")
            print("=" * 80)

            if reply:
                print(f"回复长度: {len(reply)} 字符")
                print("-" * 40)
                print(reply)
                print("-" * 40)

                add_to_session(session_id, 'assistant', reply)
                print(f"✓ AI回复已保存到会话")
            else:
                print("✗ AI返回空回复")

            print("=" * 80 + "\n")

            return reply

        except Exception as e:
            print(f"\n✗ AI调用失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    def process_consultation(self, message, session_id=None):
        """处理咨询"""
        try:
            session_id = self.create_or_get_session(session_id, 'consultation')
            district = extract_district_from_message(message)

            enhanced_context = None
            if district and any(kw in message for kw in ['均价', '房价', '价格', '多少钱']):
                try:
                    area_stats = get_area_statistics(f"{district}")
                    enhanced_context = area_stats
                except Exception as e:
                    print(f"✗ 获取统计失败: {e}")
            print(enhanced_context)
            reply = self.call_ai(session_id, message, enhanced_context)

            if not reply:
                return {'success': False, 'error': 'AI服务不可用'}

            related_data = {}
            if district:
                related_data['district'] = district

            return {
                'success': True,
                'session_id': session_id,
                'reply': reply,
                'related_data': related_data if related_data else None
            }

        except Exception as e:
            print(f"✗ 咨询失败: {e}")
            return {'success': False, 'error': str(e)}

    def process_recommendation(self, message, session_id=None):
        """处理推荐"""
        try:
            session_id = self.create_or_get_session(session_id, 'recommendation')

            # 提取用户需求
            requirements = extract_requirements_from_message(message)
            print(f"📋 提取需求: {requirements}")

            # 确定查询区域
            target_district = requirements['district'] or '朝阳'

            # 查询房源数据
            print(f"🔍 查询 {target_district} 区房源...")
            houses = query_house_data_by_area(target_district, limit=100)
            print(f"✓ 查询到 {len(houses)} 套房源")

            # 格式化房源清单（紧凑格式 + 需求过滤）
            house_inventory = format_house_inventory_compact(houses, requirements)
            print(f"📝 格式化后清单长度: {len(house_inventory)} 字符")

            # 更新系统提示词
            system_prompt = self.PROMPTS['recommendation'].format(
                house_inventory=house_inventory
            )

            history = get_session_history(session_id)
            if history and history[0]['role'] == 'system':
                history[0]['content'] = system_prompt
            else:
                history.insert(0, {
                    'role': 'system',
                    'content': system_prompt,
                    'timestamp': datetime.now().isoformat()
                })

            save_session_to_file(session_id)
            print(f"✓ 系统提示词已更新，包含房源清单")

            # 调用AI（不需要额外的enhanced_context，房源已在系统提示词中）
            reply = self.call_ai(session_id, message)

            if not reply:
                return {'success': False, 'error': 'AI服务不可用'}

            return {
                'success': True,
                'session_id': session_id,
                'reply': reply
            }

        except Exception as e:
            print(f"✗ 推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def process_valuation(self, house_id, session_id=None):
        """处理估值请求"""
        try:
            session_id = self.create_or_get_session(session_id, 'valuation')

            # 1. 计算估价
            print(f"🔍 开始估价计算...")
            valuation_result = calculate_house_valuation(house_id)

            # 2. 构建估价数据文本
            valuation_text = f"""房源ID: {house_id}
估算价格: {valuation_result['estimated_price']}万元
价格区间: {valuation_result['price_range']['min']}-{valuation_result['price_range']['max']}万元
市场情绪: {valuation_result['market_sentiment']}

综合评分:
"""
            for factor in valuation_result['factors']:
                valuation_text += f"- {factor['name']}: {factor['score']}分 (权重{factor['weight']}%)\n"

            valuation_text += f"\n购买建议: {valuation_result['advice']}\n{valuation_result['advice_detail']}"

            # 3. 调用AI进行总结
            user_message = f"请帮我总结这套房子的估价情况"
            reply = self.call_ai(session_id, user_message, valuation_text)

            if not reply:
                return {'success': False, 'error': 'AI服务不可用'}

            return {
                'success': True,
                'session_id': session_id,
                'reply': reply,
                'valuation': valuation_result
            }

        except Exception as e:
            print(f"✗ 估值处理失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


# ============================================
# 蓝图：AI聊天模块
# ============================================

ai_bp = Blueprint('ai_chat', __name__, url_prefix='/api/beijing/ai')
ai_service = AIService()


@ai_bp.route('/chat', methods=['POST'])
def chat():
    """房价咨询接口"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    message = data.get('message', '').strip()
    if not message:
        return jsonify({'code': 400, 'message': 'message不能为空'}), 400

    session_id = data.get('session_id', '')

    result = ai_service.process_consultation(message, session_id)

    if result['success']:
        return jsonify({
            'code': 200,
            'data': {
                'reply': result['reply'],
                'session_id': result['session_id'],
                'related_data': result['related_data']
            }
        }), 200
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@ai_bp.route('/recommend', methods=['POST'])
def recommend():
    """房源推荐接口"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    message = data.get('message', '').strip()
    if not message:
        return jsonify({'code': 400, 'message': 'message不能为空'}), 400

    session_id = data.get('session_id', '')

    result = ai_service.process_recommendation(message, session_id)

    if result['success']:
        return jsonify({
            'code': 200,
            'data': {
                'reply': result['reply'],
                'session_id': result['session_id']
            }
        }), 200
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@ai_bp.route('/valuation', methods=['POST'])
def valuation():
    """房屋估价接口"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    house_id = data.get('house_id')
    if not house_id:
        return jsonify({'code': 400, 'message': 'house_id不能为空'}), 400

    session_id = data.get('session_id', '')

    try:
        # 使用AI服务处理估值
        result = ai_service.process_valuation(house_id, session_id)

        if result['success']:
            return jsonify({
                'code': 200,
                'data': {
                    'reply': result['reply'],  # AI的总结
                    'session_id': result['session_id'],
                    'valuation': result['valuation']  # 完整的估价数据
                }
            }), 200
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500

    except Exception as e:
        print(f"✗ 估价失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'估价失败: {str(e)}'
        }), 500


@ai_bp.route('/chat/history', methods=['GET'])
def get_history():
    """获取会话历史"""
    session_id = request.args.get('session_id', '')
    if not session_id:
        return jsonify({'code': 400, 'message': 'session_id不能为空'}), 400

    try:
        history = get_session_history(session_id)
        if not history:
            return jsonify({'code': 404, 'message': '会话不存在'}), 404

        user_messages = [msg for msg in history if msg['role'] != 'system']
        session_data = session_storage.get(session_id, {})

        return jsonify({
            'code': 200,
            'data': {
                'session_id': session_id,
                'chat_type': session_data.get('chat_type', 'unknown'),
                'created_at': session_data.get('created_at', 'N/A'),
                'message_count': len(user_messages),
                'messages': user_messages
            }
        }), 200

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@ai_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """列出所有会话"""
    try:
        sessions = []

        for session_id, session_data in session_storage.items():
            history = session_data.get('history', [])
            user_messages = [msg for msg in history if msg['role'] != 'system']

            sessions.append({
                'session_id': session_id,
                'chat_type': session_data.get('chat_type', 'unknown'),
                'created_at': session_data.get('created_at', 'N/A'),
                'message_count': len(user_messages),
                'last_message': user_messages[-1]['content'][:50] + '...' if user_messages else 'N/A'
            })

        sessions.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            'code': 200,
            'data': {
                'total': len(sessions),
                'sessions': sessions
            }
        }), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


# 注册蓝图
app.register_blueprint(ai_bp)
