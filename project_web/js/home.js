/**
 * 主页逻辑 - 全国房产数据总览
 * 房产数据分析系统
 */

// 全局变量
let chinaMapChart = null;
let trendChart = null;
let cityData = [];
let provincePopupChart = null;
let provincePopup = null;
let hoverTimeout = null;

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
  // 加载系统配置
  await loadSystemConfig();
  
  // 初始化图表
  initCharts();
  
  // 加载数据
  await Promise.all([
    loadOverviewData(),
    loadCityPrices(),
    loadRankingData('price'),
    loadProvinces(),
    loadTrendData("", "2025")
  ]);
}

/**
 * 加载系统配置
 */
async function loadSystemConfig() {
  try {
    const config = await API.system.getConfig();
    
    // 存储配置供其他模块使用
    window.appConfig = config;
    
    // 可以根据配置显示/隐藏功能
    if (config.features) {
      // 例如：根据配置控制 AI 聊天功能
      if (!config.features.ai_chat) {
        document.querySelector('[href="beijing.html"]')?.classList.add('disabled');
      }
    }
    
    console.log('系统配置加载完成:', config);
  } catch (error) {
    console.error('加载系统配置失败:', error);
    // 配置加载失败不影响主流程
  }
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
    
    // 地图悬停事件
    chinaMapChart.on('mouseover', function(params) {
      if (params.componentType === 'series' && params.seriesType === 'map') {
        clearTimeout(hoverTimeout);
        hoverTimeout = setTimeout(() => {
          showProvincePopup(params.name, params.event.event);
        }, 300);
      }
    });
    
    chinaMapChart.on('mouseout', function(params) {
      clearTimeout(hoverTimeout);
      hoverTimeout = setTimeout(() => {
        hideProvincePopup();
      }, 200);
    });
    
    // 初始化弹窗
    provincePopup = document.getElementById('provincePopup');
    const popupChartContainer = document.getElementById('popupChart');
    if (popupChartContainer) {
      provincePopupChart = echarts.init(popupChartContainer);
    }
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
        <p class="loading-text">加载排行榜数据...</p>
      </div>
    `;
    
    const data = await API.national.getRanking(type, 10);
    //printf('加载排行榜数据:', data.ranking);
    
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
    // ✅ 修复：根据 type 决定如何计算样式类
    let changeClass, valueDisplay;
    
    if (type === 'price') {
      // 房价排行：使用 item.change
      changeClass = item.change > 0 ? 'up' : (item.change < 0 ? 'down' : '');
      valueDisplay = `${formatNumber(item.value)} 元/㎡`;
    } else if (type === 'change') {
      // 涨幅排行：使用 item.value
      changeClass = item.value > 0 ? 'up' : (item.value < 0 ? 'down' : '');
      valueDisplay = `${item.value > 0 ? '+' : ''}${item.value}%`;
    } else if (type === 'rent_ratio') {
      // 租售比排行
      changeClass = '';
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
          <div class="ranking-price ${changeClass}">${valueDisplay}</div>
        </div>
      </div>
    `;
  });
  
  rankingList.innerHTML = html;
  lucide.createIcons();
  
  // 绑定点击事件
  rankingList.querySelectorAll('.ranking-item').forEach(item => {
    item.addEventListener('click', function(e) {
      const city = this.dataset.city;
      if (city === '北京') {
        window.location.href = 'beijing.html';
      }
    });
  });
  
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
  // 移除已存在的 toast
  const existingToast = document.querySelector('.toast-message');
  if (existingToast) existingToast.remove();
  
  const toast = document.createElement('div');
  toast.className = `toast-message toast-${type}`;
  
  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ'
  };
  
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-text">${message}</span>
  `;
  
  document.body.appendChild(toast);
  
  // 动画显示
  setTimeout(() => toast.classList.add('show'), 10);
  
  // 3秒后自动消失
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2500);
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
async function loadTrendData(city = '', year = '') {
  try {
    console.log('📈 加载趋势数据:', { city, year });
    
    const data = await API.national.getTrend(city, year);
    
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
  
  // ✅ 趋势图城市筛选
  document.getElementById('trendCityFilter')?.addEventListener('change', function() {
    const city = this.value;
    const year = document.getElementById('trendYearFilter')?.value || '';
    loadTrendData(city, year);
  });
  
  // ✅ 新增：趋势图年份筛选
  document.getElementById('trendYearFilter')?.addEventListener('change', function() {
    const city = document.getElementById('trendCityFilter')?.value || '';
    const year = this.value;
    console.log('🔍 切换年份:', year);
    loadTrendData(city, year);
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
 * 显示省份悬停弹窗
 */
function showProvincePopup(provinceName, mouseEvent) {
  if (!provincePopup || !provinceName) return;
  
  // 获取该省的城市数据
  const provinceCities = cityData.filter(city => city.province_name === provinceName);
  
  if (provinceCities.length === 0) {
    return;
  }
  
  // 计算统计数据(使用加权平均)
  const totalListings = provinceCities.reduce((sum, city) => sum + (city.listing_count || 0), 0);
  const totalPrice = provinceCities.reduce((sum, city) => 
    sum + (city.city_avg_price * (city.listing_count || 0)), 0
  );
  const avgPrice = totalListings > 0 ? Math.round(totalPrice / totalListings) : 0;
  
  // 获取主要城市(按房价排序,取前5个)
  const topCities = provinceCities
    .sort((a, b) => b.city_avg_price - a.city_avg_price)
    .slice(0, 5)
    .map(c => c.city_name);
  
  // 更新弹窗内容
  document.getElementById('popupProvinceName').textContent = provinceName;
  document.getElementById('popupAvgPrice').textContent = formatNumber(avgPrice) + ' 元/㎡';
  document.getElementById('popupListingCount').textContent = formatLargeNumber(totalListings) + ' 套';
  document.getElementById('popupCityCount').textContent = provinceCities.length + ' 个';
  document.getElementById('popupCities').textContent = '主要: ' + topCities.join('、');
  
  // 渲染城市热力图
  renderProvinceCityHeatmap(provinceCities, provinceName);
  
  // 定位弹窗
  const x = mouseEvent.clientX || mouseEvent.pageX;
  const y = mouseEvent.clientY || mouseEvent.pageY;
  
  provincePopup.style.left = (x + 20) + 'px';
  provincePopup.style.top = (y - 100) + 'px';
  
  // 显示弹窗
  provincePopup.classList.add('active');
}

/**
 * 隐藏省份悬停弹窗
 */
function hideProvincePopup() {
  if (provincePopup) {
    provincePopup.classList.remove('active');
  }
}

/**
 * 渲染省份城市热力图(省级地图+散点)
 */
function renderProvinceCityHeatmap(cities, provinceName) {
  if (!provincePopupChart || cities.length === 0) return;
  
  // 省份名称映射(ECharts地图名称)
  const provinceMapNames = {
    '北京': 'beijing', '天津': 'tianjin', '河北': 'hebei', '山西': 'shanxi',
    '内蒙古': 'neimenggu', '辽宁': 'liaoning', '吉林': 'jilin', '黑龙江': 'heilongjiang',
    '上海': 'shanghai', '江苏': 'jiangsu', '浙江': 'zhejiang', '安徽': 'anhui',
    '福建': 'fujian', '江西': 'jiangxi', '山东': 'shandong', '河南': 'henan',
    '湖北': 'hubei', '湖南': 'hunan', '广东': 'guangdong', '广西': 'guangxi',
    '海南': 'hainan', '重庆': 'chongqing', '四川': 'sichuan', '贵州': 'guizhou',
    '云南': 'yunnan', '西藏': 'xizang', '陕西': 'shanxi1', '甘肃': 'gansu',
    '青海': 'qinghai', '宁夏': 'ningxia', '新疆': 'xinjiang', '台湾': 'taiwan',
    '香港': 'xianggang', '澳门': 'aomen'
  };
  
  const mapName = provinceMapNames[provinceName];
  
  // 如果没有对应的省级地图,使用散点图
  if (!mapName) {
    renderCityScatterChart(cities);
    return;
  }
  
  // 动态加载省级地图
  const mapUrl = `https://geo.datav.aliyun.com/areas_v3/bound/${mapName}_full.json`;
  
  fetch(mapUrl)
    .then(response => response.json())
    .then(geoJson => {
      // 注册省级地图
      echarts.registerMap(mapName, geoJson);
      
      // 准备散点数据
      const scatterData = cities.map(city => ({
        name: city.city_name,
        value: [0, 0, city.city_avg_price],
        itemStyle: {
          color: getPriceColor(city.city_avg_price)
        }
      }));
      
      const option = {
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 12
          },
          formatter: function(params) {
            if (params.seriesType === 'scatter') {
              return `${params.name}<br/>房价: ${params.value[2].toLocaleString()} 元/㎡`;
            }
            return params.name;
          }
        },
        geo: {
          map: mapName,
          roam: false,
          itemStyle: {
            areaColor: '#f0f9ff',
            borderColor: '#93c5fd',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              areaColor: '#dbeafe'
            }
          }
        },
        series: [{
          type: 'scatter',
          coordinateSystem: 'geo',
          data: scatterData,
          symbolSize: function(val) {
            return Math.max(8, Math.min(20, val[2] / 3000));
          },
          label: {
            show: true,
            formatter: '{b}',
            position: 'right',
            fontSize: 10,
            color: '#374151'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 11,
              fontWeight: 'bold'
            },
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          }
        }]
      };
      
      provincePopupChart.setOption(option, true);
    })
    .catch(error => {
      console.error('加载省级地图失败:', error);
      // 降级为散点图
      renderCityScatterChart(cities);
    });
}

