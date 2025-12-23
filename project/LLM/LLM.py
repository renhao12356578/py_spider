"""LLM业务逻辑模块 - 房产推荐提示词"""
from tools.house_query import query_house_data_by_area


# ================= 房源数据获取（延迟加载） =================
_housing_data_cache = None


def get_housing_data():
    """延迟加载房源数据"""
    global _housing_data_cache
    if _housing_data_cache is None:
        result = query_house_data_by_area("海淀", 100)
        if result and len(result) > 0:
            _housing_data_cache = "【房源库存清单】：" + (str(result[0]) if result[0] else "无数据")
        else:
            _housing_data_cache = "【房源库存清单】：暂无数据"
    return _housing_data_cache

# ================= 系统提示词 =================
RECOMANDATION_PROMPT_TEMPLATE = """
你是一位专业的资深房产顾问。你的任务是根据用户的需求，从【房源库存清单】中推荐最匹配的房子。

{housing_data}

你的工作准则：
1. **需求挖掘**：认真分析用户的每一句话。如果用户需求模糊（比如只说“我想买房”），你需要主动询问预算、区域、户型或购房目的（刚需/投资/学区）。
2. **记忆力**：你必须记住用户之前的对话。例如，如果用户之前说了“预算800万”，下一轮他说“还是太贵了”，你推荐的房子必须显著低于800万。
3. **严格匹配**：**只能推荐清单里有的房子**，严禁编造虚假房源。如果没有匹配的，请诚实告知并询问是否调整条件。
4. **回复风格**：专业、热情、有逻辑。推荐时请说明推荐理由（结合用户需求）。
"""


def get_recomandation_prompt():
    """获取房产推荐提示词（延迟加载房源数据）"""
    return RECOMANDATION_PROMPT_TEMPLATE.format(housing_data=get_housing_data())
