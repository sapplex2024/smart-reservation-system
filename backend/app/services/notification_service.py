from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from enum import Enum

from app.models.database import Reservation, User, ReservationStatus

class NotificationType(str, Enum):
    STATUS_CHANGE = "status_change"
    REMINDER = "reminder"
    APPROVAL_REQUEST = "approval_request"
    CANCELLATION = "cancellation"

class NotificationService:
    def __init__(self):
        self.notifications = []  # 简单的内存存储，实际应用中可以使用数据库或消息队列
    
    async def send_status_change_notification(
        self,
        reservation: Reservation,
        old_status: ReservationStatus,
        new_status: ReservationStatus,
        db: Session
    ) -> Dict[str, Any]:
        """
        发送预约状态变更通知
        """
        try:
            user = db.query(User).filter(User.id == reservation.user_id).first()
            if not user:
                return {"success": False, "error": "用户不存在"}
            
            notification = {
                "id": len(self.notifications) + 1,
                "type": NotificationType.STATUS_CHANGE,
                "user_id": user.id,
                "reservation_id": reservation.id,
                "title": "预约状态更新",
                "message": self._format_status_change_message(reservation, old_status, new_status),
                "data": {
                    "reservation_id": reservation.id,
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "reservation_title": reservation.title
                },
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            self.notifications.append(notification)
            
            # 如果是审批请求，同时通知管理员
            if new_status == ReservationStatus.PENDING:
                await self._notify_approvers(reservation, db)
            
            return {"success": True, "notification_id": notification["id"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_reminder_notification(
        self,
        reservation: Reservation,
        reminder_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        发送预约提醒通知
        """
        try:
            user = db.query(User).filter(User.id == reservation.user_id).first()
            if not user:
                return {"success": False, "error": "用户不存在"}
            
            notification = {
                "id": len(self.notifications) + 1,
                "type": NotificationType.REMINDER,
                "user_id": user.id,
                "reservation_id": reservation.id,
                "title": "预约提醒",
                "message": self._format_reminder_message(reservation, reminder_type),
                "data": {
                    "reservation_id": reservation.id,
                    "reminder_type": reminder_type,
                    "start_time": reservation.start_time.isoformat()
                },
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            self.notifications.append(notification)
            
            return {"success": True, "notification_id": notification["id"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的通知列表
        """
        user_notifications = [
            n for n in self.notifications 
            if n["user_id"] == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n["read"]]
        
        # 按创建时间倒序排列
        user_notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        return user_notifications[:limit]
    
    async def mark_notification_read(
        self,
        notification_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        标记通知为已读
        """
        for notification in self.notifications:
            if notification["id"] == notification_id and notification["user_id"] == user_id:
                notification["read"] = True
                return {"success": True}
        
        return {"success": False, "error": "通知不存在"}
    
    async def mark_all_notifications_read(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        标记用户所有通知为已读
        """
        count = 0
        for notification in self.notifications:
            if notification["user_id"] == user_id and not notification["read"]:
                notification["read"] = True
                count += 1
        
        return {"success": True, "marked_count": count}
    
    async def get_unread_count(self, user_id: int) -> int:
        """
        获取用户未读通知数量
        """
        return len([
            n for n in self.notifications 
            if n["user_id"] == user_id and not n["read"]
        ])
    
    async def _notify_approvers(
        self,
        reservation: Reservation,
        db: Session
    ) -> None:
        """
        通知审批人员
        """
        # 获取管理员和经理角色的用户
        from app.models.database import UserRole
        approvers = db.query(User).filter(
            User.role.in_([UserRole.ADMIN, UserRole.MANAGER]),
            User.is_active == True
        ).all()
        
        for approver in approvers:
            notification = {
                "id": len(self.notifications) + 1,
                "type": NotificationType.APPROVAL_REQUEST,
                "user_id": approver.id,
                "reservation_id": reservation.id,
                "title": "待审批预约",
                "message": f"用户 {reservation.user.full_name} 提交了新的预约申请：{reservation.title}",
                "data": {
                    "reservation_id": reservation.id,
                    "requester_name": reservation.user.full_name,
                    "reservation_title": reservation.title,
                    "start_time": reservation.start_time.isoformat()
                },
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            self.notifications.append(notification)
    
    def _format_status_change_message(
        self,
        reservation: Reservation,
        old_status: ReservationStatus,
        new_status: ReservationStatus
    ) -> str:
        """
        格式化状态变更消息
        """
        status_messages = {
            ReservationStatus.PENDING: "待审批",
            ReservationStatus.APPROVED: "已批准",
            ReservationStatus.REJECTED: "已拒绝",
            ReservationStatus.COMPLETED: "已完成",
            ReservationStatus.CANCELLED: "已取消"
        }
        
        old_text = status_messages.get(old_status, old_status.value)
        new_text = status_messages.get(new_status, new_status.value)
        
        return f"您的预约 \"{reservation.title}\" 状态已从 {old_text} 更新为 {new_text}。"
    
    def _format_reminder_message(
        self,
        reservation: Reservation,
        reminder_type: str
    ) -> str:
        """
        格式化提醒消息
        """
        time_str = reservation.start_time.strftime("%Y年%m月%d日 %H:%M")
        
        if reminder_type == "1_hour":
            return f"提醒：您的预约 \"{reservation.title}\" 将在1小时后（{time_str}）开始。"
        elif reminder_type == "1_day":
            return f"提醒：您的预约 \"{reservation.title}\" 将在明天（{time_str}）开始。"
        elif reminder_type == "start":
            return f"提醒：您的预约 \"{reservation.title}\" 现在开始了！"
        else:
            return f"提醒：您有一个预约 \"{reservation.title}\" 在 {time_str}。"
    
    async def schedule_reminders(
        self,
        reservation: Reservation,
        db: Session
    ) -> Dict[str, Any]:
        """
        安排预约提醒（简化版本，实际应用中应使用任务队列）
        """
        try:
            now = datetime.utcnow()
            start_time = reservation.start_time
            
            # 如果预约已经开始或已过期，不安排提醒
            if start_time <= now:
                return {"success": True, "message": "预约时间已过，无需安排提醒"}
            
            reminders_scheduled = []
            
            # 提前1天提醒
            one_day_before = start_time - timedelta(days=1)
            if one_day_before > now:
                reminders_scheduled.append("1_day")
            
            # 提前1小时提醒
            one_hour_before = start_time - timedelta(hours=1)
            if one_hour_before > now:
                reminders_scheduled.append("1_hour")
            
            # 开始时提醒
            reminders_scheduled.append("start")
            
            return {
                "success": True,
                "reminders_scheduled": reminders_scheduled,
                "message": f"已安排 {len(reminders_scheduled)} 个提醒"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}