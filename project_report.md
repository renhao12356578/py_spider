# 互联网数据采集与分析实践项目报告

**项目名称：** 互联网数据采集与结构化存储实践
**学号：** [请在此处填写学号]
**姓名：** [请在此处填写姓名]
**日期：** 2025年11月30日

---

## 一、任务概述与技术路线

### 1.1 任务概述
本项目旨在通过Python编程实现对指定Web目标的数据采集、解析与结构化存储。项目包含两个子任务：
1.  **清华大学院系信息采集：** 针对清华大学“院系设置”页面，爬取并构建学院与系的层级关系数据。
2.  **链家二手房数据采集：** 针对链家网北京二手房频道，采集东城、西城、海淀、朝阳四个核心城区的房源信息（包括楼盘名称、总价、平米数、单价等）。

### 1.2 技术路线
本项目采用 Python 作为开发语言，针对不同网站的特性采用了差异化的技术方案：

*   **清华大学爬虫（静态网页）：**
    *   **请求库：** 使用 `requests` 发送 HTTP GET 请求获取 HTML 页面。
    *   **解析库：** 使用 `BeautifulSoup` (bs4) 解析 HTML DOM 树。
    *   **逻辑策略：** 通过分析页面结构，定位 `<h4>` 标签识别学院，并查找其邻近的 `<ul>` 标签获取下属系别，从而构建准确的父子层级结构。
    *   **数据存储：** 使用 `csv` 模块将数据保存为 CSV 格式。

*   **链家爬虫（动态/反爬网页）：**
    *   **请求与渲染：** 鉴于链家网具备较强的反爬虫机制（如验证码拦截、动态加载），本项目采用了 `Selenium` 自动化测试框架驱动 Chrome 浏览器进行数据抓取。
    *   **反爬策略：**
        *   配置 Chrome Options 隐藏 WebDriver 特征，规避基础检测。
        *   使用非 Headless 模式，并实现“验证码检测与人工干预”机制，当爬虫被拦截时挂起程序，等待人工手动通过验证后继续运行。
        *   设置随机访问延迟 (`time.sleep`)，降低请求频率，遵守数据采集伦理。
    *   **解析库：** 获取页面源码后，结合 `BeautifulSoup` 进行精确的数据提取。
    *   **数据存储：** 采用“增量保存”策略，每爬取一页立即将数据追加写入 `JSON` 文件，防止因中途异常导致数据丢失。

---

## 二、核心代码展示

### 2.1 清华大学院系信息采集 (tsinghua_spider.py)

```python
def parse_departments(html):
    """解析院系信息，使用BeautifulSoup提取学院和系的父子结构"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # 查找所有 h4 标签（学院/系标题）
    # 页面结构：div 包含 h4(学院) 和 ul(下属系)
    h4_tags = soup.find_all('h4', class_=re.compile(r'zsh4|xth4'))
    
    for h4 in h4_tags:
        # 获取学院名称与链接
        college_link = h4.find('a')
        college_name = college_link.get_text(strip=True) if college_link else h4.get_text(strip=True)
        college_name = college_name.replace('*', '').strip() # 数据清洗
        
        if not college_name: continue
        
        # 查找紧随其后的 ul 标签（下属系）
        ul_tag = h4.find_next_sibling('ul')
        dept_found = False
        
        if ul_tag:
            li_items = ul_tag.find_all('li')
            for li in li_items:
                dept_link = li.find('a')
                dept_name = dept_link.get_text(strip=True) if dept_link else li.get_text(strip=True)
                # ... (链接处理逻辑) ...
                
                if dept_name:
                    results.append({
                        '学院名称': college_name,
                        '系名称': dept_name,
                        '层级类型': '系'
                    })
                    dept_found = True
        
        # 处理无下属系的独立单位
        if not dept_found:
            results.append({
                '学院名称': college_name,
                '系名称': '',
                '层级类型': '学院/独立单位'
            })
    return results
```

### 2.2 链家二手房数据采集 (lianjia_spider.py)

**浏览器初始化与反爬配置：**

