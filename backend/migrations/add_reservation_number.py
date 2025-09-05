#!/usr/bin/env python3
"""
数据库迁移脚本：添加预约编号字段

添加 reservation_number 字段到 reservations 表，并为现有记录生成预约编号
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.database import Base, Reservation

def generate_reservation_number(created_at: datetime, sequence: int) -> str:
    """
    生成预约编号
    格式：年月日期+编号 (例如：250903001)
    """
    date_str = created_at.strftime('%y%m%d')
    return f"{date_str}{sequence:03d}"

def migrate_add_reservation_number():
    """
    执行迁移：添加 reservation_number 字段并为现有记录生成编号
    """
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("开始迁移：添加预约编号字段...")
        
        # 1. 检查并添加新字段（允许为空，稍后更新）
        print("1. 检查并添加 reservation_number 字段...")
        
        # 检查字段是否已存在
        result = session.execute(text("PRAGMA table_info(reservations)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'reservation_number' not in columns:
            # 添加新字段
            session.execute(text("""
                ALTER TABLE reservations 
                ADD COLUMN reservation_number VARCHAR(20)
            """))
            session.commit()
            print("   ✓ reservation_number 字段添加成功")
        else:
            print("   ✓ reservation_number 字段已存在，跳过添加")
        
        # 2. 为现有记录生成预约编号
        print("2. 为现有记录生成预约编号...")
        
        # 获取所有现有预约，按创建时间排序
        reservations = session.execute(text("""
            SELECT id, created_at 
            FROM reservations 
            ORDER BY created_at ASC
        """)).fetchall()
        
        # 按日期分组生成编号
        date_counters = {}
        
        for reservation in reservations:
            reservation_id = reservation[0]
            created_at_str = reservation[1]
            
            # 将字符串转换为 datetime 对象
            if isinstance(created_at_str, str):
                # 尝试解析不同的日期格式
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S.%f')
            else:
                created_at = created_at_str
            
            # 获取日期字符串
            date_key = created_at.strftime('%y%m%d')
            
            # 获取当天的序号
            if date_key not in date_counters:
                date_counters[date_key] = 1
            else:
                date_counters[date_key] += 1
            
            # 生成预约编号
            reservation_number = generate_reservation_number(created_at, date_counters[date_key])
            
            # 更新记录
            session.execute(text("""
                UPDATE reservations 
                SET reservation_number = :reservation_number 
                WHERE id = :id
            """), {
                'reservation_number': reservation_number,
                'id': reservation_id
            })
            
            print(f"  预约 ID {reservation_id} -> 编号 {reservation_number}")
        
        session.commit()
        
        # 3. 设置字段为非空和唯一
        print("3. 设置字段约束...")
        session.execute(text("""
            CREATE UNIQUE INDEX idx_reservation_number ON reservations(reservation_number)
        """))
        session.commit()
        
        # 注意：SQLite不支持ALTER COLUMN，所以我们不能直接设置NOT NULL约束
        # 在生产环境中，可能需要重建表来添加NOT NULL约束
        
        print("迁移完成！")
        print(f"已为 {len(reservations)} 条记录生成预约编号")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_add_reservation_number()