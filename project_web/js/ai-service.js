/**
 * AI 服务模块
 * 房产数据分析系统
 */

const AIService = {
  // 生成唯一会话 ID
  sessionId: null,
  
  /**
   * 获取或创建会话 ID
   */
  getSessionId() {
    if (!this.sessionId) {
      this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    return this.sessionId;
  },
  
  /**
   * AI 智能推荐
   * @param {object} params - 推荐参数
   */
  async recommend(params) {
    try {
      const data = await API.ai.recommend(params);
      return data;
    } catch (error) {
      console.error('AI 推荐失败:', error);
      throw error;
    }
  },
  
  /**
   * AI 对话
   * @param {string} message - 用户消息
   */
  async chat(message) {
    try {
      const sessionId = this.getSessionId();
      const data = await API.ai.chat(message, sessionId);
      return data;
    } catch (error) {
      console.error('AI 对话失败:', error);
      throw error;
    }
  },
  
  /**
   * 获取聊天历史
   */
  async getChatHistory() {
    try {
      const sessionId = this.getSessionId();
      const data = await API.ai.getChatHistory(sessionId);
      return data;
    } catch (error) {
      console.error('获取聊天历史失败:', error);
      throw error;
    }
  },
  
  /**
   * 获取市场评估
   * @param {number} houseId - 房源 ID
   */
  async getValuation(houseId) {
    try {
      const data = await API.ai.getValuation(houseId);
      return data;
    } catch (error) {
      console.error('获取市场评估失败:', error);
      throw error;
    }
  },
  
  /**
   * 格式化推荐结果为 HTML
   * @param {array} recommendations - 推荐列表
   */
  formatRecommendations(recommendations) {
    if (!recommendations || !recommendations.length) {
      return `
        <div class="empty-result">
          <i data-lucide="search-x"></i>
          <h4>未找到匹配房源</h4>
          <p>请尝试调整筛选条件</p>
        </div>
      `;
    }
    
    let html = '';
    recommendations.forEach(item => {
      html += `
        <div class="recommend-item" data-house-id="${item.house_id}">
          <div class="recommend-header">
            <div>
              <div class="recommend-title">${item.district || '北京'} · ${item.layout || '暂无户型'}</div>
              <div class="recommend-tags">
                <span class="tag tag-primary">${item.layout || '-'}</span>
                <span class="tag">${item.area || '-'}㎡</span>
                ${item.has_elevator ? '<span class="tag tag-success">有电梯</span>' : ''}
              </div>
            </div>
            <div class="recommend-score">
              <span class="score-value">${item.match_score?.toFixed(1) || '-'}</span>
              <span class="score-label">匹配度</span>
            </div>
          </div>
          
          <div class="recommend-info">
            <div class="info-item">
              <span class="info-label">总价</span>
              <span class="info-value">${item.total_price?.toFixed(0) || '-'}万</span>
            </div>
            <div class="info-item">
              <span class="info-label">单价</span>
              <span class="info-value">${item.price_per_sqm?.toLocaleString() || '-'}元/㎡</span>
            </div>
            <div class="info-item">
              <span class="info-label">面积</span>
              <span class="info-value">${item.area || '-'}㎡</span>
            </div>
            <div class="info-item">
              <span class="info-label">楼层</span>
              <span class="info-value">${item.floor || '-'}层</span>
            </div>
          </div>
          
          ${item.reason ? `
            <div class="recommend-reason">
              <div class="reason-label">
                <i data-lucide="sparkles" style="width: 14px; height: 14px;"></i>
                AI 推荐理由
              </div>
              <div class="reason-text">${item.reason}</div>
            </div>
          ` : ''}
        </div>
      `;
    });
    
    return html;
  },
  
  /**
   * 格式化聊天消息为 HTML
   * @param {string} role - 角色 (user/assistant)
   * @param {string} content - 消息内容
   */
  formatChatMessage(role, content) {
    const avatar = role === 'user' ? '👤' : '🤖';
    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    return `
      <div class="chat-message ${role}">
        <div class="chat-avatar">${avatar}</div>
        <div>
          <div class="chat-bubble">${this.formatMessageContent(content)}</div>
          <div class="chat-time">${time}</div>
        </div>
      </div>
    `;
  },
  
  /**
   * 格式化消息内容（支持换行）
   * @param {string} content - 消息内容
   */
  formatMessageContent(content) {
    if (!content) return '';
    return content.replace(/\n/g, '<br>');
  },
  
  /**
   * 格式化市场评估报告
   * @param {object} valuation - 评估数据
   */
  formatValuation(valuation) {
    if (!valuation) return '';
    
    const adviceBadgeClass = {
      '快速入手': 'buy',
      '持平观望': 'hold',
      '议价空间': 'negotiate'
    };
    
    let factorsHtml = '';
    if (valuation.factors) {
      valuation.factors.forEach(factor => {
        factorsHtml += `
          <div class="factor-item">
            <span class="factor-name">${factor.name}</span>
            <div class="factor-bar">
              <div class="factor-fill" style="width: ${factor.score}%;"></div>
            </div>
            <span class="factor-score">${factor.score}</span>
          </div>
        `;
      });
    }
    
    return `
      <div class="valuation-card">
        <div class="valuation-header">
          <div class="valuation-price">
            <div class="valuation-price-value">${valuation.estimated_price || '-'}万</div>
            <div class="valuation-price-label">AI 估值</div>
          </div>
          <div class="valuation-range">
            <span>预估区间：${valuation.price_range?.min || '-'} - ${valuation.price_range?.max || '-'}万</span>
          </div>
        </div>
        
        <div class="factors-list">
          ${factorsHtml}
        </div>
        
        <div class="market-advice">
          <div class="advice-header">
            <span class="advice-type">${valuation.market_sentiment || '市场分析'}</span>
            <span class="advice-badge ${adviceBadgeClass[valuation.advice] || 'hold'}">${valuation.advice || '观望'}</span>
          </div>
          <div class="advice-text">${valuation.advice_detail || '暂无详细建议'}</div>
        </div>
      </div>
    `;
  }
};

// 导出
window.AIService = AIService;

