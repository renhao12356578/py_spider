from flask import Flask, send_file, request, jsonify,Blueprint,render_template,redirect
import uuid
import re
import os
from datetime import datetime
from pathlib import Path
from LLM.LLM import recomandation_prompt,get_area_statistics,call_spark_api
from route import router_bp
app = Flask(__name__,static_folder='../project_web',static_url_path='/project_web')

#注册route.py的蓝图
app.register_blueprint(router_bp)

# ==========================================


# 会话存储目录
SESSION_DIR = Path(__file__).parent / 'LLM' / 'chat_sessions'
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# 会话存储（生产环境建议使用Redis等持久化存储）
session_storage = {}

#基础界面调转
@app.route('/')
def index():
    return redirect('/project_web/index.html')


def save_session_to_file(session_id):
    """将会话保存到文件"""
    try:
        if session_id not in session_storage:
            return

        file_path = SESSION_DIR / f"{session_id}.txt"
        session_data = session_storage[session_id]

        with open(file_path, 'w', encoding='utf-8') as f:
            # 写入会话元数据
            f.write(f"=== 会话ID: {session_id} ===\n")
            f.write(f"创建时间: {session_data.get('created_at', 'N/A')}\n")
            f.write(f"最后更新: {datetime.now().isoformat()}\n")
            f.write(f"消息总数: {len(session_data['history'])}\n")
            f.write("=" * 60 + "\n\n")

            # 写入对话历史
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

        # 解析文件内容
        history = []
        current_role = None
        current_content = []
        current_timestamp = None

        for line in content.split('\n'):
            line = line.strip()

            # 跳过分隔线和空行
            if line.startswith('=') or line.startswith('-') or not line:
                continue

            # 解析角色和时间戳
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
                # 累积内容
                if current_role:
                    current_content.append(line)

        # 添加最后一条消息
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
            session_id = file_path.stem  # 文件名（不含扩展名）
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
    # 匹配类似 "65,000元/㎡" 或 "65000元/平" 的模式
    pattern = r'(\d{1,3}(?:,\d{3})*|\d+)(?:元|万)'
    matches = re.findall(pattern, reply)

    if matches:
        # 取第一个匹配的价格，去除逗号
        price_str = matches[0].replace(',', '')
        try:
            return int(price_str)
        except:
            return None
    return None


def get_session_history(session_id):
    """获取会话历史"""
    # 如果内存中没有，尝试从文件加载
    if session_id not in session_storage:
        loaded_data = load_session_from_file(session_id)
        if loaded_data:
            session_storage[session_id] = loaded_data
        else:
            # 创建新会话
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

    # 限制历史记录长度（保留最近20条）
    if len(history) > 20:
        session_storage[session_id]['history'] = history[-20:]

    # 每次添加消息后自动保存到文件
    save_session_to_file(session_id)


@app.route('/api/beijing/ai/chat', methods=['POST'])
def ai_chat():
    """
    北京房产AI聊天接口
    """
    try:
        # 解析请求数据

        data = request.get_json()

        if not data:
            return jsonify({
                'code': 400,
                'message': '请求体不能为空'
            }), 400

        message = data.get('message', '').strip()
        session_id = data.get('session_id', '')

        # 验证必填字段
        if not message:
            return jsonify({
                'code': 400,
                'message': 'message字段不能为空'
            }), 400

        # 如果没有提供session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 获取会话历史
        history = get_session_history(session_id)

        # 初始化会话（如果是新会话）
        if len(history) == 0:
            # 添加系统提示词（假设你有recomandation_prompt）
            add_to_session(session_id, 'system', recomandation_prompt)

        # 添加用户消息
        add_to_session(session_id, 'user', message)

        # 提取区域信息
        district = extract_district_from_message(message)

        # 如果检测到区域查询，可以先获取统计数据
        enhanced_message = message
        if district and ('均价' in message or '房价' in message or '价格' in message):
            try:
                # 调用你的get_area_statistics函数获取数据
                area_stats = get_area_statistics(f"北京{district}区")
                enhanced_message = f"{message}\n\n参考数据：{area_stats}"
            except Exception as e:
                print(f"获取区域统计数据失败: {e}")

        # 调用LLM API（使用你已有的call_spark_api函数）
        reply = call_spark_api(enhanced_message)

        if not reply:
            return jsonify({
                'code': 500,
                'message': 'LLM服务暂时不可用，请稍后重试'
            }), 500

        # 添加助手回复到历史
        add_to_session(session_id, 'assistant', reply)

        # 构建响应数据
        related_data = {}

        if district:
            related_data['district'] = district

            # 尝试从回复中提取价格
            avg_price = extract_price_from_reply(reply)
            if avg_price:
                related_data['avg_price'] = avg_price

        # 返回成功响应
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


