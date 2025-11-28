"""
命令行工具：58同城二手房爬虫
提供友好的命令行界面进行数据爬取
"""
import argparse
import sys
from spider_58_enhanced import Spider58Enhanced
from config import (
    BEIJING_DISTRICTS, DISTRICT_AREAS, PRICE_RANGES, 
    ROOM_TYPES, AREA_RANGES, ORIENTATIONS, FLOOR_TYPES,
    BUILDING_AGE, DECORATION_TYPES
)


def list_options():
    """列出所有可用的筛选选项"""
    print("\n" + "="*60)
    print("[OPTIONS] 可用的筛选选项")
    print("="*60)
    
    print("\n[DISTRICT] 北京各区域:")
    districts = [k for k in BEIJING_DISTRICTS.keys() if k != '不限']
    for i, district in enumerate(districts, 1):
        print(f"  {district}", end="  ")
        if i % 6 == 0:
            print()
    print()
    
    print("\n[AREA] 各区域商圈（示例-朝阳区）:")
    if '朝阳' in DISTRICT_AREAS:
        areas = [k for k in DISTRICT_AREAS['朝阳'].keys() if k != '不限'][:20]
        for i, area in enumerate(areas, 1):
            print(f"  {area}", end="  ")
            if i % 5 == 0:
                print()
        print(f"\n  ... 共 {len(DISTRICT_AREAS['朝阳'])} 个商圈")
    
    print("\n[PRICE] 价格区间:")
    for price_range in [k for k in PRICE_RANGES.keys() if k != '不限']:
        print(f"  {price_range}", end="  ")
    print()
    
    print("\n[ROOM] 房型:")
    for room_type in [k for k in ROOM_TYPES.keys() if k != '不限']:
        print(f"  {room_type}", end="  ")
    print()
    
    print("\n[SIZE] 面积区间:")
    for area_range in [k for k in AREA_RANGES.keys() if k != '不限']:
        print(f"  {area_range}", end="  ")
    print()
    
    print("\n[ORIENT] 朝向:")
    for orient in [k for k in ORIENTATIONS.keys() if k != '不限']:
        print(f"  {orient}", end="  ")
    print()
    
    print("\n[FLOOR] 楼层:")
    for floor in [k for k in FLOOR_TYPES.keys() if k != '不限']:
        print(f"  {floor}", end="  ")
    print()
    
    print("\n[DECOR] 装修:")
    for dec in [k for k in DECORATION_TYPES.keys() if k != '不限']:
        print(f"  {dec}", end="  ")
    print()
    
    print("\n[AGE] 房龄:")
    for age in [k for k in BUILDING_AGE.keys() if k != '不限']:
        print(f"  {age}", end="  ")
    print()
    
    print("\n" + "="*60 + "\n")


