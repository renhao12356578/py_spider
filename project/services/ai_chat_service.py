"""
AI聊天服务
提供会话管理和AI对话功能
"""
import uuid
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from LLM.spark_client import call_spark_api
from tools.house_query import get_area_statistics, query_houses_by_requirements, count_matched_houses
from services.message_parser import extract_district_from_message


# 会话存储目录
SESSION_DIR = Path('chat_sessions')
SESSION_DIR.mkdir(exist_ok=True)

# 会话存储
session_storage = {}


# ============================================
# 会话管理
# ============================================

def save_session_to_file(session_id: str):
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

    except Exception as e:
        print(f"✗ 保存会话失败: {e}")


def load_session_from_file(session_id: str) -> Optional[Dict]:
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


def get_session_history(session_id: str) -> List[Dict]:
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


def add_to_session(session_id: str, role: str, content: str, chat_type: str = 'consultation'):
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

    def create_or_get_session(self, session_id: str = None, chat_type: str = 'consultation') -> str:
        """创建或获取会话"""
        if not session_id:
            session_id = str(uuid.uuid4())

        history = get_session_history(session_id)
        if len(history) == 0:
            system_prompt = self.PROMPTS.get(chat_type, self.PROMPTS['consultation'])
            add_to_session(session_id, 'system', system_prompt, chat_type)

        return session_id

    def build_messages(self, session_id: str) -> List[Dict]:
        """构建消息列表"""
        history = get_session_history(session_id)
        messages = []
        for msg in history:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        return messages

    def call_ai(self, session_id: str, user_message: str, enhanced_context: str = None) -> Optional[str]:
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

            # 调用AI
            reply = call_spark_api(messages)

            if reply:
                add_to_session(session_id, 'assistant', reply)

            return reply

        except Exception as e:
            print(f"✗ AI调用失败: {e}")
            return None

    def process_consultation(self, message: str, session_id: str = None) -> Dict:
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

    def process_recommendation(self, requirements: Dict) -> Dict:
        """处理推荐请求 - 返回全部符合条件的房源"""
        try:
            # 1. 查询符合条件的全部房源（不限制数量）
            matched_houses = query_houses_by_requirements(requirements, limit=1000)

            # 2. 统计总匹配数
            total_matched = count_matched_houses(requirements)

            if len(matched_houses) == 0:
                return {
                    'success': True,
                    'recommendations': [],
                    'total_matched': 0,
                    'message': '未找到符合条件的房源，建议调整筛选条件'
                }

            # 3. 构建推荐结果（返回全部）
            recommendations = []
            for house in matched_houses:
                match_score = self._calculate_simple_match_score(house, requirements)

                recommendation = {
                    'house_id': house.get('id') or house.get('house_id'),
                    'total_price': house.get('total_price'),
                    'price_per_sqm': house.get('price_per_sqm'),
                    'area': house.get('area'),
                    'layout': house.get('layout'),
                    'district': house.get('region') or house.get('district'),
                    'match_score': match_score,
                    'reason': self._generate_recommendation_reason(house)
                }
                recommendations.append(recommendation)

            return {
                'success': True,
                'recommendations': recommendations,
                'total_matched': total_matched
            }

        except Exception as e:
            print(f"✗ 推荐失败: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_simple_match_score(self, house: Dict, requirements: Dict) -> int:
        """计算简单匹配度"""
        score = 70

        # 预算匹配
        if requirements.get('budget_max'):
            total_price = house.get('total_price', 0)
            if total_price <= requirements['budget_max']:
                score += 15
            elif total_price <= requirements['budget_max'] * 1.1:
                score += 5

        # 区域匹配
        if requirements.get('district'):
            region = house.get('region', '')
            if requirements['district'] in region:
                score += 10

        # 户型匹配
        if requirements.get('layout'):
            layout = house.get('layout', '')
            if requirements['layout'] in layout:
                score += 5

        return min(100, score)

    def _generate_recommendation_reason(self, house: Dict) -> str:
        """生成推荐理由"""
        reasons = []

        region = house.get('region', '')
        if any(area in region for area in ['海淀', '西城', '东城']):
            reasons.append("优质学区")

        total_price = house.get('total_price', 0)
        if total_price < 500:
            reasons.append("价格适中")
        elif total_price >= 1000:
            reasons.append("高端住宅")

        layout = house.get('layout', '')
        if '3室' in layout or '三室' in layout:
            reasons.append("户型实用")

        if not reasons:
            reasons.append("性价比高")

        return "、".join(reasons[:2])
