"""
AI聊天相关路由
"""
from flask import Blueprint, request, jsonify
from pathlib import Path
import csv

# 导入服务层
from services.ai_chat_service import (
    AIService,
    get_session_history,
    session_storage,
    load_all_sessions
)
from services.valuation_service import calculate_house_valuation


# ============================================
# 蓝图定义
# ============================================

ai_bp = Blueprint('ai_chat', __name__, url_prefix='/api/beijing/ai')
ai_service = AIService()


# ============================================
# 路由定义
# ============================================

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
        # 计算估价
        valuation_result = calculate_house_valuation(house_id)

        # 构建估价数据文本
        valuation_text = f"""房源ID: {house_id}
估算价格: {valuation_result['estimated_price']}万元
价格区间: {valuation_result['price_range']['min']}-{valuation_result['price_range']['max']}万元
市场情绪: {valuation_result['market_sentiment']}

综合评分:
"""
        for factor in valuation_result['factors']:
            valuation_text += f"- {factor['name']}: {factor['score']}分 (权重{factor['weight']}%)\n"

        valuation_text += f"\n购买建议: {valuation_result['advice']}\n{valuation_result['advice_detail']}"

        # 调用AI进行总结
        session_id = ai_service.create_or_get_session(session_id, 'valuation')
        reply = ai_service.call_ai(session_id, "请帮我总结这套房子的估价情况", valuation_text)

        return jsonify({
            'code': 200,
            'data': {
                'reply': reply,
                'session_id': session_id,
                'valuation': valuation_result
            }
        }), 200

    except Exception as e:
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


@ai_bp.route('/value/<city>', methods=['GET'])
def value_report(city):
    """基于 summary_all.csv 中指定城市的数据撰写报告"""
    try:
        base = Path(__file__).parent
        summary_path = base / 'summary_all.csv'

        # 读取 summary
        summary = None
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('city') == city:
                        summary = row
                        break

        if not summary:
            return jsonify({'code': 404, 'message': f'城市 {city} 未在 summary_all 中找到'}), 404

        # 提取关键信息
        current_price = summary.get('current_price', 'N/A')
        trend = summary.get('trend', 'N/A')
        change_percent = summary.get('change_percent', '0')
        confidence = summary.get('confidence', 'N/A')
        linear_slope = summary.get('linear_slope', '0')
        polynomial_r_squared = summary.get('polynomial_r_squared', '0')
        forecast_periods = summary.get('forecast_periods', '0')
        ma_trend = summary.get('ma_trend', '0')

        # 构造提示词
        prompt = f"""请基于以下城市房地产市场数据，生成一份专业的市场分析报告：

【城市】{city}
【当前价格】{current_price}
【市场趋势】{trend}
【价格变动】{change_percent}%
【置信度】{confidence}
【线性斜率】{linear_slope}
【多项式拟合度】{polynomial_r_squared}
【移动平均趋势】{ma_trend}

请生成400-500字的分析报告，包括：
1. 当前市场状况
2. 技术指标解读
3. 趋势研判
4. 投资建议
5. 结论展望"""

        # 调用AI生成报告
        ai = AIService()
        report = ai.call_ai(None, "请根据数据生成房地产市场分析报告", prompt)

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
        return jsonify({'code': 500, 'message': str(e)}), 500
