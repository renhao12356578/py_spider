/**
 * 北京页面逻辑 - 深度地区分析
 * 房产数据分析系统
 */

// 全局变量
let districtMapChart = null;
let floorChart = null;
let layoutChart = null;
let orientationChart = null;
let elevatorChart = null;
let scatterChart = null;
let boxplotChart = null;

// 分页状态
let currentPage = 1;
let pageSize = 20;
let totalHouses = 0;

// 当前筛选条件
let currentFilters = {};

document.addEventListener('DOMContentLoaded', function() {
  // 检查登录状态
  // if (!Auth.requireAuth()) return;
  
  // 更新用户显示
  updateUserDisplay();
  
  // 初始化页面
  initPage();
  
  // 绑定事件
  bindEvents();
});

/**
 * 更新用户显示
 */
function updateUserDisplay() {
  const user = Auth.getUser();
  const userDisplay = document.getElementById('userDisplay');
  if (user && userDisplay) {
    userDisplay.textContent = user.nickname || user.username || '用户';
  }
}

/**
 * 初始化页面
 */
async function initPage() {
  // 加载概览数据
  await loadOverviewData();
  
  // 加载区域数据
  await loadDistrictData();
}

/**
 * 加载概览数据
 */
async function loadOverviewData() {
  try {
    const data = await API.beijing.getOverview();
    
    document.getElementById('bjAvgPrice').textContent = formatNumber(data.avg_price);
    document.getElementById('bjAvgTotal').textContent = formatNumber(data.avg_total_price);
    document.getElementById('bjTotalCount').textContent = formatLargeNumber(data.total_listings);
    document.getElementById('bjHotDistrict').textContent = data.hot_districts?.[0] || '--';
    
  } catch (error) {
    console.error('加载概览数据失败:', error);
  }
}


/**
 * 加载区域数据
 */
async function loadDistrictData() {
  const rankingContainer = document.getElementById('districtList');
  const mapContainer = document.getElementById('districtMap');
  
  try {
    // ✅ 显示排名列表加载动画（使用 Spinner）
    if (rankingContainer) {
      rankingContainer.innerHTML = `
        <div class="loading">
          <div class="loading-spinner"></div>
          <p class="loading-text">加载区域排名...</p>
        </div>
      `;
    }
    
    // ✅ 显示地图加载动画（使用图表骨架屏）
    if (mapContainer && !mapContainer.dataset.initialized) {
      mapContainer.dataset.originalContent = mapContainer.innerHTML;
      mapContainer.innerHTML = `
        <div class="skeleton-chart">
          <div class="skeleton-chart-header">
            <div class="skeleton-chart-title"></div>
            <div class="skeleton-chart-legend">
              <div class="skeleton-chart-legend-item"></div>
              <div class="skeleton-chart-legend-item"></div>
              <div class="skeleton-chart-legend-item"></div>
            </div>
          </div>
          <div class="skeleton-chart-body"></div>
        </div>
      `;
    }
    
    // 并行加载排名和地图数据
    const [rankingData, pricesData] = await Promise.all([
      API.beijing.getDistrictRanking(),
      API.beijing.getDistrictPrices()
    ]);
    
    // ✅ 渲染排名列表
    renderDistrictList(rankingData.ranking || []);
    
    // ✅ 清除骨架屏并初始化图表
    if (mapContainer) {
      mapContainer.innerHTML = '';
      
      if (!districtMapChart) {
        districtMapChart = echarts.init(mapContainer);
        
        // 添加 resize 监听（仅一次）
        if (!window.districtMapResizeAdded) {
          window.addEventListener('resize', () => districtMapChart?.resize());
          window.districtMapResizeAdded = true;
        }
      }
      
      renderDistrictMap(pricesData.districts || []);
      mapContainer.dataset.initialized = 'true';
    }
    
  } catch (error) {
    console.error('加载区域数据失败:', error);
    
    if (rankingContainer) {
      rankingContainer.innerHTML = `
        <div class="chart-error">
          <i data-lucide="alert-circle"></i>
          <p>加载失败，请刷新重试</p>
        </div>
      `;
    }
    
    if (mapContainer) {
      mapContainer.innerHTML = `
        <div class="chart-error">
          <i data-lucide="alert-circle"></i>
          <p>加载失败，请刷新重试</p>
        </div>
      `;
    }
    
    lucide.createIcons();
  }
}

