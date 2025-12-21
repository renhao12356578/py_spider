from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import datetime
# 导入数据库类
from .reportDB import ReportDatabase

reports_bp = Blueprint('reports', __name__, url_prefix='/api')
db = ReportDatabase()

# ============ 路由路径列表 ============
"""
路由路径说明：
1. GET    /api/reports/types      - 获取报告类型列表
2. GET    /api/reports            - 获取报告列表（带分页和筛选）
3. GET    /api/reports/<int:report_id> - 获取报告详情
4. POST   /api/reports            - 创建新报告
5. PUT    /api/reports/<int:report_id> - 更新报告
6. DELETE /api/reports/<int:report_id> - 删除报告
"""

# reports_routes.py (修改后的蓝图)
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
sys.path.append("..") #相对路径或绝对路径
from LLM.use_data import get_area_statistics
from .reportDB import ReportDatabase

reports_bp = Blueprint('reports', __name__, url_prefix='/api')
db = ReportDatabase()

from functools import wraps
def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证令牌',
                'data': None
            }), 401
        
        # 提取token（去掉Bearer前缀）
        token = auth_header.replace('Bearer ', '').strip()
        
        try:
            user_id = int(token)
        except:
            return jsonify({
                'code': 401,
                'message': '无效的认证令牌',
                'data': None
            }), 401
        
        # 将user_id添加到请求上下文中
        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function
# ============ AI生成报告 ============

@reports_bp.route('/reports/generate/ai', methods=['POST'])
@require_auth
def generate_ai_report():
    """
    使用AI生成区域分析报告
    POST /api/reports/generate/ai

    请求体示例：
    {
        "area": "海淀区",
        "report_type": "市场分析",
        "city": "北京",
        "format_type": "professional"  # 可选
    }
    """
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # 验证必要字段
        if 'area' not in data or not data['area']:
            return jsonify({
                "code": 400,
                "message": "缺少必要字段: area"
            }), 400

        # 获取参数
        area = data['area']
        report_type = data.get('report_type', '市场分析')
        city = data.get('city')
        format_type = data.get('format_type', 'professional')

        # 使用AI生成报告
        result = db.generate_ai_report(
            area=area,
            report_type=report_type,
            city=city,
            user_id=current_user
        )

        return jsonify({
            "code": 201,
            "data": result,
            "message": "AI报告生成成功"
        }), 201

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"AI报告生成失败: {str(e)}"
        }), 500


