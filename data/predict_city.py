import pymysql
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
from config import DB_CONFIG, get_db_connection


# ==================== 历史数据查询接口 ====================

def get_historical_prices(
        province: str,
        city: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
) -> str:
    """
    获取历史房价数据（用于预测分析）
    :param province: 省份名称（必填）
    :param city: 城市名称（可选）
    :param district: 区县名称（可选）
    :param start_date: 开始日期 YYYY-MM-DD（可选）
    :param end_date: 结束日期 YYYY-MM-DD（可选）
    :return: JSON格式的历史数据
    """
    if not province or not province.strip():
        return json.dumps({
            "code": 400,
            "data": {},
            "message": "province参数为必填项"
        }, ensure_ascii=False)

    connection = get_db_connection()
    if not connection:
        return json.dumps({
            "code": 500,
            "data": {},
            "message": "数据库连接失败"
        }, ensure_ascii=False)

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建查询条件（使用参数化查询以避免注入）
        where_clauses: List[str] = []
        params: List = []

        where_clauses.append("province_name LIKE %s")
        params.append(f"%{province.strip()}%")

        if city and city.strip():
            where_clauses.append("city_name LIKE %s")
            params.append(f"%{city.strip()}%")

        if district and district.strip():
            where_clauses.append("district_name LIKE %s")
            params.append(f"%{district.strip()}%")

        if start_date:
            where_clauses.append("record_date >= %s")
            params.append(start_date)

        if end_date:
            where_clauses.append("record_date <= %s")
            params.append(end_date)

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # 查询历史数据（假设你有historical_prices表）
        query = f"""
        SELECT
            year,
            month,
            month_avg_price as avg_price
        FROM trend
        WHERE city_name LIKE '%{city.strip()}%'
        ORDER BY year ASC, month ASC
        """

        # 该查询从 trend 表返回 year/month/avg_price，直接执行（参数已内联到 query 中）
        cursor.execute(query)
        records = cursor.fetchall()

        # 格式化数据（根据 SELECT 字段：year/month/avg_price）
        formatted_records = []
        for record in records:
            year = record.get('year')
            month = record.get('month')
            # 构造便于展示的日期字符串，例如 "2024-07"
            try:
                month_int = int(month)
                date_str = f"{int(year)}-{month_int:02d}"
            except Exception:
                date_str = f"{year}-{month}"

            formatted_records.append({
                "year": year,
                "month": month,
                "date": date_str,
                "city": city or "",
                "avg_price": int(record['avg_price']) if record.get('avg_price') is not None else 0,
                "price": int(record['avg_price']) if record.get('avg_price') is not None else 0
            })

        response = {
            "code": 200,
            "data": {
                "records": formatted_records,
                "count": len(formatted_records)
            }
        }

        cursor.close()
        connection.close()
        return json.dumps(response, ensure_ascii=False)

    except Exception as e:
        print(f"历史数据查询失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"查询失败: {str(e)}"
        }, ensure_ascii=False)


# ==================== 房价预测核心类 ====================