/**
 * 渲染区域列表
 */
function renderDistrictList(ranking) {
  const container = document.getElementById('districtList');
  
  if (!ranking.length) {
    container.innerHTML = `
      <div class="empty-result">
        <i data-lucide="inbox"></i>
        <p>暂无数据</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }
  
  let html = '';
  ranking.forEach((item, index) => {
    const changeClass = item.change > 0 ? 'up' : (item.change < 0 ? 'down' : '');
    const changeIcon = item.change > 0 ? '↑' : (item.change < 0 ? '↓' : '-');
    const changeValue = item.change ? `${changeIcon} ${Math.abs(item.change)}%` : '-';
    
    html += `
      <div class="district-item" data-district="${item.district}">
        <div class="district-rank">${index + 1}</div>
        <div class="district-info">
          <div class="district-name">${item.district}</div>
          <div class="district-count">${item.count ? item.count + '套房源' : ''}</div>
        </div>
        <div class="district-price">
          <div class="district-price-value">${formatNumber(item.avg_price)}元/㎡</div>
          <div class="district-price-change ${changeClass}">${changeValue}</div>
        </div>
      </div>
    `;
  });
  
  container.innerHTML = html;
}

/**
 * 渲染区域地图（使用柱状图代替）
 */
function renderDistrictMap(districts) {
  if (!districtMapChart) return;
  
  const data = districts.map(item => ({
    name: item.name,
    value: item.avg_price
  }));
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      padding: [12, 16],
      textStyle: {
        color: '#1f2937'
      },
      formatter: function(params) {
        const item = params[0];
        return `
          <div style="font-weight: 600; margin-bottom: 8px;">${item.name}</div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #6b7280;">均价</span>
            <span style="font-weight: 600; color: #2563eb;">${item.value?.toLocaleString()} 元/㎡</span>
          </div>
        `;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: {
        lineStyle: { color: '#e5e7eb' }
      },
      axisLabel: {
        color: '#6b7280',
        rotate: 45
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: {
        color: '#6b7280',
        formatter: value => (value / 10000).toFixed(0) + '万'
      },
      splitLine: {
        lineStyle: { color: '#f3f4f6', type: 'dashed' }
      }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value),
      barWidth: '60%',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#2563eb' },
            { offset: 1, color: '#7c3aed' }
          ]
        },
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#1d4ed8' },
              { offset: 1, color: '#6d28d9' }
            ]
          }
        }
      }
    }]
  };
  
  districtMapChart.setOption(option);
}

/**
 * 初始化分析图表 - 复用原有逻辑
 */
function initAnalysisCharts() {
  const containers = {
    floor: document.getElementById('floorChart'),
    layout: document.getElementById('layoutChart'),
    orientation: document.getElementById('orientationChart'),
    elevator: document.getElementById('elevatorChart')
  };
  
  // ✅ 为每个容器临时设置加载动画（使用骨架屏）
  Object.values(containers).forEach(container => {
    if (container && !container.dataset.initialized) {
      container.dataset.originalContent = container.innerHTML;
      container.innerHTML = `
        <div class="skeleton-chart">
          <div class="skeleton-chart-body"></div>
        </div>
      `;
    }
  });
}

/**
 * 加载分析数据 - 复用原有逻辑
 */
async function loadAnalysisData() {
  initAnalysisCharts();
  
  const containers = {
    floor: document.getElementById('floorChart'),
    layout: document.getElementById('layoutChart'),
    orientation: document.getElementById('orientationChart'),
    elevator: document.getElementById('elevatorChart')
  };
  
  try {
    // 并行加载所有分析数据
    const [floorData, layoutData, orientationData, elevatorData] = await Promise.all([
      API.beijing.getFloorAnalysis(),
      API.beijing.getLayoutAnalysis(),
      API.beijing.getOrientationAnalysis(),
      API.beijing.getElevatorAnalysis()
    ]);
    
    // ✅ 渲染楼层分析（清除骨架屏 + 初始化图表）
    if (containers.floor && floorData.floor_analysis) {
      containers.floor.innerHTML = '';
      if (!floorChart) {
        floorChart = echarts.init(containers.floor);
      }
      const option = Charts.getBarChartOption(
        floorData.floor_analysis,
        'category',
        'avg_price'
      );
      floorChart.setOption(option);
      containers.floor.dataset.initialized = 'true';
    }
    
    // ✅ 渲染户型分析
    if (containers.layout && layoutData.layout_analysis) {
      containers.layout.innerHTML = '';
      if (!layoutChart) {
        layoutChart = echarts.init(containers.layout);
      }
      const option = Charts.getBarChartOption(
        layoutData.layout_analysis,
        'layout',
        'avg_price'
      );
      layoutChart.setOption(option);
      containers.layout.dataset.initialized = 'true';
    }
    
    // ✅ 渲染朝向分析
    if (containers.orientation && orientationData.orientation_analysis) {
      containers.orientation.innerHTML = '';
      if (!orientationChart) {
        orientationChart = echarts.init(containers.orientation);
      }
      const option = Charts.getPieChartOption(
        orientationData.orientation_analysis,
        'orientation',
        'count'
      );
      orientationChart.setOption(option);
      containers.orientation.dataset.initialized = 'true';
    }
    
    // ✅ 渲染电梯分析
    if (containers.elevator && elevatorData.elevator_analysis) {
      containers.elevator.innerHTML = '';
      if (!elevatorChart) {
        elevatorChart = echarts.init(containers.elevator);
      }
      const data = elevatorData.elevator_analysis.map(item => ({
        name: item.has_elevator ? '有电梯' : '无电梯',
        value: item.avg_price,
        count: item.count
      }));
      const option = Charts.getBarChartOption(data, 'name', 'value');
      elevatorChart.setOption(option);
      containers.elevator.dataset.initialized = 'true';
    }
    
    // ✅ 添加窗口 resize 事件监听（仅一次）
    if (!window.beijingChartsResizeAdded) {
      window.addEventListener('resize', () => {
        floorChart?.resize();
        layoutChart?.resize();
        orientationChart?.resize();
        elevatorChart?.resize();
      });
      window.beijingChartsResizeAdded = true;
    }
    
  } catch (error) {
    console.error('加载分析数据失败:', error);
    
    // ✅ 显示错误提示
    Object.entries(containers).forEach(([key, container]) => {
      if (container) {
        container.innerHTML = '<div class="chart-error"><i data-lucide="alert-circle"></i><p>加载失败，请稍后重试</p></div>';
      }
    });
    lucide.createIcons();
  }
}

/**
 * 加载散点图 - 独立函数
 */
async function loadScatterChart(district = '') {
  const scatterContainer = document.getElementById('scatterChart');
  if (!scatterContainer) return;
  
  try {
    // 先销毁旧实例
    if (scatterChart) {
      scatterChart.dispose();
      scatterChart = null;
    }
    
    // 显示加载动画（使用骨架屏）
    scatterContainer.innerHTML = `
      <div class="skeleton-chart">
        <div class="skeleton-chart-body"></div>
      </div>
    `;
    
    // 请求数据
    const params = district ? { district } : { limit: 500 };
    console.log('📊 散点图请求参数:', params);
    
    const scatterData = await API.beijing.getScatterData(params);
    console.log('✅ 散点图数据加载成功，数据点数量:', scatterData.points?.length || 0);
    
    // 按区域分组数据
    const districtGroups = {};
    (scatterData.points || []).forEach(p => {
      const area = parseFloat(p.area) || 0;
      const totalPrice = parseFloat(p.total_price) || 0;
      const districtName = p.district || p.region || '未知区域';
      const layout = p.layout || '未知户型';
      
      if (!districtGroups[districtName]) {
        districtGroups[districtName] = [];
      }
      
      districtGroups[districtName].push([area, totalPrice, `${districtName} - ${layout}`]);
    });
    
    console.log('🎨 数据分组结果:', Object.keys(districtGroups).map(k => `${k}(${districtGroups[k].length})`));
    
    // 数据验证
    if (Object.keys(districtGroups).length === 0) {
      scatterContainer.innerHTML = `
        <div class="chart-error">
          <i data-lucide="inbox"></i>
          <p>暂无${district ? district + '区' : ''}散点图数据</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }
    
    // 定义区域颜色映射
    const districtColors = {
      '东城': '#FF6B6B', '西城': '#4ECDC4', '朝阳': '#45B7D1', '海淀': '#96CEB4',
      '丰台': '#FFEAA7', '石景山': '#DFE6E9', '门头沟': '#A29BFE', '房山': '#FD79A8',
      '通州': '#FDCB6E', '顺义': '#6C5CE7', '昌平': '#00B894', '大兴': '#E17055',
      '怀柔': '#74B9FF', '平谷': '#A29BFE', '密云': '#55EFC4', '延庆': '#FAB1A0'
    };
    
    // 清除加载动画后再初始化图表
    scatterContainer.innerHTML = '';
    scatterChart = echarts.init(scatterContainer);
    
    // 为每个区域创建一个 series
    const seriesList = Object.entries(districtGroups).map(([districtName, points]) => ({
      name: districtName,
      type: 'scatter',
      symbolSize: 8,
      data: points,
      itemStyle: {
        color: districtColors[districtName] || '#2563eb',
        opacity: 0.7
      },
      emphasis: {
        itemStyle: {
          opacity: 1,
          borderWidth: 2,
          borderColor: '#fff',
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.3)'
        }
      }
    }));
    
    const scatterOption = {
      title: { 
        text: district ? `${district} - 面积总价分布` : '全市面积总价分布', 
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 600, color: '#1f2937' }
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: { color: '#1f2937' },
        formatter: function(params) {
          const area = params.value[0] || 0;
          const totalPrice = params.value[1] || 0;
          const label = params.value[2] || '房源信息';
          
          return `
            <div style="font-weight: 600; margin-bottom: 8px;">${label}</div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">面积:</span>
              <span style="font-weight: 600;">${area.toFixed(2)}㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">总价:</span>
              <span style="font-weight: 600; color: #ef4444;">${totalPrice.toFixed(0)}万</span>
            </div>
          `;
        }
      },
      legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 10,
        top: 50,
        bottom: 20,
        data: Object.keys(districtGroups),
        textStyle: { fontSize: 12 },
        pageIconSize: 12,
        pageTextStyle: { fontSize: 12 }
      },
      grid: {
        left: '10%',
        right: district ? '4%' : '120px',
        bottom: '10%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '面积(㎡)',
        nameTextStyle: { color: '#6b7280', fontSize: 12 },
        axisLabel: { color: '#6b7280' },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
      },
      yAxis: {
        type: 'value',
        name: '总价(万)',
        nameTextStyle: { color: '#6b7280', fontSize: 12 },
        axisLabel: { color: '#6b7280' },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
      },
      series: seriesList
    };
    
    scatterChart.setOption(scatterOption);
    console.log('✅ 散点图渲染完成，共', seriesList.length, '个区域');
    
  } catch (error) {
    console.error('❌ 散点图加载失败:', error);
    scatterContainer.innerHTML = `
      <div class="chart-error">
        <i data-lucide="alert-circle"></i>
        <p>加载散点图失败</p>
        <p style="font-size:12px;color:#999;margin-top:8px;">
          ${error.message || '未知错误'}
        </p>
      </div>
    `;
    lucide.createIcons();
  }
}

