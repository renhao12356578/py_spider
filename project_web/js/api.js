/**
 * API 请求封装模块
 * 房产数据分析系统
 */
const API = {
  // 基础配置
  BASE_URL: 'http://127.0.0.1:5000/api',

  // 模拟模式开关 - 设为 true 使用模拟数据，false 请求真实后端
  MOCK_MODE: false,

  // 模拟延迟（毫秒）- 模拟网络请求延迟
  MOCK_DELAY:0,
  
  /**
   * 模拟延迟
   */
  async mockDelay() {
    return new Promise(resolve => setTimeout(resolve, this.MOCK_DELAY));
  },
  
  /**
   * 通用请求方法
   * @param {string} endpoint - API 端点
   * @param {object} options - 请求配置
   * @returns {Promise<any>} - 响应数据
   */
  async request(endpoint, options = {}) {
    // 如果开启模拟模式，尝试返回模拟数据
    if (this.MOCK_MODE) {
      const mockData = this.getMockData(endpoint, options);
      if (mockData !== null) {
        await this.mockDelay();
        console.log(`[MOCK] ${options.method || 'GET'} ${endpoint}`, mockData);
        return mockData;
      }
    }

    const token = localStorage.getItem('token');

    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(`${this.BASE_URL}${endpoint}`, config);
      const data = await response.json();
      
      // Token 过期处理
      if (data.code === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
        throw new Error('登录已过期，请重新登录');
      }
      
      if (data.code !== 200) {
        throw new Error(data.message || '请求失败');
      }
      
      return data.data;
    } catch (error) {
      console.error('API Error:', error);
      /*
      // 后端不可用时，尝试使用模拟数据
      if (error.message === 'Failed to fetch') {
        const mockData = this.getMockData(endpoint, options);
        if (mockData !== null) {
          console.warn(`[MOCK FALLBACK] 后端不可用，使用模拟数据: ${endpoint}`);
          return mockData;
        }
      }
      */
      throw error;
    }
  },
  
  /**
   * 根据端点获取模拟数据
   * @param {string} endpoint - API 端点
   * @param {object} options - 请求配置
   * @returns {any} - 模拟数据或 null
   */
  getMockData(endpoint, options = {}) {
    if (typeof MockData === 'undefined') {
      console.warn('MockData 未加载');
      return null;
    }
    
    // 认证模块
    if (endpoint === '/auth/login') return MockData.auth.login;
    if (endpoint === '/auth/register') return MockData.auth.register;
    if (endpoint === '/auth/send-captcha') return MockData.auth.captcha;
    if (endpoint.startsWith('/auth/check-username')) return MockData.auth.checkUsername;
    if (endpoint.startsWith('/auth/check-phone')) return MockData.auth.checkPhone;
    if (endpoint === '/auth/forgot-password') return MockData.auth.captcha;
    if (endpoint === '/auth/reset-password') return { message: '密码重置成功' };
    if (endpoint === '/auth/logout') return { message: '已退出登录' };
    
    // 全国数据模块
    if (endpoint === '/national/overview') return MockData.national.overview;
    if (endpoint.startsWith('/national/city-prices')) return MockData.national.cityPrices;
    if (endpoint === '/national/provinces') return MockData.national.provinces;
    if (endpoint.startsWith('/national/ranking')) {
      const type = new URLSearchParams(endpoint.split('?')[1]).get('type') || 'price';
      return MockData.national.ranking[type] || MockData.national.ranking.price;
    }
    if (endpoint.startsWith('/national/search')) return MockData.national.search;
    if (endpoint.startsWith('/national/trend')) return MockData.national.trend;
    
    // 北京数据模块
    if (endpoint === '/beijing/overview') return MockData.beijing.overview;
    if (endpoint === '/beijing/district-ranking') return MockData.beijing.districtRanking;
    if (endpoint === '/beijing/district-prices') return MockData.beijing.districtPrices;
    if (endpoint === '/beijing/analysis/floor') return MockData.beijing.floorAnalysis;
    if (endpoint === '/beijing/analysis/layout') return MockData.beijing.layoutAnalysis;
    if (endpoint === '/beijing/analysis/orientation') return MockData.beijing.orientationAnalysis;
    if (endpoint === '/beijing/analysis/elevator') return MockData.beijing.elevatorAnalysis;
    if (endpoint.startsWith('/beijing/chart/scatter')) return MockData.beijing.scatterData;
    if (endpoint === '/beijing/chart/boxplot') return MockData.beijing.boxplotData;
    if (endpoint.startsWith('/beijing/houses')) return MockData.beijing.houses;
    
    // AI 服务模块
    if (endpoint === '/beijing/ai/recommend') return MockData.ai.recommend;
    if (endpoint === '/beijing/ai/chat') return MockData.ai.chat;
    if (endpoint.startsWith('/beijing/ai/chat/history')) return MockData.ai.chatHistory;
    if (endpoint === '/beijing/ai/valuation') return MockData.ai.valuation;
    
    // 用户模块
    if (endpoint === '/user/profile' && (!options.method || options.method === 'GET')) return MockData.user.profile;
    if (endpoint === '/user/profile' && options.method === 'PUT') return { message: '更新成功' };
    if (endpoint === '/user/change-password') return { message: '密码修改成功' };
    if (endpoint === '/user/avatar') return { avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + Date.now() };
    if (endpoint === '/user/notifications/settings' && (!options.method || options.method === 'GET')) return MockData.user.notificationSettings;
    if (endpoint === '/user/notifications/settings' && options.method === 'PUT') return { message: '设置已保存' };
    if (endpoint.startsWith('/user/notifications')) return MockData.user.notifications;
    
    // 收藏模块
    if (endpoint.startsWith('/favorites/houses') && (!options.method || options.method === 'GET')) return MockData.favorites.houses;
    if (endpoint === '/favorites/houses' && options.method === 'POST') return { favorite_id: Date.now(), message: '收藏成功' };
    if (endpoint.startsWith('/favorites/houses/') && options.method === 'DELETE') return { message: '取消收藏成功' };
    if (endpoint === '/favorites/cities' && (!options.method || options.method === 'GET')) return MockData.favorites.cities;
    if (endpoint === '/favorites/cities' && options.method === 'POST') return { message: '关注成功' };
    if (endpoint.startsWith('/favorites/cities/') && options.method === 'DELETE') return { message: '取消关注成功' };
    if (endpoint.startsWith('/favorites/reports')) return MockData.favorites.reports;
    
    // 报告模块
    if (endpoint === '/reports/types') return MockData.report.types;
    if (endpoint === '/reports' && (!options.method || options.method === 'GET')) return MockData.report.list;
    if (endpoint.match(/^\/reports\/\d+$/) && (!options.method || options.method === 'GET')) return MockData.report.detail;
    if (endpoint === '/reports/generate') return { report_id: Date.now(), status: 'generating', estimated_time: 30, message: '报告生成中' };
    if (endpoint === '/reports/my') return MockData.report.myReports;
    
    // 系统模块
    if (endpoint === '/system/config') return MockData.system.config;
    if (endpoint === '/system/data-update-time') return MockData.system.dataUpdateTime;
    if (endpoint === '/system/feedback') return { ticket_id: 'FB' + Date.now(), message: '感谢您的反馈' };
    if (endpoint === '/system/version') return MockData.system.version;
    
    return null;
  },
  
  /**
   * GET 请求
   */
  get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  },
  
  /**
   * POST 请求
   */
  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },
  
  // ============================================
  // 认证模块
  // ============================================
  auth: {
    /**
     * 用户登录
     * POST /api/auth/login
     */
    login(username, password) {
      return API.post('/auth/login', { username, password });
    },
    
    /**
     * 用户注册
     * POST /api/auth/register
     */
    register(data) {
      return API.post('/auth/register', data);
    },
    
    /**
     * 发送验证码
     * POST /api/auth/send-captcha
     */
    sendCaptcha(phone, type = 'register') {
      return API.post('/auth/send-captcha', { phone, type });
    },
    
    /**
     * 检查用户名是否可用
     * GET /api/auth/check-username
     */
    checkUsername(username) {
      return API.get('/auth/check-username', { username });
    },
    
    /**
     * 检查手机号是否已注册
     * GET /api/auth/check-phone
     */
    checkPhone(phone) {
      return API.get('/auth/check-phone', { phone });
    },
    
    /**
     * 忘记密码 - 发送重置链接
     * POST /api/auth/forgot-password
     */
    forgotPassword(phone) {
      return API.post('/auth/forgot-password', { phone });
    },
    
    /**
     * 重置密码
     * POST /api/auth/reset-password
     */
    resetPassword(phone, captcha, newPassword) {
      return API.post('/auth/reset-password', { phone, captcha, new_password: newPassword });
    },
    
    /**
     * 退出登录
     * POST /api/auth/logout
     */
    logout() {
      return API.post('/auth/logout');
    }
  },
  
  // ============================================
  // 全国数据模块
  // ============================================
  national: {
    /**
     * 获取全国概览数据
     * GET /api/national/overview
     */
    getOverview() {
      return API.get('/national/overview');
    },
    
    /**
     * 获取所有城市房价（地图用）
     * GET /api/national/city-prices
     */
    getCityPrices(params = {}) {
      return API.get('/national/city-prices', params);
    },
    
    /**
     * 获取省份列表
     * GET /api/national/provinces
     */
    getProvinces() {
      return API.get('/national/provinces');
    },
    
    /**
     * 获取城市排行榜
     * GET /api/national/ranking
     * @param {string} type - 排行类型: price / change / rent_ratio
     * @param {number} limit - 返回数量
     * @param {string} order - 排序: desc / asc
     */
    getRanking(type = 'price', limit = 10, order = 'desc') {
      return API.get('/national/ranking', { type, limit, order });
    },
    
    /**
     * 城市搜索
     * GET /api/national/search
     */
    search(keyword) {
      return API.get('/national/search', { keyword });
    },
    
    /**
     * 获取价格趋势
     * GET /api/national/trend
     */
    getTrend(city = '', year = '') {
      const params = {};
      if (city) params.city = city;
      if (year) params.year = year;
      return API.get('/national/trend', params);
    }
  },
  
  // ============================================
  // 北京数据模块
  // ============================================
  beijing: {
    /**
     * 获取北京概览
     * GET /api/beijing/overview
     */
    getOverview() {
      return API.get('/beijing/overview');
    },
    
    /**
     * 获取行政区排名
     * GET /api/beijing/district-ranking
     */
    getDistrictRanking() {
      return API.get('/beijing/district-ranking');
    },
    
    /**
     * 获取行政区房价（地图用）
     * GET /api/beijing/district-prices
     */
    getDistrictPrices() {
      return API.get('/beijing/district-prices');
    },
    
    /**
     * 特征分析 - 楼层
     * GET /api/beijing/analysis/floor
     */
    getFloorAnalysis() {
      return API.get('/beijing/analysis/floor');
    },
    
    /**
     * 特征分析 - 户型
     * GET /api/beijing/analysis/layout
     */
    getLayoutAnalysis() {
      return API.get('/beijing/analysis/layout');
    },
    
    /**
     * 特征分析 - 朝向
     * GET /api/beijing/analysis/orientation
     */
    getOrientationAnalysis() {
      return API.get('/beijing/analysis/orientation');
    },
    
    /**
     * 特征分析 - 电梯
     * GET /api/beijing/analysis/elevator
     */
    getElevatorAnalysis() {
      return API.get('/beijing/analysis/elevator');
    },
    
    /**
     * 散点图数据
     * GET /api/beijing/chart/scatter
     */
    getScatterData(params = {}) {
      return API.get('/beijing/chart/scatter', params);
    },
    
    /**
     * 箱线图数据
     * GET /api/beijing/chart/boxplot
     */
    getBoxplotData() {
      return API.get('/beijing/chart/boxplot');
    },
    
    /**
     * 房源列表查询
     * GET /api/beijing/houses
     */
    getHouses(params = {}) {
      return API.get('/beijing/houses', params);
    }
  },
  
  // ============================================
  // AI 服务模块
  // ============================================
  ai: {
    /**
     * AI 智能推荐
     * POST /api/beijing/ai/recommend
     */
    recommend(params) {
      return API.post('/beijing/ai/recommend', params);
    },
    
    /**
     * AI 对话
     * POST /api/beijing/ai/chat
     */
    chat(message, sessionId) {
      return API.post('/beijing/ai/chat', { message, session_id: sessionId });
    },
    
    /**
     * 获取聊天历史
     * GET /api/beijing/ai/chat/history
     */
    getChatHistory(sessionId) {
      return API.get('/beijing/ai/chat/history', { session_id: sessionId });
    },
    
    /**
     * 市场评估
     * POST /api/beijing/ai/valuation
     */
    getValuation(houseId) {
      return API.post('/beijing/ai/valuation', { house_id: houseId });
    }
  },
  
  // ============================================
  // 用户模块
  // ============================================
  user: {
    /**
     * 获取当前用户信息
     * GET /api/user/profile
     */
    getProfile() {
      return API.get('/user/profile');
    },
    
    /**
     * 更新用户信息
     * PUT /api/user/profile
     */
    updateProfile(data) {
      return API.request('/user/profile', {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    },
    
    /**
     * 修改密码
     * POST /api/user/change-password
     */
    changePassword(oldPassword, newPassword) {
      return API.post('/user/change-password', { 
        old_password: oldPassword, 
        new_password: newPassword 
      });
    },
    
    /**
     * 获取通知设置
     * GET /api/user/notifications/settings
     */
    getNotificationSettings() {
      return API.get('/user/notifications/settings');
    },
    
    /**
     * 更新通知设置
     * PUT /api/user/notifications/settings
     */
    updateNotificationSettings(settings) {
      return API.request('/user/notifications/settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      });
    },
    
    /**
     * 获取消息列表
     * GET /api/user/notifications
     */
    getNotifications(params = {}) {
      return API.get('/user/notifications', params);
    },
    
    /**
     * 标记消息已读
     * POST /api/user/notifications/read
     */
    markNotificationRead(ids) {
      return API.post('/user/notifications/read', { ids });
    }
  },
  
  // ============================================
  // 收藏模块
  // ============================================
  favorites: {
    /**
     * 获取收藏的房源列表
     * GET /api/favorites/houses
     */
    getHouses(params = {}) {
      return API.get('/favorites/houses', params);
    },
    
    /**
     * 添加房源收藏
     * POST /api/favorites/houses
     */
    addHouse(houseId, note = '') {
      return API.post('/favorites/houses', { house_id: houseId, note });
    },
    
    /**
     * 取消房源收藏
     * DELETE /api/favorites/houses/:id
     */
    removeHouse(houseId) {
      return API.request(`/favorites/houses/${houseId}`, { method: 'DELETE' });
    },
    
    /**
     * 获取关注的城市列表
     * GET /api/favorites/cities
     */
    getCities() {
      return API.get('/favorites/cities');
    },
    
    /**
     * 添加城市关注
     * POST /api/favorites/cities
     */
    addCity(cityName) {
      return API.post('/favorites/cities', { city_name: cityName });
    },
    
    /**
     * 取消城市关注
     * DELETE /api/favorites/cities/:name
     */
    removeCity(cityName) {
      return API.request(`/favorites/cities/${encodeURIComponent(cityName)}`, { method: 'DELETE' });
    },
    
    /**
     * 获取收藏的报告列表
     * GET /api/favorites/reports
     */
    getReports(params = {}) {
      return API.get('/favorites/reports', params);
    },
    
    /**
     * 添加报告收藏
     * POST /api/favorites/reports
     */
    addReport(reportId) {
      return API.post('/favorites/reports', { report_id: reportId });
    },
    
    /**
     * 取消报告收藏
     * DELETE /api/favorites/reports/:id
     */
     
    removeReport(reportId) {
      return API.request(`/favorites/reports/${reportId}`, { method: 'DELETE' });
    }
  },
  
  // ============================================
  // 报告模块
  // ============================================
  report: {
    /**
     * 获取报告类型列表
     * GET /api/reports/types
     */
    getTypes() {
      return API.get('/reports/types');
    },
    
    /**
     * 获取报告列表
     * GET /api/reports
     */
    getList(params = {}) {
      return API.get('/reports', params);
    },
    
    /**
     * 获取报告详情
     * GET /api/reports/:id
     */
    getDetail(reportId) {
      return API.get(`/reports/${reportId}`);
    },
    
    /**
     * 生成自定义报告
     * POST /api/reports/generate
     */
    generate(params) {
      return API.post('/reports/generate', params);
    },
    
    /**
     * 获取我的报告
     * GET /api/reports/my
     */
    getMyReports(params = {}) {
      return API.get('/reports/my', params);
    },
    
    /**
     * 删除我的报告
     * DELETE /api/reports/:id
     */
    deleteReport(reportId) {
      return API.request(`/reports/${reportId}`, { method: 'DELETE' });
    }
  },
  
  // ============================================
  // 系统模块
  // ============================================
  system: {
    /**
     * 获取系统配置
     * GET /api/system/config
     */
    getConfig() {
      return API.get('/system/config');
    },
    
    /**
     * 获取数据更新时间
     * GET /api/system/data-update-time
     */
    getDataUpdateTime() {
      return API.get('/system/data-update-time');
    },
    
    /**
     * 提交反馈
     * POST /api/system/feedback
     */
    submitFeedback(data) {
      return API.post('/system/feedback', data);
    },
    
    /**
     * 获取版本信息
     * GET /api/system/version
     */
    getVersion() {
      return API.get('/system/version');
    }
  }
};

// 导出
window.API = API;
