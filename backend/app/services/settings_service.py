from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.database import SystemSettings

class SettingsService:
    """系统设置服务"""
    
    def __init__(self):
        self.default_settings = {
            "general": {
                "system_name": "智能预约系统",
                "system_description": "基于AI的智能预约管理系统",
                "default_language": "zh-CN",
                "timezone": "Asia/Shanghai",
                "theme_mode": "light"
            },
            "reservation": {
                "working_hours": ["09:00", "18:00"],
                "advance_booking_days": 30,
                "min_duration": 30,
                "max_duration": 240,
                "auto_approval": False,
                "cancellation_deadline": 2
            },
            "notification": {
                "email_enabled": True,
                "sms_enabled": False,
                "push_enabled": True,
                "reminder_times": [15, 30, 60],
                "rate_limit": 10
            },
            "ai": {
                "model": "qwen",
                "api_key": "",
                "temperature": 0.7,
                "max_tokens": 2000,
                "speech_recognition": True,
                "speech_synthesis": True
            },
            "security": {
                "password_policy": ["minLength", "requireNumbers"],
                "session_timeout": 120,
                "max_login_attempts": 5,
                "lockout_duration": 15,
                "two_factor_auth": False
            }
        }
    
    def get_all_settings(self, db: Session) -> Dict[str, Any]:
        """获取所有系统设置"""
        try:
            settings = {}
            
            # 从数据库获取设置
            db_settings = db.query(SystemSettings).all()
            
            # 如果数据库中没有设置，使用默认设置
            if not db_settings:
                return self.default_settings
            
            # 按类别组织设置
            for setting in db_settings:
                if setting.category not in settings:
                    settings[setting.category] = {}
                
                try:
                    # 尝试解析JSON值
                    value = json.loads(setting.value) if setting.value else None
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON，直接使用字符串值
                    value = setting.value
                
                settings[setting.category][setting.key] = value
            
            # 合并默认设置（确保所有必需的设置都存在）
            for category, default_values in self.default_settings.items():
                if category not in settings:
                    settings[category] = default_values
                else:
                    for key, default_value in default_values.items():
                        if key not in settings[category]:
                            settings[category][key] = default_value
            
            return settings
            
        except Exception as e:
            print(f"获取设置失败: {e}")
            return self.default_settings
    
    def get_category_settings(self, db: Session, category: str) -> Dict[str, Any]:
        """获取指定类别的设置"""
        try:
            all_settings = self.get_all_settings(db)
            return all_settings.get(category, {})
        except Exception as e:
            print(f"获取类别设置失败: {e}")
            return self.default_settings.get(category, {})
    
    def get_setting(self, db: Session, category: str, key: str) -> Any:
        """获取单个设置值"""
        try:
            category_settings = self.get_category_settings(db, category)
            return category_settings.get(key)
        except Exception as e:
            print(f"获取设置失败: {e}")
            return None
    
    def update_settings(self, db: Session, settings: Dict[str, Any]) -> bool:
        """更新系统设置"""
        try:
            for category, category_settings in settings.items():
                if not isinstance(category_settings, dict):
                    continue
                
                for key, value in category_settings.items():
                    # 查找现有设置
                    existing_setting = db.query(SystemSettings).filter(
                        SystemSettings.category == category,
                        SystemSettings.key == key
                    ).first()
                    
                    # 将值转换为JSON字符串（如果需要）
                    if isinstance(value, (dict, list)):
                        json_value = json.dumps(value, ensure_ascii=False)
                    else:
                        json_value = str(value) if value is not None else None
                    
                    if existing_setting:
                        # 更新现有设置
                        existing_setting.value = json_value
                        existing_setting.updated_at = datetime.utcnow()
                    else:
                        # 创建新设置
                        new_setting = SystemSettings(
                            category=category,
                            key=key,
                            value=json_value,
                            description=f"{category}.{key} setting"
                        )
                        db.add(new_setting)
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"更新设置失败: {e}")
            db.rollback()
            return False
    
    def reset_settings(self, db: Session, category: Optional[str] = None) -> bool:
        """重置设置到默认值"""
        try:
            if category:
                # 重置指定类别的设置
                db.query(SystemSettings).filter(
                    SystemSettings.category == category
                ).delete()
                
                # 添加默认设置
                if category in self.default_settings:
                    default_values = self.default_settings[category]
                    for key, value in default_values.items():
                        json_value = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                        new_setting = SystemSettings(
                            category=category,
                            key=key,
                            value=json_value,
                            description=f"{category}.{key} setting"
                        )
                        db.add(new_setting)
            else:
                # 重置所有设置
                db.query(SystemSettings).delete()
                
                # 添加所有默认设置
                for category, category_settings in self.default_settings.items():
                    for key, value in category_settings.items():
                        json_value = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                        new_setting = SystemSettings(
                            category=category,
                            key=key,
                            value=json_value,
                            description=f"{category}.{key} setting"
                        )
                        db.add(new_setting)
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"重置设置失败: {e}")
            db.rollback()
            return False
    
    def get_system_info(self, db: Session) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            from ..models.database import User, Reservation
            import psutil
            import platform
            
            # 获取统计数据
            total_users = db.query(User).count()
            total_reservations = db.query(Reservation).count()
            
            # 获取系统资源信息
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取系统运行时间
            boot_time = psutil.boot_time()
            uptime = datetime.now().timestamp() - boot_time
            
            return {
                "version": "1.0.0",
                "build_time": "2024-01-20 10:30:00",
                "uptime": int(uptime),
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "db_status": "connected",
                "total_users": total_users,
                "total_reservations": total_reservations,
                "memory_used": f"{memory.used // (1024**2)} MB",
                "memory_total": f"{memory.total // (1024**2)} MB",
                "memory_percent": memory.percent,
                "storage_used": f"{disk.used // (1024**3)} GB",
                "storage_total": f"{disk.total // (1024**3)} GB",
                "storage_percent": (disk.used / disk.total) * 100
            }
            
        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return {
                "version": "1.0.0",
                "build_time": "2024-01-20 10:30:00",
                "uptime": 0,
                "platform": "Unknown",
                "python_version": "Unknown",
                "db_status": "error",
                "total_users": 0,
                "total_reservations": 0,
                "memory_used": "0 MB",
                "memory_total": "0 MB",
                "memory_percent": 0,
                "storage_used": "0 GB",
                "storage_total": "0 GB",
                "storage_percent": 0
            }
    
    def export_settings(self, db: Session) -> Dict[str, Any]:
        """导出所有设置"""
        try:
            settings = self.get_all_settings(db)
            return {
                "settings": settings,
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        except Exception as e:
            print(f"导出设置失败: {e}")
            return {}
    
    def import_settings(self, db: Session, settings_data: Dict[str, Any]) -> bool:
        """导入设置"""
        try:
            if "settings" not in settings_data:
                return False
            
            return self.update_settings(db, settings_data["settings"])
            
        except Exception as e:
            print(f"导入设置失败: {e}")
            return False
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, list]:
        """验证设置数据"""
        errors = {}
        
        try:
            # 验证预约设置
            if "reservation" in settings:
                reservation = settings["reservation"]
                
                if "advance_booking_days" in reservation:
                    days = reservation["advance_booking_days"]
                    if not isinstance(days, int) or days < 1 or days > 365:
                        errors.setdefault("reservation", []).append("提前预约天数必须在1-365之间")
                
                if "min_duration" in reservation and "max_duration" in reservation:
                    min_dur = reservation["min_duration"]
                    max_dur = reservation["max_duration"]
                    if min_dur >= max_dur:
                        errors.setdefault("reservation", []).append("最小预约时长必须小于最大预约时长")
            
            # 验证AI设置
            if "ai" in settings:
                ai = settings["ai"]
                
                if "temperature" in ai:
                    temp = ai["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                        errors.setdefault("ai", []).append("温度参数必须在0-1之间")
                
                if "max_tokens" in ai:
                    tokens = ai["max_tokens"]
                    if not isinstance(tokens, int) or tokens < 100 or tokens > 4000:
                        errors.setdefault("ai", []).append("最大令牌数必须在100-4000之间")
            
            # 验证安全设置
            if "security" in settings:
                security = settings["security"]
                
                if "session_timeout" in security:
                    timeout = security["session_timeout"]
                    if not isinstance(timeout, int) or timeout < 30 or timeout > 1440:
                        errors.setdefault("security", []).append("会话超时时间必须在30-1440分钟之间")
                
                if "max_login_attempts" in security:
                    attempts = security["max_login_attempts"]
                    if not isinstance(attempts, int) or attempts < 3 or attempts > 10:
                        errors.setdefault("security", []).append("最大登录尝试次数必须在3-10之间")
            
        except Exception as e:
            errors["general"] = [f"验证设置时发生错误: {str(e)}"]
        
        return errors