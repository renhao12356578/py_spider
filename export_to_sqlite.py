"""
MySQL数据库导出到SQLite脚本
导出所有表和完整数据到项目根目录的SQLite数据库
"""
import pymysql
import sqlite3
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'project'))
from utils.database import get_db_connection


def get_all_tables(mysql_conn):
    """获取MySQL数据库中的所有表"""
    cursor = mysql_conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables


def get_table_structure(mysql_conn, table_name):
    """获取表结构信息"""
    cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    columns = cursor.fetchall()
    cursor.close()
    return columns


def mysql_type_to_sqlite(mysql_type):
    """将MySQL数据类型转换为SQLite数据类型"""
    mysql_type = mysql_type.upper()
    
    if 'INT' in mysql_type:
        return 'INTEGER'
    elif 'DECIMAL' in mysql_type or 'NUMERIC' in mysql_type or 'FLOAT' in mysql_type or 'DOUBLE' in mysql_type:
        return 'REAL'
    elif 'DATETIME' in mysql_type or 'TIMESTAMP' in mysql_type or 'DATE' in mysql_type or 'TIME' in mysql_type:
        return 'TEXT'
    elif 'TEXT' in mysql_type or 'BLOB' in mysql_type:
        return 'TEXT'
    else:
        return 'TEXT'


def create_sqlite_table(sqlite_conn, table_name, columns):
    """在SQLite中创建表"""
    cursor = sqlite_conn.cursor()
    
    # 构建CREATE TABLE语句
    column_definitions = []
    for col in columns:
        col_name = col['Field']
        col_type = mysql_type_to_sqlite(col['Type'])
        
        # 处理主键
        if col['Key'] == 'PRI':
            if 'auto_increment' in col['Extra'].lower():
                col_def = f"`{col_name}` INTEGER PRIMARY KEY AUTOINCREMENT"
            else:
                col_def = f"`{col_name}` {col_type} PRIMARY KEY"
        else:
            col_def = f"`{col_name}` {col_type}"
            
            # 处理NOT NULL
            if col['Null'] == 'NO':
                col_def += " NOT NULL"
            
            # 处理默认值
            if col['Default'] is not None:
                if col_type == 'TEXT':
                    col_def += f" DEFAULT '{col['Default']}'"
                else:
                    col_def += f" DEFAULT {col['Default']}"
        
        column_definitions.append(col_def)
    
    create_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(column_definitions)})"
    
    try:
        cursor.execute(create_sql)
        sqlite_conn.commit()
        print(f"✅ 创建表: {table_name}")
    except Exception as e:
        print(f"❌ 创建表失败 {table_name}: {e}")
    finally:
        cursor.close()


def export_table_data(mysql_conn, sqlite_conn, table_name, columns):
    """导出表数据"""
    mysql_cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # 获取MySQL表数据
        mysql_cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = mysql_cursor.fetchall()
        
        if not rows:
            print(f"  └─ {table_name}: 0 条记录")
            return
        
        # 准备插入语句
        column_names = [col['Field'] for col in columns]
        placeholders = ', '.join(['?' for _ in column_names])
        insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{c}`' for c in column_names])}) VALUES ({placeholders})"
        
        # 批量插入数据
        inserted_count = 0
        for row in rows:
            try:
                values = tuple(row[col] for col in column_names)
                sqlite_cursor.execute(insert_sql, values)
                inserted_count += 1
            except Exception as e:
                print(f"  └─ 插入数据失败: {e}")
                continue
        
        sqlite_conn.commit()
        print(f"  └─ {table_name}: {inserted_count} 条记录")
        
    except Exception as e:
        print(f"❌ 导出数据失败 {table_name}: {e}")
    finally:
        mysql_cursor.close()
        sqlite_cursor.close()


def export_mysql_to_sqlite():
    """主函数：导出MySQL数据库到SQLite"""
    print("=" * 60)
    print("MySQL 数据库导出到 SQLite")
    print("=" * 60)
    
    # 生成SQLite数据库文件名（带时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sqlite_db_path = os.path.join(os.path.dirname(__file__), f'house_data_{timestamp}.db')
    
    print(f"\n📁 SQLite数据库路径: {sqlite_db_path}")
    
    # 连接MySQL数据库
    print("\n🔌 连接MySQL数据库...")
    mysql_conn = get_db_connection()
    if not mysql_conn:
        print("❌ MySQL数据库连接失败")
        return
    
    print("✅ MySQL连接成功")
    
    # 连接SQLite数据库
    print("\n🔌 创建SQLite数据库...")
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        print("✅ SQLite数据库创建成功")
    except Exception as e:
        print(f"❌ SQLite数据库创建失败: {e}")
        mysql_conn.close()
        return
    
    try:
        # 获取所有表
        print("\n📋 获取所有表...")
        tables = get_all_tables(mysql_conn)
        print(f"✅ 找到 {len(tables)} 个表: {', '.join(tables)}")
        
        # 导出每个表
        print("\n🚀 开始导出数据...")
        for i, table_name in enumerate(tables, 1):
            print(f"\n[{i}/{len(tables)}] 处理表: {table_name}")
            
            # 获取表结构
            columns = get_table_structure(mysql_conn, table_name)
            
            # 创建SQLite表
            create_sqlite_table(sqlite_conn, table_name, columns)
            
            # 导出数据
            export_table_data(mysql_conn, sqlite_conn, table_name, columns)
        
        print("\n" + "=" * 60)
        print("✅ 数据导出完成！")
        print(f"📁 SQLite数据库文件: {sqlite_db_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 导出过程出错: {e}")
    finally:
        mysql_conn.close()
        sqlite_conn.close()
        print("\n🔒 数据库连接已关闭")


if __name__ == "__main__":
    export_mysql_to_sqlite()
