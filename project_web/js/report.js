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
      const response = await API.report.getTypes();
      const types = response.types || response || [];
      const container = document.querySelector('.report-types');
      if (!container || !types || types.length === 0) return;
      
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
      // 显示加载动画
      container.innerHTML = `
        <div class="loading">
          <div class="loading-spinner"></div>
          <p class="loading-text">加载报告列表...</p>
        </div>
      `;
      
      const data = await API.report.getList({ page, page_size: limit });
      const reportList = data.reports || data.list || [];
      
      if (!reportList || reportList.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无报告，点击上方生成第一份报告</div>';
        return;
      }
      
      let html = '';
      reportList.forEach(report => {
        html += `
          <div class="report-item" data-id="${report.id}">
            <div class="report-cover">
              ${report.cover_image ? 
                `<img src="${report.cover_image}" alt="${report.title}">` : 
                '<i data-lucide="file-text"></i>'
              }
            </div>
            <div class="report-content">
              <h4 class="report-title">${report.title}</h4>
              <p class="report-summary">${report.summary || '暂无摘要'}</p>
              <div class="report-meta">
                <span class="report-type">${report.type || '报告'}</span>
                <span class="report-date">${report.created_at || '-'}</span>
              </div>
            </div>
            <div class="report-actions">
              <button class="btn btn-primary btn-sm view-btn" data-id="${report.id}">
                <i data-lucide="eye"></i>
                查看
              </button>
            </div>
          </div>
        `;
      });
      
      container.innerHTML = html;
      lucide.createIcons();
      
      // 绑定查看按钮
      container.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
          const reportId = this.dataset.id;
          viewReport(reportId);
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
          <button class="btn btn-secondary report-modal-close-btn">关闭</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    lucide.createIcons();
    
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
      // 已登录用户：打开生成报告模态框
      generateBtn.addEventListener('click', function() {
        openGenerateModal();
      });
    }
  }

  // ========== 打开/关闭生成报告模态框 ==========
  function openGenerateModal() {
    const modal = document.getElementById('generateReportModal');
    if (modal) {
      modal.style.display = 'flex';
      modal.style.alignItems = 'center';
      modal.style.justifyContent = 'center';
      modal.style.position = 'fixed';
      modal.style.top = '0';
      modal.style.left = '0';
      modal.style.width = '100%';
      modal.style.height = '100%';
      modal.style.zIndex = '9999';
      modal.style.background = 'rgba(0, 0, 0, 0.5)';
      lucide.createIcons();
    }
  }

  window.closeGenerateModal = function() {
    const modal = document.getElementById('generateReportModal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  // ========== 处理生成报告表单提交 ==========
  setTimeout(() => {
    const form = document.getElementById('generateReportForm');
    if (form) {
      console.log('表单已找到，绑定提交事件');
      form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('表单提交事件触发');
      
      const formData = new FormData(this);
      const metrics = [];
      formData.getAll('metrics').forEach(m => metrics.push(m));
      
      const districts = formData.get('districts') ? formData.get('districts').split(',').map(d => d.trim()) : [];
      
      const params = {
        type: formData.get('type'),
        city: formData.get('city'),
        districts: districts,
        date_range: {
          start: formData.get('start_date') || '',
          end: formData.get('end_date') || ''
        },
        metrics: metrics,
        format: formData.get('format')
      };
      
      const submitBtn = document.querySelector('#generateReportModal button[type="submit"]');
      if (!submitBtn) {
        console.error('找不到提交按钮');
        return;
      }
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<div class="btn-spinner"></div> 生成中...';
      
      try {
        const result = await API.report.generate(params);
        alert(`报告生成成功！报告ID: ${result.report_id || 'N/A'}`);
        closeGenerateModal();
        form.reset();
        
        // 刷新报告列表
        setTimeout(() => {
          loadReportList();
          loadMyReports();
        }, 1000);
        
      } catch (error) {
        alert(error.message || '生成报告失败，请稍后重试');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="zap"></i> 生成报告';
        lucide.createIcons();
      }
    });
    } else {
      console.error('找不到表单元素 generateReportForm');
    }
  }, 100);
  
  // ========== 加载我的报告 (仅登录用户) ==========
  async function loadMyReports() {
    const container = document.querySelector('.my-reports-list');
    
    if (!container) return;
    
    // ✅ 未登录用户：显示提示
    if (!isLoggedIn) {
      container.innerHTML = '<div class="empty-state">登录后查看我的报告</div>';
      return;
    }
    
    try {
      const data = await API.report.getMyReports({ page: 1, page_size: 5 });
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
  
  // ========== 加载静态报告 ==========
  async function loadStaticReports() {
    try {
      const data = await API.report.getStaticReports();
      const reports = data.reports || [];
      
      console.log('静态报告数据:', reports);
      
      if (reports.length === 0) {
        console.log('没有静态报告');
        return;
      }
      
      // 找到第一个 report-section 作为插入点
      const firstSection = document.querySelector('.report-section');
      if (!firstSection) {
        console.error('找不到 .report-section 元素');
        return;
      }
      
      // 创建静态报告区域
      const staticSection = document.createElement('div');
      staticSection.className = 'report-section static-reports-section';
      staticSection.innerHTML = `
        <div class="section-header">
          <h2 class="section-title">
            <i data-lucide="file-text"></i>
            官方报告
          </h2>
        </div>
        <div class="static-reports-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px;">
          ${reports.map(report => `
            <div class="static-report-card" style="background: var(--bg-card); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-md); transition: transform 0.2s, box-shadow 0.2s; cursor: pointer;">
              <div style="display: flex; align-items: start; gap: 12px; margin-bottom: 12px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                  <i data-lucide="file-text" style="width: 24px; height: 24px; color: white;"></i>
                </div>
                <div style="flex: 1; min-width: 0;">
                  <h4 style="font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; line-height: 1.4;">${report.title}</h4>
                  <div style="display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-secondary);">
                    <span><i data-lucide="calendar" style="width: 12px; height: 12px;"></i> ${report.created_at}</span>
                    <span><i data-lucide="file" style="width: 12px; height: 12px;"></i> ${report.size_mb} MB</span>
                  </div>
                </div>
              </div>
              <a href="${API.report.downloadStaticReport(report.filename)}" 
                 class="btn btn-primary btn-sm btn-block" 
                 style="margin-top: 12px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px;"
                 download>
                <i data-lucide="download" style="width: 14px; height: 14px;"></i>
                下载报告
              </a>
            </div>
          `).join('')}
        </div>
      `;
      
      // 插入到第一个 report-section 之前
      firstSection.parentNode.insertBefore(staticSection, firstSection);
      lucide.createIcons();
      
      // 添加悬停效果
      document.querySelectorAll('.static-report-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
          this.style.transform = 'translateY(-4px)';
          this.style.boxShadow = 'var(--shadow-lg)';
        });
        card.addEventListener('mouseleave', function() {
          this.style.transform = 'translateY(0)';
          this.style.boxShadow = 'var(--shadow-md)';
        });
      });
      
      console.log('静态报告加载成功');
      
    } catch (error) {
      console.error('加载静态报告失败:', error);
    }
  }
  
  // ========== 初始化加载 ==========
  loadReportTypes();
  loadStaticReports();
  loadReportList();
  loadMyReports();
  loadDataUpdateTime();
});

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