@reports_bp.route('/reports/format', methods=['POST'])
@require_auth
def format_report():
    """
    格式化报告内容
    POST /api/reports/format

    请求体示例：
    {
        "content": "原始报告内容...",
        "format_type": "professional"  # professional, academic, summary, markdown
    }
    """
    try:
        data = request.get_json()

        if 'content' not in data or not data['content']:
            return jsonify({
                "code": 400,
                "message": "缺少必要字段: content"
            }), 400

        content = data['content']
        format_type = data.get('format_type', 'professional')

        # 格式化内容
        formatted_content = db.format_existing_report(content, format_type)

        return jsonify({
            "code": 200,
            "data": {
                "original_length": len(content),
                "formatted_length": len(formatted_content),
                "formatted_content": formatted_content,
                "format_type": format_type
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"格式化失败: {str(e)}"
        }), 500




@reports_bp.route('/reports/area/statistics', methods=['GET'])
def get_area_statistics_api():
    """
    获取区域统计信息
    GET /api/reports/area/statistics?area=海淀区
    """
    try:
        area = request.args.get('area')

        if not area:
            return jsonify({
                "code": 400,
                "message": "缺少查询参数: area"
            }), 400

        # 获取区域统计信息
        statistics = get_area_statistics(area)

        return jsonify({
            "code": 200,
            "data": {
                "area": area,
                "statistics": statistics,
                "retrieved_at": datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取统计信息失败: {str(e)}"
        }), 500

@reports_bp.route('/reports/<int:report_id>/generate-image', methods=['POST'])
@require_auth
def generate_content_image(report_id):
    """
    为报告内容实时生成图片
    POST /api/reports/{report_id}/generate-image

    请求体示例：
    {
        "content": "需要生成图片的内容段落...",
        "title": "报告标题"  // 可选
    }

    返回示例：
    {
        "code": 200,
        "data": {
            "image_generated": true,
            "image_filename": "content_123_20231201120000.png",
            "image_path": "/path/to/image.png",
            "prompt": "生成图片的提示词",
            "revised_prompt": "优化后的提示词"
        }
    }
    """
    try:
        data = request.get_json()

        # 获取报告信息
        report = db.get_report_full_content(report_id)
        if not report:
            return jsonify({
                "code": 404,
                "message": "报告不存在"
            }), 404

        # 获取内容
        content = data.get('content')
        if not content:
            # 如果没有提供内容，使用报告内容
            content = report.get('content', '')[:500]

        # 生成图片
        title = data.get('title', report.get('title'))
        image_result = db.ai_service.generate_image_for_content(content, title)

        if image_result["success"]:
            # 保存图片
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_filename = db.save_image_from_base64(
                image_result["image_data"],
                prefix=f"content_{report_id}_{timestamp}"
            )

            if image_filename:
                # 关联图片到报告
                db._associate_image_with_report(report_id, image_filename, "content_generated")

                return jsonify({
                    "code": 200,
                    "data": {
                        "image_generated": True,
                        "image_filename": image_filename,
                        "image_path": os.path.join(db.img_path, image_filename),
                        "prompt": image_result.get("prompt", ""),
                        "revised_prompt": image_result.get("revised_prompt", ""),
                        "model": db.ai_service.image_model
                    }
                })

        return jsonify({
            "code": 500,
            "message": "图片生成失败",
            "details": image_result
        }), 500

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"图片生成失败: {str(e)}"
        }), 500


# ============ 创建报告（增强版） ============

@reports_bp.route('/reports/create', methods=['POST'])
@require_auth
def create_report():
    """
    创建报告（支持AI生成图片）
    POST /api/reports
    """
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # 验证必要字段
        required_fields = ['title', 'summary', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "code": 400,
                    "message": f"缺少必要字段或字段为空: {field}"
                }), 400

        # 获取参数
        title = data['title']
        summary = data['summary']
        content = data['content']
        report_type = data.get('type')
        city = data.get('city')
        generate_image = data.get('generate_image', True)

        # 创建报告
        result = db.create_report_with_ai_support(
            title=title,
            summary=summary,
            content=content,
            report_type=report_type,
            city=city,
            user_id=current_user,
            generate_image=generate_image
        )

        if result["success"]:
            return jsonify({
                "code": 201,
                "data": {
                    "report_id": result["report_id"],
                    "has_image": result["has_image"],
                    "message": result["message"]
                }
            }), 201
        else:
            return jsonify({
                "code": 500,
                "message": result.get("error", "创建报告失败")
            }), 500

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"创建报告失败: {str(e)}"
        }), 500


# ============ 获取内容历史 ============

@reports_bp.route('/reports/<int:report_id>/history', methods=['GET'])
@require_auth
def get_content_history(report_id):
    """
    获取报告内容修改历史
    GET /api/reports/{report_id}/history
    """
    try:
        history = db.get_content_history(report_id)

        return jsonify({
            "code": 200,
            "data": {
                "history": history,
                "total": len(history)
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取历史记录失败: {str(e)}"
        }), 500


# ============ AI生成报告草稿 ============

@reports_bp.route('/reports/generate-draft', methods=['POST'])
@require_auth
def generate_report_draft():
    """
    AI生成报告草稿
    POST /api/reports/generate-draft

    请求体示例：
    {
        "topic": "2024年人工智能发展趋势",
        "outline": ["引言", "现状分析", "发展趋势", "结论"],
        "style": "学术报告"
    }
    """
    try:
        data = request.get_json()

        if 'topic' not in data:
            return jsonify({
                "code": 400,
                "message": "缺少topic字段"
            }), 400

        # 调用AI生成草稿
        result = db.ai_service.generate_report_draft(
            topic=data['topic'],
            outline=data.get('outline')
        )

        if result["success"]:
            return jsonify({
                "code": 200,
                "data": {
                    "draft": result["draft"],
                    "tokens_used": result.get("tokens_used", 0)
                }
            })
        else:
            return jsonify({
                "code": 500,
                "message": f"生成草稿失败: {result.get('error', '未知错误')}"
            }), 500

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成草稿失败: {str(e)}"
        }), 500

