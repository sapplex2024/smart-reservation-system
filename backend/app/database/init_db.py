from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, User, SystemSettings, SystemLog
from app.core.config import settings
from app.api.auth import get_password_hash
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        
        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # 检查是否已有管理员用户
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                # 创建默认管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin123"),
                    full_name="系统管理员",
                    role="admin",
                    is_active=True
                )
                db.add(admin_user)
                logger.info("创建默认管理员用户: admin/admin123")
            
            # 初始化系统设置
            default_settings = [
                # 通用设置
                ("general", "system_name", "智能预约系统", "系统名称"),
                ("general", "system_description", "基于AI的智能预约管理系统", "系统描述"),
                ("general", "timezone", "Asia/Shanghai", "系统时区"),
                ("general", "language", "zh-CN", "系统语言"),
                ("general", "date_format", "YYYY-MM-DD", "日期格式"),
                ("general", "time_format", "HH:mm:ss", "时间格式"),
                
                # 预约设置
                ("reservation", "max_advance_days", "30", "最大提前预约天数"),
                ("reservation", "min_advance_hours", "2", "最小提前预约小时数"),
                ("reservation", "max_duration_hours", "8", "单次预约最大时长（小时）"),
                ("reservation", "allow_overlap", "false", "是否允许重叠预约"),
                ("reservation", "auto_confirm", "true", "是否自动确认预约"),
                ("reservation", "cancellation_deadline_hours", "24", "取消预约截止时间（小时）"),
                
                # 通知设置
                ("notification", "email_enabled", "true", "启用邮件通知"),
                ("notification", "sms_enabled", "false", "启用短信通知"),
                ("notification", "reminder_hours", "24,2", "提醒时间（小时，逗号分隔）"),
                ("notification", "admin_email", "admin@example.com", "管理员邮箱"),
                
                # AI设置
                ("ai", "model_provider", "qwen", "AI模型提供商"),
                ("ai", "model_name", "qwen-turbo", "AI模型名称"),
                ("ai", "max_tokens", "2000", "最大token数"),
                ("ai", "temperature", "0.7", "生成温度"),
                ("ai", "enable_voice", "true", "启用语音功能"),
                ("ai", "voice_provider", "aliyun", "语音服务提供商"),
                
                # 安全设置
                ("security", "session_timeout_minutes", "60", "会话超时时间（分钟）"),
                ("security", "max_login_attempts", "5", "最大登录尝试次数"),
                ("security", "lockout_duration_minutes", "30", "账户锁定时间（分钟）"),
                ("security", "password_min_length", "8", "密码最小长度"),
                ("security", "require_password_change_days", "90", "强制密码更改天数"),
                ("security", "enable_two_factor", "false", "启用双因素认证"),
            ]
            
            for category, key, value, description in default_settings:
                existing_setting = db.query(SystemSettings).filter(
                    SystemSettings.category == category,
                    SystemSettings.key == key
                ).first()
                
                if not existing_setting:
                    setting = SystemSettings(
                        category=category,
                        key=key,
                        value=value,
                        description=description
                    )
                    db.add(setting)
            
            # 提交更改
            db.commit()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            db.rollback()
            logger.error(f"数据库初始化失败: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise

def create_sample_data():
    """创建示例数据"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # 创建示例用户
            sample_users = [
                {
                    "username": "manager",
                    "email": "manager@example.com",
                    "password": "manager123",
                    "full_name": "部门经理",
                    "role": "manager"
                },
                {
                    "username": "user1",
                    "email": "user1@example.com",
                    "password": "user123",
                    "full_name": "普通用户1",
                    "role": "user"
                },
                {
                    "username": "user2",
                    "email": "user2@example.com",
                    "password": "user123",
                    "full_name": "普通用户2",
                    "role": "user"
                }
            ]
            
            for user_data in sample_users:
                existing_user = db.query(User).filter(User.username == user_data["username"]).first()
                if not existing_user:
                    user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        hashed_password=get_password_hash(user_data["password"]),
                        full_name=user_data["full_name"],
                        role=user_data["role"],
                        is_active=True
                    )
                    db.add(user)
                    logger.info(f"创建示例用户: {user_data['username']}/{user_data['password']}")
            
            # 创建示例日志
            admin_user = db.query(User).filter(User.username == "admin").first()
            if admin_user:
                sample_logs = [
                    {
                        "level": "INFO",
                        "message": "系统启动成功",
                        "category": "system",
                        "user_id": admin_user.id
                    },
                    {
                        "level": "INFO",
                        "message": "数据库初始化完成",
                        "category": "database",
                        "user_id": admin_user.id
                    },
                    {
                        "level": "ACCESS",
                        "message": "管理员登录",
                        "category": "auth",
                        "user_id": admin_user.id,
                        "extra_data": '{"ip": "127.0.0.1", "user_agent": "System Init"}'
                    }
                ]
                
                for log_data in sample_logs:
                    log = SystemLog(**log_data)
                    db.add(log)
            
            db.commit()
            logger.info("示例数据创建完成")
            
        except Exception as e:
            db.rollback()
            logger.error(f"示例数据创建失败: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise

if __name__ == "__main__":
    print("初始化数据库...")
    init_database()
    
    print("创建示例数据...")
    create_sample_data()
    
    print("数据库初始化完成！")
    print("\n默认账户:")
    print("管理员: admin/admin123")
    print("经理: manager/manager123")
    print("用户: user1/user123, user2/user123")