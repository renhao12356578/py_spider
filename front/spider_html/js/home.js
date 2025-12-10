/**
 * 主页逻辑 - 全国房产数据总览
 * 房产数据分析系统
 */

// 全局变量
let chinaMapChart = null;
let trendChart = null;
let cityData = [];

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
  // 初始化图表
  initCharts();
  
  // 加载数据
  await Promise.all([
    loadOverviewData(),
    loadCityPrices(),
    loadRankingData('price'),
    loadProvinces(),
    loadTrendData()
  ]);
}

/**
 * 初始化图表实例
 */
function initCharts() {
  // 中国地图
  const mapContainer = document.getElementById('chinaMap');
  if (mapContainer) {
    chinaMapChart = echarts.init(mapContainer);
    
    // 响应式
    window.addEventListener('resize', () => {
      chinaMapChart.resize();
    });
    
    // 地图点击事件
    chinaMapChart.on('click', function(params) {
      if (params.name === '北京') {
        window.location.href = 'beijing.html';
      }
    });
  }
  
  // 趋势图
  const trendContainer = document.getElementById('trendChart');
  if (trendContainer) {
    trendChart = echarts.init(trendContainer);
    
    window.addEventListener('resize', () => {
      trendChart.resize();
    });
  }
}

/**
 * 加载概览数据
 */
async function loadOverviewData() {
  try {
    const data = await API.national.getOverview();
    
    // 更新统计卡片
    updateStatCard('statAvgPrice', formatNumber(data.national_avg_price));
    updateStatCard('statHighestPrice', formatNumber(data.highest_city?.price));
    updateStatCard('statLowestPrice', formatNumber(data.lowest_city?.price));
    updateStatCard('statTotalListings', formatLargeNumber(data.total_listings));
    
    // 更新城市名称
    document.getElementById('statHighestCity').innerHTML = 
      `<span style="color: var(--text-muted);">${data.highest_city?.name || '--'}</span>`;
    document.getElementById('statLowestCity').innerHTML = 
      `<span style="color: var(--text-muted);">${data.lowest_city?.name || '--'}</span>`;
    document.getElementById('statTotalCities').innerHTML = 
      `<span style="color: var(--text-muted);">覆盖 ${data.total_cities || '--'} 个城市</span>`;
      
  } catch (error) {
    console.error('加载概览数据失败:', error);
    showToast('加载数据失败，请刷新重试', 'error');
  }
}

/**
 * 加载城市房价数据
 */
async function loadCityPrices(params = {}) {
  try {
    const data = await API.national.getCityPrices(params);
    cityData = data.cities || [];
    
    // 更新地图
    if (chinaMapChart) {
      const option = Charts.getChinaMapOption(cityData);
      chinaMapChart.setOption(option);
    }
  } catch (error) {
    console.error('加载城市数据失败:', error);
  }
}

/**
 * 加载排行榜数据
 */
async function loadRankingData(type = 'price') {
  const rankingList = document.getElementById('rankingList');
  
  try {
    // 显示加载状态
    rankingList.innerHTML = `
      <div class="loading">
        <div class="loading-spinner"></div>
      </div>
    `;
    
    const data = await API.national.getRanking(type, 10);
    
    // 渲染排行榜
    renderRankingList(data.ranking || [], type);
    
  } catch (error) {
    console.error('加载排行榜失败:', error);
    rankingList.innerHTML = `
      <div class="empty-state">
        <i data-lucide="alert-circle"></i>
        <p>加载失败，请重试</p>
      </div>
    `;
    lucide.createIcons();
  }
}

/**
 * 渲染排行榜
 */
