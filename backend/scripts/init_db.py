#!/usr/bin/env python3
"""
数据库初始化脚本
创建表结构并插入示例数据
"""

import sys
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.models.database import create_tables, SessionLocal, User, Resource, Reservation
from app.models.database import UserRole, ReservationType, ReservationStatus, ResourceType

# 创建密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def init_database():
    """
    初始化数据库
    """
    print("正在创建数据库表...")
    create_tables()
    print("数据库表创建完成")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("数据库已有数据，跳过初始化")
            return
        
        print("正在插入示例数据...")
        
        # 创建示例用户
        users = [
            User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                role=UserRole.ADMIN,
                permissions={"manage_all": True, "approve_reservations": True}
            ),
            User(
                username="manager",
                email="manager@example.com",
                hashed_password=get_password_hash("manager123"),
                full_name="部门经理",
                role=UserRole.MANAGER,
                permissions={"approve_reservations": True, "manage_resources": True}
            ),
            User(
                username="demo",
                email="demo@example.com",
                hashed_password=get_password_hash("demo123"),
                full_name="演示用户",
                role=UserRole.EMPLOYEE,
                permissions={"create_reservations": True}
            ),
            User(
                username="employee1",
                email="emp1@example.com",
                hashed_password=get_password_hash("emp123"),
                full_name="张三",
                role=UserRole.EMPLOYEE,
                permissions={"create_reservations": True}
            ),
            User(
                username="employee2",
                email="emp2@example.com",
                hashed_password=get_password_hash("emp123"),
                full_name="李四",
                role=UserRole.EMPLOYEE,
                permissions={"create_reservations": True}
            )
        ]
        
        for user in users:
            db.add(user)
        
        # 创建示例资源
        resources = [
            # 会议室
            Resource(
                name="大会议室A",
                type=ResourceType.MEETING_ROOM,
                capacity=20,
                location="1楼东侧",
                description="配备投影仪、白板、视频会议设备",
                features={
                    "projector": True,
                    "whiteboard": True,
                    "video_conference": True,
                    "air_conditioning": True
                }
            ),
            Resource(
                name="小会议室B",
                type=ResourceType.MEETING_ROOM,
                capacity=8,
                location="2楼西侧",
                description="适合小型讨论，配备电视屏幕",
                features={
                    "tv_screen": True,
                    "whiteboard": True,
                    "air_conditioning": True
                }
            ),
            Resource(
                name="培训室C",
                type=ResourceType.MEETING_ROOM,
                capacity=30,
                location="3楼中央",
                description="大型培训室，配备音响系统",
                features={
                    "projector": True,
                    "sound_system": True,
                    "microphone": True,
                    "air_conditioning": True
                }
            ),
            Resource(
                name="讨论室D",
                type=ResourceType.MEETING_ROOM,
                capacity=6,
                location="2楼东侧",
                description="安静的小型讨论空间",
                features={
                    "whiteboard": True,
                    "quiet_environment": True
                }
            ),
            # 停车位
            Resource(
                name="地下车位A01",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="地下一层A区",
                description="标准停车位",
                features={"covered": True, "security_camera": True}
            ),
            Resource(
                name="地下车位A02",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="地下一层A区",
                description="标准停车位",
                features={"covered": True, "security_camera": True}
            ),
            Resource(
                name="地下车位B01",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="地下一层B区",
                description="标准停车位",
                features={"covered": True, "security_camera": True}
            ),
            Resource(
                name="地面车位C01",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="地面停车场C区",
                description="露天停车位",
                features={"outdoor": True}
            ),
            Resource(
                name="地面车位C02",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="地面停车场C区",
                description="露天停车位",
                features={"outdoor": True}
            ),
            Resource(
                name="访客车位V01",
                type=ResourceType.PARKING_SPACE,
                capacity=1,
                location="大门口访客区",
                description="访客专用停车位",
                features={"visitor_only": True, "near_entrance": True}
            )
        ]
        
        for resource in resources:
            db.add(resource)
        
        # 提交用户和资源数据
        db.commit()
        
        # 获取创建的用户和资源ID
        demo_user = db.query(User).filter(User.username == "demo").first()
        employee1 = db.query(User).filter(User.username == "employee1").first()
        meeting_room_a = db.query(Resource).filter(Resource.name == "大会议室A").first()
        meeting_room_b = db.query(Resource).filter(Resource.name == "小会议室B").first()
        parking_a01 = db.query(Resource).filter(Resource.name == "地下车位A01").first()
        
        # 创建示例预约
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        day_after_tomorrow = now + timedelta(days=2)
        
        reservations = [
            # 今天的预约（已批准）
            Reservation(
                type=ReservationType.MEETING,
                user_id=demo_user.id,
                resource_id=meeting_room_b.id,
                start_time=now.replace(hour=14, minute=0, second=0, microsecond=0),
                end_time=now.replace(hour=16, minute=0, second=0, microsecond=0),
                title="项目讨论会议",
                description="讨论Q1项目进展",
                status=ReservationStatus.APPROVED,
                participants=["张三", "李四", "王五"],
                details={"attendees": 4, "equipment": ["投影仪"]}
            ),
            # 明天的预约（待审批）
            Reservation(
                type=ReservationType.MEETING,
                user_id=employee1.id,
                resource_id=meeting_room_a.id,
                start_time=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=12, minute=0, second=0, microsecond=0),
                title="部门周会",
                description="每周例行会议",
                status=ReservationStatus.PENDING,
                participants=["全体成员"],
                details={"attendees": 15, "recurring": True}
            ),
            # 访客预约
            Reservation(
                type=ReservationType.VISITOR,
                user_id=demo_user.id,
                resource_id=None,
                start_time=tomorrow.replace(hour=15, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=17, minute=0, second=0, microsecond=0),
                title="客户拜访 - 王总",
                description="重要客户来访洽谈合作",
                status=ReservationStatus.APPROVED,
                participants=["王总", "助理小刘"],
                details={
                    "visitor_company": "ABC科技有限公司",
                    "contact_phone": "13800138000",
                    "purpose": "商务洽谈"
                }
            ),
            # 车位预约
            Reservation(
                type=ReservationType.VEHICLE,
                user_id=employee1.id,
                resource_id=parking_a01.id,
                start_time=day_after_tomorrow.replace(hour=8, minute=0, second=0, microsecond=0),
                end_time=day_after_tomorrow.replace(hour=18, minute=0, second=0, microsecond=0),
                title="车位预约 - 京A12345",
                description="日常通勤车位",
                status=ReservationStatus.APPROVED,
                participants=[],
                details={
                    "license_plate": "京A12345",
                    "vehicle_type": "轿车",
                    "driver_name": "张三"
                }
            )
        ]
        
        for reservation in reservations:
            db.add(reservation)
        
        # 提交所有数据
        db.commit()
        
        print("示例数据插入完成")
        print("\n创建的用户账号：")
        print("- 管理员: admin / admin123")
        print("- 经理: manager / manager123")
        print("- 演示用户: demo / demo123")
        print("- 员工1: employee1 / emp123")
        print("- 员工2: employee2 / emp123")
        
        print("\n创建的资源：")
        print(f"- 会议室: {len([r for r in resources if r.type == ResourceType.MEETING_ROOM])}个")
        print(f"- 停车位: {len([r for r in resources if r.type == ResourceType.PARKING_SPACE])}个")
        
        print(f"\n创建的示例预约: {len(reservations)}个")
        
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("开始初始化智能预约系统数据库...")
    init_database()
    print("数据库初始化完成！")