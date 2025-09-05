from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..models.database import get_db, SystemLog
from ..models.database import User
from ..api.auth import get_current_user
from ..services.logger_service import logger_service

router = APIRouter()

# Pydantic模型
class LogResponse(BaseModel):
    id: int
    level: str
    message: str
    category: str
    user_id: Optional[int]
    extra_data: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LogStats(BaseModel):
    total_logs: int
    level_stats: dict
    category_stats: dict
    recent_errors: int

class LogExportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = "json"  # json or csv
    level: Optional[str] = None
    category: Optional[str] = None

@router.get("/", response_model=List[LogResponse])
async def get_logs(
    db: Session = Depends(get_db),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    category: Optional[str] = Query(None, description="日志类别过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取系统日志列表"""
    try:
        logs = logger_service.get_logs(
            db=db,
            level=level,
            category=category,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        logger_service.log_info(
            f"Retrieved {len(logs)} log entries",
            category="log_access"
        )
        
        return logs
    except Exception as e:
        logger_service.log_error(
            f"Failed to retrieve logs: {str(e)}",
            category="log_error",
            exception=e
        )
        raise HTTPException(status_code=500, detail="获取日志失败")

@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期")
):
    """获取日志统计信息"""
    try:
        stats = logger_service.get_log_stats(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        
        logger_service.log_info(
            f"Retrieved log statistics",
            category="log_access"
        )
        
        return stats
    except Exception as e:
        logger_service.log_error(
            f"Failed to retrieve log stats: {str(e)}",
            category="log_error",
            exception=e
        )
        raise HTTPException(status_code=500, detail="获取日志统计失败")

@router.post("/export")
async def export_logs(
    export_request: LogExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出日志"""
    # 检查权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 验证格式
        if export_request.format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        # 导出日志
        exported_data = logger_service.export_logs(
            db=db,
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            format=export_request.format
        )
        
        logger_service.log_info(
            f"User {current_user.username} exported logs in {export_request.format} format",
            category="log_export",
            user_id=current_user.id,
            extra_data={
                "format": export_request.format,
                "start_date": export_request.start_date.isoformat() if export_request.start_date else None,
                "end_date": export_request.end_date.isoformat() if export_request.end_date else None
            }
        )
        
        # 设置响应头
        from fastapi.responses import Response
        
        if export_request.format == "json":
            media_type = "application/json"
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            media_type = "text/csv"
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content=exported_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger_service.log_error(
            f"Failed to export logs: {str(e)}",
            category="log_error",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(status_code=500, detail="导出日志失败")

@router.delete("/cleanup")
async def cleanup_old_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days_to_keep: int = Query(30, ge=1, le=365, description="保留天数")
):
    """清理旧日志"""
    # 检查权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        deleted_count = logger_service.cleanup_old_logs(db=db, days_to_keep=days_to_keep)
        
        logger_service.log_info(
            f"User {current_user.username} cleaned up {deleted_count} old log entries (kept {days_to_keep} days)",
            category="log_maintenance",
            user_id=current_user.id,
            extra_data={
                "deleted_count": deleted_count,
                "days_to_keep": days_to_keep
            }
        )
        
        return {
            "success": True,
            "message": f"成功清理 {deleted_count} 条旧日志记录",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger_service.log_error(
            f"Failed to cleanup old logs: {str(e)}",
            category="log_error",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(status_code=500, detail="清理日志失败")

@router.get("/levels")
async def get_log_levels():
    """获取可用的日志级别"""
    return {
        "levels": ["INFO", "WARNING", "ERROR", "ACCESS", "SECURITY", "API"]
    }

@router.get("/categories")
async def get_log_categories(
    db: Session = Depends(get_db)
):
    """获取可用的日志类别"""
    try:
        categories = db.query(SystemLog.category).distinct().all()
        category_list = [category[0] for category in categories]
        
        return {
            "categories": category_list
        }
        
    except Exception as e:
        logger_service.log_error(
            f"Failed to retrieve log categories: {str(e)}",
            category="log_error",
            exception=e
        )
        raise HTTPException(status_code=500, detail="获取日志类别失败")

@router.get("/recent-errors")
async def get_recent_errors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="最近多少小时")
):
    """获取最近的错误日志"""
    # 检查权限
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        error_logs = logger_service.get_logs(
            db=db,
            level="ERROR",
            start_date=start_date,
            limit=50
        )
        
        return {
            "recent_errors": error_logs,
            "count": len(error_logs),
            "hours": hours
        }
        
    except Exception as e:
        logger_service.log_error(
            f"Failed to retrieve recent errors: {str(e)}",
            category="log_error",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(status_code=500, detail="获取最近错误失败")