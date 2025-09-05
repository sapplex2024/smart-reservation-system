from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd
import io
import json
from ..models.database import Reservation, User, Resource, ReservationType, ReservationStatus
from ..models.database import get_db

class ReportService:
    def __init__(self):
        pass
    
    def get_reservation_statistics(self, 
                                 db: Session,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取预约统计数据
        """
        # 设置默认时间范围（最近30天）
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 基础查询条件
        base_query = db.query(Reservation).filter(
            Reservation.created_at >= start_date,
            Reservation.created_at <= end_date
        )
        
        if user_id:
            base_query = base_query.filter(Reservation.user_id == user_id)
        
        # 总预约数
        total_reservations = base_query.count()
        
        # 按状态统计
        status_stats = {}
        for status in ReservationStatus:
            count = base_query.filter(Reservation.status == status).count()
            status_stats[status.value] = count
        
        # 按类型统计
        type_stats = {}
        for res_type in ReservationType:
            count = base_query.filter(Reservation.type == res_type).count()
            type_stats[res_type.value] = count
        
        # 按日期统计（最近7天）
        daily_stats = []
        for i in range(7):
            date = end_date - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = base_query.filter(
                Reservation.created_at >= day_start,
                Reservation.created_at < day_end
            ).count()
            
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': count
            })
        
        daily_stats.reverse()  # 按时间正序排列
        
        # 按小时统计（今天）
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        hourly_stats = []
        for hour in range(24):
            hour_start = today + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            count = base_query.filter(
                Reservation.created_at >= hour_start,
                Reservation.created_at < hour_end
            ).count()
            
            hourly_stats.append({
                'hour': hour,
                'count': count
            })
        
        # 热门时间段统计
        popular_times = db.query(
            func.extract('hour', Reservation.start_time).label('hour'),
            func.count(Reservation.id).label('count')
        ).filter(
            Reservation.created_at >= start_date,
            Reservation.created_at <= end_date
        )
        
        if user_id:
            popular_times = popular_times.filter(Reservation.user_id == user_id)
        
        popular_times = popular_times.group_by(
            func.extract('hour', Reservation.start_time)
        ).order_by(
            func.count(Reservation.id).desc()
        ).limit(5).all()
        
        popular_times_data = [{
            'hour': int(time.hour),
            'count': time.count
        } for time in popular_times]
        
        # 用户活跃度统计（仅管理员可见）
        user_activity = []
        if not user_id:  # 管理员视图
            user_stats = db.query(
                User.username,
                User.full_name,
                func.count(Reservation.id).label('reservation_count')
            ).join(
                Reservation, User.id == Reservation.user_id
            ).filter(
                Reservation.created_at >= start_date,
                Reservation.created_at <= end_date
            ).group_by(
                User.id, User.username, User.full_name
            ).order_by(
                func.count(Reservation.id).desc()
            ).limit(10).all()
            
            user_activity = [{
                'username': stat.username,
                'full_name': stat.full_name,
                'reservation_count': stat.reservation_count
            } for stat in user_stats]
        
        # 资源使用统计
        resource_stats = db.query(
            Resource.name,
            Resource.type,
            func.count(Reservation.id).label('usage_count')
        ).join(
            Reservation, Resource.id == Reservation.resource_id
        ).filter(
            Reservation.created_at >= start_date,
            Reservation.created_at <= end_date
        )
        
        if user_id:
            resource_stats = resource_stats.filter(Reservation.user_id == user_id)
        
        resource_stats = resource_stats.group_by(
            Resource.id, Resource.name, Resource.type
        ).order_by(
            func.count(Reservation.id).desc()
        ).all()
        
        resource_usage = [{
            'name': stat.name,
            'type': stat.type.value if stat.type else 'unknown',
            'usage_count': stat.usage_count
        } for stat in resource_stats]
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_reservations': total_reservations,
                'status_distribution': status_stats,
                'type_distribution': type_stats
            },
            'trends': {
                'daily_stats': daily_stats,
                'hourly_stats': hourly_stats,
                'popular_times': popular_times_data
            },
            'user_activity': user_activity,
            'resource_usage': resource_usage
        }
    
    def export_reservations_to_excel(self, 
                                   db: Session,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   user_id: Optional[int] = None,
                                   status_filter: Optional[List[str]] = None) -> bytes:
        """
        导出预约数据到Excel文件
        """
        # 设置默认时间范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 构建查询
        query = db.query(
            Reservation.id,
            Reservation.type,
            Reservation.status,
            Reservation.start_time,
            Reservation.end_time,
            Reservation.description,
            Reservation.created_at,
            Reservation.updated_at,
            User.username,
            User.full_name,
            User.email,
            Resource.name.label('resource_name'),
            Resource.type.label('resource_type')
        ).join(
            User, Reservation.user_id == User.id
        ).join(
            Resource, Reservation.resource_id == Resource.id
        ).filter(
            Reservation.created_at >= start_date,
            Reservation.created_at <= end_date
        )
        
        if user_id:
            query = query.filter(Reservation.user_id == user_id)
        
        if status_filter and len(status_filter) > 0:
            query = query.filter(Reservation.status.in_(status_filter))
        
        # 执行查询
        reservations = query.order_by(Reservation.created_at.desc()).all()
        
        # 转换为DataFrame
        data = []
        for res in reservations:
            # 计算持续时间（分钟）
            duration_minutes = 0
            if res.start_time and res.end_time:
                duration = res.end_time - res.start_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            data.append({
                '预约ID': res.id,
                '预约类型': res.type.value if res.type else '',
                '预约状态': res.status.value if res.status else '',
                '开始时间': res.start_time.strftime('%Y-%m-%d %H:%M:%S') if res.start_time else '',
                '结束时间': res.end_time.strftime('%Y-%m-%d %H:%M:%S') if res.end_time else '',
                '持续时间(分钟)': duration_minutes,
                '描述': res.description or '',
                '用户名': res.username,
                '用户姓名': res.full_name,
                '用户邮箱': res.email,
                '资源名称': res.resource_name,
                '资源类型': res.resource_type.value if res.resource_type else '',
                '创建时间': res.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '更新时间': res.updated_at.strftime('%Y-%m-%d %H:%M:%S') if res.updated_at else ''
            })
        
        df = pd.DataFrame(data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 预约数据表
            df.to_excel(writer, sheet_name='预约数据', index=False)
            
            # 统计数据表
            stats = self.get_reservation_statistics(db, start_date, end_date, user_id)
            
            # 状态统计
            status_df = pd.DataFrame([
                {'状态': k, '数量': v} for k, v in stats['summary']['status_distribution'].items()
            ])
            status_df.to_excel(writer, sheet_name='状态统计', index=False)
            
            # 类型统计
            type_df = pd.DataFrame([
                {'类型': k, '数量': v} for k, v in stats['summary']['type_distribution'].items()
            ])
            type_df.to_excel(writer, sheet_name='类型统计', index=False)
            
            # 日期趋势
            daily_df = pd.DataFrame(stats['trends']['daily_stats'])
            daily_df.columns = ['日期', '预约数量']
            daily_df.to_excel(writer, sheet_name='日期趋势', index=False)
            
            # 资源使用统计
            if stats['resource_usage']:
                resource_df = pd.DataFrame(stats['resource_usage'])
                resource_df.columns = ['资源名称', '资源类型', '使用次数']
                resource_df.to_excel(writer, sheet_name='资源使用统计', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    def export_reservations_to_csv(self, 
                                 db: Session,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 user_id: Optional[int] = None,
                                 status_filter: Optional[List[str]] = None) -> str:
        """
        导出预约数据到CSV文件
        """
        # 设置默认时间范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 构建查询（与Excel导出相同的逻辑）
        query = db.query(
            Reservation.id,
            Reservation.type,
            Reservation.status,
            Reservation.start_time,
            Reservation.end_time,
            Reservation.description,
            Reservation.created_at,
            User.username,
            User.full_name,
            Resource.name.label('resource_name')
        ).join(
            User, Reservation.user_id == User.id
        ).join(
            Resource, Reservation.resource_id == Resource.id
        ).filter(
            Reservation.created_at >= start_date,
            Reservation.created_at <= end_date
        )
        
        if user_id:
            query = query.filter(Reservation.user_id == user_id)
        
        if status_filter and len(status_filter) > 0:
            query = query.filter(Reservation.status.in_(status_filter))
        
        reservations = query.order_by(Reservation.created_at.desc()).all()
        
        # 转换为DataFrame
        data = []
        for res in reservations:
            # 计算持续时间（分钟）
            duration_minutes = 0
            if res.start_time and res.end_time:
                duration = res.end_time - res.start_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            data.append({
                '预约ID': res.id,
                '预约类型': res.type.value if res.type else '',
                '预约状态': res.status.value if res.status else '',
                '开始时间': res.start_time.strftime('%Y-%m-%d %H:%M:%S') if res.start_time else '',
                '结束时间': res.end_time.strftime('%Y-%m-%d %H:%M:%S') if res.end_time else '',
                '持续时间(分钟)': duration_minutes,
                '描述': res.description or '',
                '用户名': res.username,
                '用户姓名': res.full_name,
                '资源名称': res.resource_name,
                '创建时间': res.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False, encoding='utf-8-sig')  # 使用utf-8-sig编码支持中文
    
    def get_user_report(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取用户个人报表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 获取用户统计数据
        stats = self.get_reservation_statistics(db, start_date, end_date, user_id)
        
        # 用户最近预约
        recent_reservations = db.query(
            Reservation.id,
            Reservation.type,
            Reservation.status,
            Reservation.start_time,
            Reservation.end_time,
            Resource.name.label('resource_name')
        ).join(
            Resource, Reservation.resource_id == Resource.id
        ).filter(
            Reservation.user_id == user_id
        ).order_by(
            Reservation.created_at.desc()
        ).limit(10).all()
        
        recent_data = []
        for res in recent_reservations:
            # 计算持续时间（分钟）
            duration_minutes = 0
            if res.start_time and res.end_time:
                duration = res.end_time - res.start_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            recent_data.append({
                'id': res.id,
                'type': res.type.value if res.type else '',
                'status': res.status.value if res.status else '',
                'reservation_time': res.start_time.isoformat() if res.start_time else '',
                'duration': duration_minutes,
                'resource_name': res.resource_name
            })
        
        return {
            'user_info': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email
            },
            'statistics': stats,
            'recent_reservations': recent_data
        }