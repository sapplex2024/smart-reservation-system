import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from sqlalchemy.orm import Session
from ..models.database import get_db, SystemLog
from ..models.database import User

class LoggerService:
    def __init__(self):
        self.setup_loggers()
        
    def setup_loggers(self):
        """设置日志记录器"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 应用日志
        self.app_logger = logging.getLogger('app')
        self.app_logger.setLevel(logging.INFO)
        app_handler = RotatingFileHandler(
            log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        app_handler.setFormatter(formatter)
        self.app_logger.addHandler(app_handler)
        
        # 错误日志
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = RotatingFileHandler(
            log_dir / 'error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        
        # 访问日志
        self.access_logger = logging.getLogger('access')
        self.access_logger.setLevel(logging.INFO)
        access_handler = TimedRotatingFileHandler(
            log_dir / 'access.log',
            when='midnight',
            interval=1,
            backupCount=30
        )
        access_handler.setFormatter(formatter)
        self.access_logger.addHandler(access_handler)
        
        # 安全日志
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.WARNING)
        security_handler = RotatingFileHandler(
            log_dir / 'security.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=20
        )
        security_handler.setFormatter(formatter)
        self.security_logger.addHandler(security_handler)
        
        # API日志
        self.api_logger = logging.getLogger('api')
        self.api_logger.setLevel(logging.INFO)
        api_handler = TimedRotatingFileHandler(
            log_dir / 'api.log',
            when='midnight',
            interval=1,
            backupCount=7
        )
        api_handler.setFormatter(formatter)
        self.api_logger.addHandler(api_handler)
    
    def log_info(self, message: str, category: str = 'general', user_id: Optional[int] = None, extra_data: Optional[Dict] = None):
        """记录信息日志"""
        self.app_logger.info(f"[{category}] {message}")
        self._save_to_db('INFO', message, category, user_id, extra_data)
    
    def log_warning(self, message: str, category: str = 'general', user_id: Optional[int] = None, extra_data: Optional[Dict] = None):
        """记录警告日志"""
        self.app_logger.warning(f"[{category}] {message}")
        self._save_to_db('WARNING', message, category, user_id, extra_data)
    
    def log_error(self, message: str, category: str = 'general', user_id: Optional[int] = None, extra_data: Optional[Dict] = None, exception: Optional[Exception] = None):
        """记录错误日志"""
        if exception:
            self.error_logger.error(f"[{category}] {message}", exc_info=exception)
        else:
            self.error_logger.error(f"[{category}] {message}")
        self._save_to_db('ERROR', message, category, user_id, extra_data)
    
    def log_access(self, method: str, path: str, status_code: int, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """记录访问日志"""
        message = f"{method} {path} - {status_code}"
        if ip_address:
            message += f" - {ip_address}"
        
        self.access_logger.info(message)
        
        extra_data = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        self._save_to_db('ACCESS', message, 'access', user_id, extra_data)
    
    def log_security(self, event: str, user_id: Optional[int] = None, ip_address: Optional[str] = None, extra_data: Optional[Dict] = None):
        """记录安全日志"""
        message = f"Security Event: {event}"
        if ip_address:
            message += f" from {ip_address}"
        
        self.security_logger.warning(message)
        
        if not extra_data:
            extra_data = {}
        extra_data['ip_address'] = ip_address
        
        self._save_to_db('SECURITY', message, 'security', user_id, extra_data)
    
    def log_api(self, endpoint: str, method: str, user_id: Optional[int] = None, request_data: Optional[Dict] = None, response_data: Optional[Dict] = None, duration_ms: Optional[float] = None):
        """记录API调用日志"""
        message = f"API Call: {method} {endpoint}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
        
        self.api_logger.info(message)
        
        extra_data = {
            'endpoint': endpoint,
            'method': method,
            'request_data': request_data,
            'response_data': response_data,
            'duration_ms': duration_ms
        }
        self._save_to_db('API', message, 'api', user_id, extra_data)
    
    def _save_to_db(self, level: str, message: str, category: str, user_id: Optional[int] = None, extra_data: Optional[Dict] = None):
        """保存日志到数据库"""
        try:
            db = next(get_db())
            log_entry = SystemLog(
                level=level,
                message=message,
                category=category,
                user_id=user_id,
                extra_data=json.dumps(extra_data) if extra_data else None,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            # 如果数据库记录失败，至少记录到文件
            self.error_logger.error(f"Failed to save log to database: {str(e)}")
    
    def get_logs(self, db: Session, level: Optional[str] = None, category: Optional[str] = None, 
                 user_id: Optional[int] = None, start_date: Optional[datetime] = None, 
                 end_date: Optional[datetime] = None, limit: int = 100, offset: int = 0) -> List[SystemLog]:
        """从数据库获取日志"""
        query = db.query(SystemLog)
        
        if level:
            query = query.filter(SystemLog.level == level)
        if category:
            query = query.filter(SystemLog.category == category)
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        return query.order_by(SystemLog.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_log_stats(self, db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取日志统计信息"""
        query = db.query(SystemLog)
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        total_logs = query.count()
        
        # 按级别统计
        level_stats = {}
        for level in ['INFO', 'WARNING', 'ERROR', 'ACCESS', 'SECURITY', 'API']:
            count = query.filter(SystemLog.level == level).count()
            level_stats[level] = count
        
        # 按类别统计
        category_stats = {}
        categories = db.query(SystemLog.category).distinct().all()
        for (category,) in categories:
            count = query.filter(SystemLog.category == category).count()
            category_stats[category] = count
        
        # 最近24小时错误数
        recent_errors = query.filter(
            SystemLog.level == 'ERROR',
            SystemLog.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            'total_logs': total_logs,
            'level_stats': level_stats,
            'category_stats': category_stats,
            'recent_errors': recent_errors
        }
    
    def cleanup_old_logs(self, db: Session, days_to_keep: int = 30):
        """清理旧日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = db.query(SystemLog).filter(SystemLog.created_at < cutoff_date).delete()
        db.commit()
        
        self.log_info(f"Cleaned up {deleted_count} old log entries", 'maintenance')
        return deleted_count
    
    def export_logs(self, db: Session, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None, format: str = 'json') -> str:
        """导出日志"""
        logs = self.get_logs(db, start_date=start_date, end_date=end_date, limit=10000)
        
        if format == 'json':
            log_data = []
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'level': log.level,
                    'message': log.message,
                    'category': log.category,
                    'user_id': log.user_id,
                    'extra_data': json.loads(log.extra_data) if log.extra_data else None,
                    'created_at': log.created_at.isoformat()
                }
                log_data.append(log_dict)
            
            return json.dumps(log_data, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题行
            writer.writerow(['ID', 'Level', 'Message', 'Category', 'User ID', 'Extra Data', 'Created At'])
            
            # 写入数据行
            for log in logs:
                writer.writerow([
                    log.id,
                    log.level,
                    log.message,
                    log.category,
                    log.user_id,
                    log.extra_data,
                    log.created_at.isoformat()
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

# 全局日志服务实例
logger_service = LoggerService()