/**
 * 加载箱线图 - 独立函数
 */
async function loadBoxplotChart() {
  const boxplotContainer = document.getElementById('boxplotChart');
  if (!boxplotContainer) return;
  
  // 如果已经初始化过,直接返回
  if (boxplotContainer.dataset.initialized === 'true') {
    console.log('ℹ️ 箱线图已加载,跳过重复加载');
    return;
  }
  
  try {
    // 显示加载动画（使用骨架屏）
    boxplotContainer.innerHTML = `
      <div class="skeleton-chart">
        <div class="skeleton-chart-body"></div>
      </div>
    `;
    
    const boxplotData = await API.beijing.getBoxplotData();
    console.log('✅ 箱线图数据加载成功');
    
    // 清除加载动画
    boxplotContainer.innerHTML = '';
    
    // 初始化图表实例
    if (!boxplotChart) {
      boxplotChart = echarts.init(boxplotContainer);
    }
    
    // 处理箱线图数据
    const districts = boxplotData.boxplot || [];
    const xAxisData = districts.map(d => d.district);
    const seriesData = districts.map(d => [
      parseFloat(d.min) || 0, 
      parseFloat(d.q1) || 0, 
      parseFloat(d.median) || 0, 
      parseFloat(d.q3) || 0, 
      parseFloat(d.max) || 0
    ]);
    
    const boxplotOption = {
      title: { 
        text: '各区房价分布箱线图', 
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 600, color: '#1f2937' }
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: { color: '#1f2937' },
        formatter: function(params) {
          const data = params.data;
          return `
            <div style="font-weight: 600; margin-bottom: 8px;">${params.name}</div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">最小值:</span>
              <span>${Math.round(data[1]).toLocaleString()}元/㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">下四分位:</span>
              <span>${Math.round(data[2]).toLocaleString()}元/㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">中位数:</span>
              <span style="font-weight: 600; color: #2563eb;">${Math.round(data[3]).toLocaleString()}元/㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">上四分位:</span>
              <span>${Math.round(data[4]).toLocaleString()}元/㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: #6b7280;">最大值:</span>
              <span>${Math.round(data[5]).toLocaleString()}元/㎡</span>
            </div>
          `;
        }
      },
      grid: {
        left: '10%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: { color: '#6b7280', rotate: 45 },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        name: '单价(元/㎡)',
        nameTextStyle: { color: '#6b7280', fontSize: 12 },
        axisLabel: { 
          color: '#6b7280',
          formatter: value => (value / 10000).toFixed(0) + '万'
        },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
      },
      series: [{
        name: '房价分布',
        type: 'boxplot',
        data: seriesData,
        itemStyle: {
          color: '#2563eb',
          borderColor: '#1d4ed8',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            color: '#1d4ed8',
            borderColor: '#1e40af',
            borderWidth: 3
          }
        }
      }]
    };
    
    boxplotChart.setOption(boxplotOption);
    boxplotContainer.dataset.initialized = 'true';
    console.log('✅ 箱线图渲染完成');
    
  } catch (error) {
    console.error('❌ 箱线图加载失败:', error);
    boxplotContainer.innerHTML = `
      <div class="chart-error">
        <i data-lucide="alert-circle"></i>
        <p>加载箱线图失败</p>
        <p style="font-size:12px;color:#999;margin-top:8px;">
          ${error.message || '未知错误'}
        </p>
      </div>
    `;
    lucide.createIcons();
  }
}

