/**
 * 收藏页面逻辑
 * 房产数据分析系统
 */

document.addEventListener('DOMContentLoaded', async function() {
  // 检查登录状态
  if (!Auth.requireAuth()) return;
  
  // 显示用户名
  const user = Auth.getUser();
  if (user) {
    document.getElementById('userDisplay').textContent = user.username || '用户';
  }
  
  // 退出登录
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    Auth.logout();
  });
  
  // 初始化图标
  lucide.createIcons();
  
  // 当前标签页
  let currentTab = 'houses';
  
  // ========== 加载收藏房源 ==========
  async function loadFavoriteHouses(page = 1, limit = 10) {
    const container = document.getElementById('tab-houses');
    if (!container) return;
    
    try {
      container.innerHTML = '<div class="loading">加载中...</div>';
      
      const data = await API.favorites.getHouses({ page, limit });
      
      if (!data.list || data.list.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <i data-lucide="heart" style="width: 48px; height: 48px; opacity: 0.3;"></i>
            <p>暂无收藏的房源</p>
            <a href="beijing.html" class="btn btn-primary btn-sm">去浏览房源</a>
          </div>
        `;
        lucide.createIcons();
        return;
      }
      
      let html = '<div class="fav-list">';
      data.list.forEach(item => {
        html += `
          <div class="fav-item" data-id="${item.id}">
            <div class="fav-item-info">
              <h4>${item.title || item.district + ' · ' + item.layout}</h4>
              <p>${item.area}㎡ · ${item.floor} · ${item.orientation || '南北通透'}</p>
              <div class="fav-item-price">${item.total_price}万 <span>(${item.price_per_sqm}元/㎡)</span></div>
            </div>
            <div class="fav-item-actions">
              <button class="btn btn-outline btn-sm view-btn" data-id="${item.house_id}">查看详情</button>
              <button class="btn btn-danger btn-sm remove-btn" data-id="${item.id}">取消收藏</button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      
      container.innerHTML = html;
      
      // 绑定取消收藏事件
      container.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          if (confirm('确定要取消收藏吗？')) {
            try {
              await API.favorites.removeHouse(id);
              this.closest('.fav-item').remove();
            } catch (error) {
              alert(error.message || '操作失败');
            }
          }
        });
      });
      
    } catch (error) {
      console.error('加载收藏房源失败:', error);
      container.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
  }
  
  // ========== 加载关注城市 ==========
  async function loadFavoriteCities() {
    const container = document.getElementById('tab-cities');
    if (!container) return;
    
    try {
      container.innerHTML = '<div class="loading">加载中...</div>';
      
      const data = await API.favorites.getCities();
      
      if (!data || data.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <i data-lucide="map-pin" style="width: 48px; height: 48px; opacity: 0.3;"></i>
            <p>暂无关注的城市</p>
            <a href="index.html" class="btn btn-primary btn-sm">去浏览城市</a>
          </div>
        `;
        lucide.createIcons();
        return;
      }
      
      let html = '<div class="city-grid">';
      data.forEach(city => {
        html += `
          <div class="city-card" data-city="${city.name}">
            <div class="city-info">
              <h4>${city.name}</h4>
              <p>均价: ${city.avg_price?.toLocaleString() || '-'}元/㎡</p>
              <p class="${city.change >= 0 ? 'up' : 'down'}">
                ${city.change >= 0 ? '↑' : '↓'} ${Math.abs(city.change || 0)}%
              </p>
            </div>
            <button class="btn btn-outline btn-sm unfollow-btn" data-city="${city.name}">
              取消关注
            </button>
          </div>
        `;
      });
      html += '</div>';
      
      container.innerHTML = html;
      
      // 绑定取消关注事件
      container.querySelectorAll('.unfollow-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const cityName = this.dataset.city;
          if (confirm(`确定要取消关注 ${cityName} 吗？`)) {
            try {
              await API.favorites.removeCity(cityName);
              this.closest('.city-card').remove();
            } catch (error) {
              alert(error.message || '操作失败');
            }
          }
        });
      });
      
    } catch (error) {
      console.error('加载关注城市失败:', error);
      container.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
  }
  
  // ========== 加载收藏报告 ==========
  async function loadFavoriteReports() {
    const container = document.getElementById('tab-reports');
    if (!container) return;
    
    try {
      container.innerHTML = '<div class="loading">加载中...</div>';
      
      const data = await API.favorites.getReports({ page: 1, limit: 20 });
      
      if (!data.list || data.list.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <i data-lucide="file-text" style="width: 48px; height: 48px; opacity: 0.3;"></i>
            <p>暂无收藏的报告</p>
            <a href="report.html" class="btn btn-primary btn-sm">去浏览报告</a>
          </div>
        `;
        lucide.createIcons();
        return;
      }
      
      let html = '<div class="report-list">';
      data.list.forEach(report => {
        html += `
          <div class="report-item" data-id="${report.id}">
            <div class="report-info">
              <h4>${report.title}</h4>
              <p>${report.description || ''}</p>
              <span class="report-date">${report.created_at || ''}</span>
            </div>
            <div class="report-actions">
              <button class="btn btn-primary btn-sm view-btn" data-id="${report.report_id}">查看</button>
              <button class="btn btn-outline btn-sm remove-btn" data-id="${report.id}">移除</button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      
      container.innerHTML = html;
      
      // 绑定移除事件
      container.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          try {
            await API.favorites.removeReport(id);
            this.closest('.report-item').remove();
          } catch (error) {
            alert(error.message || '操作失败');
          }
        });
      });
      
    } catch (error) {
      console.error('加载收藏报告失败:', error);
      container.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
  }
  
  // ========== 标签页切换 ==========
  document.querySelectorAll('.fav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      const tabId = this.dataset.tab;
      currentTab = tabId;
      
      // 切换标签状态
      document.querySelectorAll('.fav-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      
      // 切换内容
      document.querySelectorAll('.fav-content').forEach(c => c.classList.remove('active'));
      document.getElementById(`tab-${tabId}`)?.classList.add('active');
      
      // 加载对应数据
      if (tabId === 'houses') loadFavoriteHouses();
      else if (tabId === 'cities') loadFavoriteCities();
      else if (tabId === 'reports') loadFavoriteReports();
    });
  });
  
  // ========== 初始化加载 ==========
  loadFavoriteHouses();
});

