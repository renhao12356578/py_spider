
---

### 8号接口 `/beijing/overview`

**`avg_price` 与 `avg_total_price` 是否重复？**

**不重复，含义不同：**
- **`avg_price`**: 平均**单价** (元/㎡)，模拟数据为 `65000`
- **`avg_total_price`**: 平均**总价** (万元)，模拟数据为 `450`

这两个指标反映不同维度：
- 单价用于比较不同区域/房源的价值密度
- 总价用于衡量购房预算门槛

---

### 15号接口 `/beijing/chart/scatter`

**返回条目是随机还是顺序？**

**当前模拟数据是随机生成的：**
```javascript@r:\works\py_spider\web\spider_html\js\mock-data.js#241:246
points: Array.from({ length: 200 }, (_, i) => ({
  area: 40 + Math.random() * 160,
  total_price: 200 + Math.random() * 1500,
  price_per_sqm: 35000 + Math.random() * 60000,
  district: ['朝阳', '海淀', '西城', '东城', '丰台', '通州'][Math.floor(Math.random() * 6)]
}))
```

每次加载页面时，200个点的 `area`、`total_price`、`price_per_sqm`、`district` 都是随机值。

**如果接真实后端**，返回顺序取决于后端实现（通常按某字段排序或按数据库插入顺序）。
**这里可以扩充，可以按照要求排序，比如价格之类的**

---

### 16号接口 `/beijing/chart/boxplot`

**分析的是房价吗？**

**是的，分析的是各区房价分布（单价 元/㎡）：**
```javascript@r:\works\py_spider\web\spider_html\js\mock-data.js#250:258
boxplotData: {
  boxplot: [
    { district: '西城', min: 70000, q1: 85000, median: 95000, q3: 110000, max: 150000 },
    { district: '东城', min: 65000, q1: 80000, median: 92000, q3: 105000, max: 140000 },
    ...
  ]
}
```

每个区返回 `min`、`q1`(25分位)、`median`(中位数)、`q3`(75分位)、`max`，用于绘制箱线图展示房价分布。

**不传参是否返回所有区数据？**

**是的**。当前 [getBoxplotData()](cci:1://file:///r:/works/py_spider/web/spider_html/js/api.js:383:4-389:5) 方法不接受参数：
```javascript@r:\works\py_spider\web\spider_html\js\api.js#388:390
getBoxplotData() {
  return API.get('/beijing/chart/boxplot');
}
```

模拟数据直接返回6个区的完整箱线图数据。如需按区筛选，需要后端支持并修改接口。