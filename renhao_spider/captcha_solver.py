"""
58同城验证码处理模块
- 点击验证：自动点击按钮，等待用户完成滑块/图形验证
- 登录验证：等待用户手动登录
"""
import time
import random
from config import USER_AGENTS

# 尝试导入Selenium（可选）
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.action_chains import ActionChains
    
    SELENIUM_AVAILABLE = True
    
    # 尝试使用webdriver-manager自动管理ChromeDriver
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
        
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False


def is_captcha_page(html):
    """检测是否是验证码页面"""
    captcha_indicators = [
        '验证码',
        'captcha',
        'NEcaptcha',
        'ISDCaptcha',
        '访问过于频繁',
        'yidun/register.do',
        'antibot/yidun',
        '点击按钮进行验证'
    ]
    html_lower = html.lower()
    return any(indicator in html or indicator.lower() in html_lower for indicator in captcha_indicators)


def is_login_captcha(html):
    """检测是否是登录验证（需要用户登录）"""
    login_indicators = [
        '请登录',
        '登录验证',
        '扫码登录',
        '手机号登录',
        '账号登录',
        'login',
        '微信登录',
        '短信验证'
    ]
    html_lower = html.lower()
    return any(indicator in html or indicator.lower() in html_lower for indicator in login_indicators)


def is_click_captcha(html):
    """检测是否是点击验证（点击按钮进行验证）"""
    click_indicators = [
        '点击按钮进行验证',
        'btnSubmit',
        'ISDCaptcha',
        'NEcaptcha',
        '点击验证'
    ]
    return any(indicator in html for indicator in click_indicators)


def get_captcha_type(html):
    """获取验证码类型
    
    Returns:
        str: 'login' - 登录验证, 'click' - 点击验证, 'unknown' - 未知类型
    """
    if is_login_captcha(html):
        return 'login'
    elif is_click_captcha(html):
        return 'click'
    else:
        return 'unknown'


def create_driver():
    """创建Chrome WebDriver"""
    if not SELENIUM_AVAILABLE:
        return None
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    # 窗口最大化以便用户操作
    chrome_options.add_argument('--start-maximized')
    
    driver = None
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception:
                driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        # 隐藏webdriver特征
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return driver
    except Exception as e:
        print(f"  [ERR] 创建浏览器失败: {e}")
        return None


def handle_click_captcha(driver, timeout=120):
    """处理点击验证码
    
    自动点击验证按钮，然后等待用户完成滑块/图形验证
    
    Args:
        driver: WebDriver实例
        timeout: 超时时间（秒）
    
    Returns:
        bool: 是否验证成功
    """
    try:
        print("  [CAPTCHA] 检测到点击验证，正在自动点击...")
        
        # 等待页面完全加载
        time.sleep(2)
        
        # 尝试点击验证按钮
        clicked = False
        
        # 方法1: 通过ID点击
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSubmit"))
            )
            # 使用ActionChains模拟真实点击
            actions = ActionChains(driver)
            actions.move_to_element(btn).pause(0.5).click().perform()
            clicked = True
            print("  [OK] 已点击验证按钮")
        except Exception:
            pass
        
        # 方法2: 通过class点击
        if not clicked:
            try:
                btn = driver.find_element(By.CLASS_NAME, "btn_tj")
                actions = ActionChains(driver)
                actions.move_to_element(btn).pause(0.5).click().perform()
                clicked = True
                print("  [OK] 已点击验证按钮 (via class)")
            except Exception:
                pass
        
        # 方法3: 通过JavaScript点击
        if not clicked:
            try:
                driver.execute_script("""
                    var btn = document.getElementById('btnSubmit');
                    if (btn) btn.click();
                """)
                clicked = True
                print("  [OK] 已点击验证按钮 (via JS)")
            except Exception:
                pass
        
        if not clicked:
            print("  [WARN] 未找到验证按钮，请手动点击")
        
        # 等待验证码组件出现
        time.sleep(1)
        
        print("\n" + "=" * 60)
        print("  [!!!] 请在浏览器中完成滑块/图形验证")
        print("  [!!!] 完成后会自动继续...")
        print("=" * 60 + "\n")
        
        # 等待验证完成（页面跳转或验证码消失）
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            
            try:
                current_html = driver.page_source
                current_url = driver.current_url
                
                # 验证成功的标志
                # 1. 页面不再是验证码页面
                if not is_captcha_page(current_html):
                    print("  [OK] 验证成功!")
                    return True
                
                # 2. URL包含目标页面
                if 'ershoufang' in current_url and 'antibot' not in current_url:
                    print("  [OK] 已跳转到目标页面!")
                    return True
                
                # 3. 页面包含房源列表
                if 'property' in current_html or 'filter-region' in current_html:
                    print("  [OK] 检测到房源页面!")
                    return True
                
            except Exception:
                continue
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"  [WAIT] 等待验证完成... ({elapsed}s)")
        
        print(f"  [WARN] 验证超时 ({timeout}s)")
        return False
        
    except Exception as e:
        print(f"  [ERR] 处理点击验证失败: {e}")
        return False