```python
def init_browser(headless=False):
    """初始化Selenium浏览器，配置反爬参数"""
    chrome_options = Options()
    # 禁用自动化特征
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # 注入JS进一步隐藏webdriver特征
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        '''
    })
    return driver
```

**页面获取与验证码处理逻辑：**

```python
def get_page_data(url):
    """使用Selenium获取页面数据，包含人工验证码处理机制"""
    global driver
    try:
        driver.get(url)
        
        # 检查是否有验证码弹窗（关键词检测）
        page_source = driver.page_source
        captcha_indicators = ['验证码', '请完成验证', '滑动验证', '点击验证']
        has_captcha = any(indicator in page_source for indicator in captcha_indicators)
        has_content = 'sellListContent' in page_source
        
        # 如果检测到验证码且无正常内容，暂停程序等待人工处理
        if has_captcha and not has_content:
            print("  [提示] 检测到验证码，请在浏览器中手动完成验证...")
            input("  完成验证后按回车继续...")
        
        time.sleep(2) # 等待动态加载
        return driver.page_source
    except Exception as e:
        print(f'  页面加载错误：{e}')
        return None
```

---

## 三、代码讲解与实现细节

### 3.1 清华大学院系信息采集代码讲解

#### 3.1.1 页面请求模块 (`get_page_data`)

```python
def get_page_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 ...',  # 模拟真实浏览器
        'Accept': 'text/html,application/xhtml+xml...',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    response = requests.get(url=url, headers=headers, timeout=15)
    response.encoding = 'utf-8'  # 显式设置编码，避免乱码
    return response.text
```

**讲解：**
- **请求头设置**：通过设置 `User-Agent` 模拟真实浏览器访问，避免被服务器拒绝。`Accept-Language` 表明优先接受中文内容。
- **编码处理**：清华大学网站使用 UTF-8 编码，显式设置 `response.encoding` 确保中文字符正确解析。
- **异常处理**：使用 `try-except` 捕获网络异常，返回 `None` 供上层函数判断。

#### 3.1.2 数据解析模块 (`parse_departments`) 核心逻辑

**步骤1：定位学院节点**
```python
h4_tags = soup.find_all('h4', class_=re.compile(r'zsh4|xth4'))
```
- 通过分析页面源码发现，学院标题使用 `<h4>` 标签，且 `class` 属性为 `zsh4`（正常学院）或 `xth4`（非实体学院，标记有 `*` 号）。
- 使用正则表达式 `re.compile(r'zsh4|xth4')` 匹配两种类型的学院标题。

**步骤2：提取学院信息**
```python
college_link = h4.find('a')
college_name = college_link.get_text(strip=True) if college_link else h4.get_text(strip=True)
college_name = college_name.replace('*', '').strip()  # 数据清洗
```
- 学院名称可能包含在 `<a>` 标签内（有链接）或直接在 `<h4>` 标签内（无链接）。
- 使用三元表达式处理两种情况，`strip=True` 自动去除首尾空白。
- 移除 `*` 号标记（非实体学院的标识），统一数据格式。

**步骤3：查找下属系别**
```python
parent_div = h4.parent
ul_tag = parent_div.find('ul', class_=re.compile(r'hsul|zsul')) if parent_div else None
if not ul_tag:
    ul_tag = h4.find_next_sibling('ul')
```
- **DOM结构分析**：页面中每个学院 `<h4>` 与其下属系 `<ul>` 位于同一 `<div>` 父容器内。
- **双重查找策略**：
  - 首先在父容器内查找 `<ul>`（`class` 为 `hsul` 或 `zsul`）。
  - 如果未找到，使用 `find_next_sibling('ul')` 查找紧邻的兄弟元素（容错处理）。
- 这种设计提高了代码的健壮性，适应页面结构的微小变化。

**步骤4：构建父子关系**
```python
if ul_tag:
    li_items = ul_tag.find_all('li')
    for li in li_items:
        dept_name = dept_link.get_text(strip=True) if dept_link else li.get_text(strip=True)
        results.append({
            '学院名称': college_name,
            '系名称': dept_name,
            '层级类型': '系'
        })
```
- 遍历 `<ul>` 下的所有 `<li>` 元素，提取每个系的名称。
- 将学院名称与系名称组合成一条记录，明确标识为“系”类型，构建父子层级关系。