/**
 * 加载图表数据 - 调用独立函数
 */
async function loadChartData(district = '') {
  // 添加 resize 事件监听（仅一次）
  if (!window.beijingDataChartsResizeAdded) {
    window.addEventListener('resize', () => {
      scatterChart?.resize();
      boxplotChart?.resize();
    });
    window.beijingDataChartsResizeAdded = true;
  }
  
  // 并行加载散点图和箱线图
  await Promise.all([
    loadScatterChart(district),
    loadBoxplotChart()
  ]);
}

/**
 * 加载房源列表
 */
async function loadHouseList(page = 1) {
  const container = document.getElementById('houseList');
  currentPage = page;
  
  try {
    container.innerHTML = `
      <div class="loading">
        <div class="loading-spinner"></div>
        <p class="loading-text">加载房源列表...</p>
      </div>
    `;
    
    const params = {
      ...currentFilters,
      page: page,
      page_size: pageSize
    };
    
    const data = await API.beijing.getHouses(params);
    totalHouses = data.total || 0;
    
    renderHouseList(data.houses || []);
    renderPagination();
    
  } catch (error) {
    console.error('加载房源列表失败:', error);
    container.innerHTML = `
      <div class="empty-result">
        <i data-lucide="alert-circle"></i>
        <h4>加载失败</h4>
        <p>请刷新页面重试</p>
      </div>
    `;
    lucide.createIcons();
  }
}

