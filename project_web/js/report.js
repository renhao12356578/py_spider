/**
 * 报告页面逻辑
 * 房产数据分析系统
 */

document.addEventListener('DOMContentLoaded', async function() {
  // 检查用户是否登录，但不强制跳转
  const isLoggedIn = !!localStorage.getItem('token');
  
  // 显示用户名或登录按钮
  const userDisplay = document.getElementById('userDisplay');
  const logoutBtn = document.getElementById('logoutBtn');
  
  if (isLoggedIn) {
    const user = Auth.getUser();
    if (user && userDisplay) {
      userDisplay.textContent = user.username || '用户';
    }
    
    // 退出登录
    logoutBtn?.addEventListener('click', () => {
      Auth.logout();
    });
  } else {
    // ✅ 未登录用户：显示"登录"按钮
    if (userDisplay) {
      userDisplay.innerHTML = '<a href="login.html" style="color: var(--primary-color); text-decoration: none;">登录</a>';
    }
    if (logoutBtn) {
      logoutBtn.style.display = 'none';
    }
  }
  
  // 初始化图标
  lucide.createIcons();
  
  // 当前选中的报告类型
  let selectedReportType = null;
  
  // ========== 加载报告类型 ==========
  async function loadReportTypes() {
    try {
      const types = await API.report.getTypes();
      const container = document.querySelector('.report-types');
      if (!container || !types) return;
      
      let html = '';
      types.forEach((type, index) => {
        html += `
          <div class="report-type-card ${index === 0 ? 'active' : ''}" data-type="${type.id}">
            <div class="type-icon">
              <i data-lucide="${type.icon || 'file-text'}"></i>
            </div>
            <h4>${type.name}</h4>
            <p>${type.description || ''}</p>
          </div>
        `;
      });
      
      container.innerHTML = html;
      lucide.createIcons();
      
      // 默认选中第一个
      if (types.length > 0) {
        selectedReportType = types[0].id;
      }
      
      // 绑定点击事件
      container.querySelectorAll('.report-type-card').forEach(card => {
        card.addEventListener('click', function() {
          container.querySelectorAll('.report-type-card').forEach(c => c.classList.remove('active'));
          this.classList.add('active');
          selectedReportType = this.dataset.type;
        });
      });
      
    } catch (error) {
      console.error('加载报告类型失败:', error);
    }
  }
  
  // ========== 加载报告列表 ==========
  async function loadReportList(page = 1, limit = 10) {
    const container = document.querySelector('.report-list');
    if (!container) return;
    
    try {
      container.innerHTML = '<div class="loading">加载中...</div>';
      
      const data = await API.report.getList({ page, limit });
      
      if (!data.list || data.list.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <i data-lucide="file-text" style="width: 48px; height: 48px; opacity: 0.3;"></i>
            <p>暂无报告${isLoggedIn ? '，点击上方生成您的第一份报告' : ''}</p>
          </div>
        `;
        lucide.createIcons();
        return;
      }
      
      let html = '';
      data.list.forEach(report => {
        const statusClass = {
          'completed': 'success',
          'generating': 'warning',
          'failed': 'danger'
        }[report.status] || '';
        
        const statusText = {
          'completed': '已完成',
          'generating': '生成中',
          'failed': '失败'
        }[report.status] || report.status;
        
        // ✅ 获取收藏状态
        const isFavorited = report.is_favorited || false;
        const favoriteIcon = isFavorited ? 'star-fill' : 'star';
        const favoriteText = isFavorited ? '已收藏' : '收藏';
        const favoriteClass = isFavorited ? 'favorited' : '';
        
        html += `
          <div class="report-item" data-id="${report.id}">
            <div class="report-info">
              <h4>${report.title}</h4>
              <p>${report.type_name || ''} · ${report.created_at || ''}</p>
            </div>
            <div class="report-status">
              <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            <div class="report-actions">
              ${report.status === 'completed' ? `
                <button class="btn btn-primary btn-sm view-btn" data-id="${report.id}">查看</button>
                <button class="btn btn-outline btn-sm save-btn ${favoriteClass}" 
                        data-id="${report.id}" 
                        data-favorited="${isFavorited}"
                        title="${isLoggedIn ? favoriteText : '登录后收藏'}">
                  <i data-lucide="${favoriteIcon}" style="width: 14px; height: 14px;"></i>
                  ${isLoggedIn ? favoriteText : '收藏'}
                </button>
              ` : ''}
            </div>
          </div>
        `;
      });
      
      container.innerHTML = html;
      lucide.createIcons();
      
      // 绑定查看事件
      container.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          await viewReport(id);
        });
      });
      
      // ✅ 绑定收藏事件 - 传递按钮元素
      container.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          await toggleFavorite(id, this);
        });
      });
      
    } catch (error) {
      console.error('加载报告列表失败:', error);
      container.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
  }
  
  // ========== 查看报告详情 ==========
  async function viewReport(reportId) {
    try {
      const report = await API.report.getDetail(reportId);
      
      // 显示报告模态框
      showReportModal(report);
      
    } catch (error) {
      alert(error.message || '获取报告详情失败');
    }
  }
  
  // ========== 显示报告模态框 ==========
  function showReportModal(report) {
    // 移除已存在的模态框
    const existingModal = document.getElementById('reportModal');
    if (existingModal) existingModal.remove();
    
    // 格式化内容：将换行符转换为 <br>，保留段落格式
    const formattedContent = report.content 
      ? report.content.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
      : '暂无内容';
    
    // 生成亮点列表
    let highlightsHtml = '';
    if (report.highlights && report.highlights.length) {
      highlightsHtml = `
        <div class="report-highlights">
          <h4>报告亮点</h4>
          <ul>
            ${report.highlights.map(h => `<li>${h}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    // ✅ 收藏按钮（如果已登录）
    const isFavorited = report.is_favorited || false;
    const favoriteBtn = isLoggedIn ? `
      <button class="btn btn-outline favorite-report-btn ${isFavorited ? 'favorited' : ''}" 
              data-id="${report.report_id}" 
              data-favorited="${isFavorited}">
        <i data-lucide="${isFavorited ? 'star-fill' : 'star'}" style="width: 16px; height: 16px;"></i>
        ${isFavorited ? '已收藏' : '收藏报告'}
      </button>
    ` : '';
    
    // ✅ 未登录用户提示
    const loginHint = !isLoggedIn ? `
      <div class="login-hint" style="background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 6px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
        <i data-lucide="info" style="width: 20px; height: 20px; color: #856404;"></i>
        <span style="color: #856404;">登录后可收藏报告并生成自定义报告</span>
        <a href="login.html?redirect=${encodeURIComponent(window.location.href)}" style="margin-left: auto; color: var(--primary-color); text-decoration: none; font-weight: 500;">立即登录 →</a>
      </div>
    ` : '';
    
    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'reportModal';
    modal.className = 'report-modal';
    modal.innerHTML = `
      <div class="report-modal-overlay"></div>
      <div class="report-modal-content">
        <div class="report-modal-header">
          <h2>${report.title || '报告详情'}</h2>
          <button class="report-modal-close" title="关闭">
            <i data-lucide="x"></i>
          </button>
        </div>
        ${loginHint}
        <div class="report-modal-meta">
          <span><i data-lucide="calendar"></i> ${report.published_at ? new Date(report.published_at).toLocaleDateString('zh-CN') : '-'}</span>
          <span><i data-lucide="user"></i> ${report.author || '系统'}</span>
          <span><i data-lucide="tag"></i> ${report.type || '-'}</span>
        </div>
        ${report.summary ? `<div class="report-summary"><strong>摘要：</strong>${report.summary}</div>` : ''}
        ${highlightsHtml}
        <div class="report-content">
          <p>${formattedContent}</p>
        </div>
        <div class="report-modal-footer">
          ${favoriteBtn}
          <button class="btn btn-secondary report-modal-close-btn">关闭</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    lucide.createIcons();
    
    // ✅ 绑定收藏按钮事件
    const favoriteModalBtn = modal.querySelector('.favorite-report-btn');
    if (favoriteModalBtn) {
      favoriteModalBtn.addEventListener('click', async function() {
        const id = this.dataset.id;
        await toggleFavorite(id, this);
      });
    }
    
    // 绑定关闭事件
    modal.querySelector('.report-modal-overlay').addEventListener('click', () => modal.remove());
    modal.querySelector('.report-modal-close').addEventListener('click', () => modal.remove());
    modal.querySelector('.report-modal-close-btn').addEventListener('click', () => modal.remove());
    
    // ESC 键关闭
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', handleEsc);
      }
    };
    document.addEventListener('keydown', handleEsc);
  }
  
  // ========== 生成报告 ==========
  const generateBtn = document.querySelector('.generate-btn');
  if (generateBtn) {
    // ✅ 未登录用户：生成按钮提示登录
    if (!isLoggedIn) {
      generateBtn.innerHTML = '<i data-lucide="lock"></i> 登录后生成报告';
      generateBtn.addEventListener('click', function() {
        if (confirm('生成自定义报告需要登录，是否前往登录？')) {
          window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
        }
      });
      lucide.createIcons();
    } else {
      // 已登录用户：正常生成报告
      generateBtn.addEventListener('click', async function() {
        if (!selectedReportType) {
          alert('请先选择报告类型');
          return;
        }
        
        this.disabled = true;
        this.innerHTML = '<div class="btn-spinner"></div> 生成中...';
        
        try {
          const result = await API.report.generate({
            type: selectedReportType,
            params: {}
          });
          
          alert(`报告生成请求已提交！预计需要 ${result.estimated_time || 30} 秒`);
          
          // 刷新报告列表
          setTimeout(() => {
            loadReportList();
          }, 2000);
          
        } catch (error) {
          alert(error.message || '生成报告失败');
        } finally {
          this.disabled = false;
          this.innerHTML = '<i data-lucide="file-plus"></i> 生成报告';
          lucide.createIcons();
        }
      });
    }
  }
  
  // ========== 加载我的报告 (仅登录用户) ==========
  async function loadMyReports() {
    const container = document.querySelector('.my-reports');
    const myReportsSection = document.querySelector('.my-reports-section');
    
    // ✅ 未登录用户：隐藏"我的报告"区域
    if (!isLoggedIn) {
      if (myReportsSection) {
        myReportsSection.style.display = 'none';
      }
      return;
    }
    
    if (!container) return;
    
    try {
      const data = await API.report.getMyReports({ page: 1, limit: 5 });
      const reports = data.reports || data.list || [];
      
      if (!reports.length) {
        container.innerHTML = '<p class="empty-text">暂无生成的报告</p>';
        return;
      }
      
      let html = '<ul class="my-report-list">';
      reports.forEach(report => {
        const statusClass = report.status === 'completed' ? 'completed' : 'generating';
        const statusText = report.status === 'completed' ? '已完成' : '生成中...';
        
        html += `
          <li class="my-report-item ${statusClass}" data-report='${JSON.stringify(report).replace(/'/g, "&#39;")}'>
            <div class="my-report-info">
              <span class="my-report-title">${report.title}</span>
              <span class="my-report-date">${report.created_at ? new Date(report.created_at).toLocaleDateString('zh-CN') : '-'}</span>
            </div>
            <span class="my-report-status ${statusClass}">${statusText}</span>
          </li>
        `;
      });
      html += '</ul>';
      
      container.innerHTML = html;
      
      // 绑定点击事件查看报告详情
      container.querySelectorAll('.my-report-item.completed').forEach(item => {
        item.style.cursor = 'pointer';
        item.addEventListener('click', function() {
          try {
            const report = JSON.parse(this.dataset.report);
            showReportModal(report);
          } catch (e) {
            console.error('解析报告数据失败:', e);
          }
        });
      });
      
    } catch (error) {
      console.error('加载我的报告失败:', error);
    }
  }
  
  // ========== 加载数据更新时间 ==========
  async function loadDataUpdateTime() {
    try {
      const info = await API.system.getDataUpdateTime();
      const el = document.querySelector('.data-update-time');
      if (el && info) {
        el.textContent = `数据更新时间: ${info.last_update || '-'}`;
      }
    } catch (error) {
      console.error('加载数据更新时间失败:', error);
    }
  }
  
  // ========== 初始化加载 ==========
  loadReportTypes();
  loadReportList();
  loadMyReports();
  loadDataUpdateTime();
});

// ========== 收藏报告功能 (完整实现) ==========
async function toggleFavorite(reportId, buttonElement) {
    // ✅ 检查登录状态，未登录则提示
    if (!localStorage.getItem('token')) {
        showToast('请先登录后再收藏报告', 'warning');
        setTimeout(() => {
            window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
        }, 1500);
        return;
    }
    
    try {
        // ✅ 从按钮元素读取当前收藏状态
        const isFavorited = buttonElement.dataset.favorited === 'true';
        
        // 禁用按钮防止重复点击
        buttonElement.disabled = true;
        
        if (isFavorited) {
            // 取消收藏
            await API.favorites.removeReport(reportId);
            showToast('已取消收藏', 'success');
            
            // 更新按钮状态
            buttonElement.dataset.favorited = 'false';
            buttonElement.classList.remove('favorited');
            
            // 更新图标和文字
            const icon = buttonElement.querySelector('i');
            if (icon) {
                icon.setAttribute('data-lucide', 'star');
            }
            
            const textNode = Array.from(buttonElement.childNodes).find(node => node.nodeType === 3);
            if (textNode) {
                textNode.textContent = buttonElement.classList.contains('favorite-report-btn') ? '收藏报告' : '收藏';
            }
            
        } else {
            // 添加收藏
            await API.favorites.saveReport(reportId);
            showToast('收藏成功', 'success');
            
            // 更新按钮状态
            buttonElement.dataset.favorited = 'true';
            buttonElement.classList.add('favorited');
            
            // 更新图标和文字
            const icon = buttonElement.querySelector('i');
            if (icon) {
                icon.setAttribute('data-lucide', 'star-fill');
            }
            
            const textNode = Array.from(buttonElement.childNodes).find(node => node.nodeType === 3);
            if (textNode) {
                textNode.textContent = buttonElement.classList.contains('favorite-report-btn') ? '已收藏' : '已收藏';
            }
        }
        
        // 重新渲染图标
        lucide.createIcons();
        
    } catch (error) {
        console.error('收藏操作失败:', error);
        showToast(error.message || '操作失败，请稍后重试', 'error');
    } finally {
        // 恢复按钮状态
        buttonElement.disabled = false;
    }
}

// ========== Toast 提示函数 ==========
function showToast(message, type = 'info') {
    // 移除已存在的 Toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    const bgColor = {
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#3b82f6'
    }[type] || '#3b82f6';
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 14px 24px;
        background: ${bgColor};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        font-size: 14px;
        font-weight: 500;
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 添加动画样式 ==========
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        .btn-spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            vertical-align: middle;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .save-btn.favorited,
        .favorite-report-btn.favorited {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
    `;
    document.head.appendChild(style);
}