function renderRankingList(ranking, type) {
  const rankingList = document.getElementById('rankingList');
  
  if (!ranking.length) {
    rankingList.innerHTML = `
      <div class="empty-state">
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
    const changeIcon = item.change > 0 ? 'trending-up' : (item.change < 0 ? 'trending-down' : 'minus');
    
    let valueDisplay = '';
    let changeDisplay = '';
    
    if (type === 'price') {
      valueDisplay = `${formatNumber(item.value)} 元/㎡`;
    } else if (type === 'change') {
      valueDisplay = `${item.value > 0 ? '+' : ''}${item.value}%`;
      changeClass = item.value > 0 ? 'up' : 'down';
    } else if (type === 'rent_ratio') {
      valueDisplay = `${item.value}`;
    }
    
    html += `
      <div class="ranking-item" data-city="${item.city_name}">
        <div class="ranking-number">${index + 1}</div>
        <div class="ranking-info">
          <div class="ranking-city">${item.city_name}</div>
          <div class="ranking-province">${item.province_name || ''}</div>
        </div>
        <div class="ranking-value">
          <div class="ranking-price">${valueDisplay}</div>
        </div>
      </div>
    `;
  });
  
  rankingList.innerHTML = html;
  
  // 绑定点击事件
  rankingList.querySelectorAll('.ranking-item').forEach(item => {
    item.addEventListener('click', function() {
      const city = this.dataset.city;
      if (city === '北京') {
        window.location.href = 'beijing.html';
      }
    });
  });
}

/**
 * 加载省份列表
 */
async function loadProvinces() {
  try {
    const data = await API.national.getProvinces();
    const select = document.getElementById('provinceFilter');
    
    if (select && data.provinces) {
      data.provinces.forEach(province => {
        const option = document.createElement('option');
        option.value = province;
        option.textContent = province;
        select.appendChild(option);
      });
    }
  } catch (error) {
    console.error('加载省份列表失败:', error);
  }
}

/**
 * 加载趋势数据
 */
async function loadTrendData(city = '') {
  try {
    const data = await API.national.getTrend(city);
    
    if (trendChart && data.trends) {
      const option = Charts.getTrendLineOption(data.trends);
      trendChart.setOption(option);
    }
  } catch (error) {
    console.error('加载趋势数据失败:', error);
  }
}

/**
 * 绑定事件
 */
function bindEvents() {
  // 退出登录
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    Auth.logout();
  });
  
  // 排行榜标签切换
  document.querySelectorAll('.ranking-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      // 更新激活状态
      document.querySelectorAll('.ranking-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      
      // 加载对应数据
      loadRankingData(this.dataset.type);
    });
  });
  
  // 省份筛选
  document.getElementById('provinceFilter')?.addEventListener('change', function() {
    const province = this.value;
    loadCityPrices(province ? { province } : {});
  });
  
  // 价格区间筛选
  document.getElementById('priceRangeFilter')?.addEventListener('change', function() {
    const range = this.value;
    if (range) {
      const [min, max] = range.split('-').map(Number);
      loadCityPrices({ min_price: min, max_price: max });
    } else {
      loadCityPrices({});
    }
  });
  
  // 趋势图城市筛选
  document.getElementById('trendCityFilter')?.addEventListener('change', function() {
    loadTrendData(this.value);
  });
  
  // 搜索功能
  const searchInput = document.getElementById('citySearch');
  const searchDropdown = document.getElementById('searchDropdown');
  const searchBtn = document.getElementById('searchBtn');
  let searchTimeout = null;
  
  searchInput?.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const keyword = this.value.trim();
    
    if (keyword.length < 1) {
      searchDropdown.classList.remove('active');
      return;
    }
    
    searchTimeout = setTimeout(() => {
      searchCity(keyword);
    }, 300);
  });
  
  searchInput?.addEventListener('focus', function() {
    if (this.value.trim() && searchDropdown.innerHTML) {
      searchDropdown.classList.add('active');
    }
  });
  
  // 点击外部关闭下拉
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-container')) {
      searchDropdown?.classList.remove('active');
    }
  });
  
  searchBtn?.addEventListener('click', function() {
    const keyword = searchInput.value.trim();
    if (keyword) {
      searchCity(keyword);
    }
  });
}

/**
 * 搜索城市
 */
async function searchCity(keyword) {
  const searchDropdown = document.getElementById('searchDropdown');
  
  try {
    const data = await API.national.search(keyword);
    
    if (data.results && data.results.length) {
      let html = '';
      data.results.forEach(item => {
        html += `
          <div class="search-result-item" data-city="${item.city_name}">
            <div>
              <span class="search-result-city">${item.city_name}</span>
              <span class="search-result-province">${item.province_name}</span>
            </div>
            <span class="search-result-price">${formatNumber(item.city_avg_price)} 元/㎡</span>
          </div>
        `;
      });
      searchDropdown.innerHTML = html;
      searchDropdown.classList.add('active');
      
      // 绑定点击事件
      searchDropdown.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
          const city = this.dataset.city;
          if (city === '北京') {
            window.location.href = 'beijing.html';
          }
          searchDropdown.classList.remove('active');
        });
      });
    } else {
      searchDropdown.innerHTML = `
        <div class="search-result-item">
          <span style="color: var(--text-muted);">未找到相关城市</span>
        </div>
      `;
      searchDropdown.classList.add('active');
    }
  } catch (error) {
    console.error('搜索失败:', error);
  }
}

/**
 * 更新统计卡片
 */
function updateStatCard(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value || '--';
  }
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

