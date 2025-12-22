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
  
  // 地图颜色分级
  mapColors: ['#d4e4fc', '#85b8f8', '#4d94f5', '#2563eb', '#1e40af'],
  
  /**
   * 获取房价对应的颜色等级
   */
  getPriceColorIndex(price) {
    if (price < 10000) return 0;
    if (price < 20000) return 1;
    if (price < 30000) return 2;
    if (price < 50000) return 3;
    return 4;
  },
  
  /**
   * 中国地图配置
   */
  getChinaMapOption(data) {
    // 处理数据格式
    const mapData = data.map(item => ({
      name: item.province_name || item.city_name,
      value: item.city_avg_price,
      city_name: item.city_name,
      total_price: item.city_avg_total_price,
      listing_count: item.listing_count
    }));
    
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#1f2937',
          fontSize: 14
        },
        formatter: function(params) {
          if (!params.data) return params.name + '<br/>暂无数据';
          return `
            <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px;">${params.data.city_name || params.name}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: #6b7280;">均价</span>
              <span style="font-weight: 600; color: #2563eb;">${params.data.value?.toLocaleString() || '--'} 元/㎡</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: #6b7280;">平均总价</span>
              <span style="font-weight: 600;">${params.data.total_price || '--'} 万</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #6b7280;">挂牌数</span>
              <span style="font-weight: 600;">${params.data.listing_count?.toLocaleString() || '--'} 套</span>
            </div>
          `;
        }
      },
      visualMap: {
        min: 0,
        max: 80000,
        left: 'left',
        top: 'bottom',
        show: false,
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
          min: 0.8,
          max: 3
        },
        zoom: 1.2,
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
   * 趋势折线图配置
   */
  getTrendLineOption(data, title = '房价趋势') {
    const months = data.map(item => `${item.month}月`);
    const prices = data.map(item => item.avg_price);
    
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
        formatter: function(params) {
          const data = params[0];
          return `
            <div style="font-weight: 600; margin-bottom: 8px;">${data.name}</div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="width: 10px; height: 10px; background: ${Charts.colors.primary}; border-radius: 50%;"></span>
              <span style="color: #6b7280;">均价</span>
              <span style="font-weight: 600; color: #2563eb; margin-left: auto;">${data.value?.toLocaleString()} 元/㎡</span>
            </div>
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
        data: months,
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12
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
          fontSize: 12,
          formatter: value => (value / 10000).toFixed(1) + '万'
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      series: [{
        name: '房价',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: this.colors.primary,
          width: 3
        },
        itemStyle: {
          color: this.colors.primary,
          borderColor: '#fff',
          borderWidth: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(37, 99, 235, 0.3)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0.05)' }
            ]
          }
        },
        data: prices
      }]
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
  }
};

// 导出
window.Charts = Charts;

