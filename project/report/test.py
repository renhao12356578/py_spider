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
    test_reports =[
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
        }]
    
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