"""
配置管理模块
从环境变量中读取配置信息
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件（项目根目录）
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量文件: {env_path}")
else:
    print(f"⚠️ 未找到.env文件: {env_path}")
    print("💡 请复制.env.example为.env并填入正确的配置")

# Flask配置
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-please-change')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# 讯飞星火API配置
SPARK_APPID = os.getenv('SPARK_APPID', '')
SPARK_API_SECRET = os.getenv('SPARK_API_SECRET', '')
SPARK_API_KEY = os.getenv('SPARK_API_KEY', '')
SPARK_API_HOST = os.getenv('SPARK_API_HOST', 'wss://spark-api.xf-yun.com/v3.5/chat')

# 讯飞星火图片生成配置
SPARK_IMAGE_APPID = os.getenv('SPARK_IMAGE_APPID', '')
SPARK_IMAGE_API_SECRET = os.getenv('SPARK_IMAGE_API_SECRET', '')
SPARK_IMAGE_API_KEY = os.getenv('SPARK_IMAGE_API_KEY', '')
SPARK_IMAGE_API_HOST = os.getenv('SPARK_IMAGE_API_HOST', 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti')

# 数据库配置
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
DB_PATH = os.getenv('DB_PATH', 'project/house_data.sqlite')

# 验证必需配置
def validate_config():
    """验证必需的配置是否已设置"""
    warnings = []
    
    if FLASK_SECRET_KEY == 'dev-secret-key-please-change':
        warnings.append("⚠️ Flask SECRET_KEY使用默认值，生产环境请修改")
    
    if not SPARK_APPID or not SPARK_API_SECRET or not SPARK_API_KEY:
        warnings.append("⚠️ 讯飞星火API配置未设置，AI功能将无法使用")
    
    if warnings:
        print("\n配置警告:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    return len(warnings) == 0

# 导出配置字典（方便其他模块使用）
CONFIG = {
    'flask': {
        'secret_key': FLASK_SECRET_KEY,
        'debug': FLASK_DEBUG,
        'host': FLASK_HOST,
        'port': FLASK_PORT,
    },
    'spark': {
        'appid': SPARK_APPID,
        'api_secret': SPARK_API_SECRET,
        'api_key': SPARK_API_KEY,
        'api_host': SPARK_API_HOST,
    },
    'spark_image': {
        'appid': SPARK_IMAGE_APPID,
        'api_secret': SPARK_IMAGE_API_SECRET,
        'api_key': SPARK_IMAGE_API_KEY,
        'api_host': SPARK_IMAGE_API_HOST,
    },
    'database': {
        'type': DB_TYPE,
        'path': DB_PATH,
    }
}
