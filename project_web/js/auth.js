/**
 * 认证管理模块
 * 房产数据分析系统
 */

const Auth = {
  /**
   * 检查是否已登录
   * @returns {boolean}
   */
  isLoggedIn() {
    const token = localStorage.getItem('token');
    return !!token;
  },
  
  /**
   * 获取当前用户信息
   * @returns {object|null}
   */
  getUser() {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },
  
  /**
   * 获取 Token
   * @returns {string|null}
   */
  getToken() {
    return localStorage.getItem('token');
  },
  
  /**
   * 保存登录信息
   * @param {string} token
   * @param {object} user
   */
  saveLogin(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
  
  /**
   * 退出登录
   */
  async logout() {
    try {
      // 调用退出登录 API
      await API.auth.logout();
    } catch (error) {
      console.error('退出登录 API 调用失败:', error);
    } finally {
      // 无论 API 是否成功，都清除本地存储
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = 'login.html';
    }
  },
  
  /**
   * 检查登录状态，未登录则跳转
   */
  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  }
};

// 导出
window.Auth = Auth;

