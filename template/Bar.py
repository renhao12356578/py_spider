import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Union, Optional, Any
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')
import pymysql
pymysql.install_as_MySQLdb()

class TiDBChartBuilder:
    """
    TiDB数据库条形图构建器类 - 支持从TiDB Cloud动态读取数据
    """
    
    def __init__(self, db_config: Dict = None, data: pd.DataFrame = None):
        """
        初始化条形图构建器
        
        参数:
        - db_config: TiDB数据库配置字典
        - data: 可选，直接传入DataFrame数据
        """
        self._data = data
        self._db_engine = None
        self._db_config = db_config
        self._init_styles()
        
        # 如果提供了数据库配置，创建引擎
        if db_config:
            self.connect_to_tidb(db_config)
    
    def connect_to_tidb(self, db_config: Dict):
        """
        连接到TiDB数据库
        
        参数:
        - db_config: 数据库配置字典，包含以下字段：
            host: 主机地址
            port: 端口号
            user: 用户名
            password: 密码
            database: 数据库名
            ssl_ca: SSL证书路径
            ssl_verify_cert: 是否验证证书
            ssl_verify_identity: 是否验证身份
        """
        try:
            # 构建连接字符串
            connection_string = (
                f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
                f"?ssl_ca={db_config.get('ssl_ca', '')}"
                f"&ssl_verify_cert={db_config.get('ssl_verify_cert', True)}"
                f"&ssl_verify_identity={db_config.get('ssl_verify_identity', True)}"
            )
            
            self._db_engine = create_engine(connection_string)
            self._db_config = db_config
            print(f"成功连接到TiDB数据库: {db_config['host']}")
            
            # 测试连接
            with self._db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                print(f"数据库连接测试成功: {result.fetchone()}")
            
        except Exception as e:
            print(f"TiDB数据库连接失败: {e}")
            self._db_engine = None
    # 在 TiDBChartBuilder 类中添加以下方法：

    def load_current_price_data(self, table_name: str = "current_price") -> pd.DataFrame:
        """
        加载当前价格数据（current_price表）
    
        参数:
        - table_name: 表名，默认为"current_price"
    
        返回:
        - DataFrame对象
        """
        try:
            df = self.load_data_from_table(
                table_name=table_name,
                columns=['province_name', 'city_name', 'city_avg_price', 'city_avg_total_price', 
                        'price_rent_ratio', 'listing_count', 'district_name', 'district_avg_price', 'district_ratio']
            )
            print(f"成功加载当前价格数据，表名: {table_name}")
            return df
        except Exception as e:
            print(f"加载当前价格数据失败: {e}")
            # 尝试获取所有列
            try:
                df = self.load_data_from_table(table_name=table_name)
                print(f"使用所有列加载数据成功")
                return df
            except Exception as e2:
                print(f"加载数据失败: {e2}")
                raise

    def get_city_districts(self, city: str) -> List[str]:
        """
        获取指定城市的所有区域

        参数:
        - city: 城市名称

        返回:
        - 区域名称列表
        """
        if self._data is None:
            return []

        # 检查是否有district_name列
        if 'district_name' not in self._data.columns:
            print("数据中没有区域信息")
            return []

        # 筛选指定城市的区域
        city_districts = self._data[self._data['city_name'] == city]['district_name'].dropna().unique().tolist()
        return sorted(city_districts)

    def create_city_district_comparison(self,
                                      city: str,
                                      top_n: int = None,
                                      order_by: str = 'district_avg_price',
                                      ascending: bool = False,
                                      title: str = None,
                                      decimal_places: int = 1,
                                      **kwargs) -> go.Figure:
        """
        创建城市内不同区域价格对比图

        参数:
        - city: 城市名称
        - top_n: 显示前N个区域（None表示显示所有）
        - order_by: 排序字段 ('district_avg_price', 'district_ratio', 'listing_count')
        - ascending: 是否升序排列
        - title: 图表标题
        - decimal_places: 小数位数
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")

        # 检查必要的列是否存在
        required_cols = ['city_name', 'district_name', 'district_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")

        # 筛选指定城市的数据
        city_data = self._data[self._data['city_name'] == city].copy()

        if city_data.empty:
            print(f"错误：未找到城市 '{city}' 的数据")
            available_cities = self.get_available_cities()
            print(f"可用城市: {available_cities}")
            return self._create_empty_figure(f"未找到城市 '{city}' 的数据")

        # 检查是否有区域数据
        if city_data['district_name'].isna().all() or city_data['district_name'].nunique() == 0:
            print(f"警告：城市 '{city}' 没有区域数据")
            return self._create_empty_figure(f"城市 '{city}' 没有区域数据")

        # 处理数据
        try:
            # 按区域分组，计算平均价格
            district_data = city_data.groupby('district_name').agg({
                'district_avg_price': 'mean',
                'district_ratio': 'mean' if 'district_ratio' in city_data.columns else None,
                'listing_count': 'sum' if 'listing_count' in city_data.columns else None
            }).reset_index()

            # 重命名列名
            district_data = district_data.rename(columns={
                'district_avg_price': 'price',
                'district_ratio': 'ratio',
                'listing_count': 'count'
            })

            # 排序
            if order_by == 'district_avg_price':
                sort_col = 'price'
            elif order_by == 'district_ratio':
                sort_col = 'ratio' if 'ratio' in district_data.columns else 'price'
            elif order_by == 'listing_count':
                sort_col = 'count' if 'count' in district_data.columns else 'price'
            else:
                sort_col = 'price'

            if sort_col in district_data.columns:
                district_data = district_data.sort_values(sort_col, ascending=ascending)
            else:
                district_data = district_data.sort_values('price', ascending=ascending)

            # 限制显示数量
            if top_n is not None and top_n > 0:
                district_data = district_data.head(top_n)

            # 处理价格，保留指定位数小数
            district_data['price'] = district_data['price'].round(decimal_places)

            if 'ratio' in district_data.columns:
                district_data['ratio'] = district_data['ratio'].round(2)

            if 'count' in district_data.columns:
                district_data['count'] = district_data['count'].astype(int)

        except Exception as e:
            print(f"错误：处理区域数据时出错 - {e}")
            return self._create_empty_figure("数据处理错误")

        if district_data.empty:
            print("警告：区域数据为空")
            return self._create_empty_figure("区域数据为空")

        print(f"创建城市区域对比图，城市: {city}")
        print(f"区域数量: {len(district_data)}")
        print(f"价格范围: {district_data['price'].min():.2f} - {district_data['price'].max():.2f}")

        # 自动生成标题
        if title is None:
            order_desc = "最低" if ascending else "最高"
            if top_n is not None:
                title = f"{city}市房价{order_desc}的{top_n}个区域对比"
            else:
                title = f"{city}市各区域房价对比"

        # 从kwargs中提取特定的参数，避免重复传递
        bar_opacity = kwargs.pop('bar_opacity', 0.7)
        color_palette = kwargs.pop('color_palette', 'transparent')

        # 创建条形图
        fig = self.create_thin_bar_chart(
            data=district_data,
            x_col='district_name',
            y_col='price',
            title=title,
            bar_width=0.5,
            bar_opacity=bar_opacity,
            color_palette=color_palette,
            decimal_places=decimal_places,
            **kwargs  # 传递剩余的参数
        )

        return fig

    def create_city_district_horizontal(self,
                                      city: str,
                                      top_n: int = 10,
                                      order_by: str = 'district_avg_price',
                                      ascending: bool = True,
                                      title: str = None,
                                      decimal_places: int = 1,
                                      **kwargs) -> go.Figure:
        """
        创建城市内不同区域价格水平条形图（排名图）

        参数:
        - city: 城市名称
        - top_n: 显示前N个区域
        - order_by: 排序字段 ('district_avg_price', 'district_ratio', 'listing_count')
        - ascending: 是否升序排列
        - title: 图表标题
        - decimal_places: 小数位数
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")

        # 检查必要的列是否存在
        required_cols = ['city_name', 'district_name', 'district_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")

        # 筛选指定城市的数据
        city_data = self._data[self._data['city_name'] == city].copy()

        if city_data.empty:
            print(f"错误：未找到城市 '{city}' 的数据")
            return self._create_empty_figure(f"未找到城市 '{city}' 的数据")

        # 处理数据
        try:
            # 按区域分组，计算平均价格
            district_data = city_data.groupby('district_name').agg({
                'district_avg_price': 'mean',
                'district_ratio': 'mean' if 'district_ratio' in city_data.columns else None,
                'listing_count': 'sum' if 'listing_count' in city_data.columns else None
            }).reset_index()

            # 重命名列名
            district_data = district_data.rename(columns={
                'district_avg_price': 'price',
                'district_ratio': 'ratio',
                'listing_count': 'count'
            })

            # 排序
            if order_by == 'district_avg_price':
                sort_col = 'price'
            elif order_by == 'district_ratio':
                sort_col = 'ratio' if 'ratio' in district_data.columns else 'price'
            elif order_by == 'listing_count':
                sort_col = 'count' if 'count' in district_data.columns else 'price'
            else:
                sort_col = 'price'

            if sort_col in district_data.columns:
                district_data = district_data.sort_values(sort_col, ascending=ascending)
            else:
                district_data = district_data.sort_values('price', ascending=ascending)

            # 限制显示数量
            district_data = district_data.head(top_n)

            # 如果是升序（价格最低），反转顺序使最低的在顶部
            if ascending:
                district_data = district_data.sort_values('price', ascending=True)
            else:
                district_data = district_data.sort_values('price', ascending=False)

            # 处理价格，保留指定位数小数
            district_data['price'] = district_data['price'].round(decimal_places)

        except Exception as e:
            print(f"错误：处理区域数据时出错 - {e}")
            return self._create_empty_figure("数据处理错误")

        if district_data.empty:
            print("警告：区域数据为空")
            return self._create_empty_figure("区域数据为空")

        print(f"创建城市区域水平条形图，城市: {city}")
        print(f"区域数量: {len(district_data)}")

        # 自动生成标题
        order_desc = "最低" if ascending else "最高"
        if title is None:
            title = f"{city}市房价{order_desc}的{top_n}个区域"

        # 从kwargs中提取特定的参数，避免重复传递
        bar_opacity = kwargs.pop('bar_opacity', 0.6)

        # 创建水平条形图
        fig = self.create_thin_bar_chart(
            data=district_data,
            x_col='district_name',
            y_col='price',
            title=title,
            orientation='h',
            bar_width=0.4,
            bar_opacity=bar_opacity,
            decimal_places=decimal_places,
            **kwargs  # 传递剩余的参数
        )

        return fig
    
    def create_province_city_comparison(self,
                                       province: str,
                                       top_n: int = None,
                                       order_by: str = 'city_avg_price',
                                       ascending: bool = False,
                                       title: str = None,
                                       decimal_places: int = 1,
                                      **kwargs) -> go.Figure:
        """
        创建省内各城市房价对比图

        参数:
        - province: 省份名称
        - top_n: 显示前N个城市（None表示显示所有）
        - order_by: 排序字段 ('city_avg_price', 'city_avg_total_price', 'price_rent_ratio', 'listing_count')
        - ascending: 是否升序排列
        - title: 图表标题
        - decimal_places: 小数位数
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")

        # 检查必要的列是否存在
        required_cols = ['province_name', 'city_name', 'city_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")

        # 筛选指定省份的数据
        province_data = self._data[self._data['province_name'] == province].copy()

        if province_data.empty:
            print(f"错误：未找到省份 '{province}' 的数据")
            available_provinces = sorted(self._data['province_name'].dropna().unique().tolist())
            print(f"可用省份: {available_provinces}")
            return self._create_empty_figure(f"未找到省份 '{province}' 的数据")

        # 处理数据
        try:
            # 按城市分组，计算平均价格
            city_data = province_data.groupby('city_name').agg({
                'city_avg_price': 'mean',
                'city_avg_total_price': 'mean' if 'city_avg_total_price' in province_data.columns else None,
                'price_rent_ratio': 'mean' if 'price_rent_ratio' in province_data.columns else None,
                'listing_count': 'sum' if 'listing_count' in province_data.columns else None
            }).reset_index()

            # 重命名列名
            city_data = city_data.rename(columns={
                'city_avg_price': 'price',
                'city_avg_total_price': 'total_price',
                'price_rent_ratio': 'rent_ratio',
                'listing_count': 'count'
            })

            # 排序
            if order_by == 'city_avg_price':
                sort_col = 'price'
            elif order_by == 'city_avg_total_price':
                sort_col = 'total_price' if 'total_price' in city_data.columns else 'price'
            elif order_by == 'price_rent_ratio':
                sort_col = 'rent_ratio' if 'rent_ratio' in city_data.columns else 'price'
            elif order_by == 'listing_count':
                sort_col = 'count' if 'count' in city_data.columns else 'price'
            else:
                sort_col = 'price'

            if sort_col in city_data.columns:
                city_data = city_data.sort_values(sort_col, ascending=ascending)
            else:
                city_data = city_data.sort_values('price', ascending=ascending)

            # 限制显示数量
            if top_n is not None and top_n > 0:
                city_data = city_data.head(top_n)

            # 处理价格，保留指定位数小数
            city_data['price'] = city_data['price'].round(decimal_places)

            if 'total_price' in city_data.columns:
                city_data['total_price'] = city_data['total_price'].round(decimal_places)

            if 'rent_ratio' in city_data.columns:
                city_data['rent_ratio'] = city_data['rent_ratio'].round(2)

            if 'count' in city_data.columns:
                city_data['count'] = city_data['count'].astype(int)

        except Exception as e:
            print(f"错误：处理城市数据时出错 - {e}")
            return self._create_empty_figure("数据处理错误")

        if city_data.empty:
            print("警告：城市数据为空")
            return self._create_empty_figure("城市数据为空")

        print(f"创建省份城市对比图，省份: {province}")
        print(f"城市数量: {len(city_data)}")
        print(f"价格范围: {city_data['price'].min():.2f} - {city_data['price'].max():.2f}")

        # 自动生成标题
        if title is None:
            order_desc = "最低" if ascending else "最高"
            if top_n is not None:
                title = f"{province}房价{order_desc}的{top_n}个城市对比"
            else:
                title = f"{province}各城市房价对比"

        # 从kwargs中提取特定的参数，避免重复传递
        bar_opacity = kwargs.pop('bar_opacity', 0.7)
        color_palette = kwargs.pop('color_palette', 'transparent')

        # 创建条形图
        fig = self.create_thin_bar_chart(
            data=city_data,
            x_col='city_name',
            y_col='price',
            title=title,
            bar_width=0.5,
            bar_opacity=bar_opacity,
            color_palette=color_palette,
            decimal_places=decimal_places,
            **kwargs  # 传递剩余的参数
        )

        return fig

    def create_province_city_horizontal(self,
                                       province: str,
                                       top_n: int = 10,
                                       order_by: str = 'city_avg_price',
                                       ascending: bool = True,
                                       title: str = None,
                                       decimal_places: int = 1,
                                       **kwargs) -> go.Figure:
        """
        创建省内各城市房价水平条形图（排名图）

        参数:
        - province: 省份名称
        - top_n: 显示前N个城市
        - order_by: 排序字段 ('city_avg_price', 'city_avg_total_price', 'price_rent_ratio', 'listing_count')
        - ascending: 是否升序排列
        - title: 图表标题
        - decimal_places: 小数位数
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")

        # 检查必要的列是否存在
        required_cols = ['province_name', 'city_name', 'city_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")

        # 筛选指定省份的数据
        province_data = self._data[self._data['province_name'] == province].copy()

        if province_data.empty:
            print(f"错误：未找到省份 '{province}' 的数据")
            return self._create_empty_figure(f"未找到省份 '{province}' 的数据")

        # 处理数据
        try:
            # 按城市分组，计算平均价格
            city_data = province_data.groupby('city_name').agg({
                'city_avg_price': 'mean',
                'city_avg_total_price': 'mean' if 'city_avg_total_price' in province_data.columns else None,
                'price_rent_ratio': 'mean' if 'price_rent_ratio' in province_data.columns else None,
                'listing_count': 'sum' if 'listing_count' in province_data.columns else None
            }).reset_index()

            # 重命名列名
            city_data = city_data.rename(columns={
                'city_avg_price': 'price',
                'city_avg_total_price': 'total_price',
                'price_rent_ratio': 'rent_ratio',
                'listing_count': 'count'
            })

            # 排序
            if order_by == 'city_avg_price':
                sort_col = 'price'
            elif order_by == 'city_avg_total_price':
                sort_col = 'total_price' if 'total_price' in city_data.columns else 'price'
            elif order_by == 'price_rent_ratio':
                sort_col = 'rent_ratio' if 'rent_ratio' in city_data.columns else 'price'
            elif order_by == 'listing_count':
                sort_col = 'count' if 'count' in city_data.columns else 'price'
            else:
                sort_col = 'price'

            if sort_col in city_data.columns:
                city_data = city_data.sort_values(sort_col, ascending=ascending)
            else:
                city_data = city_data.sort_values('price', ascending=ascending)

            # 限制显示数量
            city_data = city_data.head(top_n)

            # 如果是升序（价格最低），反转顺序使最低的在顶部
            if ascending:
                city_data = city_data.sort_values('price', ascending=True)
            else:
                city_data = city_data.sort_values('price', ascending=False)

            # 处理价格，保留指定位数小数
            city_data['price'] = city_data['price'].round(decimal_places)

        except Exception as e:
            print(f"错误：处理城市数据时出错 - {e}")
            return self._create_empty_figure("数据处理错误")

        if city_data.empty:
            print("警告：城市数据为空")
            return self._create_empty_figure("城市数据为空")

        print(f"创建省份城市水平条形图，省份: {province}")
        print(f"城市数量: {len(city_data)}")

        # 自动生成标题
        order_desc = "最低" if ascending else "最高"
        if title is None:
            title = f"{province}房价{order_desc}的{top_n}个城市"

        # 从kwargs中提取特定的参数，避免重复传递
        bar_opacity = kwargs.pop('bar_opacity', 0.6)

        # 创建水平条形图
        fig = self.create_thin_bar_chart(
            data=city_data,
            x_col='city_name',
            y_col='price',
            title=title,
            orientation='h',
            bar_width=0.4,
            bar_opacity=bar_opacity,
            decimal_places=decimal_places,
            **kwargs  # 传递剩余的参数
        )

        return fig

    def create_auto_chart(self,
                        name: str,
                        chart_type: str = 'auto',
                        top_n: int = 10,
                        order_by: str = 'price',
                        ascending: bool = False,
                        title: str = None,
                        decimal_places: int = 1,
                        **kwargs) -> go.Figure:
        """
        自动根据输入名称创建图表

        参数:
        - name: 输入的名称（省份名称或城市名称）
        - chart_type: 图表类型 ('auto', 'province', 'city', 'district')
        - top_n: 显示前N个
        - order_by: 排序字段
        - ascending: 是否升序排列
        - title: 图表标题
        - decimal_places: 小数位数

        返回:
        - 图表对象
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")

        # 自动判断名称类型
        if chart_type == 'auto':
            # 检查是否是省份
            if 'province_name' in self._data.columns:
                provinces = self._data['province_name'].dropna().unique().tolist()
                if name in provinces:
                    chart_type = 'province'
                elif 'city_name' in self._data.columns:
                    cities = self._data['city_name'].dropna().unique().tolist()
                    if name in cities:
                        chart_type = 'city'
                    else:
                        return self._create_empty_figure(f"未找到 '{name}' 的数据")
                else:
                    return self._create_empty_figure("数据中缺少城市信息")
            else:
                return self._create_empty_figure("数据中缺少省份信息")

        # 根据类型创建图表
        if chart_type == 'province':
            return self.create_province_city_comparison(
                province=name,
                top_n=top_n,
                order_by=order_by,
                ascending=ascending,
                title=title,
                decimal_places=decimal_places,
                **kwargs
            )
        elif chart_type == 'city':
            return self.create_city_district_comparison(
                city=name,
                top_n=top_n,
                order_by=order_by,
                ascending=ascending,
                title=title,
                decimal_places=decimal_places,
                **kwargs
            )
        else:
            return self._create_empty_figure(f"不支持的图表类型: {chart_type}")

    
    def _init_styles(self):
        """初始化默认样式"""
        # 默认颜色方案
        self.color_palettes = {
            'category10': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'set2': ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854',
                    '#ffd92f', '#e5c494', '#b3b3b3'],
            'tableau10': ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
                         '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ac'],
            'transparent': [
                'rgba(52, 152, 219, 0.7)',   # 蓝色透明
                'rgba(231, 76, 60, 0.7)',     # 红色透明
                'rgba(46, 204, 113, 0.7)',    # 绿色透明
                'rgba(241, 196, 15, 0.7)',    # 黄色透明
                'rgba(155, 89, 182, 0.7)',    # 紫色透明
            ]
        }
        
        # 默认样式配置
        self.default_styles = {
            'font_family': "Arial, 'Microsoft YaHei', sans-serif",
            'title_size': 22,
            'title_color': '#2c3e50',
            'axis_title_size': 14,
            'axis_tick_size': 12,
            'grid_color': 'lightgrey',
            'bg_color': '#f8f9fa',
            'plot_bgcolor': 'white',
            'margin': {'l': 80, 'r': 40, 't': 100, 'b': 100},
            'bar_width': 0.4,
            'bar_gap': 0.15,
            'bar_group_gap': 0.05,
        }
        
        # 响应式配置
        self.plotly_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'scrollZoom': True,
            'responsive': True,
            'modeBarButtonsToAdd': ['hoverClosestCartesian', 'hoverCompareCartesian']
        }
    
    def load_data_from_sql(self, sql_query: str, params: Dict = None) -> pd.DataFrame:
        """
        从数据库执行SQL查询加载数据
        
        参数:
        - sql_query: SQL查询语句
        - params: 查询参数
        
        返回:
        - DataFrame对象
        """
        if self._db_engine is None:
            raise ValueError("未连接到数据库，请先调用connect_to_tidb方法")
        
        try:
            print(f"执行SQL查询: {sql_query[:100]}..." if len(sql_query) > 100 else f"执行SQL查询: {sql_query}")
            
            if params:
                df = pd.read_sql(sql_query, self._db_engine, params=params)
            else:
                df = pd.read_sql(sql_query, self._db_engine)
            
            print(f"成功加载数据，行数: {len(df)}, 列数: {len(df.columns)}")
            self._data = df
            return df
            
        except Exception as e:
            print(f"SQL查询执行失败: {e}")
            raise
    
    def load_data_from_table(self, table_name: str, columns: List[str] = None, 
                           where_clause: str = None) -> pd.DataFrame:
        """
        从数据库表加载数据
        
        参数:
        - table_name: 表名
        - columns: 要选择的列（None表示所有列）
        - where_clause: WHERE条件
        
        返回:
        - DataFrame对象
        """
        if columns:
            columns_str = ", ".join(columns)
        else:
            columns_str = "*"
        
        sql_query = f"SELECT {columns_str} FROM {table_name}"
        
        if where_clause:
            sql_query += f" WHERE {where_clause}"
        
        return self.load_data_from_sql(sql_query)
    
    def load_trend_data(self, table_name: str = "trend") -> pd.DataFrame:
        """
        加载房价趋势数据（针对标准的trend表结构）
        
        参数:
        - table_name: 表名，默认为"trend"
        
        返回:
        - DataFrame对象
        """
        try:
            df = self.load_data_from_table(
                table_name=table_name,
                columns=['city_name', 'year', 'year_avg_price', 'month', 'month_avg_price']
            )
            print(f"成功加载趋势数据，表名: {table_name}")
            return df
        except Exception as e:
            print(f"加载趋势数据失败: {e}")
            # 尝试获取所有列
            try:
                df = self.load_data_from_table(table_name=table_name)
                print(f"使用所有列加载数据成功")
                return df
            except Exception as e2:
                print(f"加载数据失败: {e2}")
                raise
    
    def load_data_from_csv(self, filepath: str, encoding: str = 'utf-8'):
        """
        从CSV文件加载数据（向后兼容）
        """
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            print(f"成功从CSV加载数据，行数: {len(df)}, 列数: {len(df.columns)}")
            self._data = df
            return df
        except Exception as e:
            print(f"CSV文件加载失败: {e}")
            raise
    
    def set_data(self, data: pd.DataFrame):
        """设置数据"""
        self._data = data
        return self
    
    def get_data(self):
        """获取当前数据"""
        return self._data
    
    def _format_value(self, value: float, decimal_places: int = 1) -> str:
        """格式化数值，保留指定位数小数"""
        if pd.isna(value):
            return "N/A"
        
        format_str = f"{{:,.{decimal_places}f}}"
        return format_str.format(value)
    
    def _check_and_prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """检查和准备数据，处理空值和格式问题"""
        if data is None:
            return pd.DataFrame()
        
        df = data.copy()
        
        # 去除字符串列的前后空格
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def get_available_years(self) -> List[int]:
        """获取数据中可用的年份列表"""
        if self._data is None or 'year' not in self._data.columns:
            return []
        
        return sorted(self._data['year'].dropna().unique().tolist())
    
    def get_available_cities(self) -> List[str]:
        """获取数据中可用的城市列表"""
        if self._data is None or 'city_name' not in self._data.columns:
            return []
        
        return sorted(self._data['city_name'].dropna().unique().tolist())
    
    def get_table_list(self) -> List[str]:
        """获取数据库中的所有表名"""
        if self._db_engine is None:
            return []
        
        try:
            with self._db_engine.connect() as conn:
                # 获取所有表名
                if self._db_config['host'].endswith('tidbcloud.com'):
                    # TiDB Cloud
                    sql = "SHOW TABLES"
                else:
                    # 标准MySQL
                    sql = "SHOW TABLES"
                
                result = conn.execute(text(sql))
                tables = [row[0] for row in result.fetchall()]
                return tables
        except Exception as e:
            print(f"获取表列表失败: {e}")
            return []
    
    def refresh_data(self, sql_query: str = None, table_name: str = None):
        """
        刷新数据（重新从数据库加载）
        
        参数:
        - sql_query: SQL查询语句，如果为None则使用上次的查询
        - table_name: 表名，如果提供则从该表加载所有数据
        """
        if sql_query:
            self.load_data_from_sql(sql_query)
        elif table_name:
            self.load_trend_data(table_name)
        else:
            print("请提供SQL查询语句或表名来刷新数据")
    
    def create_yearly_comparison(self, 
                                cities: List[str] = None,
                                start_year: int = None,
                                end_year: int = None,
                                title: str = "年度房价对比",
                                decimal_places: int = 1,
                                **kwargs) -> go.Figure:
        """
        创建年度房价对比图
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")
        
        # 检查必要列是否存在
        required_cols = ['city_name', 'year', 'year_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")
        
        # 筛选数据
        plot_data = self._data.copy()
        
        # 筛选城市
        if cities:
            cities = [str(city).strip() for city in cities]
            plot_data = plot_data[plot_data['city_name'].isin(cities)]
        
        # 筛选年份范围
        if start_year is not None:
            plot_data = plot_data[plot_data['year'] >= start_year]
        if end_year is not None:
            plot_data = plot_data[plot_data['year'] <= end_year]
        
        if plot_data.empty:
            print("警告：筛选后的数据为空")
            return self._create_empty_figure("筛选条件无数据")
        
        # 按城市和年份分组计算平均价格
        try:
            yearly_avg = plot_data.groupby(['city_name', 'year'])['year_avg_price'].mean().reset_index()
            yearly_avg['year_avg_price'] = yearly_avg['year_avg_price'].round(decimal_places)
            
            # 对年份进行排序
            yearly_avg = yearly_avg.sort_values(['year', 'city_name'])
        except Exception as e:
            print(f"错误：计算平均值时出错 - {e}")
            return self._create_empty_figure("数据处理错误")
        
        if yearly_avg.empty:
            print("警告：分组后的数据为空")
            return self._create_empty_figure("分组后无数据")
        
        print(f"创建年度对比图，数据行数：{len(yearly_avg)}")
        print(f"城市数量：{len(yearly_avg['city_name'].unique())}")
        print(f"年份范围：{yearly_avg['year'].min()} 到 {yearly_avg['year'].max()}")
        
        # 更新标题显示年份范围
        if start_year is not None or end_year is not None:
            year_range = ""
            if start_year is not None:
                year_range += f"{start_year}"
            if end_year is not None:
                if year_range:
                    year_range += f"-{end_year}年"
                else:
                    year_range += f"{end_year}年"
            
            if year_range:
                title = f"{title}（{year_range}）"
        
        # 创建分组条形图
        fig = self.create_thin_bar_chart(
            data=yearly_avg,
            x_col='year',
            y_col='year_avg_price',
            color_col='city_name',
            title=title,
            bar_width=0.15,
            bar_gap=0.2,
            bar_group_gap=0.1,
            show_labels=True,
            decimal_places=decimal_places,
            **kwargs
        )
        
        return fig
    
    def create_monthly_comparison(self,
                                 cities: List[str] = None,
                                 year: Union[int, str] = None,
                                 title: str = "月度房价对比",
                                 decimal_places: int = 1,
                                 **kwargs) -> go.Figure:
        """
        创建月度房价对比图
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")
        
        # 检查必要列是否存在
        required_cols = ['city_name', 'year', 'month', 'month_avg_price']
        missing_cols = [col for col in required_cols if col not in self._data.columns]
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")
        
        # 筛选数据
        plot_data = self._data.copy()
        
        # 筛选年份
        if year is not None:
            try:
                year_int = int(year)
                plot_data = plot_data[plot_data['year'] == year_int]
            except ValueError:
                print(f"错误：年份参数 {year} 无法转换为整数")
                return self._create_empty_figure("年份参数错误")
        
        # 筛选城市
        if cities:
            cities = [str(city).strip() for city in cities]
            plot_data = plot_data[plot_data['city_name'].isin(cities)]
        
        if plot_data.empty:
            print("警告：筛选后的数据为空")
            available_years = sorted(self._data['year'].unique()) if 'year' in self._data.columns else []
            available_cities = sorted(self._data['city_name'].unique()) if 'city_name' in self._data.columns else []
            print(f"可用年份：{available_years}")
            print(f"可用城市：{available_cities}")
            return self._create_empty_figure("筛选条件无数据")
        
        # 添加月份格式化列
        plot_data['month_str'] = plot_data['month'].astype(str) + '月'
        
        # 按城市和月份分组计算平均价格
        try:
            monthly_avg = plot_data.groupby(['city_name', 'month', 'month_str'])['month_avg_price'].mean().reset_index()
            monthly_avg['month_avg_price'] = monthly_avg['month_avg_price'].round(decimal_places)
            monthly_avg = monthly_avg.sort_values(['month', 'city_name'])
        except Exception as e:
            print(f"错误：计算月度平均值时出错 - {e}")
            return self._create_empty_figure("数据处理错误")
        
        if monthly_avg.empty:
            print("警告：月度分组后的数据为空")
            return self._create_empty_figure("月度数据无数据")
        
        print(f"创建月度对比图，数据行数：{len(monthly_avg)}")
        print(f"城市数量：{len(monthly_avg['city_name'].unique())}")
        print(f"月份数量：{len(monthly_avg['month'].unique())}")
        
        # 更新标题显示年份
        if year is not None:
            title = f"{year}年{title}"
        
        # 创建分组条形图
        fig = self.create_thin_bar_chart(
            data=monthly_avg,
            x_col='month_str',
            y_col='month_avg_price',
            color_col='city_name',
            title=title,
            bar_width=0.2,
            bar_gap=0.25,
            bar_group_gap=0.1,
            show_labels=True,
            decimal_places=decimal_places,
            **kwargs
        )
        
        return fig
    
    def create_thin_bar_chart(self,
                            data: pd.DataFrame = None,
                            x_col: str = None,
                            y_col: str = None,
                            color_col: str = None,
                            title: str = "",
                            orientation: str = 'v',
                            show_labels: bool = True,
                            color_palette: str = 'transparent',
                            bar_opacity: float = 0.8,
                            bar_width: float = None,
                            bar_gap: float = None,
                            bar_group_gap: float = None,
                            format_y_axis: bool = True,
                            decimal_places: int = 1,
                            **kwargs) -> go.Figure:
        """
        创建细条形图
        """
        # 使用传入的数据或类数据
        use_data = data if data is not None else self._data
        if use_data is None:
            print("错误：未提供数据")
            return self._create_empty_figure("无可用数据")
        
        # 检查并准备数据
        plot_data = self._check_and_prepare_data(use_data)
        
        # 验证数据
        if plot_data.empty:
            print("错误：数据为空")
            return self._create_empty_figure("数据为空")
        
        # 验证参数
        if x_col is None or y_col is None:
            print(f"错误：必须提供 x_col 和 y_col 参数")
            return self._create_empty_figure("参数错误")
        
        # 检查列是否存在
        missing_cols = []
        if x_col not in plot_data.columns:
            missing_cols.append(x_col)
        if y_col not in plot_data.columns:
            missing_cols.append(y_col)
        if color_col and color_col not in plot_data.columns:
            missing_cols.append(color_col)
        
        if missing_cols:
            print(f"错误：数据中缺少以下列：{missing_cols}")
            return self._create_empty_figure(f"缺少列：{', '.join(missing_cols)}")
        
        # 确保x轴是字符串类型（用于显示）
        if plot_data[x_col].dtype != 'object':
            plot_data[x_col] = plot_data[x_col].astype(str)
        
        # 处理大数值显示
        if format_y_axis:
            y_max = plot_data[y_col].max()
            if y_max > 10000:
                if y_max > 1_0000_0000:
                    scale_factor = 1_0000_0000
                    unit = "亿元"
                    y_axis_title = f'{self._get_axis_title(y_col)}（{unit}）'
                elif y_max > 1_0000:
                    scale_factor = 1_0000
                    unit = "万元"
                    y_axis_title = f'{self._get_axis_title(y_col)}（{unit}）'
                else:
                    scale_factor = 1000
                    unit = "千元"
                    y_axis_title = f'{self._get_axis_title(y_col)}（{unit}）'
                
                plot_data[f'{y_col}_scaled'] = plot_data[y_col] / scale_factor
                y_col_display = f'{y_col}_scaled'
            else:
                y_col_display = y_col
                y_axis_title = self._get_axis_title(y_col)
        else:
            y_col_display = y_col
            y_axis_title = self._get_axis_title(y_col)
        
        # 设置条形宽度和间隔
        bar_width = bar_width if bar_width is not None else self.default_styles['bar_width']
        bar_gap = bar_gap if bar_gap is not None else self.default_styles['bar_gap']
        bar_group_gap = bar_group_gap if bar_group_gap is not None else self.default_styles['bar_group_gap']
        
        # 获取颜色
        colors = self._get_colors(10, color_palette)
        
        # 创建条形图
        if color_col:
            # 分组条形图
            categories = sorted(plot_data[color_col].unique())
            
            if len(categories) == 0:
                print("警告：分组列没有找到类别")
                return self._create_empty_figure("分组列没有数据")
            
            fig = go.Figure()
            
            # 为每个分组创建条形
            for i, category in enumerate(categories):
                category_data = plot_data[plot_data[color_col] == category]
                
                if category_data.empty:
                    print(f"警告：分组 '{category}' 没有数据")
                    continue
                
                # 确保不超出颜色范围
                color_idx = i % len(colors)
                
                # 格式化显示值
                if show_labels:
                    text_values = category_data[y_col].apply(
                        lambda x: self._format_value(x, decimal_places)
                    )
                else:
                    text_values = None
                
                # 确定x和y值
                if orientation == 'v':
                    x_values = category_data[x_col]
                    y_values = category_data[y_col_display]
                else:
                    x_values = category_data[y_col_display]
                    y_values = category_data[x_col]
                
                # 添加条形图，设置悬停文本
                fig.add_trace(go.Bar(
                    x=x_values,
                    y=y_values,
                    name=str(category),
                    marker_color=colors[color_idx],
                    opacity=bar_opacity,
                    marker_line=dict(width=1, color='rgba(0,0,0,0.3)'),
                    text=text_values,
                    texttemplate='%{text}',
                    textposition='outside',
                    orientation=orientation,
                    width=bar_width,
                    hovertemplate=(
                        f"<b>{self._get_axis_title(color_col)}</b>: %{{name}}<br>" +
                        f"<b>{self._get_axis_title(x_col)}</b>: %{{x}}<br>" +
                        f"<b>{self._get_axis_title(y_col)}</b>: %{{y:,.{decimal_places}f}}<br>" +
                        "<extra></extra>"
                    )
                ))
            
            # 使用分组模式
            barmode = 'group'
            unique_x_values = sorted(plot_data[x_col].unique().tolist())
        else:
            # 单一颜色条形图
            color = kwargs.get('bar_color', colors[0])
            
            # 格式化显示值
            if show_labels:
                text_values = plot_data[y_col].apply(
                    lambda x: self._format_value(x, decimal_places)
                )
            else:
                text_values = None
            
            # 确定x和y值
            if orientation == 'v':
                x_values = plot_data[x_col]
                y_values = plot_data[y_col_display]
            else:
                x_values = plot_data[y_col_display]
                y_values = plot_data[x_col]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=x_values,
                    y=y_values,
                    marker_color=color,
                    opacity=bar_opacity,
                    marker_line=dict(width=1, color='rgba(0,0,0,0.3)'),
                    text=text_values,
                    texttemplate='%{text}',
                    textposition='outside',
                    orientation=orientation,
                    width=bar_width,
                    hovertemplate=(
                        f"<b>{self._get_axis_title(x_col)}</b>: %{{x}}<br>" +
                        f"<b>{self._get_axis_title(y_col)}</b>: %{{y:,.{decimal_places}f}}<br>" +
                        "<extra></extra>"
                    )
                )
            ])
            barmode = 'relative'
            unique_x_values = plot_data[x_col].unique().tolist()
        
        # 应用通用布局
        x_title = self._get_axis_title(x_col) if orientation == 'v' else y_axis_title
        y_title = y_axis_title if orientation == 'v' else self._get_axis_title(x_col)
        
        self._apply_bar_layout(
            fig, 
            title, 
            x_title, 
            y_title, 
            orientation,
            show_legend=bool(color_col),
            barmode=barmode,
            bar_gap=bar_gap,
            bar_group_gap=bar_group_gap
        )
        
        # 修复x轴显示问题
        self._fix_x_axis_display(fig, unique_x_values, orientation)
        
        return fig
    
    def create_city_price_bars(self,
                              cities: List[str] = None,
                              year_filter: Union[int, str] = None,
                              use_monthly: bool = False,
                              title: str = "城市房价对比",
                              decimal_places: int = 1,
                              **kwargs) -> go.Figure:
        """
        创建城市房价对比条形图
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")
        
        # 筛选数据
        plot_data = self._data.copy()
        
        # 筛选年份
        if year_filter is not None:
            try:
                year_int = int(year_filter)
                plot_data = plot_data[plot_data['year'] == year_int]
            except ValueError:
                print(f"错误：年份参数 {year_filter} 无法转换为整数")
                return self._create_empty_figure("年份参数错误")
        
        # 筛选城市
        if cities:
            cities = [str(city).strip() for city in cities]
            plot_data = plot_data[plot_data['city_name'].isin(cities)]
        
        # 检查筛选后是否有数据
        if plot_data.empty:
            print(f"警告：筛选条件 year={year_filter}, cities={cities} 没有找到数据")
            return self._create_empty_figure("筛选条件无数据")
        
        # 确定使用年度还是月度数据
        price_col = 'month_avg_price' if use_monthly else 'year_avg_price'
        
        if price_col not in plot_data.columns:
            print(f"错误：数据中缺少 {price_col} 列")
            return self._create_empty_figure(f"缺少 {price_col} 列")
        
        try:
            # 按城市分组计算平均价格
            price_data = plot_data.groupby('city_name')[price_col].mean().reset_index()
            price_data.rename(columns={price_col: 'price'}, inplace=True)
            price_data['price'] = price_data['price'].round(decimal_places)
            price_data = price_data.sort_values('price', ascending=False)
        except Exception as e:
            print(f"错误：计算平均价格时出错 - {e}")
            return self._create_empty_figure("数据处理错误")
        
        if price_data.empty:
            print("警告：分组后的数据为空")
            return self._create_empty_figure("分组后无数据")
        
        print(f"创建城市房价条形图，数据行数：{len(price_data)}")
        
        # 更新标题
        if year_filter is not None:
            title = f"{year_filter}年{title}"
        
        # 创建条形图
        fig = self.create_thin_bar_chart(
            data=price_data,
            x_col='city_name',
            y_col='price',
            title=title,
            decimal_places=decimal_places,
            **kwargs
        )
        
        return fig
    
    def create_horizontal_bar(self,
                             top_n: int = 10,
                             ascending: bool = True,
                             year_filter: Union[int, str] = None,
                             use_monthly: bool = False,
                             title: str = "城市房价排名",
                             decimal_places: int = 1,
                             **kwargs) -> go.Figure:
        """
        创建水平条形图（排名图）
        """
        if self._data is None:
            print("错误：未加载数据")
            return self._create_empty_figure("请先加载数据")
        
        # 筛选数据
        plot_data = self._data.copy()
        
        # 筛选年份
        if year_filter is not None:
            try:
                year_int = int(year_filter)
                plot_data = plot_data[plot_data['year'] == year_int]
            except ValueError:
                print(f"错误：年份参数 {year_filter} 无法转换为整数")
                return self._create_empty_figure("年份参数错误")
        
        # 确定使用年度还是月度数据
        price_col = 'month_avg_price' if use_monthly else 'year_avg_price'
        
        if price_col not in plot_data.columns:
            print(f"错误：数据中缺少 {price_col} 列")
            return self._create_empty_figure(f"缺少 {price_col} 列")
        
        try:
            # 按城市分组计算平均价格
            price_data = plot_data.groupby('city_name')[price_col].mean().reset_index()
            price_data.rename(columns={price_col: 'price'}, inplace=True)
            price_data['price'] = price_data['price'].round(decimal_places)
            
            # 排序并选择前N个或后N个
            price_data = price_data.sort_values('price', ascending=ascending)
            
            if top_n > 0:
                price_data = price_data.head(top_n)
            
            # 如果是升序（价格最低），反转顺序使最低的在顶部
            if ascending:
                price_data = price_data.sort_values('price', ascending=True)
            else:
                price_data = price_data.sort_values('price', ascending=False)
                
        except Exception as e:
            print(f"错误：计算平均价格时出错 - {e}")
            return self._create_empty_figure("数据处理错误")
        
        if price_data.empty:
            print("警告：分组后的数据为空")
            return self._create_empty_figure("分组后无数据")
        
        print(f"创建水平条形图，数据行数：{len(price_data)}")
        
        # 更新标题
        order_desc = "最低" if ascending else "最高"
        if year_filter is not None:
            title = f"{year_filter}年城市房价{order_desc}的{top_n}个城市"
        
        # 创建水平条形图
        fig = self.create_thin_bar_chart(
            data=price_data,
            x_col='city_name',
            y_col='price',
            title=title,
            orientation='h',
            bar_width=0.4,
            bar_opacity=0.6,
            decimal_places=decimal_places,
            **kwargs
        )
        
        return fig
    
    def create_custom_chart(self,
                           sql_query: str,
                           x_col: str,
                           y_col: str,
                           color_col: str = None,
                           title: str = "自定义图表",
                           orientation: str = 'v',
                           decimal_places: int = 1,
                           **kwargs) -> go.Figure:
        """
        创建自定义SQL查询的图表
        
        参数:
        - sql_query: 自定义SQL查询
        - x_col: x轴列名
        - y_col: y轴列名
        - color_col: 颜色分组列名
        - title: 图表标题
        - orientation: 方向（'v'垂直，'h'水平）
        - decimal_places: 小数位数
        """
        try:
            # 执行自定义SQL查询
            custom_data = self.load_data_from_sql(sql_query)
            
            # 创建图表
            fig = self.create_thin_bar_chart(
                data=custom_data,
                x_col=x_col,
                y_col=y_col,
                color_col=color_col,
                title=title,
                orientation=orientation,
                decimal_places=decimal_places,
                **kwargs
            )
            
            return fig
        except Exception as e:
            print(f"创建自定义图表失败: {e}")
            return self._create_empty_figure(f"自定义图表失败: {e}")
    
    def _create_empty_figure(self, message: str = "无数据") -> go.Figure:
        """创建空图表，显示提示信息"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="grey")
        )
        fig.update_layout(
            title="无可用数据",
            plot_bgcolor="white",
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False)
        )
        return fig
    
    def _get_axis_title(self, column_name: str) -> str:
        """获取坐标轴标题（中文化）"""
        title_map = {
            'city_name': '城市',
            'year': '年份',
            'month': '月份',
            'year_avg_price': '年度平均房价（元/㎡）',
            'month_avg_price': '月度平均房价（元/㎡）',
            'price': '房价（元/㎡）',
            'avg_price': '平均房价（元/㎡）',
            'count': '数量',
            'total': '总计',
            'price_scaled': '房价',
            'year_avg_price_scaled': '年度平均房价',
            'month_avg_price_scaled': '月度平均房价',
            'date': '日期',
            'district_name': '区域',
            'province_name': '省份',
            'city_avg_total_price': '城市平均总价（万元）',
            'price_rent_ratio': '租售比',
            'listing_count': '挂牌数量',
            'district_ratio': '区域占比',
            'district_avg_price': '区域平均房价（元/㎡）'
        }
        return title_map.get(column_name, column_name)
    
    def _fix_x_axis_display(self, fig: go.Figure, x_values: list, orientation: str = 'v'):
        """
        修复x轴显示问题
        """
        if not x_values:
            return
        
        # 确保x_values是字符串列表
        if isinstance(x_values, np.ndarray):
            x_values = x_values.tolist()
        
        x_values = [str(x) for x in x_values]
        
        # 对于月份，确保按照数字顺序排序
        if all(x.replace('月', '').isdigit() for x in x_values):
            try:
                # 提取月份数字并排序
                month_numbers = []
                for x in x_values:
                    num = int(x.replace('月', '')) if '月' in x else int(x)
                    month_numbers.append(num)
                sorted_indices = np.argsort(month_numbers)
                x_values = [x_values[i] for i in sorted_indices]
            except:
                pass
        
        # 设置x轴配置
        if orientation == 'v':
            fig.update_xaxes(
                type='category',
                categoryorder='array',
                categoryarray=x_values,
                tickmode='array',
                tickvals=x_values,
                ticktext=x_values,
                tickangle=0,
                tickfont=dict(
                    size=self.default_styles['axis_tick_size'],
                    family=self.default_styles['font_family']
                )
            )
        else:
            # 对于水平条形图，修复y轴
            fig.update_yaxes(
                type='category',
                categoryorder='array',
                categoryarray=x_values,
                tickmode='array',
                tickvals=x_values,
                ticktext=x_values,
                tickangle=0,
                tickfont=dict(
                    size=self.default_styles['axis_tick_size'],
                    family=self.default_styles['font_family']
                )
            )
    
    def _get_colors(self, n: int, palette: str = 'transparent') -> List[str]:
        """获取指定数量的颜色"""
        if palette in self.color_palettes:
            colors = self.color_palettes[palette]
        else:
            colors = self.color_palettes['transparent']
        
        # 如果需要的颜色多于调色板中的颜色，则循环使用
        if n > len(colors):
            colors = colors * (n // len(colors) + 1)
        
        return colors[:n]
    
    def _apply_bar_layout(self, fig: go.Figure, 
                         title: str, 
                         x_title: str, 
                         y_title: str,
                         orientation: str = 'v',
                         show_legend: bool = True,
                         barmode: str = 'relative',
                         bar_gap: float = 0.15,
                         bar_group_gap: float = 0.05):
        """应用条形图专用布局"""
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(
                    size=self.default_styles['title_size'],
                    color=self.default_styles['title_color'],
                    family=self.default_styles['font_family']
                )
            ),
            xaxis=dict(
                title=x_title,
                title_font=dict(
                    size=self.default_styles['axis_title_size'],
                    family=self.default_styles['font_family']
                ),
                tickfont=dict(
                    size=self.default_styles['axis_tick_size'],
                    family=self.default_styles['font_family']
                ),
                showgrid=(orientation == 'h'),
                gridcolor=self.default_styles['grid_color'],
                linecolor='black',
                linewidth=1
            ),
            yaxis=dict(
                title=y_title,
                title_font=dict(
                    size=self.default_styles['axis_title_size'],
                    family=self.default_styles['font_family']
                ),
                tickfont=dict(
                    size=self.default_styles['axis_tick_size'],
                    family=self.default_styles['font_family']
                ),
                showgrid=(orientation == 'v'),
                gridcolor=self.default_styles['grid_color'],
                linecolor='black',
                linewidth=1
            ),
            plot_bgcolor=self.default_styles['plot_bgcolor'],
            paper_bgcolor=self.default_styles['bg_color'],
            margin=self.default_styles['margin'],
            showlegend=show_legend,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(family=self.default_styles['font_family'])
            ) if show_legend else None,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='#2c3e50',
                font=dict(
                    family=self.default_styles['font_family'],
                    size=14
                )
            ),
            barmode=barmode,
            bargap=bar_gap,
            bargroupgap=bar_group_gap
        )
    
    def show(self, fig: go.Figure, config: Dict = None):
        """显示图表"""
        config = config if config is not None else self.plotly_config
        fig.show(config=config)
    
    def save(self, fig: go.Figure, filename: str, format: str = 'html'):
        """保存图表"""
        if format == 'html':
            fig.write_html(filename)
        elif format == 'png':
            fig.write_image(filename)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def print_data_info(self):
        """打印数据信息，用于调试"""
        if self._data is None:
            print("数据未加载")
            return
        
        print("=" * 60)
        print("数据信息:")
        print(f"行数: {len(self._data)}")
        print(f"列数: {len(self._data.columns)}")
        print(f"列名: {list(self._data.columns)}")
        print(f"数据类型:")
        print(self._data.dtypes)
        print()
        
        # 打印列的唯一值
        for col in ['city_name', 'year', 'month']:
            if col in self._data.columns:
                unique_vals = self._data[col].unique()
                print(f"{col} 的唯一值 ({len(unique_vals)}个): {sorted(unique_vals)[:20]}")
                if len(unique_vals) > 20:
                    print(f"   ... 还有 {len(unique_vals) - 20} 个值")
        
        # 打印价格统计信息
        for price_col in ['year_avg_price', 'month_avg_price']:
            if price_col in self._data.columns:
                print(f"{price_col} 统计:")
                print(f"  最小值: {self._data[price_col].min():.2f}")
                print(f"  最大值: {self._data[price_col].max():.2f}")
                print(f"  平均值: {self._data[price_col].mean():.2f}")
                print(f"  中位数: {self._data[price_col].median():.2f}")
        print("=" * 60)
    
    def print_database_info(self):
        """打印数据库信息"""
        if self._db_engine is None:
            print("未连接到数据库")
            return
        
        try:
            with self._db_engine.connect() as conn:
                # 获取数据库版本
                result = conn.execute(text("SELECT VERSION()"))
                version = result.fetchone()[0]
                print(f"数据库版本: {version}")
                
                # 获取所有表
                tables = self.get_table_list()
                print(f"数据库表 ({len(tables)}个): {tables}")
                
                # 获取数据表结构示例
                if tables:
                    for table in tables[:3]:  # 只显示前3个表
                        try:
                            result = conn.execute(text(f"DESCRIBE {table}"))
                            columns = [(row[0], row[1]) for row in result.fetchall()]
                            print(f"表 '{table}' 结构: {columns[:5]}...")  # 只显示前5列
                        except:
                            pass
        except Exception as e:
            print(f"获取数据库信息失败: {e}")


# 主程序 - 使用您的数据库配置
if __name__ == "__main__":
    # 1. 数据库配置
    DB_CONFIG = {
        'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
        'port': 4000,
        'user': "48pvdQxqqjLneBr.root",
        'password': "o46hvbIhibN3tTPp",
        'database': "python_project",
        'ssl_ca': "tidb-ca.pem",
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }
    
    print("=" * 70)
    print("TiDB数据库图表生成器")
    print("=" * 70)
    
    # 2. 初始化TiDB图表构建器
    print("\n1. 连接到TiDB数据库...")
    builder = TiDBChartBuilder(db_config=DB_CONFIG)
    
    # 3. 打印数据库信息
    builder.print_database_info()
    
    # 4. 加载数据（假设表名为trend）
    print("\n2. 加载数据...")
    try:
        # 尝试从trend表加载数据
        builder.load_trend_data(table_name="trend")
    except Exception as e:
        print(f"加载trend表失败: {e}")
        print("尝试查找其他表...")
        tables = builder.get_table_list()
        if tables:
            print(f"找到的表: {tables}")
            # 使用第一个表
            builder.load_trend_data(table_name=tables[0])
        else:
            print("数据库中没有任何表")
            exit(1)
    
    # 5. 打印数据信息
    print("\n3. 数据信息:")
    builder.print_data_info()
    
    # 6. 获取可用年份和城市
    available_years = builder.get_available_years()
    available_cities = builder.get_available_cities()
    print(f"\n可用年份: {available_years}")
    print(f"可用城市 ({len(available_cities)}个): {available_cities[:10]}...")
    
    # 7. 创建图表
    print("\n4. 生成图表...")
    
    # 7.1 主要城市年度房价对比图
    print("\n[图表1] 主要城市年度房价对比")
    top_cities = ['北京', '上海', '深圳', '广州', '杭州']
    
    # 检查哪些城市在数据中
    cities_in_data = [city for city in top_cities if city in available_cities]
    if not cities_in_data:
        cities_in_data = available_cities[:5]  # 使用前5个城市
    
    fig1 = builder.create_yearly_comparison(
        cities=cities_in_data,
        start_year=2022,
        end_year=2025,
        title='主要城市年度房价对比',
        color_palette='transparent',
        bar_opacity=0.7,
        decimal_places=1
    )
    builder.show(fig1)
    builder.save(fig1,"2022到2025城市房价对比柱状图.html")
    
    
    # 7.3 2023年各城市房价条形图
    print("\n[图表3] 2023年各城市平均房价")
    if 2023 in available_years:
        fig3 = builder.create_city_price_bars(
            year_filter=2025,
            title='2025年各城市平均房价',
            use_monthly=False,
            decimal_places=1
        )
        builder.show(fig3)
        builder.save(fig3,"2025年各城市平均房价柱状图.html")
    
    # 7.4 房价最高的10个城市（水平条形图）
    print("\n[图表4] 房价最高的10个城市")
    if available_years:
        latest_year = max(available_years)
        fig4 = builder.create_horizontal_bar(
            top_n=10,
            ascending=False,  # 降序，最高价格在前
            year_filter=latest_year,
            title=f'{latest_year}年房价最高的10个城市',
            decimal_places=1
        )
        builder.show(fig4)
        builder.save(fig4,"房价最高的10个城市柱状图.html")
    
    # 7.5 房价最低的10个城市（水平条形图）
    print("\n[图表5] 房价最低的10个城市")
    if available_years:
        fig5 = builder.create_horizontal_bar(
            top_n=10,
            ascending=True,  # 升序，最低价格在前
            year_filter=latest_year,
            title=f'{latest_year}年房价最低的10个城市',
            decimal_places=1
        )
        builder.show(fig5)
        builder.save(fig5,"房价最低的10个城市柱状图.html")
    
    # 7.7 不同年份的城市房价对比
    print("\n[图表7] 不同年份的城市房价对比")
    if len(available_years) >= 2:
        # 选择最近的两个年份
        recent_years = sorted(available_years)[-2:]
        year_data_list = []
        
        for year_val in recent_years:  # 修改这里：将 year 改为 year_val
            year_data = builder.get_data()
            year_data = year_data[year_data['year'] == year_val]  # 修改这里：将 year 改为 year_val
            if not year_data.empty:
                city_avg = year_data.groupby('city_name')['year_avg_price'].mean().reset_index()
                city_avg['year'] = year_val  # 修改这里：将 year 改为 year_val
                year_data_list.append(city_avg)
        
        if year_data_list:
            combined_data = pd.concat(year_data_list, ignore_index=True)
            combined_data = combined_data.sort_values(['year', 'year_avg_price'], ascending=[True, False])
            
            fig7 = builder.create_thin_bar_chart(
                data=combined_data,
                x_col='city_name',
                y_col='year_avg_price',
                color_col='year',
                title=f'{recent_years[0]}年 vs {recent_years[1]}年 城市房价对比',
                bar_width=0.2,
                bar_gap=0.25,
                bar_group_gap=0.1,
                show_labels=True,
                decimal_places=1
            )
            builder.show(fig7)
            builder.save(fig7,"2024和2025各城市房价对比柱状图.html")

    # 在主程序的图表创建部分，修改原来的区域对比测试用例：

    # 7.8 自动图表生成测试（智能判断省/市）
    print("\n[图表8] 自动图表生成测试（智能判断省/市）")
    print("注意：需要加载current_price表数据")

    # 临时保存trend数据
    original_data = builder.get_data()

    try:
        # 加载current_price表数据
        print("\n加载current_price表数据...")
        current_data = builder.load_current_price_data(table_name="current_price")

        # 设置当前数据为current_price数据
        builder.set_data(current_data)
    
        # 测试省份对比（示例：广东省）
        print("\n[自动图表1] 广东省各城市房价对比")
        try:
            fig8_1 = builder.create_auto_chart(
                name='广东',
                chart_type='auto',  # 自动判断
                top_n=15,
                order_by='city_avg_price',
                ascending=False,
                title=None,  # 自动生成标题
                decimal_places=0,
                color_palette='transparent',
                bar_opacity=0.7
            )
            builder.show(fig8_1)
            builder.save(fig8_1,"广东省各城市房价对比柱状图.html")
        except Exception as e:
            print(f"创建广东省城市对比图失败: {e}")

        # 测试手动指定类型
        print("\n[自动图表3] 北京市各区域房价对比（手动指定类型）")
        try:
            fig8_3 = builder.create_auto_chart(
                name='北京',
                chart_type='city',  # 手动指定为城市类型
                top_n=20,
                order_by='district_avg_price',
                ascending=False,
                title='北京市各区域房价',
                decimal_places=0,
                color_palette='transparent',
                bar_opacity=0.7
            )
            builder.show(fig8_3)
            builder.save(fig8_3,"北京市各区域房价柱状图.html")
        except Exception as e:
            print(f"创建北京市区域对比图失败: {e}")

    except Exception as e:
        print(f"创建自动图表失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 恢复原始数据
        print("\n恢复原始trend表数据...")
        builder.set_data(original_data)