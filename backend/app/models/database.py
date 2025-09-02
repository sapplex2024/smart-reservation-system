from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VISITOR = "visitor"

class ReservationType(str, enum.Enum):
    MEETING = "meeting"
    VISITOR = "visitor"
    VEHICLE = "vehicle"

class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ResourceType(str, enum.Enum):
    MEETING_ROOM = "meeting_room"
    PARKING_SPACE = "parking_space"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservations = relationship("Reservation", foreign_keys="[Reservation.user_id]", back_populates="user")
    approved_reservations = relationship("Reservation", foreign_keys="[Reservation.approved_by]", back_populates="approver")
    logs = relationship("SystemLog", back_populates="user")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(ResourceType), nullable=False)
    capacity = Column(Integer, default=1)
    location = Column(String(200))
    description = Column(Text)
    features = Column(JSON, default={})  # 设备、特殊功能等
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="resource")

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ReservationType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    
    # Time information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Status and approval
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Details (JSON field for flexible data)
    details = Column(JSON, default={})  # 包含访客公司信息、车牌号等
    
    # Metadata
    title = Column(String(200))
    description = Column(Text)
    participants = Column(JSON, default=[])  # 参与人员列表
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="reservations")
    resource = relationship("Resource", back_populates="reservations")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_reservations")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True)
    context = Column(JSON, default={})  # 对话上下文
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text)
    intent = Column(String(50))  # 识别的意图
    entities = Column(JSON, default={})  # 提取的实体
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # 设置类别
    key = Column(String(100), nullable=False, index=True)  # 设置键
    value = Column(Text)  # 设置值（JSON格式）
    description = Column(String(200))  # 设置描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合唯一索引
    __table_args__ = (UniqueConstraint('category', 'key', name='_category_key_uc'),)

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, ACCESS, SECURITY, API
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # general, access, security, api, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    extra_data = Column(Text, nullable=True)  # JSON格式的额外数据
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("User", back_populates="logs")

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()