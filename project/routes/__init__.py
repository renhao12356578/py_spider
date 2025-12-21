"""
路由模块初始化文件
"""
from .national_routes import national_bp
from .beijing_routes import beijing_bp
from .ai_routes import ai_bp
from .report_routes import reports_bp

__all__ = ['national_bp', 'beijing_bp',  'ai_bp', 'reports_bp']
