/**
 * 登录页面逻辑
 * 房产数据分析系统
 */

document.addEventListener('DOMContentLoaded', function() {
  // 如果已登录，跳转到主页
  if (Auth.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }
  
  // 获取元素
  const loginForm = document.getElementById('loginForm');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const togglePassword = document.getElementById('togglePassword');
  const loginBtn = document.getElementById('loginBtn');
  const loginError = document.getElementById('loginError');
  const errorMessage = document.getElementById('errorMessage');
  const rememberMe = document.getElementById('rememberMe');
  
  // 密码显示/隐藏切换
  let passwordVisible = false;
  togglePassword.addEventListener('click', function() {
    passwordVisible = !passwordVisible;
    passwordInput.type = passwordVisible ? 'text' : 'password';
    
    // 更新图标
    togglePassword.setAttribute('data-lucide', passwordVisible ? 'eye' : 'eye-off');
    lucide.createIcons();
  });
  
  // 检查记住的用户名
  const rememberedUsername = localStorage.getItem('remembered_username');
  if (rememberedUsername) {
    usernameInput.value = rememberedUsername;
    rememberMe.checked = true;
  }
  
  // 显示错误
  function showError(message) {
    errorMessage.textContent = message;
    loginError.classList.remove('hidden');
  }
  
  // 隐藏错误
  function hideError() {
    loginError.classList.add('hidden');
  }
  
  // 设置加载状态
  function setLoading(loading) {
    if (loading) {
      loginBtn.disabled = true;
      loginBtn.innerHTML = '<div class="btn-spinner"></div><span>登录中...</span>';
    } else {
      loginBtn.disabled = false;
      loginBtn.innerHTML = '<span>登录</span>';
    }
  }
  
  // 表单提交
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    hideError();
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    
    // 基础验证
    if (!username) {
      showError('请输入用户名');
      usernameInput.focus();
      return;
    }
    
    if (!password) {
      showError('请输入密码');
      passwordInput.focus();
      return;
    }
    
    setLoading(true);
    
    try {
      // 调用登录接口
      const data = await API.auth.login(username, password);
      
      // 保存登录信息
      Auth.saveLogin(data.token, data.user);
      
      // 记住用户名
      if (rememberMe.checked) {
        localStorage.setItem('remembered_username', username);
      } else {
        localStorage.removeItem('remembered_username');
      }
      
      // 跳转到主页
      window.location.href = 'index.html';
      
    } catch (error) {
      showError(error.message || '登录失败，请检查用户名和密码');
      setLoading(false);
    }
  });
  
  // 输入时隐藏错误
  usernameInput.addEventListener('input', hideError);
  passwordInput.addEventListener('input', hideError);
});

