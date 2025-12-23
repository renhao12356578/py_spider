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
from py_spider.project.LLM.LLM import recomandation_prompt
import random
from flask import Flask, request, jsonify,Blueprint
from pathlib import Path
from datetime import datetime
import uuid
import re
from py_spider.project.LLM.use_data import *
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

    def process_recommendation(self, requirements):
        """处理推荐请求 - 使用数据库直接查询"""
        try:
            # 1. 查询符合条件的房源（随机20条）
            print(f"🔍 查询条件: {requirements}")
            matched_houses = query_houses_by_requirements(requirements, limit=20)

            # 2. 统计总匹配数
            total_matched = count_matched_houses(requirements)
            print(f"✓ 总匹配数: {total_matched}, 返回: {len(matched_houses)}")

            if len(matched_houses) == 0:
                return {
                    'success': True,
                    'recommendations': [],
                    'total_matched': 0,
                    'message': '未找到符合条件的房源，建议调整筛选条件'
                }

            # 3. 从20条中随机选择3条
            sample_size = min(3, len(matched_houses))
            selected_houses = random.sample(matched_houses, sample_size)

            # 4. 构建推荐结果
            recommendations = []
            for house in selected_houses:
                # 计算简单匹配度（可选）
                match_score = self.calculate_simple_match_score(house, requirements)

                recommendation = {
                    'house_id': house.get('id') or house.get('house_id'),
                    'total_price': house.get('total_price'),
                    'price_per_sqm': house.get('price_per_sqm'),
                    'area': house.get('area'),
                    'layout': house.get('layout'),
                    'district': house.get('region') or house.get('district'),
                    'match_score': match_score,
                    'reason': self.generate_recommendation_reason(house)
                }
                recommendations.append(recommendation)

            print(f"✓ 已生成 {len(recommendations)} 条推荐")

            return {
                'success': True,
                'recommendations': recommendations,
                'total_matched': total_matched
            }

        except Exception as e:
            print(f"✗ 推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_simple_match_score(self, house, requirements):
        """计算简单匹配度（可选）"""
        score = 85.0  # 基础分

        # 预算越接近中位数，分数越高
        if requirements.get('budget_min') and requirements.get('budget_max'):
            budget_mid = (requirements['budget_min'] + requirements['budget_max']) / 2
            total_price = house.get('total_price', budget_mid)
            deviation = abs(total_price - budget_mid) / budget_mid
            score += 10 * (1 - min(deviation, 1))

        # 面积越接近中位数，分数越高
        if requirements.get('area_min') and requirements.get('area_max'):
            area_mid = (requirements['area_min'] + requirements['area_max']) / 2
            area = house.get('area', area_mid)
            deviation = abs(area - area_mid) / area_mid
            score += 5 * (1 - min(deviation, 1))

        return round(min(100, score), 1)

    RECOMMENDATION_TEMPLATES = [
        "该房源{layout}户型设计合理,{area}㎡的面积满足您的需求,总价{total_price}万在预算范围内,性价比突出。",
        "位于{district}区核心地段,{layout}格局通透,{area}平米空间宽敞,总价{total_price}万元,值得考虑。",
        "这套{layout}房源面积{area}㎡,总价{total_price}万,单价{price_per_sqm}元/㎡,在{district}区同类房源中具有竞争力。",
        "{district}区优质房源,{layout}户型方正实用,{area}㎡居住舒适,总价{total_price}万符合您的预算期望。",
        "推荐这套{layout}的房子,面积{area}平米恰到好处,总价{total_price}万,地段配套成熟,适合居家。",
        "该房源户型为{layout},{area}㎡空间布局合理,总价{total_price}万元,位于{district}区,交通便利。",
        "{layout}户型经典实用,{area}平米满足生活所需,总价{total_price}万在您的预算内,值得实地看房。",
        "这套房子{layout}设计,{area}㎡面积适中,总价{total_price}万,{district}区位置优越,推荐关注。"
    ]
    def generate_recommendation_reason(self, house):
        """生成推荐理由"""
        template = random.choice(self.RECOMMENDATION_TEMPLATES)

        reason = template.format(
            layout=house.get('layout', '未知户型'),
            area=house.get('area', 0),
            total_price=house.get('total_price', 0),
            price_per_sqm=house.get('price_per_sqm', 0),
            district=house.get('region') or house.get('district', '未知区域')
        )

        return reason

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
    """房源推荐接口 - 新版本"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    # 提取并验证参数
    requirements = {
        'budget_min': data.get('budget_min'),
        'budget_max': data.get('budget_max'),
        'district': data.get('district', '朝阳'),
        'layout': data.get('layout'),
        'area_min': data.get('area_min'),
        'area_max': data.get('area_max'),
        'floor_pref': data.get('floor_pref')
    }

    # 基本验证
    if requirements['budget_min'] and requirements['budget_max']:
        if requirements['budget_min'] > requirements['budget_max']:
            return jsonify({
                'code': 400,
                'message': '最低预算不能大于最高预算'
            }), 400

    if requirements['area_min'] and requirements['area_max']:
        if requirements['area_min'] > requirements['area_max']:
            return jsonify({
                'code': 400,
                'message': '最小面积不能大于最大面积'
            }), 400

    # 调用服务处理
    result = ai_service.process_recommendation(requirements)

    if result['success']:
        return jsonify({
            'code': 200,
            'data': {
                'recommendations': result['recommendations'],
                'total_matched': result['total_matched']
            }
        }), 200
    else:
        return jsonify({
            'code': 500,
            'message': result.get('error', '推荐失败')
        }), 500


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


# 注册蓝图（将在文件末尾统一注册，确保所有路由已定义）


@ai_bp.route('/value/<city>', methods=['GET'])
def value_report(city):
    """基于 `summary_all.csv` 中指定城市的 detail 撰写报告并返回"""
    try:
        import csv, json
        from pathlib import Path

        base = Path(__file__).parent
        summary_path = base / 'summary_all.csv'

        # 读取 summary
        summary = None
        city_list = []  # 用于调试：存储所有城市名

        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city_name = row.get('city')
                    city_list.append(city_name)  # 添加到列表用于调试
                    if city_name == city:
                        summary = row
                        break

        # Debugging: Print all city names in summary_all.csv
        print("Cities in summary_all.csv:", city_list)

        if not summary:
            return jsonify({'code': 404, 'message': f'城市 {city} 未在 summary_all 中找到'}), 404

        # 提取关键信息
        current_price = summary.get('current_price', 'N/A')
        trend = summary.get('trend', 'N/A')
        change_percent = summary.get('change_percent', '0')
        confidence = summary.get('confidence', 'N/A')
        linear_trend = summary.get('linear_trend', 'N/A')
        linear_slope = summary.get('linear_slope', '0')
        polynomial_r_squared = summary.get('polynomial_r_squared', '0')
        forecast_periods = summary.get('forecast_periods', '0')
        historical_count = summary.get('historical_count', '0')
        ma_trend = summary.get('ma_trend', '0')

        # 构造结构化的提示词
        prompt = f"""请基于以下城市房地产市场数据，生成一份专业、详细的市场分析报告：

【城市基本信息】
城市名称：{city}

【核心市场指标】
1. 当前价格：{current_price}
2. 市场趋势：{trend}
3. 价格变动幅度：{change_percent}%
4. 模型置信度：{confidence}

【模型分析结果】
1. 线性回归趋势斜率：{linear_slope}）
2. 多项式模型拟合度：{polynomial_r_squared}
3. 移动平均趋势值：{ma_trend}

【报告要求】
请生成一份400-500字的深度市场分析报告，必须包含以下章节：

一、当前市场状况分析
分析当前房价水平、涨跌趋势及变化幅度，结合置信度评估数据可靠性。

二、技术模型综合解读
结合线性回归、多项式拟合和移动平均等模型结果，解读各模型对市场趋势的判断，分析模型间的一致性或差异性。

三、市场趋势深度研判
基于所有技术指标，对未来3-6个月的市场走势进行详细研判，包括：
1. 短期走势预测（1-3个月）
2. 中期走势判断（3-6个月）
3. 关键支撑/阻力位分析

四、投资建议与风险提示
提供具体的投资建议，包括：
1. 对不同类型投资者（刚需、改善、投资）的具体建议
2. 最佳入场/出场时机建议
3. 需关注的关键风险因素
4. 应对策略建议

五、结论与展望
给出明确的综合结论，并对未来6-12个月的市场前景进行展望。

【报告风格】
语言专业但不晦涩，数据准确，逻辑清晰，结论明确，具有实用性和可操作性。"""

        # 调用 AIService 生成报告
        ai = AIService()
        user_message = "请根据上述数据和格式要求，生成专业的房地产市场分析报告："
        report = ai.call_ai(None, user_message, prompt)

        if not report:
            return jsonify({'code': 500, 'message': 'AI 未返回内容'}), 500

        return jsonify({
            'code': 200,
            'city': city,
            'report': report,
            'summary_data': {
                'current_price': current_price,
                'trend': trend,
                'change_percent': change_percent,
                'confidence': confidence,
                'forecast_periods': forecast_periods
            }
        }), 200

    except Exception as e:
        print(f"Error generating report for city {city}: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)}), 500
# 在文件末尾统一注册 ai_bp
app.register_blueprint(ai_bp)

from pathlib import Path
import csv
import codecs

