"""
58同城北京二手房信息爬虫 - 支持按区域爬取
交互式设计
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import json
from urllib.parse import urljoin
import re
from datetime import datetime
import os

from config import BEIJING_DISTRICTS, DISTRICT_AREAS, USER_AGENTS
from captcha_solver import is_captcha_page, wait_for_manual_captcha, SELENIUM_AVAILABLE


class Spider58:
    """58同城爬虫，支持按区域爬取"""
    
    def __init__(self, output_dir='data'):
        self.base_url = "https://bj.58.com/"
        self.session = requests.Session()
        self.houses = []
        self.output_dir = output_dir
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self._update_headers()
    
    def _update_headers(self):
        """更新请求头"""
        self.headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://bj.58.com/ershoufang/',
        }
        self.session.headers.update(self.headers)
    
    def build_url(self, district=None, area=None, page=1):
        """构建URL"""
        location_code = ''
        if area and district:
            if district in DISTRICT_AREAS and area in DISTRICT_AREAS[district]:
                location_code = DISTRICT_AREAS[district][area]
        elif district and district in BEIJING_DISTRICTS:
            location_code = BEIJING_DISTRICTS[district]
        
        if location_code:
            url = f"{self.base_url}{location_code}/ershoufang/"
        else:
            url = f"{self.base_url}ershoufang/"
        
        if page > 1:
            url = url.rstrip('/') + f'/pn{page}/'
        
        return url
    
    def get_page(self, url, retry=3):
        """获取网页内容，遇到验证码等待用户手动完成"""
        for i in range(retry):
            try:
                time.sleep(random.uniform(1, 3))
                
                if random.random() < 0.3:
                    self._update_headers()
                
                response = self.session.get(url, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    if is_captcha_page(response.text):
                        print(f"  [CAPTCHA] 检测到验证码")
                        
                        if SELENIUM_AVAILABLE:
                            success, html = wait_for_manual_captcha(url)
                            if success and html:
                                return html
                            else:
                                print(f"  [ERR] 验证码处理失败")
                                return None
                        else:
                            print(f"  [ERR] 需要安装Selenium: pip install selenium")
                            return None
                    
                    return response.text
                else:
                    print(f"  [ERR] HTTP状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"  [ERR] 请求异常: {e}")
                if i < retry - 1:
                    time.sleep(random.uniform(2, 5))
        
        return None
    
    def parse_house_list(self, html):
        """解析房源列表页面"""
        soup = BeautifulSoup(html, 'html.parser')
        houses = []
        
        items = soup.select('div.property')
        if not items:
            items = soup.find_all('div', class_='property')
        
        for item in items:
            try:
                house_info = self.extract_house_info(item)
                if house_info:
                    houses.append(house_info)
            except Exception as e:
                continue
        
        return houses
    
    def extract_house_info(self, item):
        """从单个房源元素中提取信息"""
        house_info = {}
        
        try:
            # 标题
            title_elem = item.select_one('h3.property-content-title-name')
            if title_elem:
                house_info['title'] = title_elem.get_text(strip=True)
            else:
                title_elem = item.select_one('[title]')
                if title_elem:
                    house_info['title'] = title_elem.get('title', '').strip()
            
            # 链接
            link_elem = item.select_one('a.property-ex, a[href*="ershoufang"]')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    house_info['url'] = urljoin(self.base_url, href)
            
            # 价格
            price_num_elem = item.select_one('span.property-price-total-num')
            price_text_elem = item.select_one('span.property-price-total-text')
            if price_num_elem:
                house_info['price'] = price_num_elem.get_text(strip=True)
                house_info['price_unit'] = price_text_elem.get_text(strip=True) if price_text_elem else '万'
            
            # 单价
            avg_price_elem = item.select_one('p.property-price-average')
            if avg_price_elem:
                house_info['price_per_sqm'] = avg_price_elem.get_text(strip=True)
            
            # 房型
            room_elem = item.select_one('p.property-content-info-attribute')
            if room_elem:
                room_spans = room_elem.find_all('span')
                room_parts = []
                for i in range(0, len(room_spans), 2):
                    if i + 1 < len(room_spans):
                        num = room_spans[i].get_text(strip=True)
                        unit = room_spans[i + 1].get_text(strip=True)
                        room_parts.append(f"{num}{unit}")
                if room_parts:
                    house_info['room_type'] = ''.join(room_parts)
            
            # 面积、朝向、楼层等
            info_texts = item.select('p.property-content-info-text')
            for info_text in info_texts:
                text = info_text.get_text(strip=True)
                
                area_match = re.search(r'(\d+(?:\.\d+)?)\s*㎡', text)
                if area_match and 'area' not in house_info:
                    house_info['area'] = area_match.group(1)
                
                if any(o in text for o in ['南北', '东西', '南', '北', '东', '西']):
                    if 'orientation' not in house_info and len(text) <= 4:
                        house_info['orientation'] = text
                
                if '层' in text and 'floor' not in house_info:
                    house_info['floor'] = text
                
                year_match = re.search(r'(\d{4})年', text)
                if year_match and 'year' not in house_info:
                    house_info['year'] = year_match.group(1)
            
            # 小区
            comm_name_elem = item.select_one('p.property-content-info-comm-name')
            if comm_name_elem:
                house_info['community'] = comm_name_elem.get_text(strip=True)
            
            # 地址
            address_elem = item.select_one('p.property-content-info-comm-address')
            if address_elem:
                address_spans = address_elem.find_all('span')
                address_parts = [span.get_text(strip=True) for span in address_spans]
                if address_parts:
                    house_info['location'] = ' '.join(address_parts)
                    if len(address_parts) > 0:
                        house_info['district'] = address_parts[0]
                    if len(address_parts) > 1:
                        house_info['business_area'] = address_parts[1]
            
            # 标签
            tags = item.select('span.property-content-info-tag')
            if tags:
                house_info['tags'] = [tag.get_text(strip=True) for tag in tags]
            
            # 爬取时间
            house_info['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if house_info.get('title'):
                return house_info
                
        except Exception as e:
            pass
        
        return None
    
    def crawl(self, district=None, area=None, max_pages=None):
        """爬取房源数据
        
        Args:
            district: 区域名称
            area: 商圈名称
            max_pages: 最大页数，None表示爬取全部
        
        Returns:
            list: 爬取到的房源列表
        """
        location_desc = ''
        if area:
            location_desc = f"{district}-{area}" if district else area
        elif district:
            location_desc = district
        else:
            location_desc = "全城"
        
        print(f"\n[START] 开始爬取: {location_desc}")
        
        page = 1
        page_houses = []
        empty_pages = 0
        
        while True:
            if max_pages and page > max_pages:
                break
            
            print(f"  [PAGE {page}] 正在爬取...")
            
            url = self.build_url(district=district, area=area, page=page)
            
            html = self.get_page(url)
            if not html:
                print(f"  [ERR] 获取页面失败")
                empty_pages += 1
                if empty_pages >= 3:
                    print(f"  [WARN] 连续3页失败，停止")
                    break
                page += 1
                continue
            
            houses = self.parse_house_list(html)
            if not houses:
                print(f"  [WARN] 未找到房源，可能已到最后一页")
                empty_pages += 1
                if empty_pages >= 2:
                    break
                page += 1
                continue
            
            # 为每条数据添加区域标记
            for house in houses:
                house['crawl_district'] = district if district else '全城'
                if area:
                    house['crawl_area'] = area
            
            empty_pages = 0
            page_houses.extend(houses)
            print(f"  [OK] 找到 {len(houses)} 条，累计 {len(page_houses)} 条")
            
            page += 1
            
            delay = random.uniform(3, 6)
            print(f"  [WAIT] 等待 {delay:.1f}秒...")
            time.sleep(delay)
        
        print(f"[DONE] {location_desc} 爬取完成，共 {len(page_houses)} 条")
        return page_houses
    
    def crawl_all_districts(self):
        """按区域爬取全城数据"""
        districts = list(BEIJING_DISTRICTS.keys())
        
        print(f"\n{'#'*60}")
        print(f"[BATCH] 按区域爬取全城数据")
        print(f"[TOTAL] 共 {len(districts)} 个区域")
        print(f"{'#'*60}")
        
        all_houses = []
        
        for i, district in enumerate(districts, 1):
            print(f"\n\n{'='*60}")
            print(f"[{i}/{len(districts)}] 正在爬取: {district}")
            print(f"{'='*60}")
            
            houses = self.crawl(district=district)
            all_houses.extend(houses)
            
            # 保存当前区域数据
            if houses:
                self.houses = houses
                self.save_to_csv(f'houses_{district}.csv')
            
            print(f"[PROGRESS] 已完成 {i}/{len(districts)} 区域，累计 {len(all_houses)} 条")
            
            # 区域间延迟
            if i < len(districts):
                delay = random.uniform(10, 20)
                print(f"\n[WAIT] 区域间隔，等待 {delay:.1f}秒...")
                time.sleep(delay)
        
        # 保存全部数据
        self.houses = all_houses
        self.save_to_csv('houses_all.csv')
        self.save_to_json('houses_all.json')
        
        print(f"\n\n{'#'*60}")
        print(f"[COMPLETE] 全部爬取完成!")
        print(f"[TOTAL] 共 {len(all_houses)} 条房源")
        print(f"{'#'*60}")
        
        self.print_summary()
        return all_houses
    
    def save_to_csv(self, filename=None):
        """保存数据到CSV"""
        if not self.houses:
            print("[WARN] 没有数据可保存")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'houses_{timestamp}.csv'
        
        filepath = os.path.join(self.output_dir, filename)
        
        all_fields = set()
        for house in self.houses:
            all_fields.update(house.keys())
        
        # 字段顺序，crawl_district 放在前面
        fieldnames = ['crawl_district', 'crawl_area', 'title', 'price', 'price_unit', 
                     'price_per_sqm', 'room_type', 'area', 'orientation', 'floor', 
                     'year', 'community', 'district', 'business_area', 'location', 
                     'tags', 'url', 'crawl_time']
        for field in sorted(all_fields):
            if field not in fieldnames:
                fieldnames.append(field)
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for house in self.houses:
                row = {}
                for key, value in house.items():
                    if isinstance(value, list):
                        row[key] = ' '.join(value)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        print(f"[OK] 已保存到 {filepath}，共 {len(self.houses)} 条")
    
    def save_to_json(self, filename=None):
        """保存数据到JSON"""
        if not self.houses:
            print("[WARN] 没有数据可保存")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'houses_{timestamp}.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.houses, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 已保存到 {filepath}，共 {len(self.houses)} 条")
    
    def print_summary(self):
        """打印统计摘要"""
        if not self.houses:
            print("[WARN] 暂无数据")
            return
        
        print(f"\n{'='*60}")
        print(f"[STATS] 数据统计")
        print(f"{'='*60}")
        print(f"总房源数: {len(self.houses)} 条")
        
        # 按爬取区域统计
        crawl_districts = {}
        for house in self.houses:
            d = house.get('crawl_district', '未知')
            crawl_districts[d] = crawl_districts.get(d, 0) + 1
        
        if crawl_districts:
            print(f"\n按爬取区域统计:")
            for d, c in sorted(crawl_districts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {d}: {c} 条")
        
        # 价格统计
        prices = []
        for house in self.houses:
            if house.get('price'):
                try:
                    prices.append(float(house['price']))
                except:
                    pass
        
        if prices:
            print(f"\n价格统计:")
            print(f"  均价: {sum(prices)/len(prices):.2f} 万")
            print(f"  最高: {max(prices):.2f} 万")
            print(f"  最低: {min(prices):.2f} 万")
    
    def clear(self):
        """清空数据"""
        self.houses = []
        print("[OK] 数据已清空")


def interactive_menu():
    """交互式菜单"""
    spider = Spider58()
    districts = list(BEIJING_DISTRICTS.keys())
    
    while True:
        print("\n" + "=" * 60)
        print("  58同城北京二手房爬虫")
        print("=" * 60)
        print("\n请选择操作:")
        print("  1. 爬取全城数据（按区域逐个爬取）")
        print("  2. 爬取指定区域")
        print("  3. 爬取指定商圈")
        print("  4. 查看已爬取数据统计")
        print("  5. 保存数据")
        print("  6. 清空数据")
        print("  0. 退出")
        print()
        
        choice = input("请输入选项 [0-6]: ").strip()
        
        if choice == '0':
            print("\n再见!")
            break
        
        elif choice == '1':
            print("\n即将爬取全城数据（按区域逐个爬取所有数据）")
            print(f"区域列表: {', '.join(districts)}")
            confirm = input("\n确认开始? [y/N]: ").strip().lower()
            if confirm == 'y':
                spider.crawl_all_districts()
        
        elif choice == '2':
            print("\n可选区域:")
            for i, d in enumerate(districts, 1):
                print(f"  {i:2}. {d}")
            print()
            
            idx = input("请输入区域编号: ").strip()
            try:
                idx = int(idx)
                if 1 <= idx <= len(districts):
                    district = districts[idx - 1]
                    
                    max_pages = input("最大页数（直接回车表示不限）: ").strip()
                    max_pages = int(max_pages) if max_pages else None
                    
                    houses = spider.crawl(district=district, max_pages=max_pages)
                    spider.houses.extend(houses)
                    
                    if houses:
                        save = input("\n是否保存数据? [Y/n]: ").strip().lower()
                        if save != 'n':
                            spider.houses = houses
                            spider.save_to_csv(f'houses_{district}.csv')
                            spider.save_to_json(f'houses_{district}.json')
                else:
                    print("[ERR] 无效的编号")
            except ValueError:
                print("[ERR] 请输入有效的数字")
        
        elif choice == '3':
            print("\n可选区域:")
            for i, d in enumerate(districts, 1):
                print(f"  {i:2}. {d}")
            print()
            
            idx = input("请输入区域编号: ").strip()
            try:
                idx = int(idx)
                if 1 <= idx <= len(districts):
                    district = districts[idx - 1]
                    
                    if district not in DISTRICT_AREAS or not DISTRICT_AREAS[district]:
                        print(f"[WARN] {district} 暂无商圈数据，请先运行 fetch_areas.py")
                        continue
                    
                    areas = list(DISTRICT_AREAS[district].keys())
                    print(f"\n{district} 可选商圈:")
                    for i, a in enumerate(areas, 1):
                        print(f"  {i:2}. {a}")
                    print()
                    
                    area_idx = input("请输入商圈编号: ").strip()
                    try:
                        area_idx = int(area_idx)
                        if 1 <= area_idx <= len(areas):
                            area = areas[area_idx - 1]
                            
                            max_pages = input("最大页数（直接回车表示不限）: ").strip()
                            max_pages = int(max_pages) if max_pages else None
                            
                            houses = spider.crawl(district=district, area=area, max_pages=max_pages)
                            spider.houses.extend(houses)
                            
                            if houses:
                                save = input("\n是否保存数据? [Y/n]: ").strip().lower()
                                if save != 'n':
                                    spider.houses = houses
                                    spider.save_to_csv(f'houses_{district}_{area}.csv')
                                    spider.save_to_json(f'houses_{district}_{area}.json')
                        else:
                            print("[ERR] 无效的编号")
                    except ValueError:
                        print("[ERR] 请输入有效的数字")
                else:
                    print("[ERR] 无效的编号")
            except ValueError:
                print("[ERR] 请输入有效的数字")
        
        elif choice == '4':
            spider.print_summary()
        
        elif choice == '5':
            if spider.houses:
                filename = input("文件名（直接回车使用默认）: ").strip()
                if filename:
                    spider.save_to_csv(filename + '.csv')
                    spider.save_to_json(filename + '.json')
                else:
                    spider.save_to_csv()
                    spider.save_to_json()
            else:
                print("[WARN] 暂无数据可保存")
        
        elif choice == '6':
            confirm = input("确认清空所有已爬取数据? [y/N]: ").strip().lower()
            if confirm == 'y':
                spider.clear()
        
        else:
            print("[ERR] 无效的选项")


def main():
    """主函数"""
    interactive_menu()


if __name__ == '__main__':
    main()
