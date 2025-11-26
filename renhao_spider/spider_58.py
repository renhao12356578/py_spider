"""
58同城北京二手房信息爬虫
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import json
from urllib.parse import urljoin, urlparse, parse_qs
import re


class Spider58:
    def __init__(self):
        self.base_url = "https://bj.58.com/ershoufang/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://bj.58.com/ershoufang/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.houses = []

    def get_page(self, url, retry=3):
        """获取网页内容，带重试机制"""
        for i in range(retry):
            try:
                # 随机延迟，避免被识别为爬虫
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(url, timeout=10)
                response.encoding = 'utf-8'
                
                # 检查是否被重定向到验证码页面
                if '验证码' in response.text or 'captcha' in response.url.lower():
                    print(f"⚠️  遇到验证码，等待更长时间...")
                    time.sleep(random.uniform(5, 10))
                    continue
                
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"❌ 请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")
                if i < retry - 1:
                    time.sleep(random.uniform(2, 5))
        
        return None

    def parse_house_list(self, html):
        """解析房源列表页面"""
        soup = BeautifulSoup(html, 'html.parser')
        houses = []
        
        # 58同城的房源信息使用 class="property" 的div
        items = soup.select('div.property')
        
        if not items:
            print("⚠️  未找到房源列表，尝试其他选择器...")
            # 备用选择器
            items = soup.find_all('div', class_='property')
        
        if items:
            print(f"✅ 找到 {len(items)} 个房源")
        else:
            print("❌ 未找到任何房源信息")
        
        for item in items:
            try:
                house_info = self.extract_house_info(item)
                if house_info:
                    houses.append(house_info)
            except Exception as e:
                print(f"⚠️  解析单个房源时出错: {e}")
                continue
        
        return houses

    def extract_house_info(self, item):
        """从单个房源元素中提取信息"""
        house_info = {}
        
        try:
            # 标题 - 使用 property-content-title-name
            title_elem = item.select_one('h3.property-content-title-name')
            if title_elem:
                house_info['title'] = title_elem.get_text(strip=True)
            else:
                # 备用：从title属性获取
                title_elem = item.select_one('[title]')
                if title_elem:
                    house_info['title'] = title_elem.get('title', '').strip()
            
            # 链接 - 在a标签的href中
            link_elem = item.select_one('a.property-ex, a[href*="ershoufang"]')
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    house_info['url'] = urljoin(self.base_url, href)
            
            # 价格 - property-price-total-num 和 property-price-total-text
            price_num_elem = item.select_one('span.property-price-total-num')
            price_text_elem = item.select_one('span.property-price-total-text')
            if price_num_elem:
                price_num = price_num_elem.get_text(strip=True)
                price_unit = price_text_elem.get_text(strip=True) if price_text_elem else '万'
                house_info['price'] = price_num
                house_info['price_unit'] = price_unit
            
            # 单价 - property-price-average
            avg_price_elem = item.select_one('p.property-price-average')
            if avg_price_elem:
                avg_price_text = avg_price_elem.get_text(strip=True)
                # 提取数字部分
                avg_match = re.search(r'(\d+(?:\.\d+)?)', avg_price_text)
                if avg_match:
                    house_info['price_per_sqm'] = avg_price_text
            
            # 房型 - property-content-info-attribute
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
            
            # 面积 - 在 property-content-info-text 中查找包含㎡的
            info_texts = item.select('p.property-content-info-text')
            for info_text in info_texts:
                text = info_text.get_text(strip=True)
                # 面积
                area_match = re.search(r'(\d+(?:\.\d+)?)\s*㎡', text)
                if area_match and 'area' not in house_info:
                    house_info['area'] = area_match.group(1)
                
                # 朝向
                if '南北' in text or '东西' in text or '南' in text or '北' in text:
                    if 'orientation' not in house_info:
                        house_info['orientation'] = text
                
                # 楼层信息
                if '层' in text and 'floor' not in house_info:
                    house_info['floor'] = text
                
                # 建造年份
                year_match = re.search(r'(\d{4})年', text)
                if year_match and 'year' not in house_info:
                    house_info['year'] = year_match.group(1)
            
            # 小区名称 - property-content-info-comm-name
            comm_name_elem = item.select_one('p.property-content-info-comm-name')
            if comm_name_elem:
                house_info['community'] = comm_name_elem.get_text(strip=True)
            
            # 地址 - property-content-info-comm-address
            address_elem = item.select_one('p.property-content-info-comm-address')
            if address_elem:
                address_spans = address_elem.find_all('span')
                address_parts = [span.get_text(strip=True) for span in address_spans]
                if address_parts:
                    house_info['location'] = ' '.join(address_parts)
            
            # 标签 - property-content-info-tag
            tags = item.select('span.property-content-info-tag')
            if tags:
                house_info['tags'] = [tag.get_text(strip=True) for tag in tags]
            
            # 如果至少提取到了标题，就认为成功
            if house_info.get('title'):
                return house_info
                
        except Exception as e:
            print(f"⚠️  提取信息时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return None

    def save_to_csv(self, filename='houses_58.csv'):
        """保存数据到CSV文件"""
        if not self.houses:
            print("❌ 没有数据可保存")
            return
        
        # 收集所有可能的字段
        all_fields = set()
        for house in self.houses:
            all_fields.update(house.keys())
        
        # 定义字段顺序
        fieldnames = ['title', 'price', 'price_unit', 'price_per_sqm', 'room_type', 'area', 
                     'orientation', 'floor', 'year', 'community', 'location', 'tags', 'url']
        # 添加其他字段
        for field in sorted(all_fields):
            if field not in fieldnames:
                fieldnames.append(field)
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for house in self.houses:
                # 将列表类型转换为字符串
                row = {}
                for key, value in house.items():
                    if isinstance(value, list):
                        row[key] = ' '.join(value)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        print(f"✅ 数据已保存到 {filename}，共 {len(self.houses)} 条记录")

    def save_to_json(self, filename='houses_58.json'):
        """保存数据到JSON文件"""
        if not self.houses:
            print("❌ 没有数据可保存")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.houses, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存到 {filename}，共 {len(self.houses)} 条记录")

    def crawl(self, max_pages=5, use_local_html=False):
        """爬取指定页数的数据
        
        Args:
            max_pages: 最大爬取页数
            use_local_html: 如果为True，使用本地58.html文件进行测试
        """
        if use_local_html:
            print("📄 使用本地HTML文件进行测试...")
            try:
                with open('58.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                houses = self.parse_house_list(html)
                if houses:
                    self.houses.extend(houses)
                    print(f"✅ 从本地文件成功提取 {len(houses)} 条房源信息")
                else:
                    print("❌ 从本地文件未找到房源信息")
            except FileNotFoundError:
                print("❌ 未找到58.html文件，切换到在线爬取模式")
                use_local_html = False
        
        if not use_local_html:
            print(f"🚀 开始爬取58同城北京二手房信息，计划爬取 {max_pages} 页...")
            
            for page in range(1, max_pages + 1):
                print(f"\n📄 正在爬取第 {page} 页...")
                
                # 构建URL（58同城的分页参数通常是PGTID和page）
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}pn{page}/"
                
                html = self.get_page(url)
                if not html:
                    print(f"❌ 第 {page} 页获取失败，跳过")
                    continue
                
                houses = self.parse_house_list(html)
                if houses:
                    self.houses.extend(houses)
                    print(f"✅ 第 {page} 页成功提取 {len(houses)} 条房源信息")
                else:
                    print(f"⚠️  第 {page} 页未找到房源信息，可能页面结构已变化")
                    # 保存当前HTML用于调试
                    with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"   已保存页面HTML到 debug_page_{page}.html 供检查")
                
                # 页面间延迟
                if page < max_pages:
                    delay = random.uniform(3, 6)
                    print(f"⏳ 等待 {delay:.1f} 秒后继续...")
                    time.sleep(delay)
        
        print(f"\n🎉 爬取完成！共获取 {len(self.houses)} 条房源信息")
        
        # 保存数据
        if self.houses:
            self.save_to_csv()
            self.save_to_json()
            
            # 打印前几条数据预览
            print("\n📊 数据预览（前5条）：")
            for i, house in enumerate(self.houses[:5], 1):
                print(f"\n{i}. {house.get('title', 'N/A')}")
                print(f"   价格: {house.get('price', 'N/A')}{house.get('price_unit', '万')}")
                if house.get('price_per_sqm'):
                    print(f"   单价: {house.get('price_per_sqm', 'N/A')}")
                print(f"   房型: {house.get('room_type', 'N/A')}")
                print(f"   面积: {house.get('area', 'N/A')}㎡")
                print(f"   朝向: {house.get('orientation', 'N/A')}")
                print(f"   小区: {house.get('community', 'N/A')}")
                print(f"   位置: {house.get('location', 'N/A')}")
                if house.get('floor'):
                    print(f"   楼层: {house.get('floor', 'N/A')}")
                if house.get('year'):
                    print(f"   建造年份: {house.get('year', 'N/A')}")
        else:
            print("❌ 未获取到任何数据，请检查：")
            print("   1. 网络连接是否正常")
            print("   2. 网站是否可访问")
            print("   3. 是否触发了反爬虫机制")
            print("   4. 页面结构是否已变化（可查看debug_page_*.html文件）")


def main():
    spider = Spider58()
    
    # 如果本地有58.html文件，可以先测试本地文件
    # spider.crawl(max_pages=1, use_local_html=True)
    
    # 爬取5页数据（可根据需要调整）
    spider.crawl(max_pages=5)


if __name__ == '__main__':
    main()

