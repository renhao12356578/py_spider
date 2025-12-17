import requests
import json

# 1. 获取JWT token
headers = {
    "Authorization": "Bearer your-jwt-token",
    "Content-Type": "application/json"
}

# 2. 生成AI报告
report_data = {
    "area": "海淀区",
    "report_type": "市场分析",
    "city": "北京",
    "format_type": "professional"
}

response = requests.post(
    "http://localhost:5000/api/reports/generate/ai",
    headers=headers,
    json=report_data
)

print(json.dumps(response.json(), indent=2, ensure_ascii=False))