@app.route('/api/beijing/ai/chat/history', methods=['GET'])
def get_chat_history():
    """
    获取会话历史记录
    查询参数: session_id
    """
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

    # 获取历史记录，过滤掉system角色的消息（不展示给用户）
    history = session_storage[session_id]['history']
    filtered_history = [
        {
            'role': msg['role'],
            'content': msg['content'],
            'timestamp': msg['timestamp']
        }
        for msg in history
        if msg['role'] != 'system'  # 不返回系统提示词
    ]

    return jsonify({
        'code': 200,
        'data': {
            'history': filtered_history,
            'session_id': session_id,
            'total_messages': len(filtered_history)
        }
    }), 200


@app.route('/api/beijing/ai/sessions/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """
    清除会话历史（可选接口）
    """
    # 从内存中删除
    if session_id in session_storage:
        del session_storage[session_id]

    # 从文件中删除
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


from flask_jwt_extended import jwt_required, get_jwt_identity

# 导入数据库类
from LLM.report import ReportDatabase

reports_bp = Blueprint('reports', __name__, url_prefix='/api')
db = ReportDatabase()


# ============ 报告类型 ============

@reports_bp.route('/reports/types', methods=['GET'])
def get_report_types():
    """
    43. 获取报告类型列表
    GET /api/reports/types
    """
    try:
        types = db.get_report_types()
        return jsonify({
            "code": 200,
            "data": {
                "types": types
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报告类型失败: {str(e)}"
        }), 500


# ============ 报告列表 ============

@reports_bp.route('/reports', methods=['GET'])
def get_reports_list():
    """
    44. 获取报告列表
    GET /api/reports
    查询参数: type, city, page, page_size
    """
    try:
        # 获取查询参数
        report_type = request.args.get('type')
        city = request.args.get('city')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        # 查询数据库
        result = db.get_reports_list(
            report_type=report_type,
            city=city,
            page=page,
            page_size=page_size
        )

        return jsonify({
            "code": 200,
            "data": result
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报告列表失败: {str(e)}"
        }), 500


# ============ 报告详情 ============

@reports_bp.route('/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    """
    45. 获取报告详情
    GET /api/reports/:id
    """
    try:
        report = db.get_report_detail(report_id)

        if not report:
            return jsonify({
                "code": 404,
                "message": "报告不存在"
            }), 404

        return jsonify({
            "code": 200,
            "data": report
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报告详情失败: {str(e)}"
        }), 500


# ============ 生成自定义报告 ============

@reports_bp.route('/reports/generate', methods=['POST'])
@jwt_required()
def generate_custom_report():
    """
    46. 生成自定义报告
    POST /api/reports/generate
    """
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # 验证必要字段
        required_fields = ['type', 'city', 'districts', 'date_range', 'metrics', 'format']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"缺少必要字段: {field}"
                }), 400

        # 添加用户ID到数据中
        data['user_id'] = current_user

        # 创建报告记录
        result = db.create_custom_report(data)

        # 启动异步生成任务（这里需要实现异步任务，如使用Celery）
        # generate_report_async.delay(result['report_id'], data)

        return jsonify({
            "code": 200,
            "data": {
                "report_id": result['report_id'],
                "status": "generating",
                "estimated_time": 30,
                "message": "报告生成中，预计30秒完成"
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成报告失败: {str(e)}"
        }), 500


# ============ 我的报告 ============

@reports_bp.route('/reports/my', methods=['GET'])
@jwt_required()
def get_my_reports():
    """
    47. 获取我的报告
    GET /api/reports/my
    """
    try:
        current_user = get_jwt_identity()
        reports = db.get_user_reports(current_user)

        return jsonify({
            "code": 200,
            "data": {
                "reports": reports
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取我的报告失败: {str(e)}"
        }), 500


# ============ 下载报告 ============

@reports_bp.route('/reports/download/<filename>', methods=['GET'])
@jwt_required()
def download_report(filename):
    """
    下载报告文件
    GET /api/reports/download/:filename
    """
    try:
        # 安全地构建文件路径
        safe_filename = os.path.basename(filename)
        filepath = os.path.join('reports', safe_filename)

        if not os.path.exists(filepath):
            return jsonify({
                "code": 404,
                "message": "文件不存在"
            }), 404

        # 更新下载次数（这里需要根据文件名找到对应的报告ID）
        # db.increment_download_count(report_id)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename
        )

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"下载失败: {str(e)}"
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'code': 404,
        'message': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'code': 500,
        'message': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    # 启动时加载所有历史会话
    print("=" * 60)
    print("🚀 正在启动北京房产AI聊天服务...")
    print("=" * 60)
    load_all_sessions()
    print("=" * 60)

    app.run(host='127.0.0.1', port=5000, debug=True)