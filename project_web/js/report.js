/**
 * 报告页面逻辑
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
            <p>暂无报告，点击上方生成您的第一份报告</p>
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
                <button class="btn btn-outline btn-sm save-btn" data-id="${report.id}">收藏</button>
              ` : ''}
            </div>
          </div>
        `;
      });
      
      container.innerHTML = html;
      
      // 绑定查看事件
      container.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          await viewReport(id);
        });
      });
      
      // 绑定收藏事件
      container.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
          const id = this.dataset.id;
          try {
            await API.favorites.saveReport(id);
            alert('收藏成功！');
            this.disabled = true;
            this.textContent = '已收藏';
          } catch (error) {
            alert(error.message || '收藏失败');
          }
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
  generateBtn?.addEventListener('click', async function() {
    if (!selectedReportType) {
      alert('请先选择报告类型');
      return;
    }
    
    this.disabled = true;
    this.innerHTML = '<div class="btn-spinner"></div> 生成中...';
    
    try {
      const result = await API.report.generate({
        type: selectedReportType,
        params: {
          // 可以添加额外参数
        }
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
  
  // ========== 加载我的报告 ==========
  async function loadMyReports() {
    const container = document.querySelector('.my-reports');
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