/**
 * 渲染房源列表
 */
function renderHouseList(houses) {
  const container = document.getElementById('houseList');
  
  if (!houses.length) {
    container.innerHTML = `
      <div class="empty-result">
        <i data-lucide="home"></i>
        <h4>暂无房源</h4>
        <p>请调整筛选条件</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }
  
  let html = '';
  houses.forEach((house, index) => {
    // 模拟一些状态标签
    const badges = [];
    if (index < 3 && currentPage === 1) badges.push('<div class="house-badge hot">热门</div>');
    else if (index % 5 === 0) badges.push('<div class="house-badge new">新上</div>');
    
    html += `
      <div class="house-item" data-house-id="${house.house_id}">
        <div class="house-image">
          ${badges.join('')}
          <i data-lucide="home" style="width: 56px; height: 56px;"></i>
        </div>
        
        <div class="house-info">
          <div class="house-title">${house.region || '北京'} · ${house.layout || '暂无户型'}</div>
          
          <div class="house-meta">
            <div class="meta-item">
              <i data-lucide="maximize-2"></i>
              <span>${house.area || '-'}㎡</span>
            </div>
            <div class="meta-item">
              <i data-lucide="compass"></i>
              <span>${house.orientation || '-'}</span>
            </div>
            <div class="meta-item">
              <i data-lucide="layers"></i>
              <span>${house.floor || '-'}层</span>
            </div>
            <div class="meta-item">
              <i data-lucide="move-vertical"></i>
              <span>${house.has_elevator || '-'}</span>
            </div>
          </div>
          
          <div class="house-tags">
            ${house.tags ? house.tags.split(' ').map(tag => `<span class="tag tag-primary">${tag}</span>`).join('') : ''}
          </div>
        </div>
        
        <div class="house-price">
          <div class="house-total-price">${house.total_price?.toFixed(0) || '-'}<span class="price-unit">万</span></div>
          <div class="house-unit-price">${house.price_per_sqm?.toLocaleString() || '-'} 元/㎡</div>
        </div>
        
        <div class="house-actions">
          <button class="action-btn favorite-btn" title="收藏房源">
            <i data-lucide="heart"></i>
          </button>
          <button class="action-btn" title="对比房源">
            <i data-lucide="repeat"></i>
          </button>
        </div>
      </div>
    `;
  });
  
  container.innerHTML = html;
  lucide.createIcons();
  
  // 绑定收藏按钮事件
  container.querySelectorAll('.favorite-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      this.classList.toggle('active');
      const icon = this.querySelector('i');
      if (this.classList.contains('active')) {
        icon.style.fill = 'var(--danger-color)';
        showToast('已加入收藏', 'success');
      } else {
        icon.style.fill = 'none';
        showToast('已取消收藏');
      }
    });
  });
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

/**
 * 渲染分页
 */
function renderPagination() {
  const container = document.getElementById('pagination');
  const totalPages = Math.ceil(totalHouses / pageSize);
  
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }
  
  let html = '';
  
  // 上一页
  html += `<button class="page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
    <i data-lucide="chevron-left" style="width: 16px; height: 16px;"></i>
  </button>`;
  
  // 页码
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);
  
  if (startPage > 1) {
    html += `<button class="page-btn" data-page="1">1</button>`;
    if (startPage > 2) {
      html += `<span style="color: var(--text-muted);">...</span>`;
    }
  }
  
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }
  
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span style="color: var(--text-muted);">...</span>`;
    }
    html += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
  }
  
  // 下一页
  html += `<button class="page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
    <i data-lucide="chevron-right" style="width: 16px; height: 16px;"></i>
  </button>`;
  
  container.innerHTML = html;
  lucide.createIcons();
  
  // 绑定分页事件
  container.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      if (!this.disabled) {
        loadHouseList(parseInt(this.dataset.page));
      }
    });
  });
}

