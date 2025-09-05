from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.database import get_db, User
from app.services.notification_service import NotificationService
from app.api.auth import get_current_user

router = APIRouter(tags=["notifications"])
notification_service = NotificationService()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_notifications(
    unread_only: bool = Query(False, description="只获取未读通知"),
    limit: int = Query(20, ge=1, le=100, description="通知数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户通知列表
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit
        )
        
        # 格式化通知数据
        formatted_notifications = []
        for notification in notifications:
            formatted_notification = {
                "id": notification["id"],
                "type": notification["type"],
                "title": notification["title"],
                "message": notification["message"],
                "data": notification["data"],
                "created_at": notification["created_at"].isoformat(),
                "read": notification["read"]
            }
            formatted_notifications.append(formatted_notification)
        
        return formatted_notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取通知失败: {str(e)}")

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """
    获取未读通知数量
    """
    try:
        count = await notification_service.get_unread_count(current_user.id)
        return {"unread_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未读数量失败: {str(e)}")

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    标记通知为已读
    """
    try:
        result = await notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if result["success"]:
            return {"message": "通知已标记为已读"}
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记已读失败: {str(e)}")

@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
):
    """
    标记所有通知为已读
    """
    try:
        result = await notification_service.mark_all_notifications_read(
            user_id=current_user.id
        )
        
        return {
            "message": f"已标记 {result['marked_count']} 个通知为已读",
            "marked_count": result["marked_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量标记已读失败: {str(e)}")

@router.post("/test")
async def create_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建测试通知（仅用于开发测试）
    """
    try:
        # 创建一个模拟的预约对象用于测试
        from app.models.database import Reservation, ReservationType, ReservationStatus
        
        # 这里创建一个临时的预约对象用于测试通知
        test_reservation = Reservation(
            id=999,
            type=ReservationType.MEETING,
            user_id=current_user.id,
            title="测试预约",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            status=ReservationStatus.PENDING
        )
        test_reservation.user = current_user
        
        # 发送测试通知
        result = await notification_service.send_status_change_notification(
            reservation=test_reservation,
            old_status=None,
            new_status=ReservationStatus.PENDING,
            db=db
        )
        
        if result["success"]:
            return {"message": "测试通知已发送", "notification_id": result["notification_id"]}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建测试通知失败: {str(e)}")

@router.get("/stats")
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取通知统计信息
    """
    try:
        all_notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            unread_only=False,
            limit=1000  # 获取所有通知进行统计
        )
        
        unread_count = len([n for n in all_notifications if not n["read"]])
        total_count = len(all_notifications)
        
        # 按类型统计
        type_stats = {}
        for notification in all_notifications:
            notification_type = notification["type"]
            if notification_type not in type_stats:
                type_stats[notification_type] = {"total": 0, "unread": 0}
            type_stats[notification_type]["total"] += 1
            if not notification["read"]:
                type_stats[notification_type]["unread"] += 1
        
        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": total_count - unread_count,
            "type_stats": type_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")