/**
 * 降级方案: 渲染城市散点图(无地图)
 */
function renderCityScatterChart(cities) {
  if (!provincePopupChart || cities.length === 0) return;
  
  // 按房价排序
  const sortedCities = cities.sort((a, b) => b.city_avg_price - a.city_avg_price);
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#1f2937',
        fontSize: 12
      },
      formatter: function(params) {
        return `${params.name}<br/>房价: ${params.value.toLocaleString()} 元/㎡`;
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedCities.map(c => c.city_name),
      axisLabel: {
        rotate: 45,
        fontSize: 10,
        color: '#6b7280'
      },
      axisLine: { lineStyle: { color: '#e5e7eb' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: v => (v / 10000).toFixed(0) + '万',
        fontSize: 10,
        color: '#6b7280'
      },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    series: [{
      type: 'scatter',
      data: sortedCities.map(c => c.city_avg_price),
      symbolSize: function(val) {
        return Math.max(10, Math.min(25, val / 2000));
      },
      itemStyle: {
        color: function(params) {
          return getPriceColor(params.value);
        },
        shadowBlur: 5,
        shadowColor: 'rgba(0, 0, 0, 0.2)'
      },
      label: {
        show: true,
        formatter: function(params) {
          return (params.value / 10000).toFixed(1) + '万';
        },
        position: 'top',
        fontSize: 9,
        color: '#6b7280'
      }
    }]
  };
  
  provincePopupChart.setOption(option, true);
}

/**
 * 根据房价获取颜色
 */
function getPriceColor(price) {
  if (price < 8000) return '#10b981';
  if (price < 12000) return '#84cc16';
  if (price < 18000) return '#eab308';
  if (price < 25000) return '#f59e0b';
  if (price < 35000) return '#ef4444';
  return '#dc2626';
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