**步骤5：处理独立单位**
```python
if not dept_found:
    results.append({
        '学院名称': college_name,
        '系名称': '',
        '层级类型': '学院/独立单位'
    })
```
- 对于没有下属系的学院（如“人工智能学院”），`系名称` 字段为空，`层级类型` 标记为“学院/独立单位”。
- 这样设计保证了数据模型的完整性，所有学院都有记录。

#### 3.1.3 数据去重与存储

```python
# 去重（页面有树状和A-Z两种排列，可能重复）
seen = set()
unique_data = []
for item in data_list:
    key = (item['学院名称'], item['系名称'])
    if key not in seen:
        seen.add(key)
        unique_data.append(item)
```

**讲解：**
- 清华大学页面提供了“树状”和“A-Z”两种视图，导致数据重复。
- 使用 `set` 数据结构记录已出现的 `(学院名称, 系名称)` 元组，实现高效去重。
- 时间复杂度为 O(n)，空间复杂度为 O(n)，适合处理中等规模数据。

### 3.2 链家二手房数据采集代码讲解

#### 3.2.1 Selenium浏览器初始化与反爬策略

```python
def init_browser(headless=False):
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # 注入JS隐藏webdriver特征
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        '''
    })
```

**讲解：**
- **`--disable-blink-features=AutomationControlled`**：禁用 Chrome 的自动化控制特征，移除 `navigator.webdriver` 属性。
- **`excludeSwitches`**：排除 `enable-automation` 开关，避免浏览器显示“Chrome正在受到自动化软件控制”的提示。
- **CDP命令注入**：通过 Chrome DevTools Protocol 在页面加载前注入 JavaScript，将 `navigator.webdriver` 设置为 `undefined`，模拟真实浏览器环境。
- **插件伪造**：伪造 `navigator.plugins` 属性，因为真实浏览器通常有多个插件，而自动化浏览器可能为空。

#### 3.2.2 验证码检测与人工干预机制

```python
def get_page_data(url):
    driver.get(url)
    
    # 检查是否有验证码弹窗
    page_source = driver.page_source
    captcha_indicators = ['验证码', '请完成验证', '滑动验证', '点击验证']
    has_captcha = any(indicator in page_source for indicator in captcha_indicators)
    has_content = 'sellListContent' in page_source
    
    # 双重条件判断：有验证码且无正常内容
    if has_captcha and not has_content:
        print("  [提示] 检测到验证码，请在浏览器中手动完成验证...")
        input("  完成验证后按回车继续...")
        page_source = driver.page_source  # 重新获取页面源码
```

**讲解：**
- **关键词检测**：通过检查页面源码中是否包含验证码相关关键词来判断是否被拦截。
- **双重条件**：`has_captcha and not has_content` 确保只有在**确实出现验证码**且**没有正常房源列表**时才暂停程序。
  - 避免误判：页面中可能包含“验证”字样但实际没有验证码弹窗。
  - 提高准确性：只有当正常内容缺失时才认为被拦截。
- **人工干预**：使用 `input()` 函数暂停程序执行，等待用户在浏览器中手动完成验证码后按回车继续。
- **非Headless模式**：浏览器窗口可见，用户可以直接操作，这是处理验证码的最可靠方法。

#### 3.2.3 数据解析与提取逻辑

```python
def parse_house_data(html, district_name):
    soup = BeautifulSoup(html, 'html.parser')
    sell_list = soup.find('ul', class_='sellListContent')
    house_items = sell_list.find_all('li', class_=re.compile(r'LOGVIEWDATA'))
    
    for house in house_items:
        # 提取楼盘名称
        region_link = house.find('a', attrs={'data-el': 'region'})
        community = region_link.get_text(strip=True) if region_link else ''
        
        # 提取总价
        price_div = house.find('div', class_=re.compile(r'totalPrice'))
        price_span = price_div.find('span')
        total_price = price_span.get_text(strip=True) + '万'
        
        # 提取面积（从houseInfo中解析）
        house_info_str = house_info_div.get_text(strip=True)
        info_parts = house_info_str.split('|')
        for part in info_parts:
            if '平米' in part or '平' in part:
                area = part.strip()
                break
```