/**
 * 绑定事件
 */
function bindEvents() {
  // 退出登录
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    Auth.logout();
  });
  
  // 标签页切换
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const tabId = this.dataset.tab;
      
      // 更新激活状态
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      // 切换内容
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById(`tab-${tabId}`).classList.add('active');
      
      // 按需加载数据
      loadTabData(tabId);
    });
  });
  
  // AI 推荐表单
  bindRecommendForm();
  
  // AI 对话
  bindChatEvents();
  
  // 房源筛选
  document.getElementById('filterSearchBtn')?.addEventListener('click', () => {
    currentFilters = {
      district: document.getElementById('houseDistrictFilter').value,
      layout: document.getElementById('houseLayoutFilter').value
    };
    
    const priceRange = document.getElementById('housePriceFilter').value;
    if (priceRange) {
      const [min, max] = priceRange.split('-').map(Number);
      currentFilters.min_price = min;
      currentFilters.max_price = max;
    }
    
    loadHouseList(1);
  });
  
  // ✅ 散点图区域切换事件
  document.querySelectorAll('#tab-chart .chart-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      document.querySelectorAll('#tab-chart .chart-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      const district = this.dataset.district || '';
      loadScatterChart(district); // ✅ 只重新加载散点图
    });
  });
}

/**
 * 按需加载标签页数据
 */
