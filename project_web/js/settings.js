/**
 * 设置页面逻辑
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
  
  // ========== 加载用户资料 ==========
  async function loadProfile() {
    try {
      const profile = await API.user.getProfile();
      
      // 填充表单
      document.querySelector('[name="nickname"]')?.setAttribute('value', profile.nickname || '');
      document.querySelector('[name="email"]')?.setAttribute('value', profile.email || '');
      document.querySelector('[name="phone"]')?.setAttribute('value', profile.phone || '');
      document.querySelector('[name="bio"]')?.value = profile.bio || '';
      
      // 显示用户名
      const usernameInput = document.querySelector('.profile-form input[readonly]');
      if (usernameInput) usernameInput.value = profile.username || '';
      
    } catch (error) {
      console.error('加载用户资料失败:', error);
    }
  }
  
  // ========== 保存用户资料 ==========
  const profileForm = document.querySelector('.profile-form');
  profileForm?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '保存中...';
    
    try {
      const formData = new FormData(this);
      await API.user.updateProfile({
        nickname: formData.get('nickname'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        bio: formData.get('bio')
      });
      
      alert('资料保存成功！');
    } catch (error) {
      alert(error.message || '保存失败，请稍后重试');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '保存修改';
    }
  });
  
  // ========== 修改密码 ==========
  const changePasswordBtn = document.querySelector('.security-item .btn');
  changePasswordBtn?.addEventListener('click', async function() {
    const oldPassword = prompt('请输入当前密码:');
    if (!oldPassword) return;
    
    const newPassword = prompt('请输入新密码 (至少8位):');
    if (!newPassword || newPassword.length < 8) {
      alert('新密码至少需要8位');
      return;
    }
    
    const confirmPassword = prompt('请再次输入新密码:');
    if (newPassword !== confirmPassword) {
      alert('两次输入的密码不一致');
      return;
    }
    
    try {
      await API.user.changePassword(oldPassword, newPassword);
      alert('密码修改成功！请重新登录');
      Auth.logout();
    } catch (error) {
      alert(error.message || '密码修改失败');
    }
  });
  
  // ========== 加载通知设置 ==========
  async function loadNotificationSettings() {
    try {
      const settings = await API.user.getNotificationSettings();
      
      // 设置开关状态
      document.querySelectorAll('.toggle-input').forEach(toggle => {
        const name = toggle.getAttribute('name');
        if (settings[name] !== undefined) {
          toggle.checked = settings[name];
        }
      });
    } catch (error) {
      console.error('加载通知设置失败:', error);
    }
  }
  
  // ========== 保存通知设置 ==========
  document.querySelectorAll('.toggle-input').forEach(toggle => {
    toggle.addEventListener('change', async function() {
      const name = this.getAttribute('name') || this.id;
      const value = this.checked;
      
      try {
        await API.user.updateNotificationSettings({ [name]: value });
      } catch (error) {
        console.error('保存通知设置失败:', error);
        // 回滚状态
        this.checked = !value;
      }
    });
  });
  
  // ========== 加载系统版本信息 ==========
  async function loadSystemInfo() {
    try {
      const version = await API.system.getVersion();
      const versionEl = document.querySelector('.about-version');
      if (versionEl && version) {
        versionEl.textContent = `版本 ${version.version || '1.0.0'}`;
      }
    } catch (error) {
      console.error('加载版本信息失败:', error);
    }
  }
  
  // ========== 提交反馈 ==========
  const feedbackForm = document.querySelector('.feedback-form');
  feedbackForm?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const textarea = this.querySelector('textarea');
    const content = textarea?.value?.trim();
    
    if (!content) {
      alert('请输入反馈内容');
      return;
    }
    
    try {
      await API.system.submitFeedback({ content, type: 'suggestion' });
      alert('感谢您的反馈！');
      textarea.value = '';
    } catch (error) {
      alert(error.message || '提交失败，请稍后重试');
    }
  });
  
  // ========== 侧边栏导航 ==========
  document.querySelectorAll('.settings-nav-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      
      document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
      this.classList.add('active');
      
      document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
    });
  });
  
  // ========== 初始化加载 ==========
  loadProfile();
  loadNotificationSettings();
  loadSystemInfo();
});