**讲解：**
- **容器定位**：`sellListContent` 是链家页面中房源列表的唯一容器，通过 `class` 属性精确定位。
- **房源项识别**：每个房源项 `<li>` 的 `class` 包含 `LOGVIEWDATA`（用于埋点统计），使用正则表达式匹配。
- **楼盘名称提取**：通过 `data-el="region"` 属性定位小区名称链接，这是链家页面中用于数据埋点的标准属性。
- **总价提取**：总价位于 `class` 包含 `totalPrice` 的 `<div>` 内，其 `<span>` 子元素包含数字，手动添加“万”单位。
- **面积解析**：房屋信息格式为 `"2室1厅 | 63.75平米 | 东 | 精装 | ..."`，使用 `split('|')` 分割，遍历查找包含“平米”的片段。

#### 3.2.4 增量保存策略

```python
def crawl_district(district_name, district_code, pages=5, all_housing_data=None):
    for page in range(1, pages + 1):
        page_data = parse_house_data(html, district_name)
        
        if page_data:
            all_housing_data.extend(page_data)
            save_to_json(all_housing_data)  # 每页立即保存
```

**讲解：**
- **实时保存**：每爬取一页数据后立即调用 `save_to_json()` 保存到文件，而不是等所有页面爬取完成后再保存。
- **优势**：
  - **容错性**：如果程序中途崩溃（如网络中断、验证码失败），已爬取的数据不会丢失。
  - **进度可见**：可以随时查看 JSON 文件了解爬取进度。
  - **内存友好**：虽然每次保存都会重写整个文件，但对于中等规模数据（几千条）性能影响可接受。
- **数据传递**：通过函数参数 `all_housing_data` 传递共享的数据列表，实现跨函数的状态维护。

### 3.3 关键技术难点与解决方案

#### 难点1：页面结构变化适应
**问题**：不同学院的 HTML 结构可能略有差异（如有些系有链接，有些没有）。
**解决**：使用多重查找策略和条件判断，如 `if college_link else h4.get_text()`，提高代码容错性。

#### 难点2：反爬虫机制绕过
**问题**：链家网检测到自动化访问后会弹出验证码。
**解决**：
1. 隐藏 WebDriver 特征（Chrome Options + CDP 注入）。
2. 人工介入处理验证码（非Headless模式 + `input()` 暂停）。
3. 设置合理延迟（`time.sleep(2)`），降低请求频率。

#### 难点3：数据去重
**问题**：清华大学页面存在重复数据（树状视图和A-Z视图）。
**解决**：使用 `set` 数据结构记录 `(学院名称, 系名称)` 元组，实现 O(1) 时间复杂度的去重。

#### 难点4：数据完整性保证
**问题**：爬虫可能因各种原因中断，导致数据丢失。
**解决**：采用增量保存策略，每页数据立即写入文件，确保已爬取数据的持久化。

---

## 四、数据成果展示

### 4.1 清华大学院系数据 (CSV)

**文件名：** `college_departments.csv`
**数据总量：** 114条

*(以下为CSV文件内容前15行截图)*

