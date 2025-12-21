"""
全国数据相关路由
"""
from flask import Blueprint, request, jsonify
import data_process as dp
import json

national_bp = Blueprint('national', __name__, url_prefix='/api/national')


@national_bp.route('/overview', methods=['GET'])
def national_overview():
    """获取全国房价概览"""
    result = dp.get_national_overview()
    return jsonify(json.loads(result))


@national_bp.route('/city-prices', methods=['GET'])
def city_prices():
    """获取指定省份的城市房价及区县数据"""
    province = request.args.get('province', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    result = dp.get_city_prices(province, min_price, max_price)
    return jsonify(json.loads(result))


@national_bp.route('/provinces', methods=['GET'])
def province_list():
    """获取所有省份列表"""
    result = dp.get_province_list()
    return jsonify(json.loads(result))


@national_bp.route('/ranking', methods=['GET'])
def city_ranking():
    """获取城市排行榜"""
    rank_type = request.args.get('rank_type', 'price')
    limit = request.args.get('limit', 10, type=int)
    order = request.args.get('order', 'desc')
    result = dp.get_city_ranking(rank_type, limit, order)
    return jsonify(json.loads(result))


@national_bp.route('/search', methods=['GET'])
def search_city():
    """城市搜索"""
    keyword = request.args.get('keyword', '')
    result = dp.search_city(keyword)
    return jsonify(json.loads(result))


@national_bp.route('/trend', methods=['GET'])
def price_trend():
    """获取城市价格趋势"""
    city = request.args.get('city', '')
    year = request.args.get('year', type=int)
    result = dp.get_price_trend(city, year)
    return jsonify(json.loads(result))