def handle_login_captcha(driver, timeout=300):
    """处理登录验证
    
    等待用户手动完成登录
    
    Args:
        driver: WebDriver实例
        timeout: 超时时间（秒）
    
    Returns:
        bool: 是否验证成功
    """
    print("\n" + "=" * 60)
    print("  [!!!] 检测到登录验证")
    print("  [!!!] 请在浏览器中手动登录")
    print("  [!!!] 完成后按 Enter 键继续...")
    print("=" * 60 + "\n")
    
    input()
    
    try:
        current_html = driver.page_source
        if not is_captcha_page(current_html):
            print("  [OK] 登录成功!")
            return True
        else:
            print("  [WARN] 仍检测到验证码，请确认是否完成登录")
            print("  [!!!] 再次按 Enter 键继续...")
            input()
            
            current_html = driver.page_source
            if not is_captcha_page(current_html):
                print("  [OK] 验证成功!")
                return True
            return False
    except Exception as e:
        print(f"  [ERR] {e}")
        return False


def wait_for_manual_captcha(url, timeout=300):
    """打开浏览器处理验证码
    
    根据验证码类型自动选择处理方式：
    - 点击验证：自动点击按钮，等待用户完成滑块/图形验证
    - 登录验证：等待用户手动完成登录
    
    Args:
        url: 目标URL
        timeout: 最大等待时间（秒）
    
    Returns:
        tuple: (success: bool, html: str or None)
    """
    if not SELENIUM_AVAILABLE:
        print("  [ERR] Selenium not available. Install: pip install selenium")
        return False, None
    
    driver = create_driver()
    if not driver:
        return False, None
    
    try:
        driver.get(url)
        
        # 等待页面加载
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        page_html = driver.page_source
        
        # 检查是否有验证码
        if not is_captcha_page(page_html):
            # 没有验证码，直接返回
            html = driver.page_source
            driver.quit()
            return True, html
        
        # 判断验证码类型
        captcha_type = get_captcha_type(page_html)
        print(f"  [CAPTCHA] 类型: {captcha_type}")
        
        success = False
        if captcha_type == 'login':
            # 登录验证：等待用户手动操作
            success = handle_login_captcha(driver, timeout)
        else:
            # 点击验证或未知类型：尝试自动点击
            success = handle_click_captcha(driver, timeout)
        
        if success:
            # 验证成功，重新访问目标页面获取内容
            driver.get(url)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # 再次检查是否还有验证码
            if is_captcha_page(driver.page_source):
                print("  [WARN] 仍然检测到验证码")
                # 再试一次
                if captcha_type == 'click':
                    success = handle_click_captcha(driver, 60)
                else:
                    success = handle_login_captcha(driver, 60)
            
            if success and not is_captcha_page(driver.page_source):
                html = driver.page_source
                driver.quit()
                return True, html
        
        driver.quit()
        return False, None
        
    except Exception as e:
        print(f"  [ERR] {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False, None


# 保留旧函数名以保持兼容性
def solve_captcha_with_selenium(url, timeout=90, headless=False):
    """使用Selenium解决验证码（兼容旧接口）"""
    success, html = wait_for_manual_captcha(url, timeout)
    return success, html, None


def get_page_with_captcha_solver(url, session=None, use_selenium=True, selenium_headless=False):
    """获取网页内容，自动处理验证码"""
    import requests
    
    if session is None:
        session = requests.Session()
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://bj.58.com/ershoufang/',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        response = session.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            if is_captcha_page(response.text):
                print(f"  [CAPTCHA] Detected on {url}")
                
                if use_selenium and SELENIUM_AVAILABLE:
                    success, html = wait_for_manual_captcha(url)
                    if success and html:
                        print(f"  [OK] Captcha solved!")
                        return html
                    else:
                        print(f"  [WARN] Failed to solve captcha")
                        return None
                elif not SELENIUM_AVAILABLE:
                    print(f"  [ERR] Selenium not available. Install: pip install selenium")
                    return None
                else:
                    return None
            
            if 'filter-region' not in response.text and 'property' not in response.text:
                print(f"  [WARN] Page seems invalid")
                return None
            
            return response.text
        else:
            print(f"  [WARN] Status code {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


def get_page(url, session=None, use_selenium=True, selenium_headless=False):
    """便捷函数：获取页面内容，自动处理验证码"""
    return get_page_with_captcha_solver(url, session=session, use_selenium=use_selenium, selenium_headless=selenium_headless)