def list_areas(district):
    """列出指定区域的所有商圈"""
    if district not in DISTRICT_AREAS:
        print(f"[ERR] 未找到区域 {district} 的商圈配置")
        print(f"可用区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'])}")
        return
    
    print(f"\n{'='*60}")
    print(f"[AREA] {district}区 商圈列表")
    print("="*60)
    
    areas = [k for k in DISTRICT_AREAS[district].keys() if k != '不限']
    for i, area in enumerate(areas, 1):
        print(f"  {area}", end="  ")
        if i % 5 == 0:
            print()
    print(f"\n\n共 {len(areas)} 个商圈")
    print("="*60 + "\n")


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("[WELCOME] 欢迎使用58同城二手房爬虫 - 交互式模式")
    print("="*60)
    
    spider = Spider58Enhanced()
    
    # 选择爬取模式
    print("\n请选择爬取模式:")
    print("1. 按区域爬取")
    print("2. 按商圈爬取")
    print("3. 批量爬取多个区域")
    print("4. 批量爬取某区域所有商圈")
    print("5. 自定义条件爬取")
    
    mode = input("\n请输入选项 (1-5): ").strip()
    
    if mode == '1':
        # 按区域爬取
        print(f"\n[DISTRICT] 可选区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'])}")
        district = input("请输入区域名称: ").strip()
        if district not in BEIJING_DISTRICTS or district == '不限':
            print(f"[ERR] 无效的区域名称: {district}")
            return
        
        max_pages = input("爬取页数 (默认5): ").strip()
        max_pages = int(max_pages) if max_pages else 5
        
        fetch_detail = input("是否爬取详情页? (y/n, 默认n): ").strip().lower() == 'y'
        
        spider.crawl(district=district, max_pages=max_pages, fetch_detail=fetch_detail)
        
    elif mode == '2':
        # 按商圈爬取
        print(f"\n[DISTRICT] 可选区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'])}")
        district = input("请输入区域名称: ").strip()
        if district not in DISTRICT_AREAS:
            print(f"[ERR] 无效的区域名称: {district}")
            return
        
        areas = [k for k in DISTRICT_AREAS[district].keys() if k != '不限']
        print(f"\n[AREA] {district}区商圈: {', '.join(areas[:15])}{'...' if len(areas) > 15 else ''}")
        area = input("请输入商圈名称: ").strip()
        if area not in DISTRICT_AREAS[district]:
            print(f"[ERR] 无效的商圈: {area}")
            return
        
        max_pages = input("爬取页数 (默认5): ").strip()
        max_pages = int(max_pages) if max_pages else 5
        
        fetch_detail = input("是否爬取详情页? (y/n, 默认n): ").strip().lower() == 'y'
        
        spider.crawl(district=district, area=area, max_pages=max_pages, fetch_detail=fetch_detail)
        
    elif mode == '3':
        # 批量爬取多个区域
        print(f"\n[DISTRICT] 可选区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'])}")
        districts_input = input("请输入区域名称（多个用逗号分隔，留空表示全部）: ").strip()
        
        if districts_input:
            districts = [d.strip() for d in districts_input.split(',')]
            invalid = [d for d in districts if d not in BEIJING_DISTRICTS or d == '不限']
            if invalid:
                print(f"[ERR] 无效的区域: {', '.join(invalid)}")
                return
        else:
            districts = None
        
        max_pages = input("每个区域爬取页数 (默认3): ").strip()
        max_pages = int(max_pages) if max_pages else 3
        
        fetch_detail = input("是否爬取详情页? (y/n, 默认n): ").strip().lower() == 'y'
        
        spider.crawl_by_districts(
            districts=districts,
            max_pages_per_district=max_pages,
            fetch_detail=fetch_detail
        )
        
    elif mode == '4':
        # 批量爬取某区域所有商圈
        print(f"\n[DISTRICT] 可选区域: {', '.join([k for k in DISTRICT_AREAS.keys()])}")
        district = input("请输入区域名称: ").strip()
        if district not in DISTRICT_AREAS:
            print(f"[ERR] 无效的区域名称: {district}")
            return
        
        max_pages = input("每个商圈爬取页数 (默认2): ").strip()
        max_pages = int(max_pages) if max_pages else 2
        
        fetch_detail = input("是否爬取详情页? (y/n, 默认n): ").strip().lower() == 'y'
        
        spider.crawl_by_areas(
            district=district,
            max_pages_per_area=max_pages,
            fetch_detail=fetch_detail
        )
        
    elif mode == '5':
        # 自定义条件
        print("\n[CUSTOM] 自定义筛选条件（直接回车跳过该条件）")
        
        # 区域
        print(f"\n[DISTRICT] 区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'][:10])}...")
        district = input("区域名称: ").strip() or None
        if district and (district not in BEIJING_DISTRICTS or district == '不限'):
            print(f"[WARN] 无效区域，已忽略")
            district = None
        
        # 商圈
        area = None
        if district and district in DISTRICT_AREAS:
            areas = [k for k in DISTRICT_AREAS[district].keys() if k != '不限']
            print(f"[AREA] 商圈: {', '.join(areas[:10])}...")
            area = input("商圈名称: ").strip() or None
            if area and area not in DISTRICT_AREAS[district]:
                print(f"[WARN] 无效商圈，已忽略")
                area = None
        
        # 价格
        print(f"[PRICE] 价格区间: {', '.join([k for k in PRICE_RANGES.keys() if k != '不限'])}")
        price_range = input("价格区间: ").strip() or None
        if price_range and price_range not in PRICE_RANGES:
            print(f"[WARN] 无效价格区间，已忽略")
            price_range = None
        
        # 房型
        print(f"[ROOM] 房型: {', '.join([k for k in ROOM_TYPES.keys() if k != '不限'])}")
        room_type = input("房型: ").strip() or None
        if room_type and room_type not in ROOM_TYPES:
            print(f"[WARN] 无效房型，已忽略")
            room_type = None
        
        # 面积
        print(f"[SIZE] 面积: {', '.join([k for k in AREA_RANGES.keys() if k != '不限'])}")
        area_range = input("面积区间: ").strip() or None
        if area_range and area_range not in AREA_RANGES:
            print(f"[WARN] 无效面积区间，已忽略")
            area_range = None
        
        max_pages = input("爬取页数 (默认5): ").strip()
        max_pages = int(max_pages) if max_pages else 5
        
        fetch_detail = input("是否爬取详情页? (y/n, 默认n): ").strip().lower() == 'y'
        
        spider.crawl(
            district=district,
            area=area,
            price_range=price_range,
            room_type=room_type,
            area_range=area_range,
            max_pages=max_pages,
            fetch_detail=fetch_detail
        )
    else:
        print("[ERR] 无效的选项")
        return
    
    # 保存数据
    spider.save_to_csv()
    spider.save_to_json()
    spider.print_summary()
    
    print("\n[DONE] 爬取完成！")


