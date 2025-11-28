"""
爬取58同城各区域的商圈数据
使用带PGTID参数的URL来获取商圈列表
遇到验证码自动解决
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from config import BEIJING_DISTRICTS, SPIDER_CONFIG, save_areas
from captcha_solver import get_page_with_captcha_solver, is_captcha_page, SELENIUM_AVAILABLE

# PGTID参数，用于绕过验证码
PGTID = "0d200001-0000-1304-bb23-ce1b21c86c0a"

# 创建全局Session，保持会话
session = requests.Session()


def get_page(url, session_obj=None, use_selenium=True, selenium_headless=False):
    """获取网页内容，使用验证码处理模块"""
    if session_obj is None:
        session_obj = session
    
    return get_page_with_captcha_solver(
        url=url,
        session=session_obj,
        use_selenium=use_selenium,
        selenium_headless=selenium_headless
    )


def parse_areas_from_html(html, district_pinyin):
    """从HTML中解析商圈数据"""
    soup = BeautifulSoup(html, 'html.parser')
    areas = {}
    
    # 获取所有区域拼音，用于排除
    district_pinyins = set(BEIJING_DISTRICTS.values())
    
    # 查找所有商圈li元素
    shangquan_items = soup.find_all('li', class_=lambda x: x and 'region-item-shangquan' in x)
    
    for item in shangquan_items:
        link = item.find('a', attrs={'data-npv': 'esf_List_shangquan'})
        if not link:
            link = item.find('a', href=re.compile(r'ershoufang'))
        
        if link:
            href = link.get('href', '')
            name = link.get_text(strip=True)
            
            if not name or name == '不限':
                continue
            
            match = re.search(r'bj\.58\.com/([^/]+)/ershoufang', href)
            if match:
                pinyin = match.group(1)
                if pinyin not in district_pinyins:
                    areas[name] = pinyin
    
    # 如果方法1没找到，直接查找带 data-npv="esf_List_shangquan" 的链接
    if not areas:
        links = soup.find_all('a', attrs={'data-npv': 'esf_List_shangquan'})
        for link in links:
            name = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not name or name == '不限':
                continue
            
            match = re.search(r'bj\.58\.com/([^/]+)/ershoufang', href)
            if match:
                pinyin = match.group(1)
                if pinyin not in district_pinyins:
                    areas[name] = pinyin
    
    return areas


def fetch_district_areas(district_name, district_pinyin, use_selenium=True, selenium_headless=False):
    """爬取指定区域的商圈列表"""
    base_district_url = f"{SPIDER_CONFIG['base_url']}{district_pinyin}/{SPIDER_CONFIG['ershoufang_path']}"
    url = f"{base_district_url}?PGTID={PGTID}"
    
    print(f"[{district_name}] URL: {url}")
    
    html = get_page(url, use_selenium=use_selenium, selenium_headless=selenium_headless)
    
    if html is None:
        # None表示遇到验证码且Selenium无法解决
        print(f"  [ERR] Failed due to captcha")
        return None
    
    if not html:
        print(f"  [ERR] Failed to fetch page")
        return {}
    
    areas = parse_areas_from_html(html, district_pinyin)
    
    if areas:
        print(f"  [OK] Found {len(areas)} areas")
    else:
        print(f"  [WARN] No areas found in HTML")
    
    return areas


def fetch_all_areas(delay_between_districts=(3, 6), use_selenium=True, selenium_headless=False):
    """爬取所有区域的商圈数据
    
    Args:
        delay_between_districts: 区域间的延迟时间范围（秒）
        use_selenium: 遇到验证码时是否立即使用Selenium解决（默认True）
        selenium_headless: Selenium是否使用无头模式（默认False）
    """
    print("=" * 60)
    print("[START] Fetching areas from 58.com")
    print(f"[INFO] Delay between districts: {delay_between_districts[0]}-{delay_between_districts[1]}s")
    if use_selenium:
        print(f"[INFO] Selenium enabled - captcha will be handled immediately")
        print(f"[INFO] Selenium headless mode: {selenium_headless}")
    else:
        print(f"[WARN] Selenium disabled - captcha will cause failures")
    print("=" * 60)
    
    all_areas = {}
    failed_districts = []  # 记录失败的区域
    
    # 爬取所有区域
    for idx, (district_name, district_pinyin) in enumerate(BEIJING_DISTRICTS.items(), 1):
        print(f"\n[{idx}/{len(BEIJING_DISTRICTS)}] [{district_name}] Fetching...")
        
        areas = fetch_district_areas(district_name, district_pinyin, 
                                    use_selenium=use_selenium, selenium_headless=selenium_headless)
        
        if areas is None:
            # None表示遇到验证码且无法解决
            print(f"  [FAIL] Failed due to captcha")
            failed_districts.append((district_name, district_pinyin))
            all_areas[district_name] = {}
        elif areas:
            all_areas[district_name] = areas
            sample = list(areas.items())[:5]
            for name, pinyin in sample:
                print(f"    {name}: {pinyin}")
            if len(areas) > 5:
                print(f"    ... total {len(areas)}")
        else:
            print(f"  [WARN] No areas found")
            all_areas[district_name] = {}
        
        # 区域间延迟
        if idx < len(BEIJING_DISTRICTS):
            delay = random.uniform(*delay_between_districts)
            print(f"    [WAIT] Waiting {delay:.1f}s...")
            time.sleep(delay)
    
    # 保存到JSON
    save_areas(all_areas)
    print("\n" + "=" * 60)
    print("[DONE] Areas saved to areas.json")
    print("=" * 60)
    
    # 统计
    total = sum(len(v) for v in all_areas.values())
    success_count = len([d for d in BEIJING_DISTRICTS.keys() if all_areas.get(d)])
    print(f"\n[STATS] {success_count}/{len(BEIJING_DISTRICTS)} districts succeeded, {total} total areas")
    if failed_districts:
        print(f"[FAILED] {len(failed_districts)} districts failed: {', '.join([d for d, p in failed_districts])}")
    
    return all_areas


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='爬取58同城各区域的商圈数据')
    parser.add_argument('--delay', type=float, nargs=2, default=[3, 6],
                        metavar=('MIN', 'MAX'),
                        help='区域间的延迟时间范围（秒），默认: 3-6')
    parser.add_argument('--no-selenium', action='store_true',
                        help='禁用Selenium（遇到验证码将失败）')
    parser.add_argument('--headless', action='store_true',
                        help='Selenium使用无头模式（不显示浏览器窗口）')
    
    args = parser.parse_args()
    
    print(f"[CONFIG] Delay: {args.delay[0]}-{args.delay[1]}s")
    print(f"[CONFIG] Use Selenium: {not args.no_selenium}")
    if not args.no_selenium:
        print(f"[CONFIG] Selenium headless: {args.headless}")
    
    if args.no_selenium and not SELENIUM_AVAILABLE:
        print("[WARN] Selenium not available, but --no-selenium specified")
    
    if not args.no_selenium and not SELENIUM_AVAILABLE:
        print("[WARN] Selenium not available! Install: pip install selenium")
        print("[WARN] You also need ChromeDriver: https://chromedriver.chromium.org/")
        print("[WARN] Continuing without Selenium...")
    
    # 爬取所有区域
    fetch_all_areas(
        delay_between_districts=tuple(args.delay),
        use_selenium=not args.no_selenium,
        selenium_headless=args.headless
    )