# ============ 报告类型 ============

@reports_bp.route('/reports/types', methods=['GET'])
def get_report_types():
    """
    获取报告类型列表
    GET /api/reports/types

    返回示例：
    {
        "code": 200,
        "data": {
            "types": ["市场分析", "政策研究", "经济预测", ...]
        }
    }
    """
    try:
        # 这里需要从数据库查询报告类型
        # 假设我们有一个报告类型表或者从现有报告中提取
        types = []
        # TODO: 根据您的数据库结构实现获取报告类型逻辑
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

@reports_bp.route('/reports/list', methods=['GET'])
def get_reports_list():
    """
    获取报告列表
    GET /api/reports?type=市场分析&city=北京&page=1&page_size=10

    查询参数:
    - type: 报告类型（可选）
    - city: 城市（可选）
    - page: 页码，默认1（可选）
    - page_size: 每页数量，默认10（可选）

    返回示例：
    {
        "code": 200,
        "data": {
            "reports": [...],
            "total": 100,
            "page": 1,
            "page_size": 10,
            "total_pages": 10
        }
    }
    """
    try:
        # 获取查询参数
        report_type = request.args.get('type')
        city = request.args.get('city')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        # 查询数据库
        result = db.get_all_reports_summary(
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
    获取报告详情
    GET /api/reports/123

    路径参数:
    - report_id: 报告ID

    返回示例：
    {
        "code": 200,
        "data": {
            "id": 123,
            "title": "报告标题",
            "summary": "报告摘要",
            "content": "完整内容...",
            ...
        }
    }
    """
    try:
        report = db.get_report_full_content(report_id)

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


# ============ 创建新报告 ============


@reports_bp.route('/reports/<int:report_id>', methods=['PUT'])
@require_auth
def update_report(report_id):
    """
    更新报告
    PUT /api/reports/123

    路径参数:
    - report_id: 报告ID

    请求体示例：
    {
        "title": "更新后的标题",
        "summary": "更新后的摘要",
        "content": "更新后的内容"
    }

    返回示例：
    {
        "code": 200,
        "data": {
            "message": "报告更新成功"
        }
    }
    """
    try:
        data = request.get_json()

        # 验证至少有一个字段需要更新
        if not any(key in data for key in ['title', 'summary', 'content']):
            return jsonify({
                "code": 400,
                "message": "至少需要提供title、summary或content中的一个字段"
            }), 400

        # 获取可更新字段
        title = data.get('title')
        summary = data.get('summary')
        content = data.get('content')

        # 更新报告
        success = db.update_report(
            report_id=report_id,
            title=title,
            summary=summary,
            content=content
        )

        if not success:
            return jsonify({
                "code": 404,
                "message": "报告不存在或更新失败"
            }), 404

        return jsonify({
            "code": 200,
            "data": {
                "message": "报告更新成功"
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"更新报告失败: {str(e)}"
        }), 500


# ============ 删除报告 ============

@reports_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id):
    """
    删除报告（软删除）
    DELETE /api/reports/123

    路径参数:
    - report_id: 报告ID

    返回示例：
    {
        "code": 200,
        "data": {
            "message": "报告已删除"
        }
    }
    """
    try:
        # 删除报告
        success = db.delete_report(report_id)

        if not success:
            return jsonify({
                "code": 404,
                "message": "报告不存在或删除失败"
            }), 404

        return jsonify({
            "code": 200,
            "data": {
                "message": "报告已删除"
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"删除报告失败: {str(e)}"
        }), 500
from flask import Flask
