# app.py - 主应用入口
import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS
from blueprints.auth import auth_bp
from blueprints.user import user_bp
from blueprints.favorites import favorites_bp

# 创建Flask应用
app = Flask(__name__)

# 启用CORS
CORS(app)

# 注册蓝图

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(favorites_bp)

if __name__ == '__main__':
    print("🚀 启动房产数据分析系统API服务...")
    print(f"🔗 访问地址: http://localhost:5000")
    print(f"📚 API文档:")
    print(f"  - 认证模块: /api/auth/*")
    print(f"  - 用户模块: /api/user/*")
    print(f"  - 收藏模块: /api/favorites/*")
    print(f"  - 测试连接: /api/test/connection")
    app.run(debug=True, port=5000)