def main():
    parser = argparse.ArgumentParser(
        description='58同城北京二手房爬虫 - 支持按区域、商圈多维度筛选',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式模式
  python main.py -i
  
  # 列出所有可用选项
  python main.py --list
  
  # 列出某区域的所有商圈
  python main.py --list-areas 朝阳
  
  # 爬取朝阳区前5页
  python main.py -d 朝阳 -p 5
  
  # 爬取朝阳区望京商圈
  python main.py -d 朝阳 -a 望京 -p 3
  
  # 批量爬取多个区域
  python main.py --districts 朝阳,海淀,丰台 -p 3
  
  # 批量爬取某区域所有商圈
  python main.py --all-areas 朝阳 -p 2
  
  # 自定义多个条件
  python main.py -d 朝阳 -a 望京 --price 300-350万 --room 二室 -p 5
  
  # 爬取详情页（更多信息但速度慢）
  python main.py -d 海淀 -p 2 --detail
        """
    )
    
    # 基本选项
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='交互式模式')
    parser.add_argument('--list', action='store_true',
                        help='列出所有可用的筛选选项')
    parser.add_argument('--list-areas', type=str, metavar='区域',
                        help='列出指定区域的所有商圈')
    
    # 位置筛选
    parser.add_argument('-d', '--district', type=str,
                        help='区域名称（如：朝阳、海淀）')
    parser.add_argument('-a', '--area', type=str,
                        help='商圈名称（如：望京、中关村）')
    
    # 房源筛选
    parser.add_argument('--price', type=str,
                        help='价格区间（如：300-350万）')
    parser.add_argument('--room', type=str,
                        help='房型（如：二室、三室）')
    parser.add_argument('--size', type=str,
                        help='面积区间（如：90-110平方米）')
    parser.add_argument('--orient', type=str,
                        help='朝向（如：南北、南）')
    parser.add_argument('--floor', type=str,
                        help='楼层（如：中层、高层）')
    parser.add_argument('--age', type=str,
                        help='房龄（如：5-10年）')
    parser.add_argument('--decor', type=str,
                        help='装修（如：精装修）')
    
    # 批量爬取
    parser.add_argument('--districts', type=str,
                        help='批量爬取多个区域，用逗号分隔（如：朝阳,海淀,丰台）')
    parser.add_argument('--all-areas', type=str, metavar='区域',
                        help='批量爬取指定区域的所有商圈')
    
    # 爬取选项
    parser.add_argument('-p', '--pages', type=int, default=5,
                        help='爬取页数（默认：5）')
    parser.add_argument('--detail', action='store_true',
                        help='爬取详情页（获取更多信息，但速度较慢）')
    parser.add_argument('-o', '--output', type=str, default='data',
                        help='输出目录（默认：data）')
    
    args = parser.parse_args()
    
    # 处理命令
    if args.list:
        list_options()
        return
    
    if args.list_areas:
        list_areas(args.list_areas)
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    # 创建爬虫实例
    spider = Spider58Enhanced(output_dir=args.output)
    
    # 批量爬取所有商圈
    if args.all_areas:
        if args.all_areas not in DISTRICT_AREAS:
            print(f"[ERR] 未找到区域 {args.all_areas} 的商圈配置")
            sys.exit(1)
        
        spider.crawl_by_areas(
            district=args.all_areas,
            max_pages_per_area=args.pages,
            fetch_detail=args.detail
        )
        spider.save_to_csv()
        spider.save_to_json()
        spider.print_summary()
        return
    
    # 批量爬取多个区域
    if args.districts:
        districts = [d.strip() for d in args.districts.split(',')]
        invalid = [d for d in districts if d not in BEIJING_DISTRICTS or d == '不限']
        if invalid:
            print(f"[ERR] 无效的区域: {', '.join(invalid)}")
            sys.exit(1)
        
        spider.crawl_by_districts(
            districts=districts,
            max_pages_per_district=args.pages,
            fetch_detail=args.detail
        )
        spider.save_to_csv()
        spider.save_to_json()
        spider.print_summary()
        return
    
    # 单次爬取模式 - 验证参数
    if args.district and (args.district not in BEIJING_DISTRICTS or args.district == '不限'):
        print(f"[ERR] 无效的区域: {args.district}")
        print(f"可用区域: {', '.join([k for k in BEIJING_DISTRICTS.keys() if k != '不限'])}")
        sys.exit(1)
    
    if args.area:
        if args.district and args.district in DISTRICT_AREAS:
            if args.area not in DISTRICT_AREAS[args.district]:
                print(f"[ERR] {args.district}区没有商圈: {args.area}")
                print(f"可用商圈: {', '.join([k for k in DISTRICT_AREAS[args.district].keys() if k != '不限'][:10])}...")
                sys.exit(1)
        else:
            print(f"[WARN] 请同时指定区域 (-d) 以使用商圈筛选")
    
    if args.price and args.price not in PRICE_RANGES:
        print(f"[ERR] 无效的价格区间: {args.price}")
        print(f"可用价格区间: {', '.join([k for k in PRICE_RANGES.keys() if k != '不限'])}")
        sys.exit(1)
    
    if args.room and args.room not in ROOM_TYPES:
        print(f"[ERR] 无效的房型: {args.room}")
        print(f"可用房型: {', '.join([k for k in ROOM_TYPES.keys() if k != '不限'])}")
        sys.exit(1)
    
    if args.size and args.size not in AREA_RANGES:
        print(f"[ERR] 无效的面积区间: {args.size}")
        print(f"可用面积区间: {', '.join([k for k in AREA_RANGES.keys() if k != '不限'])}")
        sys.exit(1)
    
    # 如果没有任何筛选条件，提示用户
    if not any([args.district, args.area, args.price, args.room, args.size]):
        print("[WARN] 未指定任何筛选条件，将爬取所有房源")
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    
    spider.crawl(
        district=args.district,
        area=args.area,
        price_range=args.price,
        room_type=args.room,
        area_range=args.size,
        orientation=args.orient,
        floor_type=args.floor,
        building_age=args.age,
        decoration=args.decor,
        max_pages=args.pages,
        fetch_detail=args.detail
    )
    
    # 保存数据
    spider.save_to_csv()
    spider.save_to_json()
    spider.print_summary()
    
    print("\n[DONE] 所有任务完成！")


if __name__ == '__main__':
    main()
