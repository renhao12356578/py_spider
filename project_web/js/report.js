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
  
  // 报告类型已集成到生成报告模态框中，不再需要单独加载
  
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
      
      // 绑定报告类型选择事件
      setTimeout(() => {
        const typeOptions = modal.querySelectorAll('.report-type-option');
        const hiddenInput = modal.querySelector('input[name="report_type"]');
        const areaInput = modal.querySelector('#areaInput');
        const areaHint = modal.querySelector('#areaHint');
        
        // 报告类型对应的提示信息
        const typeHints = {
          '市场趋势报告': '可留空，将分析全国及重点城市',
          '城市分析报告': '建议填写具体区域，如：海淀区',
          '城市对比报告': '可留空，将对比多个城市',
          '投资价值报告': '建议填写具体区域，如：朝阳区'
        };
        
        const typePlaceholders = {
          '市场趋势报告': '可留空，将分析全国数据',
          '城市分析报告': '例如：海淀区',
          '城市对比报告': '可留空，将对比多个城市',
          '投资价值报告': '例如：朝阳区'
        };
        
        typeOptions.forEach(option => {
          option.addEventListener('click', function() {
            // 移除所有选中状态
            typeOptions.forEach(opt => {
              opt.style.borderColor = '#e5e7eb';
              opt.style.background = 'white';
            });
            
            // 设置当前选中状态
            this.style.borderColor = '#3b82f6';
            this.style.background = '#eff6ff';
            
            // 更新隐藏输入值
            const selectedType = this.dataset.type;
            if (hiddenInput) {
              hiddenInput.value = selectedType;
            }
            
            // 更新区域输入提示
            if (areaInput && typePlaceholders[selectedType]) {
              areaInput.placeholder = typePlaceholders[selectedType];
            }
            
            // 更新提示文本
            if (areaHint && typeHints[selectedType]) {
              areaHint.textContent = typeHints[selectedType];
            }
          });
          
          // 悬停效果
          option.addEventListener('mouseenter', function() {
            if (this.style.borderColor !== 'rgb(59, 130, 246)') {
              this.style.borderColor = '#cbd5e1';
            }
          });
          
          option.addEventListener('mouseleave', function() {
            if (this.style.borderColor !== 'rgb(59, 130, 246)') {
              this.style.borderColor = '#e5e7eb';
            }
          });
        });
        
        // 默认选中第一个
        if (typeOptions.length > 0 && hiddenInput) {
          typeOptions[0].click();
        }
      }, 100);
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
      form.addEventListener('submit', async function(e) {
        e.preventDefault();
      
        const formData = new FormData(this);
        const area = formData.get('area');
        const city = formData.get('city');
        const report_type = formData.get('report_type');
        
        // 验证：至少填写城市或区域之一
        if (!area && !city) {
          showToast('请至少填写城市或区域之一', 'warning');
          return;
        }
        
        // 验证：必须选择报告类型
        if (!report_type) {
          showToast('请选择报告类型', 'warning');
          return;
        }
        
        const params = {
          area: area || '',
          city: city || '',
          report_type: report_type
        };
      
        const submitBtn = document.querySelector('#generateReportModal button[type="submit"]');
        if (!submitBtn) return;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="btn-spinner"></div> 正在生成...';
        
        // 创建进度提示
        const progressDiv = document.createElement('div');
        progressDiv.className = 'generation-progress';
        progressDiv.style.cssText = 'margin-top: 16px; padding: 12px; background: #f0f9ff; border-radius: 8px; font-size: 13px; color: #1e40af;';
        progressDiv.innerHTML = '<i data-lucide="loader" style="width: 14px; height: 14px; animation: spin 1s linear infinite;"></i> 正在初始化...';
        form.appendChild(progressDiv);
        lucide.createIcons();
      
        try {
          // 使用异步API
          const response = await fetch('/api/reports/generate/ai/async', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(params)
          });
          
          if (!response.ok) throw new Error('创建任务失败');
          
          const result = await response.json();
          const taskId = result.data.task_id;
          
          // 轮询任务状态
          const pollInterval = setInterval(async () => {
            try {
              const statusResponse = await fetch(`/api/reports/task/${taskId}`, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
              });
              
              if (!statusResponse.ok) {
                clearInterval(pollInterval);
                throw new Error('查询任务状态失败');
              }
              
              const statusData = await statusResponse.json();
              const task = statusData.data;
              
              // 更新进度
              if (task.status === 'pending') {
                progressDiv.innerHTML = `<i data-lucide="loader" style="width: 14px; height: 14px; animation: spin 1s linear infinite;"></i> 任务排队中...`;
              } else if (task.status === 'processing') {
                progressDiv.innerHTML = `<i data-lucide="loader" style="width: 14px; height: 14px; animation: spin 1s linear infinite;"></i> ${task.message} (${task.progress}%)`;
              } else if (task.status === 'completed') {
                clearInterval(pollInterval);
                progressDiv.innerHTML = '<i data-lucide="check-circle" style="width: 14px; height: 14px; color: #10b981;"></i> 生成完成！';
                
                showToast('报告生成成功！', 'success');
                closeGenerateModal();
                form.reset();
                progressDiv.remove();
                
                // 刷新报告列表
                setTimeout(() => {
                  loadReportList();
                  loadMyReports();
                }, 500);
              } else if (task.status === 'failed') {
                clearInterval(pollInterval);
                throw new Error(task.error || '报告生成失败');
              }
              
              lucide.createIcons();
            } catch (e) {
              clearInterval(pollInterval);
              throw e;
            }
          }, 2000); // 每2秒轮询一次
          
        } catch (error) {
          showToast(error.message || '生成报告失败', 'error');
          if (progressDiv) progressDiv.remove();
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i data-lucide="zap"></i> 生成报告';
          lucide.createIcons();
        }
      });
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
      // 同时获取任务和报告
      const [tasksResponse, reportsData] = await Promise.all([
        fetch('/api/reports/tasks/user', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }).then(r => r.json()).catch(() => ({ data: { tasks: [] } })),
        API.report.getMyReports({ page: 1, page_size: 5 })
      ]);
      
      const tasks = tasksResponse.data?.tasks || [];
      const reports = reportsData.reports || reportsData.list || [];
      
      // 筛选未完成的任务
      const activeTasks = tasks.filter(t => t.status !== 'completed' && t.status !== 'failed');
      
      if (!activeTasks.length && !reports.length) {
        container.innerHTML = '<p class="empty-text">暂无生成的报告</p>';
        return;
      }
      
      let html = '<ul class="my-report-list">';
      
      // 先显示正在生成的任务
      activeTasks.forEach(task => {
        const params = task.params || {};
        const title = `${params.area || params.city || '未知区域'}${params.report_type || '报告'}`;
        const statusText = task.status === 'pending' ? '排队中' : `生成中 (${task.progress}%)`;
        const statusClass = task.status === 'pending' ? 'pending' : 'generating';
        
        html += `
          <li class="my-report-item ${statusClass}" data-task-id="${task.task_id}">
            <div class="my-report-info">
              <span class="my-report-title">${title}</span>
              <span class="my-report-date">${new Date(task.created_at).toLocaleDateString('zh-CN')}</span>
            </div>
            <span class="my-report-status ${statusClass}">
              <i data-lucide="loader" style="width: 12px; height: 12px; animation: spin 1s linear infinite;"></i>
              ${statusText}
            </span>
          </li>
        `;
      });
      
      // 再显示已完成的报告
      reports.slice(0, 5 - activeTasks.length).forEach(report => {
        html += `
          <li class="my-report-item completed" data-report='${JSON.stringify(report).replace(/'/g, "&#39;")}'>
            <div class="my-report-info">
              <span class="my-report-title">${report.title}</span>
              <span class="my-report-date">${report.created_at ? new Date(report.created_at).toLocaleDateString('zh-CN') : '-'}</span>
            </div>
            <span class="my-report-status completed">已完成</span>
          </li>
        `;
      });
      html += '</ul>';
      
      container.innerHTML = html;
      lucide.createIcons();
      
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
      
      // 如果有正在生成的任务，启动轮询
      if (activeTasks.length > 0) {
        setTimeout(loadMyReports, 3000); // 3秒后刷新
      }
      
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
        @keyframes spin {
            to { transform: rotate(360deg); }
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
        .save-btn.favorited,
        .favorite-report-btn.favorited {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
    `;
    document.head.appendChild(style);
}

