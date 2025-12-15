"""
报告相关路由
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from LLM.report import ReportDatabase

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')
db = ReportDatabase()


@reports_bp.route('/types', methods=['GET'])
def get_report_types():
    """获取报告类型列表"""
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


@reports_bp.route('', methods=['GET'])
def get_reports_list():
    """获取报告列表"""
    try:
        report_type = request.args.get('type')
        city = request.args.get('city')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

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


@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    """获取报告详情"""
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


@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_custom_report():
    """生成自定义报告"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        required_fields = ['type', 'city', 'districts', 'date_range', 'metrics', 'format']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"缺少必要字段: {field}"
                }), 400

        data['user_id'] = current_user

        result = db.create_custom_report(data)

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


@reports_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_reports():
    """获取我的报告"""
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


@reports_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_report(filename):
    """下载报告文件"""
    try:
        safe_filename = os.path.basename(filename)
        filepath = os.path.join('reports', safe_filename)

        if not os.path.exists(filepath):
            return jsonify({
                "code": 404,
                "message": "文件不存在"
            }), 404

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
