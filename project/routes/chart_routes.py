"""
图表相关路由
使用template模板生成图表
"""
import os
import sys
from flask import Blueprint, request, jsonify, send_file
from utils.auth import require_auth

# 添加template目录到路径
template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'template')
sys.path.insert(0, template_path)

# 导入图表构建器
try:
    from Bar import TiDBChartBuilder as BarChartBuilder
    from Line import TiDBChartBuilder as LineChartBuilder
except ImportError as e:
    print(f"导入图表模板失败: {e}")
    BarChartBuilder = None
    LineChartBuilder = None

# 蓝图定义
charts_bp = Blueprint('charts', __name__, url_prefix='/api/charts')

# 数据库配置（从环境变量或配置文件读取）
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'house_data'
}


@charts_bp.route('/bar', methods=['POST'])
def generate_bar_chart():
    """生成柱状图"""
    try:
        data = request.get_json()
        city = data.get('city')
        area = data.get('area')
        
        if not city and not area:
            return jsonify({
                "code": 400,
                "message": "请至少提供城市或区域之一"
            }), 400
        
        # 使用柱状图构建器
        if BarChartBuilder:
            builder = BarChartBuilder(db_config=DB_CONFIG)
            
            # 构建SQL查询
            if area:
                query = f"""
                SELECT area, AVG(price) as avg_price, COUNT(*) as count
                FROM house_data
                WHERE area LIKE '%{area}%'
                GROUP BY area
                ORDER BY avg_price DESC
                LIMIT 10
                """
            else:
                query = f"""
                SELECT area, AVG(price) as avg_price, COUNT(*) as count
                FROM house_data
                WHERE city = '{city}'
                GROUP BY area
                ORDER BY avg_price DESC
                LIMIT 10
                """
            
            # 生成图表HTML
            chart_html = builder.query_and_build(
                query=query,
                x_column='area',
                y_column='avg_price',
                title=f'{city or area}房价分析'
            )
            
            return jsonify({
                "code": 200,
                "data": {
                    "html": chart_html,
                    "type": "bar"
                }
            }), 200
        else:
            return jsonify({
                "code": 500,
                "message": "图表模板未加载"
            }), 500
            
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成柱状图失败: {str(e)}"
        }), 500


@charts_bp.route('/line', methods=['POST'])
def generate_line_chart():
    """生成折线图"""
    try:
        data = request.get_json()
        city = data.get('city')
        area = data.get('area')
        
        if not city and not area:
            return jsonify({
                "code": 400,
                "message": "请至少提供城市或区域之一"
            }), 400
        
        # 使用折线图构建器
        if LineChartBuilder:
            builder = LineChartBuilder(db_config=DB_CONFIG)
            
            # 构建SQL查询（按时间趋势）
            if area:
                query = f"""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month, 
                       AVG(price) as avg_price
                FROM house_data
                WHERE area LIKE '%{area}%'
                GROUP BY month
                ORDER BY month
                LIMIT 12
                """
            else:
                query = f"""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month, 
                       AVG(price) as avg_price
                FROM house_data
                WHERE city = '{city}'
                GROUP BY month
                ORDER BY month
                LIMIT 12
                """
            
            # 生成图表HTML
            chart_html = builder.query_and_build(
                query=query,
                x_column='month',
                y_column='avg_price',
                title=f'{city or area}房价趋势'
            )
            
            return jsonify({
                "code": 200,
                "data": {
                    "html": chart_html,
                    "type": "line"
                }
            }), 200
        else:
            return jsonify({
                "code": 500,
                "message": "图表模板未加载"
            }), 500
            
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成折线图失败: {str(e)}"
        }), 500


@charts_bp.route('/3d', methods=['GET'])
def get_3d_chart():
    """获取3D图表HTML"""
    try:
        # 直接返回3D.html文件
        template_3d_path = os.path.join(template_path, '3D.html')
        
        if os.path.exists(template_3d_path):
            return send_file(template_3d_path, mimetype='text/html')
        else:
            return jsonify({
                "code": 404,
                "message": "3D图表模板不存在"
            }), 404
            
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取3D图表失败: {str(e)}"
        }), 500


@charts_bp.route('/data/sample', methods=['GET'])
def get_sample_data():
    """获取示例数据用于图表展示"""
    try:
        # 返回示例数据
        sample_data = {
            "bar": {
                "labels": ["海淀区", "朝阳区", "东城区", "西城区", "丰台区"],
                "values": [65000, 58000, 72000, 68000, 45000]
            },
            "line": {
                "labels": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
                "values": [60000, 61000, 62500, 63000, 64000, 65000]
            }
        }
        
        return jsonify({
            "code": 200,
            "data": sample_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取示例数据失败: {str(e)}"
        }), 500
