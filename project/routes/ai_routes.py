"""
AI聊天相关路由
"""
from flask import Blueprint, request, jsonify
import uuid
import re
from datetime import datetime
from pathlib import Path
from LLM.LLM import recomandation_prompt, get_area_statistics, call_spark_api

ai_bp = Blueprint('ai', __name__, url_prefix='/api/beijing/ai')

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
                area_stats = get_area_statistics(f"北京{district}区")
                enhanced_message = f"{message}\n\n参考数据：{area_stats}"
            except Exception as e:
                print(f"获取区域统计数据失败: {e}")

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
    }), 200
