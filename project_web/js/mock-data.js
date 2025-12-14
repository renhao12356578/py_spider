/**
 * 模拟数据模块
 * 用于前端开发测试，后端接口完成后可关闭
 * 房产数据分析系统
 */

const MockData = {
  // ============================================
  // 认证模块
  // ============================================
  auth: {
    // 登录响应
    login: {
      token: 'mock_token_' + Date.now(),
      user: {
        id: 1,
        username: 'demo_user',
        nickname: '演示用户',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=demo',
        vip_level: 1,
        phone: '138****8888'
      }
    },
    
    // 注册响应
    register: {
      user_id: 1,
      username: 'new_user',
      message: '注册成功'
    },
    
    // 验证码响应
    captcha: {
      message: '验证码已发送',
      expires_in: 300
    },
    
    // 用户名检查
    checkUsername: {
      available: true,
      message: '用户名可用'
    },
    
    // 手机号检查
    checkPhone: {
      registered: false,
      message: '手机号未注册'
    }
  },
  
  // ============================================
  // 全国数据模块
  // ============================================
  national: {
    // 全国概览
    overview: {
      national_avg_price: 16580,
      price_change_yoy: -2.3,
      price_change_mom: 0.5,
      highest_city: { name: '北京', price: 65000 },
      lowest_city: { name: '鹤岗', price: 2100 },
      total_listings: 1250000,
      total_cities: 320
    },
    
    // 城市房价数据（地图用）
    cityPrices: {
      cities: [
        { province_name: '北京', city_name: '北京', city_avg_price: 65000, listing_count: 52000, price_change: 1.2 },
        { province_name: '上海', city_name: '上海', city_avg_price: 62000, listing_count: 48000, price_change: -0.5 },
        { province_name: '广东', city_name: '深圳', city_avg_price: 58000, listing_count: 35000, price_change: -1.8 },
        { province_name: '广东', city_name: '广州', city_avg_price: 38000, listing_count: 42000, price_change: 0.3 },
        { province_name: '浙江', city_name: '杭州', city_avg_price: 35000, listing_count: 28000, price_change: 2.1 },
        { province_name: '江苏', city_name: '南京', city_avg_price: 32000, listing_count: 25000, price_change: 0.8 },
        { province_name: '福建', city_name: '厦门', city_avg_price: 45000, listing_count: 15000, price_change: -0.2 },
        { province_name: '天津', city_name: '天津', city_avg_price: 25000, listing_count: 22000, price_change: -1.5 },
        { province_name: '重庆', city_name: '重庆', city_avg_price: 12000, listing_count: 38000, price_change: 1.0 },
        { province_name: '四川', city_name: '成都', city_avg_price: 18000, listing_count: 45000, price_change: 1.5 },
        { province_name: '湖北', city_name: '武汉', city_avg_price: 18500, listing_count: 32000, price_change: -0.8 },
        { province_name: '陕西', city_name: '西安', city_avg_price: 15000, listing_count: 28000, price_change: 2.0 },
        { province_name: '辽宁', city_name: '大连', city_avg_price: 14000, listing_count: 18000, price_change: -2.1 },
        { province_name: '山东', city_name: '青岛', city_avg_price: 22000, listing_count: 25000, price_change: 0.5 },
        { province_name: '湖南', city_name: '长沙', city_avg_price: 11000, listing_count: 30000, price_change: 1.2 },
        { province_name: '河南', city_name: '郑州', city_avg_price: 13000, listing_count: 35000, price_change: -1.0 },
        { province_name: '黑龙江', city_name: '鹤岗', city_avg_price: 2100, listing_count: 5000, price_change: -5.0 }
      ]
    },
    
    // 省份列表
    provinces: {
      provinces: ['北京', '上海', '天津', '重庆', '广东', '浙江', '江苏', '山东', '河南', '四川', '湖北', '湖南', '福建', '陕西', '辽宁', '黑龙江']
    },
    
    // 城市排行榜
    ranking: {
      price: {
        type: 'price',
        ranking: [
          { rank: 1, city_name: '北京', value: 65000, change: 1.2 },
          { rank: 2, city_name: '上海', value: 62000, change: -0.5 },
          { rank: 3, city_name: '深圳', value: 58000, change: -1.8 },
          { rank: 4, city_name: '厦门', value: 45000, change: -0.2 },
          { rank: 5, city_name: '广州', value: 38000, change: 0.3 },
          { rank: 6, city_name: '杭州', value: 35000, change: 2.1 },
          { rank: 7, city_name: '南京', value: 32000, change: 0.8 },
          { rank: 8, city_name: '天津', value: 25000, change: -1.5 },
          { rank: 9, city_name: '青岛', value: 22000, change: 0.5 },
          { rank: 10, city_name: '武汉', value: 18500, change: -0.8 }
        ]
      },
      change: {
        type: 'change',
        ranking: [
          { rank: 1, city_name: '杭州', value: 2.1 },
          { rank: 2, city_name: '西安', value: 2.0 },
          { rank: 3, city_name: '成都', value: 1.5 },
          { rank: 4, city_name: '长沙', value: 1.2 },
          { rank: 5, city_name: '北京', value: 1.2 }
        ]
      }
    },
    
    // 城市搜索
    search: {
      results: [
        { city_name: '北京', province_name: '北京', city_avg_price: 65000 },
        { city_name: '上海', province_name: '上海', city_avg_price: 62000 }
      ]
    },
    
    // 价格趋势
    trend: {
      city_name: '全国',
      trends: [
        { year: 2024, month: 1, avg_price: 16200 },
        { year: 2024, month: 2, avg_price: 16150 },
        { year: 2024, month: 3, avg_price: 16300 },
        { year: 2024, month: 4, avg_price: 16280 },
        { year: 2024, month: 5, avg_price: 16350 },
        { year: 2024, month: 6, avg_price: 16400 },
        { year: 2024, month: 7, avg_price: 16450 },
        { year: 2024, month: 8, avg_price: 16500 },
        { year: 2024, month: 9, avg_price: 16520 },
        { year: 2024, month: 10, avg_price: 16550 },
        { year: 2024, month: 11, avg_price: 16560 },
        { year: 2024, month: 12, avg_price: 16580 }
      ]
    }
  },
  
  // ============================================
  // 北京数据模块
  // ============================================
  beijing: {
    // 北京概览
    overview: {
      avg_price: 65000,
      avg_total_price: 450,
      total_listings: 32000,
      price_change_mom: 0.8,
      price_change_yoy: 1.2,
      hot_districts: ['朝阳', '海淀', '西城']
    },
    
    // 行政区排名
    districtRanking: {
      ranking: [
        { rank: 1, district: '西城', avg_price: 95000, count: 2800, change: 1.2 },
        { rank: 2, district: '东城', avg_price: 92000, count: 2200, change: -0.5 },
        { rank: 3, district: '海淀', avg_price: 78000, count: 6200, change: 2.1 },
        { rank: 4, district: '朝阳', avg_price: 65000, count: 8500, change: 0.8 },
        { rank: 5, district: '丰台', avg_price: 52000, count: 4500, change: -0.3 },
        { rank: 6, district: '石景山', avg_price: 48000, count: 1800, change: 0.5 },
        { rank: 7, district: '通州', avg_price: 38000, count: 3200, change: 1.5 },
        { rank: 8, district: '昌平', avg_price: 35000, count: 2800, change: 0.2 },
        { rank: 9, district: '大兴', avg_price: 42000, count: 2500, change: -0.8 },
        { rank: 10, district: '顺义', avg_price: 32000, count: 1500, change: 0.3 },
        { rank: 11, district: '房山', avg_price: 28000, count: 1200, change: -1.2 },
        { rank: 12, district: '门头沟', avg_price: 35000, count: 800, change: 0.1 }
      ]
    },
    
    // 行政区房价（地图用）
    districtPrices: {
      districts: [
        { name: '西城', avg_price: 95000, count: 2800 },
        { name: '东城', avg_price: 92000, count: 2200 },
        { name: '海淀', avg_price: 78000, count: 6200 },
        { name: '朝阳', avg_price: 65000, count: 8500 },
        { name: '丰台', avg_price: 52000, count: 4500 },
        { name: '石景山', avg_price: 48000, count: 1800 },
        { name: '通州', avg_price: 38000, count: 3200 },
        { name: '昌平', avg_price: 35000, count: 2800 },
        { name: '大兴', avg_price: 42000, count: 2500 },
        { name: '顺义', avg_price: 32000, count: 1500 },
        { name: '房山', avg_price: 28000, count: 1200 },
        { name: '门头沟', avg_price: 35000, count: 800 }
      ]
    },
    
    // 楼层分析
    floorAnalysis: {
      floor_analysis: [
        { category: '低楼层(1-6)', avg_price: 62000, count: 8500, percentage: 26.5 },
        { category: '中楼层(7-15)', avg_price: 65000, count: 15000, percentage: 46.9 },
        { category: '高楼层(16+)', avg_price: 68000, count: 8500, percentage: 26.6 }
      ]
    },
    
    // 户型分析
    layoutAnalysis: {
      layout_analysis: [
        { layout: '1室', avg_price: 55000, avg_total: 280, count: 3200 },
        { layout: '2室', avg_price: 62000, avg_total: 420, count: 15000 },
        { layout: '3室', avg_price: 68000, avg_total: 580, count: 10000 },
        { layout: '4室+', avg_price: 75000, avg_total: 850, count: 3800 }
      ]
    },
    
    // 朝向分析
    orientationAnalysis: {
      orientation_analysis: [
        { orientation: '南', avg_price: 66000, count: 18000 },
        { orientation: '南北', avg_price: 68000, count: 8000 },
        { orientation: '东', avg_price: 62000, count: 3000 },
        { orientation: '西', avg_price: 61000, count: 2000 },
        { orientation: '北', avg_price: 58000, count: 1000 }
      ]
    },
    
    // 电梯分析
    elevatorAnalysis: {
      elevator_analysis: [
        { has_elevator: true, label: '有电梯', avg_price: 67000, count: 28000 },
        { has_elevator: false, label: '无电梯', avg_price: 55000, count: 4000 }
      ]
    },
    
    // 散点图数据
    scatterData: {
      points: Array.from({ length: 200 }, (_, i) => ({
        area: 40 + Math.random() * 160,
        total_price: 200 + Math.random() * 1500,
        price_per_sqm: 35000 + Math.random() * 60000,
        district: ['朝阳', '海淀', '西城', '东城', '丰台', '通州'][Math.floor(Math.random() * 6)]
      }))
    },
    
    // 箱线图数据
    boxplotData: {
      boxplot: [
        { district: '西城', min: 70000, q1: 85000, median: 95000, q3: 110000, max: 150000 },
        { district: '东城', min: 65000, q1: 80000, median: 92000, q3: 105000, max: 140000 },
        { district: '海淀', min: 50000, q1: 65000, median: 78000, q3: 95000, max: 130000 },
        { district: '朝阳', min: 35000, q1: 50000, median: 65000, q3: 80000, max: 120000 },
        { district: '丰台', min: 30000, q1: 42000, median: 52000, q3: 65000, max: 90000 },
        { district: '通州', min: 22000, q1: 30000, median: 38000, q3: 48000, max: 70000 }
      ]
    },
    
    // 房源列表
    houses: {
      total: 32000,
      page: 1,
      page_size: 20,
      houses: [
        { house_id: 1, total_price: 310, price_per_sqm: 35001, area: 88.57, layout: '2室1厅', orientation: '南', floor: '中层', floor_num: 8, has_elevator: '有电梯', region: '朝阳', district: '望京', tags: '精装 南向 近地铁', build_year: 2010 },
        { house_id: 2, total_price: 620, price_per_sqm: 65853, area: 94.15, layout: '3室2厅', orientation: '南北', floor: '高层', floor_num: 18, has_elevator: '有电梯', region: '海淀', district: '中关村', tags: '学区房 满五唯一', build_year: 2005 },
        { house_id: 3, total_price: 890, price_per_sqm: 92708, area: 96.0, layout: '2室2厅', orientation: '南', floor: '中层', floor_num: 12, has_elevator: '有电梯', region: '西城', district: '金融街', tags: '精装 近地铁 学区', build_year: 2008 },
        { house_id: 4, total_price: 450, price_per_sqm: 45000, area: 100.0, layout: '3室1厅', orientation: '东南', floor: '低层', floor_num: 3, has_elevator: '无电梯', region: '丰台', district: '方庄', tags: '满二 南向', build_year: 1998 },
        { house_id: 5, total_price: 280, price_per_sqm: 38356, area: 73.0, layout: '2室1厅', orientation: '南', floor: '中层', floor_num: 10, has_elevator: '有电梯', region: '通州', district: '北苑', tags: '精装 近地铁', build_year: 2015 },
        { house_id: 6, total_price: 520, price_per_sqm: 57778, area: 90.0, layout: '2室2厅', orientation: '南北', floor: '高层', floor_num: 22, has_elevator: '有电梯', region: '朝阳', district: 'CBD', tags: '精装 江景 满五', build_year: 2012 },
        { house_id: 7, total_price: 380, price_per_sqm: 42222, area: 90.0, layout: '3室1厅', orientation: '西南', floor: '中层', floor_num: 9, has_elevator: '有电梯', region: '昌平', district: '回龙观', tags: '近地铁 满二', build_year: 2011 },
        { house_id: 8, total_price: 750, price_per_sqm: 78125, area: 96.0, layout: '3室2厅', orientation: '南', floor: '中层', floor_num: 15, has_elevator: '有电梯', region: '海淀', district: '五道口', tags: '学区房 精装', build_year: 2006 },
        { house_id: 9, total_price: 260, price_per_sqm: 32500, area: 80.0, layout: '2室1厅', orientation: '东', floor: '低层', floor_num: 2, has_elevator: '无电梯', region: '大兴', district: '亦庄', tags: '满五唯一', build_year: 2003 },
        { house_id: 10, total_price: 1200, price_per_sqm: 100000, area: 120.0, layout: '4室2厅', orientation: '南北', floor: '中层', floor_num: 11, has_elevator: '有电梯', region: '东城', district: '东直门', tags: '豪装 满五 学区', build_year: 2009 }
      ]
    }
  },
  
  // ============================================
  // AI 服务模块
  // ============================================
  ai: {
    // AI 推荐
    recommend: {
      recommendations: [
        {
          house_id: 101,
          total_price: 420,
          price_per_sqm: 52500,
          area: 80,
          layout: '2室1厅',
          district: '朝阳',
          orientation: '南',
          floor: '中层',
          match_score: 95.5,
          reason: '该房源位于朝阳区望京，户型为2室1厅，面积80㎡，总价420万，完全符合您的预算和面积需求，且位于中层，采光良好，距离地铁步行5分钟。'
        },
        {
          house_id: 102,
          total_price: 380,
          price_per_sqm: 47500,
          area: 80,
          layout: '2室1厅',
          district: '朝阳',
          orientation: '南北',
          floor: '高层',
          match_score: 92.0,
          reason: '该房源南北通透，高层视野开阔，总价380万在您的预算范围内，性价比较高。'
        },
        {
          house_id: 103,
          total_price: 450,
          price_per_sqm: 50000,
          area: 90,
          layout: '2室2厅',
          district: '海淀',
          orientation: '南',
          floor: '中层',
          match_score: 88.5,
          reason: '海淀区优质房源，面积略大，但户型方正，有较好的增值潜力。'
        }
      ],
      total_matched: 156
    },
    
    // AI 对话响应
    chat: {
      reply: '根据最新数据，朝阳区当前二手房均价约为65,000元/㎡，在北京各区中处于中上水平。朝阳区内部价格差异较大：\n\n• **望京、CBD等热门板块**：均价8-10万/㎡\n• **常营、管庄等区域**：均价4-5万/㎡\n\n如果您有具体的购房需求，我可以为您推荐合适的房源。',
      session_id: 'session_' + Date.now(),
      related_data: {
        district: '朝阳',
        avg_price: 65000
      }
    },
    
    // 聊天历史
    chatHistory: {
      history: [
        { role: 'user', content: '朝阳区现在均价多少？', timestamp: '2024-12-10T10:00:00Z' },
        { role: 'assistant', content: '根据最新数据，朝阳区当前二手房均价约为65,000元/㎡...', timestamp: '2024-12-10T10:00:02Z' },
        { role: 'user', content: '望京的房子怎么样？', timestamp: '2024-12-10T10:01:00Z' },
        { role: 'assistant', content: '望京是朝阳区的热门板块之一，均价约8-9万/㎡...', timestamp: '2024-12-10T10:01:03Z' }
      ]
    },
    
    // 市场评估
    valuation: {
      valuation: {
        estimated_price: 425,
        price_range: { min: 400, max: 450 },
        price_per_sqm: 53125,
        factors: [
          { name: '地理位置', score: 85, weight: 30, detail: '朝阳区望京板块，交通便利' },
          { name: '交通便利', score: 90, weight: 25, detail: '距地铁14号线望京站步行5分钟' },
          { name: '学区资源', score: 70, weight: 20, detail: '对口普通小学，非重点学区' },
          { name: '房屋品质', score: 80, weight: 15, detail: '2010年建成，精装修，维护良好' },
          { name: '社区环境', score: 75, weight: 10, detail: '大型社区，绿化率高，配套齐全' }
        ],
        market_sentiment: '买方市场',
        advice: '议价空间',
        advice_detail: '当前该区域成交周期约45天，建议可与卖家协商5-8%的议价空间。同小区近3个月成交3套，成交价在400-440万之间。'
      }
    }
  },
  
  // ============================================
  // 用户模块
  // ============================================
  user: {
    // 用户信息
    profile: {
      user_id: 1,
      username: 'demo_user',
      phone: '138****8888',
      email: 'demo@example.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=demo',
      nickname: '房产达人',
      vip_level: 1,
      vip_expire: '2025-06-01',
      created_at: '2024-01-01T00:00:00Z'
    },
    
    // 通知设置
    notificationSettings: {
      price_alert: true,
      new_listing: true,
      market_report: false,
      system_notice: true,
      email_notify: false,
      sms_notify: true
    },
    
    // 消息列表
    notifications: {
      total: 5,
      unread: 2,
      notifications: [
        { id: 1, type: 'price_alert', title: '您关注的房源价格下调', content: '望京某小区2室1厅降价20万', read: false, created_at: '2024-12-10T08:00:00Z' },
        { id: 2, type: 'system', title: '系统维护通知', content: '将于12月15日凌晨进行系统维护', read: false, created_at: '2024-12-09T10:00:00Z' },
        { id: 3, type: 'market_report', title: '11月市场报告已发布', content: '北京11月二手房市场分析报告', read: true, created_at: '2024-12-05T09:00:00Z' }
      ]
    }
  },
  
  // ============================================
  // 收藏模块
  // ============================================
  favorites: {
    // 收藏的房源
    houses: {
      total: 5,
      page: 1,
      houses: [
        { favorite_id: 1, house_id: 1, total_price: 420, price_per_sqm: 52500, area: 80, layout: '2室1厅', district: '朝阳', note: '位置不错，考虑中', favorited_at: '2024-12-01T10:00:00Z', price_change: -5 },
        { favorite_id: 2, house_id: 2, total_price: 380, price_per_sqm: 47500, area: 80, layout: '2室1厅', district: '朝阳', note: '', favorited_at: '2024-11-28T15:00:00Z', price_change: 0 },
        { favorite_id: 3, house_id: 3, total_price: 620, price_per_sqm: 65000, area: 95, layout: '3室2厅', district: '海淀', note: '学区房', favorited_at: '2024-11-25T09:00:00Z', price_change: 10 }
      ]
    },
    
    // 关注的城市
    cities: {
      cities: [
        { city_name: '北京', avg_price: 65000, price_change: 1.2, followed_at: '2024-11-01T10:00:00Z' },
        { city_name: '上海', avg_price: 62000, price_change: -0.5, followed_at: '2024-11-15T10:00:00Z' },
        { city_name: '杭州', avg_price: 35000, price_change: 2.1, followed_at: '2024-11-20T10:00:00Z' }
      ]
    },
    
    // 收藏的报告
    reports: {
      reports: [
        { favorite_id: 1, report_id: 10, title: '2024年12月北京房产市场分析', type: 'monthly', favorited_at: '2024-12-05T10:00:00Z' },
        { favorite_id: 2, report_id: 8, title: '2024年Q3全国房价走势报告', type: 'quarterly', favorited_at: '2024-10-15T10:00:00Z' }
      ]
    }
  },
  
  // ============================================
  // 报告模块
  // ============================================
  report: {
    // 报告类型
    types: {
      types: [
        { id: 'monthly', name: '月度报告', description: '每月市场分析', icon: 'calendar' },
        { id: 'quarterly', name: '季度报告', description: '季度深度分析', icon: 'bar-chart-2' },
        { id: 'annual', name: '年度报告', description: '年度全面总结', icon: 'trending-up' },
        { id: 'district', name: '区域报告', description: '特定区域分析', icon: 'map-pin' },
        { id: 'custom', name: '自定义报告', description: '根据需求定制', icon: 'settings' }
      ]
    },
    
    // 报告列表
    list: {
      total: 20,
      page: 1,
      reports: [
        { report_id: 10, title: '2024年12月北京房产市场分析', type: 'monthly', city: '北京', cover_image: '', summary: '本月北京二手房成交量环比上涨15%，均价小幅回升...', published_at: '2024-12-10T00:00:00Z', views: 1250, is_favorited: true },
        { report_id: 9, title: '2024年11月全国房价走势报告', type: 'monthly', city: '全国', cover_image: '', summary: '11月全国房价整体平稳，一线城市微涨...', published_at: '2024-12-05T00:00:00Z', views: 3200, is_favorited: false },
        { report_id: 8, title: '2024年Q3全国房价走势报告', type: 'quarterly', city: '全国', cover_image: '', summary: '三季度全国房地产市场概况...', published_at: '2024-10-15T00:00:00Z', views: 5600, is_favorited: true },
        { report_id: 7, title: '北京海淀区深度分析', type: 'district', city: '北京', cover_image: '', summary: '海淀区房产市场特点及投资建议...', published_at: '2024-09-20T00:00:00Z', views: 2100, is_favorited: false }
      ]
    },
    
    // 报告详情
    detail: {
      report_id: 10,
      title: '2024年12月北京房产市场分析',
      type: 'monthly',
      city: '北京',
      content: '一、市场概述\n2024年12月，北京二手房市场整体呈现回暖态势。受政策利好影响，购房者入市意愿明显提升，市场成交量稳步回升。\n\n二、价格分析\n本月全市二手房均价为65,000元/平方米，环比上涨0.5%，同比下降2.3%。其中：\n- 西城区均价最高，达95,000元/㎡\n- 东城区次之，约92,000元/㎡\n- 海淀区保持在78,000元/㎡左右\n\n三、成交分析\n本月成交量环比上涨15%，主要特点如下：\n1. 刚需户型（2室1厅）成交占比最高，达45%\n2. 90㎡以下中小户型最受欢迎\n3. 朝阳、海淀成交量位居前两位\n\n四、市场展望\n预计未来三个月市场将延续平稳态势，建议购房者：\n1. 关注政策动向，把握入市时机\n2. 优先考虑交通便利、配套成熟的区域\n3. 合理控制预算，避免过度杠杆',
      summary: '本月北京二手房成交量环比上涨15%，均价小幅回升，市场信心逐步恢复。',
      highlights: ['成交量环比上涨15%', '均价同比下降2.3%', '海淀区最受关注', '刚需户型成交活跃'],
      published_at: '2024-12-10T00:00:00Z',
      author: '市场研究部',
    },
    
    // 我的报告
    myReports: {
      reports: [
        { 
          report_id: 100, 
          title: '自定义报告 - 北京朝阳海淀', 
          type: 'custom', 
          status: 'completed', 
          created_at: '2024-12-10T10:00:00Z', 
          summary: '朝阳区和海淀区2024年房产市场综合分析报告',
          content: '一、区域概况\n朝阳区和海淀区是北京最核心的两个区域，房产市场活跃度高。\n\n二、价格对比\n- 海淀区均价：78,000元/㎡\n- 朝阳区均价：65,000元/㎡\n\n三、成交分析\n两区合计成交量占全市35%，其中海淀学区房需求旺盛。\n\n四、投资建议\n建议关注朝阳望京、海淀西北旺等新兴板块。',
          highlights: ['海淀均价78000元/㎡', '朝阳成交量领先', '学区房需求旺盛'],
          author: '系统生成'
        },
        { 
          report_id: 99, 
          title: '自定义报告 - 上海浦东', 
          type: 'custom', 
          status: 'generating', 
          created_at: '2024-12-10T11:00:00Z', 
          summary: '报告生成中...',
          content: '',
          highlights: [],
          author: ''
        }
      ]
    }
  },
  
  // ============================================
  // 系统模块
  // ============================================
  system: {
    // 系统配置
    config: {
      app_name: '房析',
      version: '1.0.0',
      features: {
        ai_chat: true,
        vip_required_features: ['custom_report', 'data_export']
      },
      contact: {
        email: 'support@fangxi.com',
        phone: '400-888-8888'
      }
    },
    
    // 数据更新时间
    dataUpdateTime: {
      last_update: '2024-12-10T08:00:00Z',
      next_update: '2024-12-11T08:00:00Z',
      data_sources: [
        { name: '全国房价', updated_at: '2024-12-10T08:00:00Z' },
        { name: '北京房源', updated_at: '2024-12-10T06:00:00Z' }
      ]
    },
    
    // 版本信息
    version: {
      version: '1.0.0',
      build: '20241210',
      changelog: [
        { version: '1.0.0', date: '2024-12-10', changes: ['首次发布', '支持全国房价查询', '支持AI智能推荐'] }
      ]
    }
  }
};

// 导出
window.MockData = MockData;

