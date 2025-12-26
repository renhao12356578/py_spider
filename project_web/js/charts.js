/**
 * ECharts 图表配置模块
 * 房产数据分析系统
 */

const Charts = {
  // 主题色
  colors: {
    primary: '#2563eb',
    primaryLight: '#dbeafe',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    text: '#1f2937',
    textSecondary: '#6b7280',
    border: '#e5e7eb'
  },
  
  // 柱状图配色方案（多色）
  barColors: [
    '#2563eb', // 蓝
    '#10b981', // 绿
    '#f59e0b', // 橙
    '#06b6d4', // 青
    '#ef4444', // 红
    '#8b5cf6', // 紫
    '#ec4899', // 粉
    '#14b8a6', // 蓝绿
    '#a3e635', // 亮绿
    '#f472b6', // 玫红
    '#22d3ee', // 亮青
    '#fb923c'  // 橘
  ],
  
  // 地图颜色分级（高对比度，适应国内房价）
  mapColors: ['#e8f5e9', '#a5d6a7', '#fff176', '#ffb74d', '#ef5350', '#b71c1c'],
  
  /**
   * 获取房价对应的颜色等级
   */
  getPriceColorIndex(price) {
    if (price < 6000) return 0;   // 浅绿 - 低价
    if (price < 10000) return 1;  // 绿色 - 偏低
    if (price < 15000) return 2;  // 黄色 - 中等
    if (price < 22000) return 3;  // 橙色 - 偏高
    if (price < 30000) return 4;  // 红色 - 高价
    return 5;                      // 深红 - 极高
  },
  
  /**
   * 中国地图配置
   */
  getChinaMapOption(data) {
    // 按省份聚合数据
    const provinceMap = {};
    data.forEach(item => {
      const province = item.province_name;
      if (!provinceMap[province]) {
        provinceMap[province] = {
          totalPrice: 0,
          totalListing: 0,
          count: 0,
          cities: []
        };
      }
      provinceMap[province].totalPrice += item.city_avg_price * item.listing_count;
      provinceMap[province].totalListing += item.listing_count;
      provinceMap[province].count++;
      provinceMap[province].cities.push(item.city_name);
    });
    
    // 转换为地图数据格式
    const mapData = Object.entries(provinceMap).map(([province, info]) => ({
      name: province,
      value: info.totalListing > 0 ? Math.round(info.totalPrice / info.totalListing) : 0,
      listing_count: info.totalListing,
      city_count: info.count,
      cities: info.cities.slice(0, 5).join('、')
    }));
    
    return {
      tooltip: {
        show: false
      },
      visualMap: {
        min: 0,
        max: 35000,
        left: 'left',
        top: 'bottom',
        show: true,
        text: ['高', '低'],
        textStyle: {
          color: '#6b7280'
        },
        inRange: {
          color: this.mapColors
        },
        calculable: true
      },
      series: [{
        name: '房价',
        type: 'map',
        map: 'china',
        roam: true,
        scaleLimit: {
          min: 1,
          max: 3
        },
        zoom: 1.25,
        center: [105, 36],
        label: {
          show: true,
          fontSize: 10,
          color: '#6b7280'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 12,
            fontWeight: 'bold',
            color: '#1f2937'
          },
          itemStyle: {
            areaColor: '#fef3c7',
            borderColor: '#f59e0b',
            borderWidth: 2
          }
        },
        itemStyle: {
          areaColor: '#f3f4f6',
          borderColor: '#d1d5db',
          borderWidth: 1
        },
        data: mapData
      }]
    };
  },
  
  /**
   * 趋势折线图配置 - 支持真实数据和多种预测数据
   */
  getTrendLineOption(data, title = '房价趋势') {
    // 分离真实数据和预测数据
    const existData = data.filter(item => item.predict === 'exist');
    const predictMethods = [...new Set(data.filter(item => item.predict !== 'exist').map(item => item.predict))];
    
    const months = data.map(item => `${item.year}-${item.month}月`);
    const uniqueMonths = [...new Set(months)];
    
    // 构建系列数据
    const series = [];
    
    // 真实数据系列
    if (existData.length > 0) {
      series.push({
        name: '真实房价',
        type: 'line',
        smooth: 0.6,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: this.colors.primary, width: 2 },
        itemStyle: { color: this.colors.primary },
        data: uniqueMonths.map(m => {
          const item = existData.find(d => `${d.year}-${d.month}月` === m);
          return item ? item.avg_price : null;
        })
      });
    }
    
    // 预测数据系列（不同颜色）
    const predictColors = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    predictMethods.forEach((method, idx) => {
      const methodData = data.filter(item => item.predict === method);
      series.push({
        name: method,
        type: 'line',
        smooth: 0.6,
        symbol: 'diamond',
        symbolSize: 6,
        lineStyle: { color: predictColors[idx % 4], width: 2, type: 'dashed' },
        itemStyle: { color: predictColors[idx % 4] },
        data: uniqueMonths.map(m => {
          const item = methodData.find(d => `${d.year}-${d.month}月` === m);
          return item ? item.avg_price : null;
        })
      });
    });
    
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: { color: '#1f2937' }
      },
      legend: {
        show: predictMethods.length > 0,
        bottom: 0,
        textStyle: { fontSize: 11 }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: uniqueMonths,
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisLabel: { color: '#6b7280', fontSize: 11, rotate: 45 },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        scale: true,
        axisLabel: {
          color: '#6b7280',
          fontSize: 12,
          formatter: value => (value / 10000).toFixed(4) + '万'
        },
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
      },
      series: series
    };
  },
  
  /**
   * 柱状图配置
   */
  getBarChartOption(data, xField, yField, title = '') {
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#1f2937'
        },
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: title ? '15%' : '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item[xField]),
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12,
          rotate: data.length > 8 ? 45 : 0
        },
        axisTick: {
          show: false
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          show: false
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      series: [{
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          // 每个柱子使用不同颜色
          color: (params) => {
            const palette = Charts.barColors || [];
            return palette[params.dataIndex % palette.length] || Charts.colors.primary;
          },
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            // 高亮时同色加深（简单处理：不改变颜色）
            color: (params) => {
              const palette = Charts.barColors || [];
              return palette[params.dataIndex % palette.length] || Charts.colors.primary;
            }
          }
        },
        data: data.map(item => item[yField])
      }]
    };
  },
  
  /**
   * 饼图配置
   */
  getPieChartOption(data, nameField, valueField, title = '') {
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#1f2937'
        },
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: {
          color: '#6b7280',
          fontSize: 12
        }
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        },
        data: data.map((item, index) => ({
          name: item[nameField],
          value: item[valueField],
          itemStyle: {
            color: [
              this.colors.primary,
              this.colors.success,
              this.colors.warning,
              this.colors.info,
              this.colors.danger,
              '#8b5cf6',
              '#ec4899',
              '#14b8a6'
            ][index % 8]
          }
        }))
      }]
    };
  },
  
  /**
   * 散点图配置
   */
  getScatterChartOption(data, xField, yField, colorField, title = '') {
    // 按区域分组
    const groups = {};
    data.forEach(item => {
      const group = item[colorField] || '其他';
      if (!groups[group]) groups[group] = [];
      groups[group].push([item[xField], item[yField]]);
    });
    
    const colors = [
      this.colors.primary, this.colors.success, this.colors.warning,
      this.colors.danger, this.colors.info, '#8b5cf6', '#ec4899', '#14b8a6'
    ];
    
    const series = Object.keys(groups).map((name, index) => ({
      name: name,
      type: 'scatter',
      symbolSize: 8,
      itemStyle: {
        color: colors[index % colors.length],
        opacity: 0.7
      },
      emphasis: {
        itemStyle: {
          opacity: 1,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      },
      data: groups[name]
    }));
    
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#1f2937'
        },
        formatter: function(params) {
          return `
            <div style="font-weight: 600; margin-bottom: 8px;">${params.seriesName}</div>
            <div>面积: ${params.data[0]} ㎡</div>
            <div>总价: ${params.data[1]} 万</div>
          `;
        }
      },
      legend: {
        data: Object.keys(groups),
        top: 10,
        textStyle: {
          color: '#6b7280',
          fontSize: 12
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '面积 (㎡)',
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280'
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      yAxis: {
        type: 'value',
        name: '总价 (万)',
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        axisLine: {
          show: false
        },
        axisLabel: {
          color: '#6b7280'
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      series: series
    };
  },
  
  /**
   * 箱线图配置
   */
  getBoxplotOption(data, title = '') {
    const categories = data.map(item => item.district);
    const boxData = data.map(item => [
      item.min, item.q1, item.median, item.q3, item.max
    ]);
    
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#1f2937'
        },
        formatter: function(params) {
          return `
            <div style="font-weight: 600; margin-bottom: 8px;">${params.name}</div>
            <div>最小值: ${params.data[1]?.toLocaleString()} 元/㎡</div>
            <div>Q1: ${params.data[2]?.toLocaleString()} 元/㎡</div>
            <div>中位数: ${params.data[3]?.toLocaleString()} 元/㎡</div>
            <div>Q3: ${params.data[4]?.toLocaleString()} 元/㎡</div>
            <div>最大值: ${params.data[5]?.toLocaleString()} 元/㎡</div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12,
          rotate: categories.length > 8 ? 45 : 0
        },
        axisTick: {
          show: false
        }
      },
      yAxis: {
        type: 'value',
        name: '单价 (元/㎡)',
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        axisLine: {
          show: false
        },
        axisLabel: {
          color: '#6b7280',
          formatter: value => (value / 10000).toFixed(0) + '万'
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      series: [{
        name: '房价分布',
        type: 'boxplot',
        data: boxData,
        itemStyle: {
          color: this.colors.primaryLight,
          borderColor: this.colors.primary,
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            borderColor: '#1d4ed8',
            borderWidth: 3
          }
        }
      }]
    };
  },
  
  /**
   * 城市分级气泡图配置
   */
  getCityClusteringOption(cities) {
    const tierColors = {
      '一线城市': '#ef4444',
      '二线城市': '#f59e0b',
      '三线城市': '#10b981',
      '四线城市': '#06b6d4'
    };
    
    const seriesData = {};
    cities.forEach(city => {
      const tier = city.city_tier;
      if (!seriesData[tier]) {
        seriesData[tier] = [];
      }
      seriesData[tier].push({
        name: city.city_name,
        value: [city.city_avg_price, city.listing_count, city.city_avg_total_price]
      });
    });
    
    const series = Object.entries(seriesData).map(([tier, data]) => ({
      name: tier,
      type: 'scatter',
      symbolSize: (val) => Math.sqrt(val[1]) / 10,
      data: data,
      itemStyle: {
        color: tierColors[tier]
      }
    }));
    
    return {
      title: {
        text: '城市分级分布',
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const data = params.value;
          return `${params.seriesName}<br/>${params.name}<br/>均价: ${this.formatPrice(data[0])}<br/>挂牌量: ${data[1]}<br/>总价: ${data[2]}万`;
        }
      },
      legend: {
        data: ['一线城市', '二线城市', '三线城市', '四线城市'],
        bottom: 10
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'value',
        name: '城市均价 (元/㎡)',
        axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
      },
      yAxis: {
        type: 'value',
        name: '挂牌量',
        axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
      },
      series: series
    };
  },
  
  /**
   * 区县涨跌比热力图配置
   */
  getDistrictHeatmapOption(heatmap) {
    const data = heatmap.map(item => ({
      name: `${item.city_name}-${item.district_name}`,
      value: [item.district_avg_price, item.district_ratio]
    }));
    
    return {
      title: {
        text: '区县涨跌热力分布',
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `${params.name}<br/>均价: ${this.formatPrice(params.value[0])}<br/>涨跌比: ${params.value[1]}%`;
        }
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'value',
        name: '区县均价 (元/㎡)',
        axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
      },
      yAxis: {
        type: 'value',
        name: '涨跌比 (%)'
      },
      visualMap: {
        min: -10,
        max: 10,
        dimension: 1,
        orient: 'vertical',
        right: 10,
        top: 'center',
        text: ['涨', '跌'],
        inRange: {
          color: ['#10b981', '#fbbf24', '#ef4444']
        }
      },
      series: [{
        type: 'scatter',
        symbolSize: 8,
        data: data
      }]
    };
  },
  
  /**
   * 挂牌量TOP排行配置
   */
  getListingRankingOption(ranking) {
    const cities = ranking.map(item => item.city_name);
    const listings = ranking.map(item => item.listing_count);
    
    return {
      title: {
        text: '城市挂牌量排行',
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: { left: '3%', right: '4%', top: '15%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
      },
      yAxis: {
        type: 'category',
        data: cities,
        inverse: true
      },
      series: [{
        type: 'bar',
        data: listings,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ])
        }
      }]
    };
  },
  
  /**
   * 区县价格排行配置
   */
  getDistrictPriceRankingOption(ranking) {
    const districts = ranking.map(item => `${item.city_name}-${item.district_name}`);
    const prices = ranking.map(item => item.district_avg_price);
    
    return {
      title: {
        text: '区县房价排行',
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          const p = params[0];
          return `${p.name}<br/>均价: ${this.formatPrice(p.value)}`;
        }
      },
      grid: { left: '3%', right: '4%', top: '15%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
      },
      yAxis: {
        type: 'category',
        data: districts,
        inverse: true,
        axisLabel: { fontSize: 10 }
      },
      series: [{
        type: 'bar',
        data: prices,
        itemStyle: { color: this.colors.primary }
      }]
    };
  },
  
  /**
   * 同城区县对比配置
   */
  getCityDistrictsOption(districts, cityName) {
    const names = districts.map(d => d.district_name);
    const prices = districts.map(d => d.district_avg_price);
    const ratios = districts.map(d => d.district_ratio);
    
    return {
      title: {
        text: `${cityName} 区县对比`,
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['区县均价', '涨跌比'],
        bottom: 10
      },
      grid: { left: '3%', right: '4%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: { rotate: 45, fontSize: 10 }
      },
      yAxis: [
        {
          type: 'value',
          name: '均价 (元/㎡)',
          axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' }
        },
        {
          type: 'value',
          name: '涨跌比 (%)'
        }
      ],
      series: [
        {
          name: '区县均价',
          type: 'bar',
          data: prices,
          itemStyle: { color: this.colors.primary }
        },
        {
          name: '涨跌比',
          type: 'line',
          yAxisIndex: 1,
          data: ratios,
          itemStyle: { color: this.colors.warning }
        }
      ]
    };
  },
  
  /**
   * 区县涨跌榜配置
   */
  getDistrictChangeRankingOption(ranking, order) {
    const districts = ranking.map(item => `${item.city_name}-${item.district_name}`);
    const ratios = ranking.map(item => item.district_ratio);
    
    return {
      title: {
        text: order === 'desc' ? '区县涨幅榜' : '区县跌幅榜',
        left: 'center',
        textStyle: { color: this.colors.text, fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          const p = params[0];
          return `${p.name}<br/>涨跌比: ${p.value}%`;
        }
      },
      grid: { left: '3%', right: '4%', top: '15%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: v => v + '%' }
      },
      yAxis: {
        type: 'category',
        data: districts,
        inverse: true,
        axisLabel: { fontSize: 10 }
      },
      series: [{
        type: 'bar',
        data: ratios,
        itemStyle: {
          color: (params) => params.value > 0 ? this.colors.danger : this.colors.success
        }
      }]
    };
  },
  
  formatPrice(price) {
    if (!price) return '0';
    return (price / 10000).toFixed(2) + '万';
  }
};

// 导出
window.Charts = Charts;

