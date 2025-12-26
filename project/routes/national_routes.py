"""
全国数据相关路由
"""
from flask import Blueprint, request, jsonify
import services.data_service as ds
import json

national_bp = Blueprint('national', __name__, url_prefix='/api/national')


@national_bp.route('/overview', methods=['GET'])
def national_overview():
    """获取全国房价概览"""
    result = ds.get_national_overview()
    return jsonify(json.loads(result))


@national_bp.route('/city-prices', methods=['GET'])
def city_prices():
    """获取指定省份的城市房价及区县数据"""
    province = request.args.get('province', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    result = ds.get_city_prices(province, min_price, max_price)
    return jsonify(json.loads(result))


@national_bp.route('/provinces', methods=['GET'])
def province_list():
    """获取所有省份列表"""
    result = ds.get_province_list()
    return jsonify(json.loads(result))


@national_bp.route('/ranking', methods=['GET'])
def city_ranking():
    """获取城市排行榜"""
    rank_type = request.args.get('type', 'price')
    limit = request.args.get('limit', 10, type=int)
    order = request.args.get('order', 'desc')
    result = ds.get_city_ranking(rank_type, limit, order)
    return jsonify(json.loads(result))


@national_bp.route('/search', methods=['GET'])
def search_city():
    """城市搜索"""
    keyword = request.args.get('keyword', '')
    result = ds.search_city(keyword)
    return jsonify(json.loads(result))


@national_bp.route('/trend', methods=['GET'])
def price_trend():
    """获取城市价格趋势"""
    city = request.args.get('city', '')
    year = request.args.get('year', type=int)
    result = ds.get_price_trend(city, year)
    return jsonify(json.loads(result))


@national_bp.route('/clustering', methods=['GET'])
def city_clustering():
    """方案C：城市分级气泡图数据"""
    result = ds.get_city_clustering()
    return jsonify(json.loads(result))


@national_bp.route('/heatmap', methods=['GET'])
def district_change_heatmap():
    """方案C：区县涨跌比热力图"""
    city = request.args.get('city', '')
    result = ds.get_district_change_heatmap(city)
    return jsonify(json.loads(result))


@national_bp.route('/listing-ranking', methods=['GET'])
def listing_top_ranking():
    """方案C：挂牌量TOP排行"""
    limit = request.args.get('limit', 20, type=int)
    result = ds.get_listing_top_ranking(limit)
    return jsonify(json.loads(result))


@national_bp.route('/district-ranking', methods=['GET'])
def district_price_ranking():
    """方案D：区县价格排行"""
    limit = request.args.get('limit', 50, type=int)
    city = request.args.get('city', '')
    result = ds.get_district_price_ranking(limit, city)
    return jsonify(json.loads(result))


@national_bp.route('/city-districts', methods=['GET'])
def city_districts_comparison():
    """方案D：同城区县对比"""
    city = request.args.get('city', '')
    result = ds.get_city_districts_comparison(city)
    return jsonify(json.loads(result))


@national_bp.route('/district-change-ranking', methods=['GET'])
def district_change_ranking():
    """方案D：区县涨跌榜"""
    limit = request.args.get('limit', 30, type=int)
    order = request.args.get('order', 'desc')
    result = ds.get_district_change_ranking(limit, order)
    return jsonify(json.loads(result))
