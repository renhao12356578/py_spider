"""
北京数据相关路由
"""
from flask import Blueprint, request, jsonify
import data_process as dp
import json

beijing_bp = Blueprint('beijing', __name__, url_prefix='/api/beijing')


@beijing_bp.route('/overview', methods=['GET'])
def beijing_overview():
    """获取北京房产概览信息"""
    result = dp.get_beijing_overview()
    return jsonify(json.loads(result))


@beijing_bp.route('/district-ranking', methods=['GET'])
def district_ranking():
    """获取北京行政区单价排名"""
    result = dp.get_district_ranking()
    return jsonify(json.loads(result))


@beijing_bp.route('/district-prices', methods=['GET'])
def district_prices():
    """获取北京所有行政区的平均单价及记录数"""
    result = dp.get_district_prices()
    return jsonify(json.loads(result))


@beijing_bp.route('/analysis/floor', methods=['GET'])
def analysis_floor():
    """北京房产楼层特征分析"""
    result = dp.analysis_floor()
    return jsonify(json.loads(result))


@beijing_bp.route('/analysis/layout', methods=['GET'])
def analysis_layout():
    """北京房产户型特征分析"""
    result = dp.analysis_layout()
    return jsonify(json.loads(result))


@beijing_bp.route('/analysis/orientation', methods=['GET'])
def analysis_orientation():
    """北京房产朝向特征分析"""
    result = dp.analysis_orientation()
    return jsonify(json.loads(result))


@beijing_bp.route('/analysis/elevator', methods=['GET'])
def analysis_elevator():
    """北京房产电梯特征分析"""
    result = dp.analysis_elevator()
    return jsonify(json.loads(result))


@beijing_bp.route('/chart/scatter', methods=['GET'])
def get_scatter_data():
    """获取北京房产面积-价格散点图数据"""
    district = request.args.get('district')
    limit = request.args.get('limit', 1000, type=int)
    result = dp.get_scatter_data(district, limit)
    return jsonify(json.loads(result))


@beijing_bp.route('/chart/boxplot', methods=['GET'])
def get_boxplot_data():
    """获取北京指定区域的单价箱线图数据"""
    district = request.args.get('district', '')
    result = dp.get_boxplot_data(district)
    return jsonify(json.loads(result))

@beijing_bp.route('/houses', methods=['GET'])
def query_houses_list():
    """北京数据模块 - 房源列表查询"""
    # 提取所有筛选参数
    district = request.args.get('district')
    layout = request.args.get('layout')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    min_area = request.args.get('min_area', type=int)
    max_area = request.args.get('max_area', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    result = dp.query_houses_list(
        district=district,
        layout=layout,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        page=page,
        page_size=page_size
    )
    return jsonify(json.loads(result))