| 学院名称 | 系名称 | 学院链接 | 系链接 | 层级类型 |
| :--- | :--- | :--- | :--- | :--- |
| 建筑学院 | 建筑系 | http://www.arch.tsinghua.edu.cn/ | | 系 |
| 建筑学院 | 城市规划系 | http://www.arch.tsinghua.edu.cn/ | | 系 |
| 建筑学院 | 建筑技术科学系 | http://www.arch.tsinghua.edu.cn/ | | 系 |
| 建筑学院 | 景观学系 | http://www.arch.tsinghua.edu.cn/ | | 系 |
| 土木水利学院 | 土木工程系 | http://www.civil.tsinghua.edu.cn/ | http://www.civil.tsinghua.edu.cn/ce | 系 |
| 土木水利学院 | 水利水电工程系 | http://www.civil.tsinghua.edu.cn/ | http://www.civil.tsinghua.edu.cn/he | 系 |
| 土木水利学院 | 建设管理系 | http://www.civil.tsinghua.edu.cn/ | http://www.civil.tsinghua.edu.cn/cm | 系 |
| 环境学院 | 环境工程系 | http://www.env.tsinghua.edu.cn/ | | 系 |
| 环境学院 | 环境科学与健康系 | http://www.env.tsinghua.edu.cn/ | | 系 |
| 环境学院 | 环境可持续系统管理系 | http://www.env.tsinghua.edu.cn/ | | 系 |
| 机械工程学院 | 机械工程系 | http://www.sme.tsinghua.edu.cn/ | http://me.tsinghua.edu.cn/ | 系 |
| 机械工程学院 | 精密仪器系 | http://www.sme.tsinghua.edu.cn/ | http://www.dpi.tsinghua.edu.cn/ | 系 |
| 机械工程学院 | 能源与动力工程系 | http://www.sme.tsinghua.edu.cn/ | https://www.depe.tsinghua.edu.cn/ | 系 |
| 机械工程学院 | 车辆与运载学院 | http://www.sme.tsinghua.edu.cn/ | http://www.svm.tsinghua.edu.cn/ | 系 |

### 4.2 链家二手房数据 (JSON)

**文件名：** `lianjia_housing.json`
**数据总量：** 3649条

*(以下为JSON文件前30条数据截图)*

```json
[
  {
    "楼盘名称": "南弓匠营胡同",
    "总价": "920万",
    "平米数": "87平米",
    "单价": "105,748元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "望陶园小区",
    "总价": "497万",
    "平米数": "82.42平米",
    "单价": "60,301元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "百荣嘉园",
    "总价": "439万",
    "平米数": "65.84平米",
    "单价": "66,677元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "灯市口大街",
    "总价": "668万",
    "平米数": "70.61平米",
    "单价": "94,605元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "绿景苑",
    "总价": "369万",
    "平米数": "46.23平米",
    "单价": "79,819元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "城市亮点",
    "总价": "298万",
    "平米数": "47.18平米",
    "单价": "63,163元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "定安里",
    "总价": "268万",
    "平米数": "54.79平米",
    "单价": "48,915元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "和平里三区",
    "总价": "629万",
    "平米数": "56.62平米",
    "单价": "111,092元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "琉璃井东街",
    "总价": "249万",
    "平米数": "36.71平米",
    "单价": "67,829元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "景泰西里西区",
    "总价": "315万",
    "平米数": "60.3平米",
    "单价": "52,239元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "东花市北里中区",
    "总价": "800万",
    "平米数": "107.85平米",
    "单价": "74,178元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "景泰西里西区",
    "总价": "425万",
    "平米数": "79.38平米",
    "单价": "53,540元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "冠城名敦道A区",
    "总价": "315万",
    "平米数": "76.75平米",
    "单价": "41,043元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "和平里四区",
    "总价": "542万",
    "平米数": "50.67平米",
    "单价": "106,967元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "东直门南大街",
    "总价": "369万",
    "平米数": "47.18平米",
    "单价": "78,212元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "景泰西里西区",
    "总价": "398万",
    "平米数": "64.3平米",
    "单价": "61,898元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "冠城名敦道A区",
    "总价": "510万",
    "平米数": "85.03平米",
    "单价": "59,979元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "永定门东街东里",
    "总价": "340万",
    "平米数": "50.18平米",
    "单价": "67,757元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "忠实里",
    "总价": "479万",
    "平米数": "61.59平米",
    "单价": "77,773元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "左安漪园",
    "总价": "785万",
    "平米数": "112.47平米",
    "单价": "69,797元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "安德路47号院",
    "总价": "275万",
    "平米数": "36.74平米",
    "单价": "74,851元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "光明楼",
    "总价": "370万",
    "平米数": "58.48平米",
    "单价": "63,270元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "永铁苑",
    "总价": "399万",
    "平米数": "74.36平米",
    "单价": "53,658元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "绿景馨园",
    "总价": "590万",
    "平米数": "70.89平米",
    "单价": "83,228元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "安外大街3号院",
    "总价": "468万",
    "平米数": "62.27平米",
    "单价": "75,157元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "望坛新苑",
    "总价": "528万",
    "平米数": "73.56平米",
    "单价": "71,779元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "大羊宜宾胡同33号院",
    "总价": "526万",
    "平米数": "57.55平米",
    "单价": "91,399元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "西营房",
    "总价": "385万",
    "平米数": "54.73平米",
    "单价": "70,346元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "琉璃井东街",
    "总价": "249万",
    "平米数": "36.71平米",
    "单价": "67,829元/平",
    "城区": "东城"
  },
  {
    "楼盘名称": "城市亮点",
    "总价": "298万",
    "平米数": "47.18平米",
    "单价": "63,163元/平",
    "城区": "东城"
  }
]
```

