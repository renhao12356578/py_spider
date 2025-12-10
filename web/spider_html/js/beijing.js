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
  
  // 初始化第一个标签页的图表
  initDistrictCharts();
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
 * 初始化区域图表
 */
function initDistrictCharts() {
  const mapContainer = document.getElementById('districtMap');
  if (mapContainer) {
    districtMapChart = echarts.init(mapContainer);
    window.addEventListener('resize', () => districtMapChart?.resize());
  }
}

/**
 * 加载区域数据
 */
async function loadDistrictData() {
  try {
    // 加载排名数据
    const rankingData = await API.beijing.getDistrictRanking();
    renderDistrictList(rankingData.ranking || []);
    
    // 加载地图数据
    const pricesData = await API.beijing.getDistrictPrices();
    renderDistrictMap(pricesData.districts || []);
    
  } catch (error) {
    console.error('加载区域数据失败:', error);
    document.getElementById('districtList').innerHTML = `
      <div class="empty-result">
        <i data-lucide="alert-circle"></i>
        <p>加载失败，请刷新重试</p>
      </div>
    `;
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
          <div class="tooltip-title">${item.name}</div>
          <div class="tooltip-row">
            <span class="tooltip-label">均价</span>
            <span class="tooltip-value">${item.value?.toLocaleString()} 元/㎡</span>
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
 * 初始化分析图表
 */
function initAnalysisCharts() {
  const floorContainer = document.getElementById('floorChart');
  const layoutContainer = document.getElementById('layoutChart');
  const orientationContainer = document.getElementById('orientationChart');
  const elevatorContainer = document.getElementById('elevatorChart');
  
  if (floorContainer && !floorChart) {
    floorChart = echarts.init(floorContainer);
  }
  if (layoutContainer && !layoutChart) {
    layoutChart = echarts.init(layoutContainer);
  }
  if (orientationContainer && !orientationChart) {
    orientationChart = echarts.init(orientationContainer);
  }
  if (elevatorContainer && !elevatorChart) {
    elevatorChart = echarts.init(elevatorContainer);
  }
  
  window.addEventListener('resize', () => {
    floorChart?.resize();
    layoutChart?.resize();
    orientationChart?.resize();
    elevatorChart?.resize();
  });
}

/**
 * 加载分析数据
 */
async function loadAnalysisData() {
  initAnalysisCharts();
  
  try {
    // 并行加载所有分析数据
    const [floorData, layoutData, orientationData, elevatorData] = await Promise.all([
      API.beijing.getFloorAnalysis(),
      API.beijing.getLayoutAnalysis(),
      API.beijing.getOrientationAnalysis(),
      API.beijing.getElevatorAnalysis()
    ]);
    
    // 渲染楼层分析
    if (floorChart && floorData.floor_analysis) {
      const option = Charts.getBarChartOption(
        floorData.floor_analysis,
        'category',
        'avg_price'
      );
      floorChart.setOption(option);
    }
    
    // 渲染户型分析
    if (layoutChart && layoutData.layout_analysis) {
      const option = Charts.getBarChartOption(
        layoutData.layout_analysis,
        'layout',
        'avg_price'
      );
      layoutChart.setOption(option);
    }
    
    // 渲染朝向分析
    if (orientationChart && orientationData.orientation_analysis) {
      const option = Charts.getPieChartOption(
        orientationData.orientation_analysis,
        'orientation',
        'count'
      );
      orientationChart.setOption(option);
    }
    
    // 渲染电梯分析
    if (elevatorChart && elevatorData.elevator_analysis) {
      const data = elevatorData.elevator_analysis.map(item => ({
        name: item.has_elevator ? '有电梯' : '无电梯',
        value: item.avg_price,
        count: item.count
      }));
      const option = Charts.getBarChartOption(data, 'name', 'value');
      elevatorChart.setOption(option);
    }
    
  } catch (error) {
    console.error('加载分析数据失败:', error);
  }
}

/**
 * 初始化数据图表
 */
function initDataCharts() {
  const scatterContainer = document.getElementById('scatterChart');
  const boxplotContainer = document.getElementById('boxplotChart');
  
  if (scatterContainer && !scatterChart) {
    scatterChart = echarts.init(scatterContainer);
  }
  if (boxplotContainer && !boxplotChart) {
    boxplotChart = echarts.init(boxplotContainer);
  }
  
  window.addEventListener('resize', () => {
    scatterChart?.resize();
    boxplotChart?.resize();
  });
}

/**
 * 加载图表数据
 */
async function loadChartData(district = '') {
  initDataCharts();
  
  try {
    // 加载散点图数据
    const scatterData = await API.beijing.getScatterData({ district, limit: 500 });
    if (scatterChart && scatterData.points) {
      const option = Charts.getScatterChartOption(
        scatterData.points,
        'area',
        'total_price',
        'district'
      );
      scatterChart.setOption(option);
    }
    
    // 加载箱线图数据
    const boxplotData = await API.beijing.getBoxplotData();
    if (boxplotChart && boxplotData.boxplot) {
      const option = Charts.getBoxplotOption(boxplotData.boxplot);
      boxplotChart.setOption(option);
    }
    
  } catch (error) {
    console.error('加载图表数据失败:', error);
  }
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
  houses.forEach(house => {
    html += `
      <div class="house-item" data-house-id="${house.house_id}">
        <div class="house-image">
          <i data-lucide="home" style="width: 48px; height: 48px;"></i>
        </div>
        <div class="house-info">
          <div class="house-title">${house.region || '北京'} · ${house.layout || '暂无户型'}</div>
          <div class="house-meta">
            <span>${house.area || '-'}㎡</span>
            <span>${house.orientation || '-'}</span>
            <span>${house.floor || '-'}层</span>
            <span>${house.has_elevator || '-'}</span>
          </div>
          <div class="house-tags">
            ${house.tags ? house.tags.split(' ').map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
          </div>
        </div>
        <div class="house-price">
          <div class="house-total-price">${house.total_price?.toFixed(0) || '-'}<span>万</span></div>
          <div class="house-unit-price">${house.price_per_sqm?.toLocaleString() || '-'}元/㎡</div>
        </div>
      </div>
    `;
  });
  
  container.innerHTML = html;
  lucide.createIcons();
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
    <i data-lucide="chevron-left"></i>
  </button>`;
  
  // 页码
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);
  
  if (startPage > 1) {
    html += `<button class="page-btn" data-page="1">1</button>`;
    if (startPage > 2) {
      html += `<span class="text-muted">...</span>`;
    }
  }
  
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }
  
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span class="text-muted">...</span>`;
    }
    html += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
  }
  
  // 下一页
  html += `<button class="page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
    <i data-lucide="chevron-right"></i>
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
  
  // 散点图区域切换
  document.querySelectorAll('#tab-chart .chart-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      document.querySelectorAll('#tab-chart .chart-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      loadChartData(this.dataset.district);
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

