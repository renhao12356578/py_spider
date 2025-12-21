"""
优化后的Flask应用主文件
- 统一数据库配置
- 模块化路由结构
- 清晰的职责分离
"""
from flask import Flask, redirect
from pathlib import Path

# 导入所有路由蓝图
from report.report import reports_bp
from routes import national_bp, beijing_bp, ai_bp
from auth import auth_bp
from user import user_bp
from favorites import favorites_bp
from routes.ai_routes import load_all_sessions

# 创建Flask应用
app = Flask(__name__, static_folder='../project_web', static_url_path='/project_web')

# 注册所有蓝图
app.register_blueprint(auth_bp)      # 认证路由: /api/auth/*
app.register_blueprint(national_bp)  # 全国数据路由: /api/national/*
app.register_blueprint(beijing_bp)   # 北京数据路由: /api/beijing/*
app.register_blueprint(ai_bp)        # AI聊天路由: /api/beijing/ai/*
app.register_blueprint(reports_bp)   # 报告路由: /api/reports/*
app.register_blueprint(user_bp)      # 用户路由: /api/user/*
app.register_blueprint(favorites_bp) # 收藏路由: /api/favorites/*

@app.route('/')
def index():
    """首页重定向"""
    return redirect('/project_web/index.html')


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return {
        'code': 404,
        'message': '接口不存在'
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return {
        'code': 500,
        'message': '服务器内部错误'
    }, 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 正在启动北京房产数据分析服务...")
    print("=" * 60)
    print("📋 已注册的路由模块:")
    print("  - 认证模块: /api/auth/*")
    print("  - 全国数据: /api/national/*")
    print("  - 北京数据: /api/beijing/*")
    print("  - AI聊天: /api/beijing/ai/*")
    print("  - 报告管理: /api/reports/*")
    print("=" * 60)
    
    # 加载AI聊天会话历史
    load_all_sessions()
    
    print("=" * 60)
    print("✅ 服务启动成功!")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=True)
