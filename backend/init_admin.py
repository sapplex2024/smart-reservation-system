#!/usr/bin/env python3
"""
初始化管理员用户脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import get_db, User, UserRole, engine, Base
from app.api.auth import get_password_hash

def create_admin_user():
    """创建默认管理员用户"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("管理员用户已存在")
            return
        
        # 创建管理员用户
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="系统管理员",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("管理员用户创建成功:")
        print(f"用户名: admin")
        print(f"密码: admin123")
        print(f"角色: {admin_user.role.value}")
        
    except Exception as e:
        print(f"创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()