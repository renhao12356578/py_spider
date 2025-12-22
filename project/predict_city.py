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
        
        predict_error = np.sqrt(np.sum((y - (slope * X + intercept))**2) / (len(X) - 2))
        margin = 1.96 * predict_error
        
        return {
            "method": "线性回归",
            "formula": f"y = {slope:.2f}x + {intercept:.2f}",
            "r_squared": float(r_value**2),
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
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        future_indices = np.arange(len(X), len(X) + forecast_periods)
        predictions = poly_func(future_indices)
        
        return {
            "method": f"{degree}次多项式回归",
            "r_squared": float(r_squared),
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
            
            ensemble_pred = methods_results["ensemble"]["predictions"]
            avg_change = (ensemble_pred[-1] - current_price) / current_price * 100
            
            return {
                "current_price": current_price,
                "historical_avg": historical_avg,
                "forecast_dates": forecast_dates,
                "forecast_results": methods_results,
                "summary": {
                    "trend": "上涨" if avg_change > 2 else "下跌" if avg_change < -2 else "持平",
                    "change_percent": round(avg_change, 2),
                    "confidence": "中等"
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


# ==================== 使用示例 ====================

def example_usage():
    """示例：如何使用预测功能"""
    
    # 示例1: 预测某个城市的房价
    result = predict_city_prices(
        province="北京",
        city="北京",
        forecast_periods=36
    )
    print("城市预测结果:")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # 示例2: 预测某个区县的房价
    result2 = predict_city_prices(
        province="北京",
        city="北京",
        district="朝阳",
        forecast_periods=12
    )
    print("区县预测结果:")
    print(result2)


if __name__ == "__main__":
    example_usage()