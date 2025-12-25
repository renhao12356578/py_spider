#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试报告生成脚本
用于测试 ReportDatabase 类的报告创建和图片生成功能
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportDB import ReportDatabase


def create_test_report_data():
    """生成测试报告的数据"""
    test_reports = [
        {
            "title": "北京海淀区房地产市场分析报告",
            "summary": "本报告深入分析了北京海淀区2024年房地产市场的发展趋势，包括价格走势、成交量变化以及未来预测。",
            "content": """# 北京海淀区房地产市场分析报告

## 一、市场概况

北京海淀区作为科技创新中心，房地产市场一直保持较高活跃度。2024年，海淀区房地产市场呈现出以下特点：

### 1.1 价格走势
- 平均房价：85,000元/平方米
- 同比增长：3.5%
- 环比增长：1.2%

### 1.2 成交量分析
- 年度成交套数：12,500套
- 成交面积：150万平方米
- 同比增长：8.3%

## 二、区域热点

### 2.1 中关村片区
中关村作为科技企业聚集地，周边配套设施完善，教育资源优质，房价保持稳定增长。

### 2.2 五道口区域
毗邻多所知名高校，租赁市场活跃，投资价值较高。

### 2.3 上地产业园
科技产业带动效应明显，新房供应充足，价格相对合理。

## 三、市场预测

### 3.1 短期趋势（未来6个月）
预计价格将保持平稳，波动幅度不超过2%。

### 3.2 中期趋势（未来1-2年）
随着区域产业升级和基础设施改善，房价有望温和上涨。

## 四、投资建议

1. 关注地铁沿线项目
2. 重视学区房的长期价值
3. 注意政策调控影响
4. 分散投资降低风险

## 五、结论

海淀区房地产市场整体呈现稳中有升的态势，具有较好的投资价值。建议投资者根据自身需求，选择合适的区域和项目。

---
报告生成时间：{report_time}
""".format(report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "report_type": "市场分析",
            "city": "北京",
            "area": "海淀区"
        },
        {
            "title": "上海浦东新区投资价值报告",
            "summary": "浦东新区作为上海的经济中心，本报告评估了该区域的房地产投资价值和回报率分析。",
            "content": """# 上海浦东新区投资价值报告

## 一、区域概况

浦东新区是上海的金融和贸易中心，拥有完善的基础设施和优越的地理位置。

### 1.1 经济指标
- GDP增速：7.2%
- 人均可支配收入：120,000元/年
- 外资企业数量：15,000家

### 1.2 房地产现状
- 平均房价：72,000元/平方米
- 租售比：1:450
- 空置率：8.5%

## 二、投资价值分析

### 2.1 地理位置优势
- 毗邻陆家嘴金融区
- 交通便利，地铁线路密集
- 国际学校和医疗资源丰富

### 2.2 产业支撑
- 金融服务业
- 高端制造业
- 现代服务业

## 三、投资回报率测算

### 3.1 租金收益
预期年租金回报率：2.5% - 3.0%

### 3.2 资本增值
预期年资本增值率：4% - 6%

### 3.3 综合回报
预期综合年回报率：6.5% - 9%

## 四、风险提示

1. 政策调控风险
2. 市场供需变化
3. 利率波动影响
4. 区域竞争加剧

## 五、投资建议

- 优先考虑核心商圈
- 关注新兴产业园区
- 长期持有为主
- 做好资金规划

---
报告生成时间：{report_time}
""".format(report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "report_type": "投资价值报告",
            "city": "上海",
            "area": "浦东新区"
        },
        {
            "title": "深圳南山区季度市场报告",
            "summary": "2024年第四季度深圳南山区房地产市场动态总结，包括成交数据、价格变化和市场热点。",
            "content": """# 深圳南山区2024年Q4市场报告

## 一、季度概况

2024年第四季度，南山区房地产市场保持活跃，科技产业带动效应明显。

### 1.1 成交数据
- 本季度成交套数：3,200套
- 成交金额：280亿元
- 环比增长：5.8%

### 1.2 价格变化
- 平均房价：95,000元/平方米
- 环比上涨：2.1%
- 同比上涨：4.3%

## 二、区域表现

### 2.1 科技园片区
- 成交占比：35%
- 平均单价：102,000元/平方米
- 主力户型：两房、三房

### 2.2 蛇口片区
- 成交占比：28%
- 平均单价：88,000元/平方米
- 海景房热度持续

### 2.3 后海片区
- 成交占比：22%
- 平均单价：96,000元/平方米
- 新盘供应充足

## 三、热点项目

1. **深圳湾科技生态园**
   - 位置：深圳湾
   - 均价：115,000元/平方米
   - 特点：临海高端住宅

2. **科技园创新中心**
   - 位置：科技园北区
   - 均价：98,000元/平方米
   - 特点：产业配套完善

3. **蛇口太子湾**
   - 位置：蛇口片区
   - 均价：92,000元/平方米
   - 特点：滨海豪宅

## 四、市场趋势

### 4.1 需求特点
- 改善型需求增加
- 学区房热度不减
- 科技人才购房需求旺盛

### 4.2 供应情况
- 新增供应：1,800套
- 去化周期：8个月
- 库存压力适中

## 五、下季度展望

预计明年第一季度市场将保持稳定，价格涨幅收窄，成交量可能略有回落。

---
报告生成时间：{report_time}
""".format(report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "report_type": "季度报告",
            "city": "深圳",
            "area": "南山区"
        }
    ]
    
    return test_reports


def test_create_reports():
    """测试创建报告功能"""
    print("=" * 80)
    print("开始测试报告生成功能")
    print("=" * 80)
    
    # 初始化 ReportDatabase
    report_db = ReportDatabase(storage_path='reports_storage')
    
    # 获取测试数据
    test_reports = create_test_report_data()
    
    results = []
    
    for idx, report_data in enumerate(test_reports, 1):
        print(f"\n[{idx}/{len(test_reports)}] 正在创建报告: {report_data['title']}")
        print("-" * 80)
        
        try:
            # 使用 create_report_with_ai_support 方法创建报告
            result = report_db.create_report_with_ai_support(
                title=report_data['title'],
                summary=report_data['summary'],
                content=report_data['content'],
                report_type=report_data['report_type'],
                city=report_data['city'],
                user_id='test_user_001',
                generate_image=True  # 启用图片生成
            )
            
            if result.get('success'):
                print(f"✅ 报告创建成功！")
                print(f"   - 报告ID: {result['report_id']}")
                print(f"   - 文本路径: {result['txt_path']}")
                print(f"   - 图片路径: {result['cover_image_path']}")
                print(f"   - 图片生成: {'是' if result.get('has_image') else '否'}")
                
                results.append({
                    'status': 'success',
                    'report_id': result['report_id'],
                    'title': report_data['title'],
                    'txt_path': result['txt_path'],
                    'image_path': result['cover_image_path']
                })
            else:
                print(f"❌ 报告创建失败: {result.get('error')}")
                results.append({
                    'status': 'failed',
                    'title': report_data['title'],
                    'error': result.get('error')
                })
                
        except Exception as e:
            print(f"❌ 发生异常: {str(e)}")
            results.append({
                'status': 'error',
                'title': report_data['title'],
                'error': str(e)
            })
    
    # 输出测试总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    
    print(f"总计: {len(results)} 个报告")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    if success_count > 0:
        print("\n✅ 成功创建的报告:")
        for r in results:
            if r['status'] == 'success':
                print(f"   - ID {r['report_id']}: {r['title']}")
                print(f"     文本: {r['txt_path']}")
                print(f"     图片: {r['image_path']}")
    
    if failed_count > 0:
        print("\n❌ 失败的报告:")
        for r in results:
            if r['status'] != 'success':
                print(f"   - {r['title']}: {r.get('error', '未知错误')}")
    
    return results


def test_ai_generate_report():
    """测试AI生成报告功能"""
    print("\n" + "=" * 80)
    print("测试AI生成报告功能")
    print("=" * 80)
    
    report_db = ReportDatabase(storage_path='reports_storage')
    
    test_areas = [
        {"area": "朝阳区", "city": "北京", "type": "市场分析"},
        {"area": "天河区", "city": "广州", "type": "投资价值报告"}
    ]
    
    for test_case in test_areas:
        print(f"\n正在为 {test_case['city']}{test_case['area']} 生成 {test_case['type']}...")
        
        try:
            result = report_db.generate_ai_report(
                area=test_case['area'],
                report_type=test_case['type'],
                city=test_case['city'],
                user_id='test_user_001'
            )
            
            print(f"✅ AI报告生成成功！")
            print(f"   - 报告ID: {result['report_id']}")
            print(f"   - 标题: {result['title']}")
            print(f"   - 封面图片: {result['cover_image']}")
            print(f"   - 内容预览: {result['content_preview'][:100]}...")
            
        except Exception as e:
            print(f"❌ AI报告生成失败: {str(e)}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("ReportDatabase 测试脚本")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 确保存储目录存在

    
    # 测试1: 创建普通报告（带图片生成）
    results = test_create_reports()
    
    # 测试2: AI生成报告（可选，需要AI服务配置）
    # 如果不需要测试AI生成，可以注释掉下面这行
    # test_ai_generate_report()
    
    print("\n" + "=" * 80)
    print(f"测试完成！结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print("\n提示:")
    print("1. 请检查 reports_storage/texts/ 目录下的文本文件")
    print("2. 请检查 reports_storage/images/ 目录下的图片文件")
    print("3. 请检查数据库 reports 表中的记录")
    print("4. 确保已配置讯飞星火API密钥（在 report_database.py 文件顶部）")


if __name__ == '__main__':
    main()