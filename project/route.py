from flask import Flask, request, jsonify
import data_process as dp
import json

app = Flask(__name__,static_folder='../project_web',static_url_path='/project_web')

# ------------------------------
# 认证模块路由
# ------------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    result = dp.user_login(username, password)
    return jsonify(json.loads(result))


# ------------------------------
# 全国数据模块路由
# ------------------------------
@app.route('/api/national/overview', methods=['GET'])
def national_overview():
    """获取全国房价概览"""
    result = dp.get_national_overview()
    return jsonify(json.loads(result))


@app.route('/api/national/city-prices', methods=['GET'])
def city_prices():
    """获取指定省份的城市房价及区县数据"""
    province = request.args.get('province', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    result = dp.get_city_prices(province, min_price, max_price)
    return jsonify(json.loads(result))


@app.route('/api/national/provinces', methods=['GET'])
def province_list():
    """获取所有省份列表"""
    result = dp.get_province_list()
    return jsonify(json.loads(result))


@app.route('/api/national/ranking', methods=['GET'])
def city_ranking():
    """获取城市排行榜"""
    rank_type = request.args.get('rank_type', 'price')
    limit = request.args.get('limit', 10, type=int)
    order = request.args.get('order', 'desc')
    result = dp.get_city_ranking(rank_type, limit, order)
    return jsonify(json.loads(result))


@app.route('/api/national/search', methods=['GET'])
def search_city():
    """城市搜索"""
    keyword = request.args.get('keyword', '')
    result = dp.search_city(keyword)
    return jsonify(json.loads(result))


@app.route('/api/national/trend', methods=['GET'])
def price_trend():
    """获取城市价格趋势"""
    city = request.args.get('city', '')
    year = request.args.get('year', type=int)
    result = dp.get_price_trend(city, year)
    return jsonify(json.loads(result))


# ------------------------------
# 北京数据模块路由
# ------------------------------
@app.route('/api/beijing/overview', methods=['GET'])
def beijing_overview():
    """获取北京房产概览信息"""
    result = dp.get_beijing_overview()
    return jsonify(json.loads(result))


@app.route('/api/beijing/district-ranking', methods=['GET'])
def district_ranking():
    """获取北京行政区单价排名"""
    result = dp.get_district_ranking()
    return jsonify(json.loads(result))


@app.route('/api/beijing/district-prices', methods=['GET'])
def district_prices():
    """获取北京所有行政区的平均单价及记录数"""
    result = dp.get_district_prices()
    return jsonify(json.loads(result))


@app.route('/api/beijing/analysis/floor', methods=['GET'])
def analysis_floor():
    """北京房产楼层特征分析"""
    result = dp.analysis_floor()
    return jsonify(json.loads(result))


@app.route('/api/beijing/analysis/layout', methods=['GET'])
def analysis_layout():
    """北京房产户型特征分析"""
    result = dp.analysis_layout()
    return jsonify(json.loads(result))


@app.route('/api/beijing/analysis/orientation', methods=['GET'])
def analysis_orientation():
    """北京房产朝向特征分析"""
    result = dp.analysis_orientation()
    return jsonify(json.loads(result))


@app.route('/api/beijing/analysis/elevator', methods=['GET'])
def analysis_elevator():
    """北京房产电梯特征分析"""
    result = dp.analysis_elevator()
    return jsonify(json.loads(result))


@app.route('/api/beijing/chart/scatter', methods=['GET'])
def get_scatter_data():
    """获取北京房产面积-价格散点图数据"""
    district = request.args.get('district')
    limit = request.args.get('limit', 1000, type=int)
    result = dp.get_scatter_data(district, limit)
    return jsonify(json.loads(result))


@app.route('/api/beijing/chart/boxplot', methods=['GET'])
def get_boxplot_data():
    """获取北京指定区域的单价箱线图数据"""
    district = request.args.get('district', '')
    result = dp.get_boxplot_data(district)
    return jsonify(json.loads(result))


if __name__ == '__main__':
    # 开发环境使用，生产环境请使用WSGI服务器
    app.run(debug=True, host='127.0.0.1', port=5000)