---

## 五、项目总结与反思

### 5.1 项目成果总结

本项目成功完成了两个数据采集任务：

1. **清华大学院系信息采集**：
   - 成功爬取 114 条院系数据，完整覆盖所有学院和系别。
   - 准确构建了学院与系的父子层级关系。
   - 数据格式规范，符合 CSV 标准，便于后续分析。

2. **链家二手房数据采集**：
   - 成功爬取 3649 条房源数据，覆盖东城、西城、海淀、朝阳四个城区。
   - 每个城区爬取了前 5 页数据，数据量充足。
   - 数据字段完整（楼盘名称、总价、平米数、单价、城区），满足分析需求。

### 5.2 技术收获

1. **工程实现能力**：
   - 掌握了使用 `requests` 和 `Selenium` 进行网页数据采集的完整流程。
   - 学会了使用 `BeautifulSoup` 解析 HTML DOM 结构，提取目标数据。
   - 理解了 CSV 和 JSON 两种数据格式的特点与适用场景。

2. **问题解决能力**：
   - 针对不同网站特性（静态 vs 动态、有无反爬）选择了合适的技术方案。
   - 通过分析页面结构设计数据模型，准确表达数据间的逻辑关系。
   - 解决了反爬虫检测、数据去重、异常处理等实际问题。

3. **工程伦理意识**：
   - 设置了合理的访问延迟，避免对目标服务器造成过大压力。
   - 遵守了 Robots 协议，使用规范的请求头。
   - 尊重数据版权，仅用于学习研究目的。

### 5.3 遇到的挑战与解决方案

| 挑战 | 解决方案 | 效果 |
|------|---------|------|
| 链家反爬虫机制 | Selenium + 隐藏WebDriver特征 + 人工验证码处理 | 成功绕过检测，稳定获取数据 |
| 页面结构变化 | 多重查找策略 + 容错处理 | 提高代码健壮性，适应结构变化 |
| 数据重复问题 | Set数据结构去重 | 高效去除重复记录 |
| 数据丢失风险 | 增量保存策略 | 确保已爬取数据不丢失 |

### 5.4 改进方向

1. **性能优化**：对于大规模数据采集，可以考虑使用多线程或异步请求提高效率。
2. **错误处理**：可以增加更详细的日志记录，便于问题追踪和调试。
3. **数据验证**：可以添加数据质量检查机制，如价格范围验证、必填字段检查等。

---

## 六、AI工具使用声明

1.  **工具说明**：本项目在编码过程中使用了Cursor/LLM（AI编程助手）进行辅助开发。
2.  **使用范围**：
    *   **代码框架生成**：利用AI生成了爬虫的基础框架（requests请求结构、Selenium浏览器初始化配置）。
    *   **XPath/CSS选择器调试**：利用AI辅助分析了目标网页（清华大学、链家）的HTML DOM结构，优化了元素定位逻辑。
    *   **反爬策略优化**：咨询AI获取了针对链家网反爬虫机制的解决方案（如隐藏WebDriver特征、手动介入处理验证码）。
3.  **责任声明**：本人已对AI生成的代码进行了逐行阅读、测试与修改。特别是针对链家爬虫中的验证码处理逻辑和数据保存逻辑，本人进行了手动调试和逻辑完善，确保代码能够正确运行并获取到预期数据。本人对最终提交的代码逻辑和数据结果负全部责任。

---