const loadedTabs = new Set(['district']);

function loadTabData(tabId) {
  if (loadedTabs.has(tabId)) return;
  loadedTabs.add(tabId);
  
  switch (tabId) {
    case 'analysis':
      loadAnalysisData();
      break;
    case 'chart':
      loadChartData();
      break;
    case 'list':
      loadHouseList(1);
      break;
  }
}

/**
 * 绑定 AI 推荐表单
 */
function bindRecommendForm() {
  // 选项按钮组
  document.querySelectorAll('.option-group').forEach(group => {
    group.querySelectorAll('.option-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        // 切换选中状态
        group.querySelectorAll('.option-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
      });
    });
  });
  
  // 表单提交
  document.getElementById('recommendForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const params = {
      budget_min: parseInt(document.getElementById('budgetMin').value) || undefined,
      budget_max: parseInt(document.getElementById('budgetMax').value) || undefined,
      district: document.querySelector('#districtOptions .option-btn.active')?.dataset.value || undefined,
      layout: document.querySelector('#layoutOptions .option-btn.active')?.dataset.value || undefined,
      area_min: parseInt(document.getElementById('areaMin').value) || undefined,
      area_max: parseInt(document.getElementById('areaMax').value) || undefined,
      floor_pref: document.querySelector('#floorOptions .option-btn.active')?.dataset.value || undefined
    };
    
    // 清理空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key];
      }
    });
    
    const resultContainer = document.getElementById('recommendList');
    const resultCount = document.getElementById('resultCount');
    
    try {
      resultContainer.innerHTML = `
        <div class="loading">
          <div class="loading-spinner"></div>
          <p class="loading-text">AI 正在推荐...</p>
        </div>
      `;
      
      const data = await AIService.recommend(params);
      
      resultCount.innerHTML = `共找到 <span>${data.total_matched || 0}</span> 套匹配房源`;
      resultContainer.innerHTML = AIService.formatRecommendations(data.recommendations);
      lucide.createIcons();
      
    } catch (error) {
      resultContainer.innerHTML = `
        <div class="empty-result">
          <i data-lucide="alert-circle"></i>
          <h4>推荐失败</h4>
          <p>${error.message || '请稍后重试'}</p>
        </div>
      `;
      lucide.createIcons();
    }
  });
}

/**
 * 绑定 AI 对话事件
 */
function bindChatEvents() {
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  const messagesContainer = document.getElementById('chatMessages');
  
  // 发送消息
  async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // 显示用户消息
    messagesContainer.innerHTML += AIService.formatChatMessage('user', message);
    chatInput.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // 禁用发送按钮
    sendBtn.disabled = true;
    
    try {
      const data = await AIService.chat(message);
      messagesContainer.innerHTML += AIService.formatChatMessage('assistant', data.reply);
      
    } catch (error) {
      messagesContainer.innerHTML += AIService.formatChatMessage(
        'assistant',
        '抱歉，我遇到了一些问题，请稍后再试。'
      );
    }
    
    sendBtn.disabled = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    lucide.createIcons();
  }
  
  sendBtn?.addEventListener('click', sendMessage);
  
  chatInput?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
  
  // 快捷问题
  document.querySelectorAll('.quick-question').forEach(btn => {
    btn.addEventListener('click', function() {
      chatInput.value = this.dataset.question;
      sendMessage();
    });
  });
}

/**
 * 格式化数字
 */
function formatNumber(num) {
  if (!num && num !== 0) return '--';
  return num.toLocaleString();
}

/**
 * 格式化大数字
 */
function formatLargeNumber(num) {
  if (!num && num !== 0) return '--';
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  }
  return num.toLocaleString();
}

