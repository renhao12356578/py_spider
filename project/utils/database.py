"""
数据库连接池管理模块
提供数据库连接的创建、复用和管理
"""
import pymysql
import os
import traceback

try:
    from dbutils.pooled_db import PooledDB
    POOL_AVAILABLE = True
except ImportError:
    POOL_AVAILABLE = False
    print("[WARNING] DBUtils not installed, using direct connection mode")
    print("          Install with: pip install DBUtils")

# 数据库配置
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_CONFIG = {
    'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    'port': 4000,
    'user': "48pvdQxqqjLneBr.root",
    'password': "o46hvbIhibN3tTPp",
    'database': "python_project",
    'ssl_ca': os.path.join(_CURRENT_DIR, "tidb-ca.pem"),
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}

# 全局连接池对象
_db_pool = None


def init_db_pool():
    """
    初始化数据库连接池
    应在应用启动时调用一次
    """
    global _db_pool
    
    if not POOL_AVAILABLE:
        print("[WARNING] Connection pool unavailable, using direct connection mode")
        return
    
    if _db_pool is not None:
        print("[INFO] Connection pool already initialized, skipping")
        return
    
    try:
        # 检查SSL证书
        cert_file = DB_CONFIG.get('ssl_ca')
        use_ssl = cert_file and os.path.exists(cert_file)
        
        if use_ssl:
            print(f"[INFO] Using SSL connection, cert: {cert_file}")
            pool_config = DB_CONFIG.copy()
        else:
            print("[WARNING] SSL cert not found, using non-SSL connection")
            pool_config = {k: v for k, v in DB_CONFIG.items() 
                          if k not in ['ssl_ca', 'ssl_verify_cert', 'ssl_verify_identity']}
        
        # 创建连接池
        _db_pool = PooledDB(
            creator=pymysql,
            maxconnections=20,      # 最大连接数
            mincached=2,            # 启动时创建的空闲连接数
            maxcached=5,            # 连接池中最多空闲连接数
            maxshared=0,            # 最多共享连接数（0表示不共享）
            blocking=True,          # 连接不够时是否阻塞等待
            maxusage=None,          # 单个连接最多被重复使用次数（None表示无限制）
            setsession=[],          # 连接建立时执行的SQL命令
            ping=1,                 # 连接前检查连接是否可用（0=不检查, 1=默认检查, 2=悲观检查, 4=乐观检查, 7=总是检查）
            **pool_config
        )
        
        # 测试连接
        test_conn = _db_pool.connection()
        test_conn.close()
        
        print("[SUCCESS] Database connection pool initialized")
        print("   - Max connections: 20")
        print("   - Min cached: 2")
        print("   - Max cached: 5")
        
    except Exception as e:
        print(f"[ERROR] Failed to init connection pool: {e}")
        traceback.print_exc()
        _db_pool = None


def get_db_connection():
    """
    获取数据库连接
    - 如果连接池可用，从池中获取
    - 否则创建新连接
    
    Returns:
        connection: pymysql连接对象
    """
    # 使用连接池
    if _db_pool is not None:
        try:
            return _db_pool.connection()
        except Exception as e:
            print(f"[ERROR] Failed to get connection from pool: {e}")
            # 降级到普通连接
            return _get_direct_connection()
    
    # 降级到普通连接
    return _get_direct_connection()


def _get_direct_connection():
    """
    直接创建数据库连接（不使用连接池）
    仅在连接池不可用时使用
    
    Returns:
        connection: pymysql连接对象或None
    """
    try:
        # 检查证书文件
        cert_file = DB_CONFIG.get('ssl_ca')
        if cert_file and os.path.exists(cert_file):
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        else:
            # 无SSL连接
            config_no_ssl = {k: v for k, v in DB_CONFIG.items() 
                           if k not in ['ssl_ca', 'ssl_verify_cert', 'ssl_verify_identity']}
            connection = pymysql.connect(**config_no_ssl)
            return connection
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None


def close_db_pool():
    """
    关闭数据库连接池
    应在应用关闭时调用
    """
    global _db_pool
    if _db_pool is not None:
        try:
            _db_pool.close()
            _db_pool = None
            print("[SUCCESS] Database connection pool closed")
        except Exception as e:
            print(f"[WARNING] Error closing connection pool: {e}")

