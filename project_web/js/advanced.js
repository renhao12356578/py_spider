/**
 * 高级分析页面逻辑
 */

let charts = {};

document.addEventListener('DOMContentLoaded', () => {
  updateUserDisplay();
  initTabs();
  initFilters();
  bindEvents();
  loadAllData();
});

function updateUserDisplay() {
  const user = Auth.getUser();
  const userDisplay = document.getElementById('userDisplay');
  if (user && userDisplay) {
    userDisplay.textContent = user.nickname || user.username || '用户';
  }
}

function bindEvents() {
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    Auth.logout();
  });
}

function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;
      
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      btn.classList.add('active');
      document.getElementById(`${tabName}Tab`).classList.add('active');
      
      resizeCharts();
    });
  });
}

function initFilters() {
  document.getElementById('heatmapCityFilter')?.addEventListener('input', debounce(loadDistrictHeatmap, 500));
  document.getElementById('listingRankingLimit')?.addEventListener('change', loadListingRanking);
  document.getElementById('districtRankingCityFilter')?.addEventListener('input', debounce(loadDistrictPriceRanking, 500));
  document.getElementById('districtRankingLimit')?.addEventListener('change', loadDistrictPriceRanking);
  document.getElementById('cityDistrictsBtn')?.addEventListener('click', loadCityDistricts);
  document.getElementById('districtChangeOrder')?.addEventListener('change', loadDistrictChangeRanking);
  document.getElementById('districtChangeLimit')?.addEventListener('change', loadDistrictChangeRanking);
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

async function loadAllData() {
  await Promise.all([
    loadCityClustering(),
    loadDistrictHeatmap(),
    loadListingRanking(),
    loadDistrictPriceRanking(),
    loadDistrictChangeRanking()
  ]);
}

async function loadCityClustering() {
  const chartDom = document.getElementById('cityClusteringChart');
  if (!chartDom) return;
  
  try {
    showLoading(chartDom);
    const data = await API.national.getCityClustering();
    
    if (!charts.clustering) {
      charts.clustering = echarts.init(chartDom);
    }
    
    const option = Charts.getCityClusteringOption(data.cities);
    charts.clustering.setOption(option);
    hideLoading(chartDom);
  } catch (error) {
    console.error('加载城市分级数据失败:', error);
    showError(chartDom, '加载失败，请稍后重试');
  }
}

async function loadDistrictHeatmap() {
  const chartDom = document.getElementById('districtHeatmapChart');
  if (!chartDom) return;
  
  try {
    showLoading(chartDom);
    const city = document.getElementById('heatmapCityFilter')?.value || '';
    const data = await API.national.getDistrictHeatmap(city);
    
    if (!charts.heatmap) {
      charts.heatmap = echarts.init(chartDom);
    }
    
    const option = Charts.getDistrictHeatmapOption(data.heatmap);
    charts.heatmap.setOption(option);
    hideLoading(chartDom);
  } catch (error) {
    console.error('加载区县热力图数据失败:', error);
    showError(chartDom, '加载失败，请稍后重试');
  }
}

async function loadListingRanking() {
  try {
    const limit = parseInt(document.getElementById('listingRankingLimit')?.value || 20);
    const data = await API.national.getListingRanking(limit);
    const chartDom = document.getElementById('listingRankingChart');
    if (!chartDom) return;
    
    if (!charts.listingRanking) {
      charts.listingRanking = echarts.init(chartDom);
    }
    
    const option = Charts.getListingRankingOption(data.ranking);
    charts.listingRanking.setOption(option);
  } catch (error) {
    console.error('加载挂牌量排行数据失败:', error);
  }
}

async function loadDistrictPriceRanking() {
  try {
    const limit = parseInt(document.getElementById('districtRankingLimit')?.value || 50);
    const city = document.getElementById('districtRankingCityFilter')?.value || '';
    const data = await API.national.getDistrictPriceRanking(limit, city);
    const chartDom = document.getElementById('districtPriceRankingChart');
    if (!chartDom) return;
    
    if (!charts.districtPriceRanking) {
      charts.districtPriceRanking = echarts.init(chartDom);
    }
    
    const option = Charts.getDistrictPriceRankingOption(data.ranking);
    charts.districtPriceRanking.setOption(option);
  } catch (error) {
    console.error('加载区县价格排行数据失败:', error);
  }
}

async function loadCityDistricts() {
  try {
    const city = document.getElementById('cityDistrictsInput')?.value?.trim();
    if (!city) {
      alert('请输入城市名称');
      return;
    }
    
    const data = await API.national.getCityDistricts(city);
    const chartDom = document.getElementById('cityDistrictsChart');
    if (!chartDom) return;
    
    if (!charts.cityDistricts) {
      charts.cityDistricts = echarts.init(chartDom);
    }
    
    const option = Charts.getCityDistrictsOption(data.districts, data.city_name);
    charts.cityDistricts.setOption(option);
  } catch (error) {
    console.error('加载同城区县对比数据失败:', error);
    alert('查询失败，请检查城市名称是否正确');
  }
}

async function loadDistrictChangeRanking() {
  try {
    const limit = parseInt(document.getElementById('districtChangeLimit')?.value || 30);
    const order = document.getElementById('districtChangeOrder')?.value || 'desc';
    const data = await API.national.getDistrictChangeRanking(limit, order);
    const chartDom = document.getElementById('districtChangeRankingChart');
    if (!chartDom) return;
    
    if (!charts.districtChangeRanking) {
      charts.districtChangeRanking = echarts.init(chartDom);
    }
    
    const option = Charts.getDistrictChangeRankingOption(data.ranking, order);
    charts.districtChangeRanking.setOption(option);
  } catch (error) {
    console.error('加载区县涨跌榜数据失败:', error);
  }
}

function resizeCharts() {
  setTimeout(() => {
    Object.values(charts).forEach(chart => {
      if (chart && chart.resize) {
        chart.resize();
      }
    });
  }, 100);
}

window.addEventListener('resize', debounce(resizeCharts, 300));

function formatNumber(num) {
  if (!num) return '0';
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatLargeNumber(num) {
  if (!num) return '0';
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  }
  return num.toString();
}

function showLoading(container) {
  const loading = document.createElement('div');
  loading.className = 'chart-loading';
  loading.innerHTML = '<div class="loading-spinner"></div><p>加载中...</p>';
  container.appendChild(loading);
}

function hideLoading(container) {
  const loading = container.querySelector('.chart-loading');
  if (loading) {
    loading.remove();
  }
}

function showError(container, message) {
  hideLoading(container);
  const error = document.createElement('div');
  error.className = 'chart-error';
  error.innerHTML = `<i data-lucide="alert-circle"></i><p>${message}</p>`;
  container.appendChild(error);
  lucide.createIcons();
}
