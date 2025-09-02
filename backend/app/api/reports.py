from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import io
from ..models.database import get_db
from ..api.auth import get_current_user
from ..models.database import User
from ..services.report_service import ReportService

router = APIRouter()
report_service = ReportService()

@router.get("/statistics")
async def get_statistics(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取预约统计数据
    """
    try:
        # 普通用户只能查看自己的统计，管理员可以查看全部
        user_id = None if current_user.role == 'admin' else current_user.id
        
        stats = report_service.get_reservation_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_report(
    user_id: int,
    days: int = Query(30, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户个人报表
    """
    try:
        # 检查权限：用户只能查看自己的报表，管理员可以查看任何用户
        if current_user.role != 'admin' and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="权限不足")
        
        report = report_service.get_user_report(
            db=db,
            user_id=user_id,
            days=days
        )
        
        return {
            "success": True,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户报表失败: {str(e)}")

@router.get("/export/excel")
async def export_excel(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    status_filter: Optional[List[str]] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出预约数据到Excel文件
    """
    try:
        # 普通用户只能导出自己的数据，管理员可以导出全部
        user_id = None if current_user.role == 'admin' else current_user.id
        
        excel_data = report_service.export_reservations_to_excel(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            status_filter=status_filter
        )
        
        # 生成文件名
        filename = f"预约数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 返回Excel文件
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")

@router.get("/export/csv")
async def export_csv(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    status_filter: Optional[List[str]] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出预约数据到CSV文件
    """
    try:
        # 普通用户只能导出自己的数据，管理员可以导出全部
        user_id = None if current_user.role == 'admin' else current_user.id
        
        csv_data = report_service.export_reservations_to_csv(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            status_filter=status_filter
        )
        
        # 生成文件名
        filename = f"预约数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 返回CSV文件
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出CSV失败: {str(e)}")

@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表板数据
    """
    try:
        # 获取最近7天的统计数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 普通用户只能查看自己的数据，管理员可以查看全部
        user_id = None if current_user.role == 'admin' else current_user.id
        
        stats = report_service.get_reservation_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # 简化数据结构，只返回仪表板需要的关键信息
        dashboard_data = {
            'summary': stats['summary'],
            'daily_trend': stats['trends']['daily_stats'],
            'popular_times': stats['trends']['popular_times'],
            'top_resources': stats['resource_usage'][:5]  # 只显示前5个最常用资源
        }
        
        # 如果是管理员，添加用户活跃度数据
        if current_user.role == 'admin':
            dashboard_data['top_users'] = stats['user_activity'][:5]
        
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")

@router.get("/analytics")
async def get_analytics(
    period: str = Query("month", description="统计周期: week, month, quarter, year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取高级分析数据
    """
    try:
        # 根据周期设置时间范围
        end_date = datetime.now()
        if period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # 默认一个月
        
        # 普通用户只能查看自己的数据，管理员可以查看全部
        user_id = None if current_user.role == 'admin' else current_user.id
        
        stats = report_service.get_reservation_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": {
                "period": period,
                "statistics": stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析数据失败: {str(e)}")

@router.get("/quick-stats")
async def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取快速统计数据（用于页面头部显示）
    """
    try:
        # 今天的统计
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # 本周的统计
        week_start = today - timedelta(days=today.weekday())
        
        # 本月的统计
        month_start = today.replace(day=1)
        
        user_id = None if current_user.role == 'admin' else current_user.id
        
        # 今天的预约数
        today_stats = report_service.get_reservation_statistics(
            db=db, start_date=today, end_date=tomorrow, user_id=user_id
        )
        
        # 本周的预约数
        week_stats = report_service.get_reservation_statistics(
            db=db, start_date=week_start, end_date=tomorrow, user_id=user_id
        )
        
        # 本月的预约数
        month_stats = report_service.get_reservation_statistics(
            db=db, start_date=month_start, end_date=tomorrow, user_id=user_id
        )
        
        return {
            "success": True,
            "data": {
                "today": today_stats['summary']['total_reservations'],
                "this_week": week_stats['summary']['total_reservations'],
                "this_month": month_stats['summary']['total_reservations'],
                "pending_count": today_stats['summary']['status_distribution'].get('PENDING', 0),
                "approved_count": today_stats['summary']['status_distribution'].get('APPROVED', 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取快速统计失败: {str(e)}")