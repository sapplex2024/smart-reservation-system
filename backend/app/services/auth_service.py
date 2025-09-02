from sqlalchemy.orm import Session
from ..models.database import User
from ..api.auth import get_password_hash, verify_password
from typing import Optional

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, 
                   full_name: str = None, role: str = "user") -> User:
        """创建新用户"""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name or username,
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user_password(db: Session, user: User, new_password: str) -> bool:
        """更新用户密码"""
        try:
            user.hashed_password = get_password_hash(new_password)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def deactivate_user(db: Session, user: User) -> bool:
        """停用用户"""
        try:
            user.is_active = False
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def activate_user(db: Session, user: User) -> bool:
        """激活用户"""
        try:
            user.is_active = True
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def update_user_role(db: Session, user: User, new_role: str) -> bool:
        """更新用户角色"""
        try:
            user.role = new_role
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """检查用户是否为管理员"""
        return user.role == "admin"
    
    @staticmethod
    def is_manager(user: User) -> bool:
        """检查用户是否为经理"""
        return user.role in ["admin", "manager"]
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """检查用户是否可以管理其他用户"""
        return user.role in ["admin", "manager"]
    
    @staticmethod
    def can_access_logs(user: User) -> bool:
        """检查用户是否可以访问日志"""
        return user.role in ["admin", "manager"]
    
    @staticmethod
    def can_modify_settings(user: User) -> bool:
        """检查用户是否可以修改系统设置"""
        return user.role == "admin"