from flask import Blueprint, request, jsonify
from datetime import datetime
from utils import get_db_connection
import pymysql

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

@system_bp.route('/config', methods=['GET'])
def get_config():
    """
    获取系统配置
    GET /api/system/config
    """
    try:
        config = {
            "code": 200,
            "data": {
                "features": {
                    "ai_chat": True,
                    "reports": True,
                    "data_analysis": True
                },
                "system_name": "北京房产数据分析系统",
                "version": "1.0.0"
            },
            "message": "获取配置成功"
        }
        return jsonify(config)
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取配置失败: {str(e)}"
        }), 500


@system_bp.route('/data-update-time', methods=['GET'])
def get_data_update_time():
    """
    获取数据更新时间
    GET /api/system/data-update-time
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "code": 200,
                "data": {"last_update": "2024-12-24"}
            })
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 使用正确的表名 beijing_house_info
        cursor.execute("""
            SELECT MAX(DATE(NOW())) as last_update 
            FROM beijing_house_info
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 如果查询失败，返回当前日期
        last_update = result['last_update'] if result and result['last_update'] else datetime.now().strftime('%Y-%m-%d')
        
        return jsonify({
            "code": 200,
            "data": {
                "last_update": last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else None,
                "update_frequency": "每日更新"
            },
            "message": "获取成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取数据更新时间失败: {str(e)}"
        }), 500


@system_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    提交用户反馈
    POST /api/system/feedback
    请求体: {"type": "bug/feature/other", "content": "反馈内容", "contact": "联系方式(可选)"}
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({
                "code": 400,
                "message": "反馈内容不能为空"
            }), 400
        
        feedback_type = data.get('type', 'other')
        content = data.get('content')
        contact = data.get('contact', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                contact VARCHAR(255),
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        
        cursor.execute("""
            INSERT INTO system_feedback (type, content, contact)
            VALUES (%s, %s, %s)
        """, (feedback_type, content, contact))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "code": 200,
            "message": "感谢您的反馈,我们会尽快处理"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"提交反馈失败: {str(e)}"
        }), 500


@system_bp.route('/version', methods=['GET'])
def get_version():
    """
    获取系统版本信息
    GET /api/system/version
    """
    try:
        version_info = {
            "code": 200,
            "data": {
                "version": "1.0.0",
                "release_date": "2024-12-01",
                "features": [
                    "全国房产数据分析",
                    "北京地区详细数据",
                    "AI智能问答",
                    "数据报告生成"
                ],
                "update_log": [
                    {
                        "version": "1.0.0",
                        "date": "2025-12-01",
                        "changes": ["初始版本发布"]
                    }
                ]
            },
            "message": "获取版本信息成功"
        }
        return jsonify(version_info)
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取版本信息失败: {str(e)}"
        }), 500
