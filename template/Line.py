import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Union, Optional, Any
import warnings
warnings.filterwarnings('ignore')
from sqlalchemy import create_engine, text
import pymysql
pymysql.install_as_MySQLdb()

class TiDBLineChartBuilder:
    """
    TiDB数据库折线图构建器类 - 支持从TiDB Cloud动态读取数据
    """
    
    def __init__(self, db_config: Dict = None, data: pd.DataFrame = None):
        """
        初始化折线图构建器
        
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
    
    def _init_styles(self):
        """初始化默认样式"""
        # 默认颜色方案
        self.color_palettes = {
            'category10': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'set2': ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854',
                    '#ffd92f', '#e5c494', '#b3b3b3'],
            'tableau10': ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
                         '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ac']
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
            'margin': {'l': 80, 'r': 40, 't': 100, 'b': 80}
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
    
    def set_data(self, data: pd.DataFrame):
        """设置数据"""
        self._data = data
        return self
    
    def get_data(self):
        """获取当前数据"""
        return self._data
    
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
            'date': '日期'
        }
        return title_map.get(column_name, column_name)
    
    def _format_date_for_display(self, date_str: str, format_type: str = 'month_only') -> str:
        """
        格式化日期显示
        
        参数:
        - date_str: 日期字符串，如 '2023-11'
        - format_type: 格式类型 ('full_year_month', 'month_only', 'year_only')
        
        返回:
        - 格式化后的中文日期字符串
        """
        try:
            # 解析日期字符串
            if '-' in date_str:
                year, month = date_str.split('-')
            else:
                # 尝试其他格式
                year = date_str[:4]
                month = date_str[4:] if len(date_str) > 4 else '01'
            
            year = int(year)
            month = int(month)
            
            # 中文月份名称
            month_names = ['1月', '2月', '3月', '4月', '5月', '6月', 
                          '7月', '8月', '9月', '10月', '11月', '12月']
            
            if format_type == 'full_year_month':
                return f"{year}年{month_names[month-1]}"
            elif format_type == 'month_only':
                return month_names[month-1]
            elif format_type == 'year_only':
                return f"{year}年"
            else:
                return f"{year}年{month_names[month-1]}"
        except:
            return date_str
    
    def create_line_chart(self, 
                         data: pd.DataFrame = None,
                         x_col: str = None,
                         y_cols: Union[str, List[str]] = None,
                         line_names: List[str] = None,
                         title: str = "",
                         color_palette: str = 'category10',
                         show_legend: bool = True,
                         smooth_lines: bool = True,
                         show_markers: bool = True,
                         optimize_date_ticks: bool = True,
                         date_format_type: str = 'full_year_month',
                         **kwargs) -> go.Figure:
        """
        创建折线图 - 修复日期显示问题版本
        
        参数:
        - data: 数据框，如果不提供则使用self._data
        - x_col: x轴列名
        - y_cols: y轴列名或列名列表
        - line_names: 线条名称列表
        - title: 图表标题
        - color_palette: 颜色方案名称
        - show_legend: 是否显示图例
        - smooth_lines: 是否使用平滑线条
        - show_markers: 是否显示标记点
        - optimize_date_ticks: 是否优化日期刻度显示
        - date_format_type: 日期格式类型 ('full_year_month', 'month_only', 'year_only')
        """
        # 使用传入的数据或类数据
        use_data = data if data is not None else self._data
        if use_data is None:
            raise ValueError("未提供数据，请通过参数或set_data方法设置数据")
        
        # 验证参数
        if x_col is None:
            raise ValueError("必须提供 x_col 参数")
        if y_cols is None:
            raise ValueError("必须提供 y_cols 参数")
        
        # 确保y_cols是列表
        if isinstance(y_cols, str):
            y_cols = [y_cols]
        
        # 获取颜色
        colors = self._get_colors(len(y_cols), color_palette)
        
        # 创建图形
        fig = go.Figure()
        
        # 添加每条折线
        for i, y_col in enumerate(y_cols):
            if y_col not in use_data.columns:
                print(f"警告: 列 '{y_col}' 不存在于数据中，跳过")
                continue
            
            line_name = line_names[i] if line_names and i < len(line_names) else y_col
            
            # 对于日期列，悬停时显示中文格式
            if x_col == 'date':
                hover_dates = use_data[x_col].apply(
                    lambda x: self._format_date_for_display(str(x), 'full_year_month')
                )
            else:
                hover_dates = use_data[x_col]
            
            fig.add_trace(go.Scatter(
                x=use_data[x_col],  # 原始数据
                y=use_data[y_col],
                mode='lines+markers' if show_markers else 'lines',
                name=line_name,
                line=dict(
                    color=colors[i],
                    width=kwargs.get('line_width', 3),
                    shape='spline' if smooth_lines else 'linear'
                ),
                marker=dict(
                    size=kwargs.get('marker_size', 8),
                    color=colors[i],
                    line=dict(width=2, color='white')
                ) if show_markers else None,
                hovertemplate=(
                    f"<b>{self._get_axis_title(x_col)}</b>: %{{customdata}}<br>"
                    f"<b>{line_name}</b>: %{{y:,.0f}}<br>"
                    "<extra></extra>"
                ),
                customdata=hover_dates
            ))
        
        # 应用样式
        axis_title = '日期' if x_col == 'date' else self._get_axis_title(x_col)
        self._apply_common_layout(fig, title, axis_title, '房价（元/㎡）', show_legend)
        
        # 特殊处理日期轴
        if x_col == 'date' and optimize_date_ticks:
            # 修复：使用正确的日期数据和格式
            self._setup_date_axis(fig, use_data[x_col].tolist(), date_format_type)
        
        return fig
    
    def create_single_city_monthly_chart(self,
                                        city: str,
                                        year: int = None,
                                        title: str = None,
                                        smooth_lines: bool = True,
                                        show_markers: bool = True,
                                        **kwargs) -> go.Figure:
        """
        创建单个城市的月度房价折线图
        
        参数:
        - city: 城市名称
        - year: 年份（可选，不指定则使用所有年份）
        - title: 图表标题（可选，不指定则自动生成）
        - smooth_lines: 是否使用平滑线条
        - show_markers: 是否显示标记点
        """
        if self._data is None:
            raise ValueError("未加载数据，请先加载数据")
        
        # 筛选城市数据
        city_data = self._data[self._data['city_name'] == city].copy()
        
        if city_data.empty:
            raise ValueError(f"未找到城市 '{city}' 的数据")
        
        # 筛选年份（如果指定）
        if year is not None:
            city_data = city_data[city_data['year'] == year]
        
        if city_data.empty:
            raise ValueError(f"未找到城市 '{city}' 在 {year} 年的数据")
        
        # 创建日期列（格式：YYYY-MM）
        city_data['date'] = city_data.apply(
            lambda row: f"{int(row['year'])}-{int(row['month']):02d}", 
            axis=1
        )
        
        # 按日期排序
        city_data = city_data.sort_values(['year', 'month'])
        
        # 自动生成标题
        if title is None:
            if year is not None:
                title = f"{city} {year}年月度房价趋势"
            else:
                title = f"{city} 月度房价趋势"
        
        # 创建折线图
        fig = self.create_line_chart(
            data=city_data,
            x_col='date',
            y_cols=['month_avg_price'],
            line_names=[f'{city}月均房价'],
            title=title,
            color_palette='category10',
            optimize_date_ticks=True,
            date_format_type='month_only',
            smooth_lines=smooth_lines,
            show_markers=show_markers,
            **kwargs
        )
        
        return fig
    
    def create_multi_city_comparison(self,
                                    cities: List[str],
                                    year: int = None,
                                    title: str = None,
                                    smooth_lines: bool = True,
                                    show_markers: bool = True,
                                    **kwargs) -> go.Figure:
        """
        创建多个城市的房价对比折线图
        
        参数:
        - cities: 城市名称列表
        - year: 年份（可选，不指定则使用所有年份）
        - title: 图表标题（可选，不指定则自动生成）
        - smooth_lines: 是否使用平滑线条
        - show_markers: 是否显示标记点
        """
        if self._data is None:
            raise ValueError("未加载数据，请先加载数据")
        
        # 筛选多个城市数据
        city_data_list = []
        
        for city in cities:
            city_df = self._data[self._data['city_name'] == city].copy()
            
            if city_df.empty:
                print(f"警告: 未找到城市 '{city}' 的数据，跳过")
                continue
            
            # 筛选年份（如果指定）
            if year is not None:
                city_df = city_df[city_df['year'] == year]
            
            if city_df.empty:
                print(f"警告: 未找到城市 '{city}' 在 {year} 年的数据，跳过")
                continue
            
            # 创建日期列（格式：YYYY-MM）
            city_df['date'] = city_df.apply(
                lambda row: f"{int(row['year'])}-{int(row['month']):02d}", 
                axis=1
            )
            
            # 按日期排序
            city_df = city_df.sort_values(['year', 'month'])
            
            # 重命名列名，以城市名为前缀
            city_df.rename(columns={'month_avg_price': city}, inplace=True)
            
            # 只保留需要的列
            city_df = city_df[['date', city]]
            
            city_data_list.append(city_df)
        
        if not city_data_list:
            raise ValueError("未找到任何城市的有效数据")
        
        # 合并所有城市数据
        comparison_data = city_data_list[0]
        
        for i in range(1, len(city_data_list)):
            comparison_data = pd.merge(
                comparison_data, 
                city_data_list[i], 
                on='date', 
                how='outer'
            )
        
        # 按日期排序
        comparison_data = comparison_data.sort_values('date')
        
        # 自动生成标题
        if title is None:
            if year is not None:
                title = f"{year}年多城市房价对比"
            else:
                title = "多城市房价对比"
        
        # 创建折线图
        fig = self.create_line_chart(
            data=comparison_data,
            x_col='date',
            y_cols=cities,
            line_names=cities,
            title=title,
            color_palette='tableau10',
            optimize_date_ticks=True,
            date_format_type='month_only',
            smooth_lines=smooth_lines,
            show_markers=show_markers,
            **kwargs
        )
        
        return fig
    
    def create_yearly_trend_chart(self,
                             cities: List[str] = None,
                             start_year: int = None,
                             end_year: int = None,
                             title: str = "年度房价趋势",
                             **kwargs) -> go.Figure:
        """
        创建年度房价趋势折线图
    
        参数:
        - cities: 城市名称列表（可选，不指定则使用所有城市）
        - start_year: 起始年份（可选）
        - end_year: 结束年份（可选）
       - title: 图表标题
        """
        if self._data is None:
            raise ValueError("未加载数据，请先加载数据")
    
        # 筛选数据
        trend_data = self._data.copy()
    
        # 筛选城市
        if cities:
            trend_data = trend_data[trend_data['city_name'].isin(cities)]
    
        # 筛选年份范围
        if start_year is not None:
            trend_data = trend_data[trend_data['year'] >= start_year]
        if end_year is not None:
            trend_data = trend_data[trend_data['year'] <= end_year]
    
        if trend_data.empty:
            raise ValueError("筛选条件无数据")
    
        # 按城市和年份分组
        yearly_data = trend_data.groupby(['city_name', 'year'])['year_avg_price'].mean().reset_index()
        yearly_data = yearly_data.sort_values(['year', 'city_name'])
    
        # 准备对比数据
        comparison_data = pd.DataFrame()
    
        for city in yearly_data['city_name'].unique():
            city_df = yearly_data[yearly_data['city_name'] == city][['year', 'year_avg_price']].copy()
            city_df = city_df.sort_values('year')
            city_df.rename(columns={'year_avg_price': city}, inplace=True)
        
            if comparison_data.empty:
                comparison_data = city_df
            else:
                comparison_data = pd.merge(comparison_data, city_df, on='year', how='outer')
    
        # 按年份排序
        comparison_data = comparison_data.sort_values('year')
    
        # 从 kwargs 中提取特定参数，避免重复传递
        show_markers = kwargs.pop('show_markers', True)
        smooth_lines = kwargs.pop('smooth_lines', True)
    
        # 创建折线图
        fig = self.create_line_chart(
            data=comparison_data,
            x_col='year',
            y_cols=list(yearly_data['city_name'].unique()),
            line_names=list(yearly_data['city_name'].unique()),
            title=title,
            color_palette='set2',
            optimize_date_ticks=False,  # 年份不需要特殊处理
            show_markers=show_markers,
            smooth_lines=smooth_lines,
            **kwargs  # 传递剩余的参数
        )
    
        return fig
    
    def create_city_price_comparison(self,
                               cities: List[str] = None,
                               year: Union[int, str] = None,
                               title: str = "城市房价对比",
                               **kwargs) -> go.Figure:
        """
        创建城市房价对比折线图（类似条形图的折线表示）
    
        参数:
        - cities: 城市名称列表（可选，不指定则使用所有城市）
        - year: 年份（可选）
        - title: 图表标题
        """
        if self._data is None:
            raise ValueError("未加载数据，请先加载数据")
    
        # 筛选数据
        plot_data = self._data.copy()
    
        # 筛选年份
        if year is not None:
            plot_data = plot_data[plot_data['year'] == year]
    
        # 筛选城市
        if cities:
            plot_data = plot_data[plot_data['city_name'].isin(cities)]
    
        if plot_data.empty:
            raise ValueError("筛选条件无数据")
    
        # 按城市分组计算平均价格
        city_avg = plot_data.groupby('city_name')['year_avg_price'].mean().reset_index()
        city_avg = city_avg.sort_values('year_avg_price', ascending=False)
    
        # 自动生成标题
        if year is not None:
            title = f"{year}年{title}"
    
        # 从 kwargs 中提取特定参数，避免重复传递
        show_markers = kwargs.pop('show_markers', True)
        smooth_lines = kwargs.pop('smooth_lines', False)
    
        # 创建折线图（将折线图用作条形图的替代）
        fig = self.create_line_chart(
            data=city_avg,
            x_col='city_name',
            y_cols=['year_avg_price'],
            line_names=['平均房价'],
            title=title,
            color_palette='category10',
            optimize_date_ticks=False,
            show_markers=show_markers,
            smooth_lines=smooth_lines,  # 对于分类数据，不使用平滑线条
            **kwargs  # 传递剩余的参数
        )
    
        return fig
    
    def create_multi_year_comparison(self,
                                city: str,
                                years: List[int] = None,
                                title: str = "多年度房价对比",
                                **kwargs) -> go.Figure:
        """
        创建单个城市多年度对比折线图
    
        参数:
        - city: 城市名称
        - years: 年份列表（可选）
        - title: 图表标题
        """
        if self._data is None:
            raise ValueError("未加载数据，请先加载数据")

        # 筛选城市数据
        city_data = self._data[self._data['city_name'] == city].copy()
    
        if city_data.empty:
            raise ValueError(f"未找到城市 '{city}' 的数据")
    
        # 筛选年份
        if years:
            city_data = city_data[city_data['year'].isin(years)]
    
        if city_data.empty:
            raise ValueError(f"未找到城市 '{city}' 在指定年份的数据")
    
        # 按年份和月份分组
        monthly_data = city_data.groupby(['year', 'month'])['month_avg_price'].mean().reset_index()
        monthly_data = monthly_data.sort_values(['year', 'month'])
    
        # 准备对比数据
        comparison_data = pd.DataFrame()
    
        for year_val in monthly_data['year'].unique():
            year_df = monthly_data[monthly_data['year'] == year_val][['month', 'month_avg_price']].copy()
            year_df = year_df.sort_values('month')
            year_df.rename(columns={'month_avg_price': f'{year_val}年'}, inplace=True)
        
            if comparison_data.empty:
                comparison_data = year_df
            else:
                comparison_data = pd.merge(comparison_data, year_df, on='month', how='outer')
    
        # 按月份排序
        comparison_data = comparison_data.sort_values('month')
    
        # 自动生成标题
        title = f"{city}多年度房价对比"
    
        # 从 kwargs 中提取特定参数，避免重复传递
        show_markers = kwargs.pop('show_markers', True)
        smooth_lines = kwargs.pop('smooth_lines', True)
    
        # 创建折线图
        fig = self.create_line_chart(
            data=comparison_data,
            x_col='month',
            y_cols=[f'{year}年' for year in monthly_data['year'].unique()],
            line_names=[f'{year}年' for year in monthly_data['year'].unique()],
            title=title,
            color_palette='set2',
            optimize_date_ticks=False,
            show_markers=show_markers,
            smooth_lines=smooth_lines,
            **kwargs  # 传递剩余的参数
        )
    
        return fig

    
    def _setup_date_axis(self, fig: go.Figure, dates: List[str], format_type: str = 'full_year_month'):
        """
        设置日期轴显示 - 修复版本
        
        参数:
        - fig: 图表对象
        - dates: 日期列表（字符串格式）
        - format_type: 日期格式类型
        """
        if not dates:
            return
        
        # 确保日期是字符串
        dates = [str(d) for d in dates]
        
        # 创建映射：日期 -> 格式化显示
        date_to_display = {}
        for date in dates:
            date_to_display[date] = self._format_date_for_display(date, format_type)
        
        # 创建刻度标签
        ticktext = []
        tickvals = []
        
        # 如果日期较少，全部显示
        if len(dates) <= 12:
            tickvals = dates
            ticktext = [date_to_display[d] for d in dates]
        else:
            # 日期较多，间隔显示
            step = max(1, len(dates) // 8)  # 最多显示8个刻度
            
            for i in range(0, len(dates), step):
                date = dates[i]
                tickvals.append(date)
                ticktext.append(date_to_display[date])
            
            # 确保显示最后一个日期
            if dates[-1] not in tickvals:
                tickvals.append(dates[-1])
                ticktext.append(date_to_display[dates[-1]])
        
        # 设置x轴配置
        fig.update_xaxes(
            type='category',  # 使用分类类型确保正确映射
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=45,
            tickfont=dict(
                size=self.default_styles['axis_tick_size'] - 2,
                family=self.default_styles['font_family']
            ),
            categoryorder='array',  # 保持原始顺序
            categoryarray=dates
        )
    
    def _get_colors(self, n: int, palette: str = 'category10') -> List[str]:
        """获取指定数量的颜色"""
        if palette in self.color_palettes:
            colors = self.color_palettes[palette]
        else:
            colors = self.color_palettes['category10']
        
        # 如果需要的颜色多于调色板中的颜色，则循环使用
        if n > len(colors):
            colors = colors * (n // len(colors) + 1)
        
        return colors[:n]
    
    def _apply_common_layout(self, fig: go.Figure, 
                           title: str, 
                           x_title: str, 
                           y_title: str,
                           show_legend: bool = True):
        """应用通用布局"""
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
                showgrid=True,
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
                showgrid=True,
                gridcolor=self.default_styles['grid_color'],
                linecolor='black',
                linewidth=1
            ),
            plot_bgcolor=self.default_styles['plot_bgcolor'],
            paper_bgcolor=self.default_styles['bg_color'],
            margin=dict(
                l=self.default_styles['margin']['l'],
                r=self.default_styles['margin']['r'],
                t=self.default_styles['margin']['t'] + 20,
                b=self.default_styles['margin']['b'] + 20
            ),
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
            )
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
        print()
        
        # 打印列的唯一值
        for col in ['city_name', 'year', 'month']:
            if col in self._data.columns:
                unique_vals = self._data[col].unique()
                print(f"{col} 的唯一值 ({len(unique_vals)}个): {sorted(unique_vals)[:10]}")
                if len(unique_vals) > 10:
                    print(f"   ... 还有 {len(unique_vals) - 10} 个值")
        
        # 打印价格统计信息
        for price_col in ['year_avg_price', 'month_avg_price']:
            if price_col in self._data.columns:
                print(f"{price_col} 统计:")
                print(f"  最小值: {self._data[price_col].min():.2f}")
                print(f"  最大值: {self._data[price_col].max():.2f}")
                print(f"  平均值: {self._data[price_col].mean():.2f}")
                print(f"  中位数: {self._data[price_col].median():.2f}")
        print("=" * 60)


# 主程序 - 使用TiDB数据库配置
if __name__ == "__main__":
    # 1. 数据库配置（与Bar.py相同）
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
    print("TiDB数据库折线图生成器")
    print("=" * 70)
    
    # 2. 初始化TiDB折线图构建器
    print("\n1. 连接到TiDB数据库...")
    builder = TiDBLineChartBuilder(db_config=DB_CONFIG)
    
    # 3. 加载数据（从trend表）
    print("\n2. 加载数据...")
    try:
        builder.load_trend_data(table_name="trend")
        builder.print_data_info()
    except Exception as e:
        print(f"加载数据失败: {e}")
        exit(1)
    
    # 4. 获取可用年份和城市
    available_years = builder.get_available_years()
    available_cities = builder.get_available_cities()
    print(f"\n可用年份: {available_years}")
    print(f"可用城市 ({len(available_cities)}个): {available_cities[:10]}...")
    
    # 5. 创建折线图（与Bar.py一样多的测试用例）
    print("\n3. 生成折线图（6个测试用例）...")
    
    # 5.1 单个城市月度房价趋势（北京）- 对应柱形图的单个城市条形图
    print("\n[折线图1] 北京月度房价趋势（2023年）")
    if '北京' in available_cities and 2023 in available_years:
        try:
            fig1 = builder.create_single_city_monthly_chart(
                city='北京',
                year=2025,
                title='北京2025年月度房价趋势',
                smooth_lines=True,
                show_markers=True
            )
            builder.show(fig1)
            builder.save(fig1,"北京2025年月度房价趋势折线图.html")
        except Exception as e:
            print(f"创建北京房价趋势图失败: {e}")
    else:
        print("北京或2023年数据不可用，跳过此图表")
    
    # 5.2 多个城市对比（最近年份）- 对应柱形图的月度对比图
    print("\n[折线图2] 主要城市月度房价对比")
    if available_years:
        latest_year = max(available_years)
        
        # 选择几个主要城市
        major_cities = ['北京', '上海', '深圳', '广州']
        cities_in_data = [city for city in major_cities if city in available_cities]
        
        if len(cities_in_data) >= 2:
            try:
                fig2 = builder.create_multi_city_comparison(
                    cities=cities_in_data,
                    year=latest_year,
                    title=f'{latest_year}年主要城市月度房价对比',
                    smooth_lines=True,
                    show_markers=True
                )
                builder.show(fig2)
                builder.save(fig2,"2025年主要城市月度房价对比折线图.html")
            except Exception as e:
                print(f"创建多城市对比图失败: {e}")
        else:
            print("可用的主要城市不足，跳过此图表")
    
    # 5.3 年度房价趋势图 - 对应柱形图的年度对比图
    print("\n[折线图3] 主要城市年度房价趋势")
    if len(available_years) >= 3:
        try:
            # 选择几个主要城市
            major_cities = ['北京', '上海', '深圳']
            cities_in_data = [city for city in major_cities if city in available_cities]
            
            if len(cities_in_data) >= 2:
                fig3 = builder.create_yearly_trend_chart(
                    cities=cities_in_data,
                    start_year=min(available_years),
                    end_year=max(available_years),
                    title='主要城市年度房价趋势',
                    smooth_lines=True,
                    show_markers=True
                )
                builder.show(fig3)
                builder.save(fig3,"主要城市年度房价趋势折线图.html")
        except Exception as e:
            print(f"创建年度趋势图失败: {e}")
    else:
        print("可用年份不足，跳过此图表")
    
    
    # 5.5 多年度对比图（单个城市）- 对应柱形图的不同年份对比
    print("\n[折线图5] 北京多年度房价对比")
    if '北京' in available_cities and len(available_years) >= 2:
        try:
            # 选择最近3个年份
            recent_years = sorted(available_years)[-5:] if len(available_years) >= 5 else available_years
            
            fig5 = builder.create_multi_year_comparison(
                city='北京',
                years=recent_years,
                title='北京多年度房价对比'
            )
            builder.show(fig5)
            builder.save(fig5,"北京多年度房价对比折线图.html")
        except Exception as e:
            print(f"创建多年度对比图失败: {e}")
    else:
        print("北京数据或可用年份不足，跳过此图表")
    
    # 5.6 完整数据多城市对比（所有年份）- 对应柱形图的完整对比
    print("\n[折线图6] 多城市完整数据对比")
    major_cities = ['北京', '上海', '深圳', '广州']
    cities_in_data = [city for city in major_cities if city in available_cities]
    
    if len(cities_in_data) >= 2:
        try:
            # 创建合并数据
            city_data_list = []
            
            for city in cities_in_data:
                city_df = builder.get_data()[builder.get_data()['city_name'] == city].copy()
                
                if not city_df.empty:
                    # 创建日期列
                    city_df['date'] = city_df.apply(
                        lambda row: f"{int(row['year'])}-{int(row['month']):02d}", 
                        axis=1
                    )
                    
                    # 按日期排序
                    city_df = city_df.sort_values(['year', 'month'])
                    
                    # 重命名列
                    city_df.rename(columns={'month_avg_price': city}, inplace=True)
                    city_df = city_df[['date', city]]
                    
                    city_data_list.append(city_df)
            
            if len(city_data_list) >= 2:
                # 合并数据
                comparison_data = city_data_list[0]
                for i in range(1, len(city_data_list)):
                    comparison_data = pd.merge(
                        comparison_data, 
                        city_data_list[i], 
                        on='date', 
                        how='outer'
                    )
                
                comparison_data = comparison_data.sort_values('date')
                
                # 创建折线图
                fig6 = builder.create_line_chart(
                    data=comparison_data,
                    x_col='date',
                    y_cols=cities_in_data,
                    line_names=cities_in_data,
                    title='多城市房价对比',
                    color_palette='set2',
                    optimize_date_ticks=True,
                    date_format_type='full_year_month',
                    smooth_lines=True,
                    show_markers=True
                )
                builder.show(fig6)
                builder.save(fig6,"多城市房价对比折线图.html")
        except Exception as e:
            print(f"创建完整对比图失败: {e}")
    else:
        print("可用的主要城市不足，跳过此图表")
    
    print("\n" + "=" * 70)
    print("折线图生成完成! 共生成6个测试图表")
    print("=" * 70)