"""
报告相关路由
整合报告CRUD、AI生成、格式化等功能
"""
import os
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify
from utils.auth import require_auth
from report.reportDB import ReportDatabase
from report.task_manager import task_manager
from tools.house_query import get_area_statistics

# 蓝图定义
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')
db = ReportDatabase()


# ============ 报告类型 ============

@reports_bp.route('/types', methods=['GET'])
def get_report_types():
    """获取报告类型列表"""
    try:
        types = db.get_report_types()
        return jsonify({
            "code": 200,
            "data": {"types": types}
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报告类型失败: {str(e)}"
        }), 500


# ============ 报告列表 ============

@reports_bp.route('', methods=['GET'])
def get_reports_list():
    """获取报告列表（带分页和筛选）"""
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


@reports_bp.route('/list', methods=['GET'])
def get_reports_list_alt():
    """获取报告列表（备用路径）"""
    try:
        report_type = request.args.get('type')
        city = request.args.get('city')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

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


# ============ 创建报告 ============

@reports_bp.route('/create', methods=['POST'])
@require_auth
def create_report():
    """创建报告（支持AI生成图片）"""
    try:
        data = request.get_json()
        current_user = request.user_id

        required_fields = ['title', 'summary', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "code": 400,
                    "message": f"缺少必要字段或字段为空: {field}"
                }), 400

        result = db.create_report_with_ai_support(
            title=data['title'],
            summary=data['summary'],
            content=data['content'],
            report_type=data.get('type'),
            city=data.get('city'),
            user_id=current_user,
            generate_image=data.get('generate_image', True)
        )

        if result.get("success"):
            return jsonify({
                "code": 201,
                "data": {
                    "report_id": result["report_id"],
                    "has_image": result.get("has_image"),
                    "message": result.get("message", "创建成功")
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


# ============ 更新报告 ============

@reports_bp.route('/<int:report_id>', methods=['PUT'])
@require_auth
def update_report(report_id):
    """更新报告"""
    try:
        data = request.get_json()

        if not any(key in data for key in ['title', 'summary', 'content']):
            return jsonify({
                "code": 400,
                "message": "至少需要提供title、summary或content中的一个字段"
            }), 400

        success = db.update_report(
            report_id=report_id,
            title=data.get('title'),
            summary=data.get('summary'),
            content=data.get('content')
        )

        if not success:
            return jsonify({
                "code": 404,
                "message": "报告不存在或更新失败"
            }), 404

        return jsonify({
            "code": 200,
            "data": {"message": "报告更新成功"}
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"更新报告失败: {str(e)}"
        }), 500


# ============ 删除报告 ============

@reports_bp.route('/<int:report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id):
    """删除报告（软删除）"""
    try:
        success = db.delete_report(report_id)

        if not success:
            return jsonify({
                "code": 404,
                "message": "报告不存在或删除失败"
            }), 404

        return jsonify({
            "code": 200,
            "data": {"message": "报告已删除"}
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"删除报告失败: {str(e)}"
        }), 500


# ============ AI生成报告（异步） ============

@reports_bp.route('/generate/ai/async', methods=['POST'])
@require_auth
def generate_ai_report_async():
    """使用AI生成区域分析报告（异步模式）"""
    try:
        data = request.get_json()
        current_user = request.user_id

        # 验证：至少提供area或city之一
        area = data.get('area', '').strip()
        city = data.get('city', '').strip()
        
        if not area and not city:
            return jsonify({
                "code": 400,
                "message": "请至少提供城市或区域之一"
            }), 400
        
        # 如果area为空，使用city作为area
        if not area:
            area = city
        
        # 创建任务
        task_id = task_manager.create_task('generate_report', {
            'area': area,
            'city': city,
            'report_type': data.get('report_type', '市场分析'),
            'user_id': current_user
        })
        
        # 后台线程执行报告生成
        def generate_in_background():
            try:
                task_manager.update_task(task_id, status='processing', progress=10, message='正在生成报告...')
                
                result = db.generate_ai_report(
                    area=area,
                    report_type=data.get('report_type', '市场分析'),
                    city=city if city else None,
                    user_id=current_user
                )
                
                task_manager.update_task(
                    task_id, 
                    status='completed', 
                    progress=100, 
                    message='报告生成完成',
                    result=result
                )
            except Exception as e:
                task_manager.update_task(
                    task_id,
                    status='failed',
                    progress=0,
                    message='报告生成失败',
                    error=str(e)
                )
        
        thread = threading.Thread(target=generate_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "code": 200,
            "data": {
                "task_id": task_id,
                "status": "pending",
                "message": "报告生成任务已创建"
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"创建任务失败: {str(e)}"
        }), 500


@reports_bp.route('/task/<task_id>', methods=['GET'])
@require_auth
def get_task_status(task_id):
    """查询任务状态"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({
                "code": 404,
                "message": "任务不存在"
            }), 404
        
        return jsonify({
            "code": 200,
            "data": task
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"查询任务失败: {str(e)}"
        }), 500


@reports_bp.route('/tasks/user', methods=['GET'])
@require_auth
def get_user_tasks():
    """获取当前用户的所有任务"""
    try:
        current_user = request.user_id
        all_tasks = []
        
        # 遍历所有任务，筛选当前用户的任务
        for task_id, task in task_manager.tasks.items():
            if task.get('params', {}).get('user_id') == current_user:
                all_tasks.append(task)
        
        # 按创建时间排序
        all_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            "code": 200,
            "data": {
                "tasks": all_tasks,
                "total": len(all_tasks)
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取任务列表失败: {str(e)}"
        }), 500


# ============ AI生成报告 ============

@reports_bp.route('/generate/ai', methods=['POST'])
@require_auth
def generate_ai_report():
    """使用AI生成区域分析报告"""
    try:
        data = request.get_json()
        current_user = request.user_id

        if 'area' not in data or not data['area']:
            return jsonify({
                "code": 400,
                "message": "缺少必要字段: area"
            }), 400

        result = db.generate_ai_report(
            area=data['area'],
            report_type=data.get('report_type', '市场分析'),
            city=data.get('city'),
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


@reports_bp.route('/generate/ai/stream', methods=['POST'])
@require_auth
def generate_ai_report_stream():
    """使用AI生成区域分析报告（流式输出）"""
    try:
        data = request.get_json()
        current_user = request.user_id

        # 验证：至少提供area或city之一
        area = data.get('area', '').strip()
        city = data.get('city', '').strip()
        
        if not area and not city:
            return jsonify({
                "code": 400,
                "message": "请至少提供城市或区域之一"
            }), 400
        
        # 如果area为空，使用city作为area
        if not area:
            area = city

        def generate():
            """SSE生成器"""
            import json
            for event in db.generate_ai_report_stream(
                area=area,
                report_type=data.get('report_type', '市场分析'),
                city=city if city else None,
                user_id=current_user
            ):
                # 格式化为SSE事件
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return generate(), 200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"AI报告生成失败: {str(e)}"
        }), 500


# ============ 格式化报告 ============

@reports_bp.route('/format', methods=['POST'])
@require_auth
def format_report():
    """格式化报告内容"""
    try:
        data = request.get_json()

        if 'content' not in data or not data['content']:
            return jsonify({
                "code": 400,
                "message": "缺少必要字段: content"
            }), 400

        content = data['content']
        format_type = data.get('format_type', 'professional')

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


# ============ 区域统计 ============

@reports_bp.route('/area/statistics', methods=['GET'])
def get_area_statistics_api():
    """获取区域统计信息"""
    try:
        area = request.args.get('area')
        city = request.args.get('city')

        if not area:
            return jsonify({
                "code": 400,
                "message": "缺少查询参数: area"
            }), 400

        statistics = get_area_statistics(area, city=city)

        return jsonify({
            "code": 200,
            "data": {
                "area": area,
                "city": city,
                "statistics": statistics,
                "retrieved_at": datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取统计信息失败: {str(e)}"
        }), 500


# ============ 生成图片 ============

@reports_bp.route('/<int:report_id>/generate-image', methods=['POST'])
@require_auth
def generate_content_image(report_id):
    """为报告内容生成图片"""
    try:
        data = request.get_json()

        report = db.get_report_full_content(report_id)
        if not report:
            return jsonify({
                "code": 404,
                "message": "报告不存在"
            }), 404

        content = data.get('content') or report.get('content', '')[:500]
        title = data.get('title', report.get('title'))

        image_result = db.ai_service.generate_image_for_content(content, title)

        if image_result.get("success"):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_filename = db.save_image_from_base64(
                image_result["image_data"],
                prefix=f"content_{report_id}_{timestamp}"
            )

            if image_filename:
                db._associate_image_with_report(report_id, image_filename, "content_generated")

                return jsonify({
                    "code": 200,
                    "data": {
                        "image_generated": True,
                        "image_filename": image_filename,
                        "image_path": os.path.join(db.img_path, image_filename)
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


# ============ 报告历史 ============

@reports_bp.route('/<int:report_id>/history', methods=['GET'])
@require_auth
def get_content_history(report_id):
    """获取报告内容修改历史"""
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


# ============ 生成草稿 ============

@reports_bp.route('/generate-draft', methods=['POST'])
@require_auth
def generate_report_draft():
    """AI生成报告草稿"""
    try:
        data = request.get_json()

        if 'topic' not in data:
            return jsonify({
                "code": 400,
                "message": "缺少topic字段"
            }), 400

        result = db.ai_service.generate_report_draft(
            topic=data['topic'],
            outline=data.get('outline')
        )

        if result.get("success"):
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


# ============ 自定义报告 ============

@reports_bp.route('/generate', methods=['POST'])
@require_auth
def generate_custom_report():
    """生成自定义报告"""
    try:
        data = request.get_json()
        current_user = request.user_id

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


# ============ 我的报告 ============

@reports_bp.route('/my', methods=['GET'])
@require_auth
def get_my_reports():
    """获取我的报告"""
    try:
        current_user = request.user_id
        reports = db.get_user_reports(current_user)

        return jsonify({
            "code": 200,
            "data": {"reports": reports}
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取我的报告失败: {str(e)}"
        }), 500


# ============ 下载报告 ============

@reports_bp.route('/download/<filename>', methods=['GET'])
@require_auth
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


# ============ 静态报告 ============

@reports_bp.route('/static', methods=['GET'])
def get_static_reports():
    """获取静态报告列表（down目录中的PDF文件）"""
    try:
        # 使用绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_dir = os.path.join(base_dir, 'report', 'down')
        print(f"基础目录: {base_dir}")
        print(f"静态报告目录: {static_dir}")
        print(f"目录是否存在: {os.path.exists(static_dir)}")
        
        if not os.path.exists(static_dir):
            print("静态报告目录不存在")
            return jsonify({
                "code": 200,
                "data": {"reports": []}
            })
        
        reports = []
        files = os.listdir(static_dir)
        print(f"目录中的文件: {files}")
        
        for filename in files:
            if filename.endswith('.pdf'):
                filepath = os.path.join(static_dir, filename)
                file_stat = os.stat(filepath)
                
                title = filename.replace('.pdf', '')
                
                report = {
                    "id": f"static_{len(reports)}",
                    "title": title,
                    "filename": filename,
                    "type": "官方报告",
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d'),
                    "status": "completed",
                    "is_static": True
                }
                reports.append(report)
                print(f"添加静态报告: {report['title']}")
        
        print(f"共找到 {len(reports)} 个静态报告")
        
        return jsonify({
            "code": 200,
            "data": {"reports": reports, "total": len(reports)}
        })
        
    except Exception as e:
        print(f"获取静态报告失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "code": 500,
            "message": f"获取静态报告失败: {str(e)}"
        }), 500


@reports_bp.route('/static/download/<path:filename>', methods=['GET'])
def download_static_report(filename):
    """下载静态报告文件（无需认证）"""
    try:
        from urllib.parse import unquote
        safe_filename = os.path.basename(unquote(filename))
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'report', 'down', safe_filename)
        
        print(f"下载请求文件名: {filename}")
        print(f"解码后文件名: {safe_filename}")
        print(f"完整路径: {filepath}")
        print(f"文件是否存在: {os.path.exists(filepath)}")

        if not os.path.exists(filepath):
            return jsonify({
                "code": 404,
                "message": f"文件不存在: {safe_filename}"
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