class HousePriceForecast:
    """房价预测分析类"""

    def __init__(self, historical_data: List[Dict]):
        """
        :param historical_data: [{"date": "2024-01-01", "price": 15000}, ...]
        """
        self.df = pd.DataFrame(historical_data)
        if len(self.df) == 0:
            raise ValueError("历史数据不能为空")

        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date')
        self.df['time_index'] = range(len(self.df))

    def linear_regression(self, forecast_periods: int = 6) -> Dict:
        """线性回归预测"""
        X = self.df['time_index'].values
        y = self.df['price'].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

        future_indices = np.arange(len(X), len(X) + forecast_periods)
        predictions = slope * future_indices + intercept

        predict_error = np.sqrt(np.sum((y - (slope * X + intercept)) ** 2) / (len(X) - 2))
        margin = 1.96 * predict_error

        return {
            "method": "线性回归",
            "formula": f"y = {slope:.2f}x + {intercept:.2f}",
            "r_squared": float(r_value ** 2),
            "slope": float(slope),
            "intercept": float(intercept),
            "predictions": predictions.tolist(),
            "confidence_lower": (predictions - margin).tolist(),
            "confidence_upper": (predictions + margin).tolist(),
            "trend": "上升" if slope > 0 else "下降",
            "monthly_change": float(slope)
        }

    def polynomial_regression(self, degree: int = 2, forecast_periods: int = 6) -> Dict:
        """多项式回归"""
        X = self.df['time_index'].values
        y = self.df['price'].values

        coeffs = np.polyfit(X, y, degree)
        poly_func = np.poly1d(coeffs)

        y_pred = poly_func(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        future_indices = np.arange(len(X), len(X) + forecast_periods)
        predictions = poly_func(future_indices)

        # 获取多项式系数
        coeffs_str = " + ".join([f"{coeffs[i]:.4f}x^{degree - i}" for i in range(degree + 1)])

        return {
            "method": f"{degree}次多项式回归",
            "formula": coeffs_str,
            "r_squared": float(r_squared),
            "coefficients": coeffs.tolist(),
            "predictions": predictions.tolist()
        }

    def exponential_smoothing(self, alpha: float = 0.3, forecast_periods: int = 6) -> Dict:
        """指数平滑"""
        prices = self.df['price'].values

        smoothed = [prices[0]]
        for i in range(1, len(prices)):
            smoothed.append(alpha * prices[i] + (1 - alpha) * smoothed[-1])

        recent_trend = (prices[-1] - prices[-min(3, len(prices))]) / min(3, len(prices))
        last_smoothed = smoothed[-1]
        predictions = [last_smoothed + recent_trend * (i + 1) for i in range(forecast_periods)]

        return {
            "method": "指数平滑",
            "alpha": alpha,
            "formula": f"基于alpha={alpha}的指数平滑",
            "last_smoothed_value": float(last_smoothed),
            "recent_trend": float(recent_trend),
            "predictions": predictions,
            "trend_adjustment": float(recent_trend)
        }

    def moving_average(self, window: int = 3, forecast_periods: int = 6) -> Dict:
        """移动平均"""
        prices = self.df['price'].values

        if len(prices) < window:
            window = len(prices)

        last_values = prices[-window:]
        base_prediction = np.mean(last_values)
        trend = (prices[-1] - prices[-window]) / window
        predictions = [base_prediction + trend * (i + 1) for i in range(forecast_periods)]

        return {
            "method": f"{window}期移动平均",
            "window_size": window,
            "formula": f"最近{window}期移动平均，趋势调整:{trend:.4f}",
            "base_prediction": float(base_prediction),
            "predictions": predictions,
            "trend": float(trend)
        }

    def ensemble_forecast(self, forecast_periods: int = 6) -> Dict:
        """集成预测"""
        linear = self.linear_regression(forecast_periods)
        poly = self.polynomial_regression(2, forecast_periods)
        exp = self.exponential_smoothing(0.3, forecast_periods)
        ma = self.moving_average(3, forecast_periods)

        predictions = []
        for i in range(forecast_periods):
            weighted_pred = (
                    0.25 * linear["predictions"][i] +
                    0.25 * poly["predictions"][i] +
                    0.25 * exp["predictions"][i] +
                    0.25 * ma["predictions"][i]
            )
            predictions.append(weighted_pred)

        return {
            "method": "集成预测",
            "formula": "四种方法等权重集成",
            "weights": {"linear": 0.25, "polynomial": 0.25, "exponential": 0.25, "moving_average": 0.25},
            "predictions": predictions
        }

    def generate_forecast_dates(self, forecast_periods: int = 6) -> List[str]:
        """生成预测日期"""
        last_date = self.df['date'].max()
        dates = []
        for i in range(1, forecast_periods + 1):
            future_date = last_date + timedelta(days=30 * i)
            dates.append(future_date.strftime('%Y-%m'))
        return dates

    def parse_date_to_year_month(self, date_str: str) -> tuple:
        """解析日期字符串为年和月"""
        try:
            if '-' in date_str:
                parts = date_str.split('-')
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 1
                return year, month
            else:
                # 尝试解析其他格式
                dt = datetime.strptime(date_str, '%Y%m') if len(date_str) == 6 else datetime.strptime(date_str,
                                                                                                      '%Y-%m-%d')
                return dt.year, dt.month
        except:
            # 如果解析失败，返回None
            return None, None

    def comprehensive_analysis(self, forecast_periods: int = 6) -> Dict:
        """综合分析"""
        try:
            methods_results = {
                "linear": self.linear_regression(forecast_periods),
                "polynomial": self.polynomial_regression(2, forecast_periods),
                "exponential": self.exponential_smoothing(0.3, forecast_periods),
                "moving_average": self.moving_average(3, forecast_periods),
                "ensemble": self.ensemble_forecast(forecast_periods)
            }

            forecast_dates = self.generate_forecast_dates(forecast_periods)
            current_price = float(self.df['price'].iloc[-1])
            historical_avg = float(self.df['price'].mean())

            # 提取每种方法的详细信息（排除predictions）
            methods_details = {}
            for method_name, method_res in methods_results.items():
                if method_name != 'ensemble':  # 不包含集成方法
                    details = {k: v for k, v in method_res.items() if k != 'predictions'}
                    methods_details[method_name] = details

            ensemble_pred = methods_results["ensemble"]["predictions"]
            avg_change = (ensemble_pred[-1] - current_price) / current_price * 100

            return {
                "current_price": current_price,
                "historical_avg": historical_avg,
                "forecast_dates": forecast_dates,
                "forecast_results": methods_results,
                "methods_details": methods_details,  # 新增：四种方法的详细信息
                "summary": {
                    "trend": "上涨" if avg_change > 2 else "下跌" if avg_change < -2 else "持平",
                    "change_percent": round(avg_change, 2),
                    "confidence": "中等",
                    "linear_r_squared": round(methods_results["linear"].get("r_squared", 0), 4),
                    "polynomial_r_squared": round(methods_results["polynomial"].get("r_squared", 0), 4),
                    "linear_slope": round(methods_results["linear"].get("slope", 0), 2),
                    "exponential_alpha": round(methods_results["exponential"].get("alpha", 0), 2),
                    "ma_window": methods_results["moving_average"].get("window_size", 0)
                }
            }
        except Exception as e:
            raise Exception(f"分析失败: {str(e)}")


# ==================== 预测接口 ====================

def predict_city_prices(
        province: str,
        city: Optional[str] = None,
        district: Optional[str] = None,
        forecast_periods: int = 6
) -> str:
    """
    房价预测接口
    :param province: 省份（必填）
    :param city: 城市（可选）
    :param district: 区县（可选）
    :param forecast_periods: 预测期数（默认6个月）
    """
    try:
        # 1. 获取历史数据
        historical_json = get_historical_prices(
            province=province,
            city=city,
            district=district
        )
        historical_response = json.loads(historical_json)

        if historical_response['code'] != 200:
            return historical_json

        records = historical_response['data']['records']

        if len(records) < 3:
            return json.dumps({
                "code": 400,
                "data": {},
                "message": "历史数据不足，至少需要3条记录才能进行预测"
            }, ensure_ascii=False)

        # 2. 准备预测数据
        forecast_data = [
            {"date": r['date'], "price": r['price']}
            for r in records
        ]

        # 3. 执行预测
        forecaster = HousePriceForecast(forecast_data)
        analysis = forecaster.comprehensive_analysis(forecast_periods)

        # 4. 返回结果
        response = {
            "code": 200,
            "data": {
                "location": {
                    "province": province,
                    "city": city,
                    "district": district
                },
                "historical_data_count": len(records),
                "analysis": analysis
            },
            "message": "预测成功"
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"预测失败: {e}")
        return json.dumps({
            "code": 500,
            "data": {},
            "message": f"预测失败: {str(e)}"
        }, ensure_ascii=False)


# ==================== 简化版批量预测与导出函数 ====================

def simplified_batch_predict_and_export(cities: List[str], province_override: Optional[str] = None,
                                        forecast_periods: int = 36, out_dir: str = 'outputs') -> dict:
    """
    对多个城市执行预测，仅保留指定的列在predictions_all.csv中

    :param cities: 城市名称列表（中文）
    :param province_override: 若需要，可指定统一的 province 字段
    :param forecast_periods: 预测期数（月），默认36
    :param out_dir: 导出目录
    :return: 包含写入文件路径与处理状态的字典
    """
    os.makedirs(out_dir, exist_ok=True)

    all_hist_rows = []
    all_pred_rows = []  # 只保留指定字段
    summaries = []

    for city_name in cities:
        try:
            print(f"Processing city: {city_name}")
            province = province_override or city_name

            # 获取源历史数据
            hist_json = get_historical_prices(province=province, city=city_name)
            hist_resp = json.loads(hist_json)
            if hist_resp.get('code') != 200:
                print(f"Warning: failed to fetch historical for {city_name}: {hist_resp}")
                continue

            records = hist_resp['data'].get('records', [])
            for r in records:
                all_hist_rows.append({
                    'city': city_name,
                    'year': r.get('year'),
                    'month': r.get('month'),
                    'date': r.get('date'),
                    'price': r.get('price') if 'price' in r else r.get('avg_price')
                })

            # 执行预测
            pred_json = predict_city_prices(province=province, city=city_name, forecast_periods=forecast_periods)
            pred_resp = json.loads(pred_json)
            if pred_resp.get('code') != 200:
                print(f"Warning: prediction failed for {city_name}: {pred_resp}")
                continue

            analysis = pred_resp['data'].get('analysis', {})
            forecast_dates = analysis.get('forecast_dates', [])

            # 获取预测器实例以解析日期
            forecaster = HousePriceForecast([{"date": r['date'], "price": r['price']} for r in records])

            # 记录所有方法的预测结果 - 仅保留指定字段
            methods_results = analysis.get('forecast_results', {})
            for method_name, method_res in methods_results.items():
                preds = method_res.get('predictions', []) or []
                for idx, date_str in enumerate(forecast_dates):
                    pred_val = preds[idx] if idx < len(preds) else None

                    # 解析日期为年和月
                    year, month = forecaster.parse_date_to_year_month(date_str)

                    # 只添加指定的字段
                    all_pred_rows.append({
                        'city': city_name,
                        'year': year,
                        'month': month,
                        'date': date_str,
                        'method': method_name,
                        'predicted_price': int(round(pred_val)) if pred_val is not None else None,
                        'method_formula': method_res.get('formula', '')
                    })

            # 收集summary信息
            current_price = analysis.get('current_price')
            summary_obj = analysis.get('summary', {}) or {}
            methods_details = analysis.get('methods_details', {})

            # 提取四种分析法的关键信息
            linear_detail = methods_details.get('linear', {})
            polynomial_detail = methods_details.get('polynomial', {})
            exponential_detail = methods_details.get('exponential', {})
            moving_average_detail = methods_details.get('moving_average', {})

            summary_entry = {
                'city': city_name,
                'current_price': int(round(current_price)) if current_price else None,
                'historical_count': len(records),
                'forecast_periods': forecast_periods,
                'trend': summary_obj.get('trend'),
                'change_percent': summary_obj.get('change_percent'),
                'confidence': summary_obj.get('confidence'),

                # 线性回归详情
                'linear_formula': linear_detail.get('formula', ''),
                'linear_r_squared': linear_detail.get('r_squared'),
                'linear_slope': linear_detail.get('slope'),
                'linear_trend': linear_detail.get('trend', ''),

                # 多项式回归详情
                'polynomial_formula': polynomial_detail.get('formula', ''),
                'polynomial_r_squared': polynomial_detail.get('r_squared'),
                'polynomial_degree': 2,

                # 指数平滑详情
                'exponential_alpha': exponential_detail.get('alpha'),
                'exponential_formula': exponential_detail.get('formula', ''),
                'exponential_last_smoothed': exponential_detail.get('last_smoothed_value'),
                'exponential_trend': exponential_detail.get('recent_trend'),

                # 移动平均详情
                'ma_window_size': moving_average_detail.get('window_size'),
                'ma_formula': moving_average_detail.get('formula', ''),
                'ma_base_prediction': moving_average_detail.get('base_prediction'),
                'ma_trend': moving_average_detail.get('trend'),
            }

            summaries.append(summary_entry)

        except Exception as e:
            print(f"Error processing {city_name}: {e}")
            continue

    # 导出 CSV 文件
    # 1. 历史数据
    hist_df = pd.DataFrame(all_hist_rows)
    hist_path = os.path.join(out_dir, 'historical_all.csv')
    if not hist_df.empty:
        hist_df.to_csv(hist_path, index=False, encoding='utf-8-sig')
        print(f"Wrote historical data -> {hist_path}")
    else:
        hist_path = None
        print("Warning: No historical data to export")

    # 2. 预测数据 - 仅保留指定字段
    pred_df = pd.DataFrame(all_pred_rows)
    pred_path = os.path.join(out_dir, 'predictions_all.csv')
    if not pred_df.empty:
        # 确保year和month列为整数类型
        pred_df['year'] = pd.to_numeric(pred_df['year'], errors='coerce').astype('Int64')
        pred_df['month'] = pd.to_numeric(pred_df['month'], errors='coerce').astype('Int64')

        # 只保留指定的字段并按顺序排列
        keep_columns = ['city', 'year', 'month', 'date', 'method', 'predicted_price', 'method_formula']

        # 检查所有需要的列是否存在
        existing_columns = [col for col in keep_columns if col in pred_df.columns]
        pred_df = pred_df[existing_columns]

        pred_df.to_csv(pred_path, index=False, encoding='utf-8-sig')
        print(f"Wrote predictions (simplified columns) -> {pred_path}")

        # 显示数据示例
        print("\nPredictions data sample (first 5 rows):")
        print(pred_df.head())
    else:
        pred_path = None
        print("Warning: No prediction data to export")

    # 3. 汇总数据
    summary_df = pd.DataFrame(summaries)
    summary_path = os.path.join(out_dir, 'summary_all.csv')
    if not summary_df.empty:
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
        print(f"Wrote summary -> {summary_path}")

        # 显示数据示例
        print("\nSummary data sample (first 3 rows):")
        print(summary_df[['city', 'current_price', 'trend', 'change_percent']].head(3))
    else:
        summary_path = None
        print("Warning: No summary data to export")

    return {
        'historical_csv': hist_path,
        'predictions_csv': pred_path,
        'summary_csv': summary_path,
        'cities_processed': len(summaries)
    }


# ==================== 版本对比函数 ====================

def compare_predictions_format():
    """对比新旧版本的predictions_all.csv格式"""
    # 旧版本可能存在的字段
    old_columns = [
        'city', 'year', 'month', 'date', 'predicted_price', 'method',
        'method_formula', 'r_squared', 'slope', 'trend', 'alpha', 'window_size'
    ]

    # 新版本只保留的字段
    new_columns = [
        'city', 'year', 'month', 'date', 'method', 'predicted_price', 'method_formula'
    ]

    print("新旧版本predictions_all.csv字段对比:")
    print("=" * 60)
    print("旧版本字段 ({})个:".format(len(old_columns)))
    for col in old_columns:
        print(f"  - {col}")

    print("\n新版本字段 ({})个:".format(len(new_columns)))
    for col in new_columns:
        print(f"  - {col}")

    print("\n移除了以下字段:")
    removed = [col for col in old_columns if col not in new_columns]
    for col in removed:
        print(f"  - {col}")


# ==================== 主执行函数 ====================

if __name__ == "__main__":
    # 显示格式对比
    compare_predictions_format()

    print("\n" + "=" * 60)
    print("开始批量预测...")
    print("=" * 60)

    # 用户提供的城市列表
    cities_to_run = [
        '昆明', '福州', '济南', '贵阳', '南昌', '杭州', '合肥', '乌鲁木齐', '广州', '郑州',
        '武汉', '南宁', '成都', '兰州', '西宁', '石家庄', '哈尔滨', '长春', '银川', '上海',
        '天津', '重庆', '呼和浩特', '西安', '长沙', '沈阳', '太原', '南京', '海口', '北京', '深圳'
    ]

    # 运行批量预测并导出（36个月）
    summary = simplified_batch_predict_and_export(
        cities=cities_to_run,
        forecast_periods=36,
        out_dir='outputs_simplified'
    )

    print("\n" + "=" * 60)
    print("批量导出完成:")
    print("=" * 60)
    print(f"处理城市数量: {summary['cities_processed']}")
    print(f"历史数据文件: {summary['historical_csv']}")
    print(f"预测数据文件: {summary['predictions_csv']}")
    print(f"汇总信息文件: {summary['summary_csv']}")

    # 显示预测文件的具体信息
    if summary['predictions_csv'] and os.path.exists(summary['predictions_csv']):
        pred_df = pd.read_csv(summary['predictions_csv'])
        print(f"\n预测数据文件详细信息:")
        print(f"总行数: {len(pred_df)}")
        print(f"城市数量: {pred_df['city'].nunique()}")
        print(f"预测方法数量: {pred_df['method'].nunique()}")
        print(f"列名: {list(pred_df.columns)}")

        # 显示每个城市的预测数据行数
        city_counts = pred_df['city'].value_counts().head(5)
        print(f"\n前5个城市的预测数据行数:")
        for city, count in city_counts.items():
            print(f"  {city}: {count}行")

    print("\n程序执行完成！")