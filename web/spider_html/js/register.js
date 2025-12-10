/**
 * 注册页面逻辑
 * 房产数据分析系统
 */

document.addEventListener('DOMContentLoaded', function() {
  // 如果已登录，跳转到主页
  if (Auth.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }
  
  // 当前步骤
  let currentStep = 1;
  
  // 获取元素
  const registerForm = document.getElementById('registerForm');
  const registerError = document.getElementById('registerError');
  const registerSuccess = document.getElementById('registerSuccess');
  const errorMessage = document.getElementById('errorMessage');
  
  // 表单字段
  const usernameInput = document.getElementById('username');
  const phoneInput = document.getElementById('phone');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  const captchaInput = document.getElementById('captcha');
  const agreeTerms = document.getElementById('agreeTerms');
  
  // 按钮
  const nextStep1 = document.getElementById('nextStep1');
  const nextStep2 = document.getElementById('nextStep2');
  const prevStep2 = document.getElementById('prevStep2');
  const prevStep3 = document.getElementById('prevStep3');
  const sendCaptchaBtn = document.getElementById('sendCaptcha');
  const submitBtn = document.getElementById('submitBtn');
  
  // 密码显隐切换
  const togglePassword = document.getElementById('togglePassword');
  const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
  
  // 密码显隐切换
  let passwordVisible = false;
  let confirmPasswordVisible = false;
  
  togglePassword?.addEventListener('click', function() {
    passwordVisible = !passwordVisible;
    passwordInput.type = passwordVisible ? 'text' : 'password';
    this.setAttribute('data-lucide', passwordVisible ? 'eye' : 'eye-off');
    lucide.createIcons();
  });
  
  toggleConfirmPassword?.addEventListener('click', function() {
    confirmPasswordVisible = !confirmPasswordVisible;
    confirmPasswordInput.type = confirmPasswordVisible ? 'text' : 'password';
    this.setAttribute('data-lucide', confirmPasswordVisible ? 'eye' : 'eye-off');
    lucide.createIcons();
  });
  
  // 步骤切换函数
  function goToStep(step) {
    currentStep = step;
    
    // 更新步骤指示器
    document.querySelectorAll('.step').forEach((s, index) => {
      s.classList.remove('active', 'completed');
      if (index + 1 < step) {
        s.classList.add('completed');
      } else if (index + 1 === step) {
        s.classList.add('active');
      }
    });
    
    document.querySelectorAll('.step-line').forEach((line, index) => {
      line.classList.toggle('active', index < step - 1);
    });
    
    // 切换表单步骤
    document.querySelectorAll('.form-step').forEach((s, index) => {
      s.classList.toggle('active', index + 1 === step);
    });
    
    // 如果是步骤3，更新摘要
    if (step === 3) {
      updateSummary();
    }
  }
  
  // 更新摘要信息
  function updateSummary() {
    document.getElementById('summaryUsername').textContent = usernameInput.value || '-';
    document.getElementById('summaryPhone').textContent = maskPhone(phoneInput.value) || '-';
    document.getElementById('summaryEmail').textContent = emailInput.value || '未填写';
  }
  
  // 手机号脱敏
  function maskPhone(phone) {
    if (!phone || phone.length < 11) return phone;
    return phone.slice(0, 3) + '****' + phone.slice(-4);
  }
  
  // 显示错误
  function showError(message) {
    errorMessage.textContent = message;
    registerError.classList.remove('hidden');
    registerSuccess.classList.add('hidden');
  }
  
  // 隐藏错误
  function hideError() {
    registerError.classList.add('hidden');
  }
  
  // 验证用户名
  function validateUsername(username) {
    const regex = /^[a-zA-Z0-9_]{4,16}$/;
    return regex.test(username);
  }
  
  // 验证手机号
  function validatePhone(phone) {
    const regex = /^1[3-9]\d{9}$/;
    return regex.test(phone);
  }
  
  // 验证邮箱
  function validateEmail(email) {
    if (!email) return true; // 选填
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }
  
  // 验证密码强度
  function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
    
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    
    strengthFill.className = 'strength-fill';
    strengthText.className = 'strength-text';
    
    if (password.length === 0) {
      strengthText.textContent = '密码强度';
    } else if (strength <= 1) {
      strengthFill.classList.add('weak');
      strengthText.classList.add('weak');
      strengthText.textContent = '弱';
    } else if (strength <= 2) {
      strengthFill.classList.add('medium');
      strengthText.classList.add('medium');
      strengthText.textContent = '中等';
    } else {
      strengthFill.classList.add('strong');
      strengthText.classList.add('strong');
      strengthText.textContent = '强';
    }
    
    return strength >= 2;
  }
  
  // 用户名实时验证
  usernameInput?.addEventListener('input', function() {
    const status = document.getElementById('usernameStatus');
    const hint = document.getElementById('usernameHint');
    
    if (this.value.length === 0) {
      status.className = 'input-status';
      hint.textContent = '';
      hint.className = 'form-hint';
    } else if (validateUsername(this.value)) {
      status.className = 'input-status valid';
      hint.textContent = '用户名可用';
      hint.className = 'form-hint success';
    } else {
      status.className = 'input-status invalid';
      hint.textContent = '4-16位字母、数字或下划线';
      hint.className = 'form-hint error';
    }
  });
  
  // 密码实时验证
  passwordInput?.addEventListener('input', function() {
    checkPasswordStrength(this.value);
    validateConfirmPassword();
  });
  
  // 确认密码验证
  confirmPasswordInput?.addEventListener('input', validateConfirmPassword);
  
  function validateConfirmPassword() {
    const hint = document.getElementById('confirmHint');
    
    if (confirmPasswordInput.value.length === 0) {
      hint.textContent = '';
      hint.className = 'form-hint';
    } else if (confirmPasswordInput.value === passwordInput.value) {
      hint.textContent = '密码一致';
      hint.className = 'form-hint success';
    } else {
      hint.textContent = '两次输入的密码不一致';
      hint.className = 'form-hint error';
    }
  }
  
  // 发送验证码
  let countdown = 0;
  sendCaptchaBtn?.addEventListener('click', function() {
    if (countdown > 0) return;
    
    if (!validatePhone(phoneInput.value)) {
      showError('请输入正确的手机号');
      return;
    }
    
    // 模拟发送验证码
    countdown = 60;
    this.disabled = true;
    this.textContent = `${countdown}s 后重发`;
    
    const timer = setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        clearInterval(timer);
        this.disabled = false;
        this.textContent = '获取验证码';
      } else {
        this.textContent = `${countdown}s 后重发`;
      }
    }, 1000);
    
    hideError();
  });
  
  // 步骤1验证
  nextStep1?.addEventListener('click', function() {
    hideError();
    
    if (!usernameInput.value.trim()) {
      showError('请输入用户名');
      usernameInput.focus();
      return;
    }
    
    if (!validateUsername(usernameInput.value)) {
      showError('用户名格式不正确');
      usernameInput.focus();
      return;
    }
    
    if (!phoneInput.value.trim()) {
      showError('请输入手机号');
      phoneInput.focus();
      return;
    }
    
    if (!validatePhone(phoneInput.value)) {
      showError('手机号格式不正确');
      phoneInput.focus();
      return;
    }
    
    if (emailInput.value && !validateEmail(emailInput.value)) {
      showError('邮箱格式不正确');
      emailInput.focus();
      return;
    }
    
    goToStep(2);
  });
  
  // 步骤2验证
  nextStep2?.addEventListener('click', function() {
    hideError();
    
    if (!passwordInput.value) {
      showError('请设置密码');
      passwordInput.focus();
      return;
    }
    
    if (passwordInput.value.length < 8) {
      showError('密码至少8位');
      passwordInput.focus();
      return;
    }
    
    if (!checkPasswordStrength(passwordInput.value)) {
      showError('密码强度不够，请包含字母和数字');
      passwordInput.focus();
      return;
    }
    
    if (passwordInput.value !== confirmPasswordInput.value) {
      showError('两次输入的密码不一致');
      confirmPasswordInput.focus();
      return;
    }
    
    if (!captchaInput.value.trim()) {
      showError('请输入验证码');
      captchaInput.focus();
      return;
    }
    
    goToStep(3);
  });
  
  // 上一步
  prevStep2?.addEventListener('click', () => goToStep(1));
  prevStep3?.addEventListener('click', () => goToStep(2));
  
  // 提交注册
  registerForm?.addEventListener('submit', async function(e) {
    e.preventDefault();
    hideError();
    
    if (!agreeTerms.checked) {
      showError('请阅读并同意用户协议和隐私政策');
      return;
    }
    
    // 禁用提交按钮
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="btn-spinner"></div><span>注册中...</span>';
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 显示成功提示
      registerSuccess.classList.remove('hidden');
      registerError.classList.add('hidden');
      
      // 2秒后跳转登录页
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 2000);
      
    } catch (error) {
      showError(error.message || '注册失败，请稍后重试');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="check" style="width: 18px; height: 18px;"></i><span>完成注册</span>';
      lucide.createIcons();
    }
  });
  
  // 输入时隐藏错误
  [usernameInput, phoneInput, emailInput, passwordInput, confirmPasswordInput, captchaInput].forEach(input => {
    input?.addEventListener('input', hideError);
  });
});

