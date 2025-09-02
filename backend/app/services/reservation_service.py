from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.database import Reservation, Resource, User, ReservationType, ReservationStatus, ResourceType
from app.services.intent_service import IntentService
from app.services.notification_service import NotificationService
from app.core.logger import get_logger

logger = get_logger(__name__)

class ReservationService:
    def __init__(self):
        self.intent_service = IntentService()
        self.notification_service = NotificationService()
    
    async def process_reservation_request(
        self,
        message: str,
        entities: Dict[str, Any],
        user_id: int,
        session_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        处理预约请求
        """
        try:
            # 确定预约类型
            reservation_type = self._determine_reservation_type(message, entities)
            
            # 提取时间信息
            time_info = self._extract_time_info(entities, session_context)
            
            # 检查是否有足够信息创建预约
            if self._has_sufficient_info(reservation_type, time_info, entities):
                # 创建预约
                reservation = await self._create_reservation(
                    reservation_type=reservation_type,
                    time_info=time_info,
                    entities=entities,
                    user_id=user_id,
                    db=db
                )
                
                if reservation:
                    # 发送状态变更通知
                    await self.notification_service.send_status_change_notification(
                        reservation=reservation,
                        old_status=None,
                        new_status=reservation.status,
                        db=db
                    )
                    
                    # 安排提醒
                    await self.notification_service.schedule_reminders(
                        reservation=reservation,
                        db=db
                    )
                    
                    return {
                        "response": f"预约创建成功！预约编号：{reservation.id}\n"
                                  f"类型：{self._get_type_display(reservation.type)}\n"
                                  f"时间：{reservation.start_time.strftime('%Y-%m-%d %H:%M')} - {reservation.end_time.strftime('%H:%M')}\n"
                                  f"状态：待审批",
                        "created": True,
                        "reservation_id": reservation.id,
                        "context": {"last_reservation_id": reservation.id},
                        "suggestions": ["查看预约详情", "修改预约", "取消预约"]
                    }
                else:
                    return {
                        "response": "抱歉，预约创建失败。可能是时间冲突或资源不可用。",
                        "created": False,
                        "suggestions": ["选择其他时间", "查看可用资源"]
                    }
            else:
                # 需要更多信息
                missing_info = self._get_missing_info(reservation_type, time_info, entities)
                context_update = {
                    "reservation_type": reservation_type,
                    "partial_info": {"time_info": time_info, "entities": entities}
                }
                
                return {
                    "response": f"我需要更多信息来完成预约：\n{missing_info}",
                    "created": False,
                    "context": context_update,
                    "suggestions": self._get_info_suggestions(reservation_type)
                }
                
        except Exception as e:
            return {
                "response": f"处理预约请求时发生错误：{str(e)}",
                "created": False,
                "suggestions": ["重新尝试", "联系管理员"]
            }
    
    async def process_query_request(
        self,
        message: str,
        entities: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        处理查询请求
        """
        try:
            # 获取用户的预约
            reservations = db.query(Reservation).filter(
                Reservation.user_id == user_id
            ).order_by(Reservation.start_time.desc()).limit(10).all()
            
            if not reservations:
                return {
                    "response": "您目前没有任何预约记录。",
                    "suggestions": ["创建新预约", "预约会议室", "预约访客"]
                }
            
            # 格式化预约信息
            response_text = "您的预约列表：\n\n"
            for i, res in enumerate(reservations, 1):
                status_text = self._get_status_display(res.status)
                type_text = self._get_type_display(res.type)
                resource_text = res.resource.name if res.resource else "无"
                
                response_text += f"{i}. {res.title}\n"
                response_text += f"   类型：{type_text}\n"
                response_text += f"   时间：{res.start_time.strftime('%m-%d %H:%M')} - {res.end_time.strftime('%H:%M')}\n"
                response_text += f"   状态：{status_text}\n"
                if res.resource:
                    response_text += f"   资源：{resource_text}\n"
                response_text += "\n"
            
            return {
                "response": response_text,
                "suggestions": ["查看详情", "修改预约", "取消预约", "创建新预约"]
            }
            
        except Exception as e:
            return {
                "response": f"查询预约时发生错误：{str(e)}",
                "suggestions": ["重新查询", "联系管理员"]
            }
    
    async def process_cancel_request(
        self,
        message: str,
        entities: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        处理取消请求
        """
        try:
            # 提取预约ID或其他标识信息
            reservation_id = self._extract_reservation_id(message, entities)
            
            if reservation_id:
                reservation = db.query(Reservation).filter(
                    and_(
                        Reservation.id == reservation_id,
                        Reservation.user_id == user_id,
                        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED])
                    )
                ).first()
                
                if reservation:
                    old_status = reservation.status
                    reservation.status = ReservationStatus.CANCELLED
                    reservation.updated_at = datetime.utcnow()
                    db.commit()
                    
                    # 发送取消通知
                    await self.notification_service.send_status_change_notification(
                        reservation=reservation,
                        old_status=old_status,
                        new_status=ReservationStatus.CANCELLED,
                        db=db
                    )
                    
                    return {
                        "response": f"预约 #{reservation.id} 已成功取消。\n"
                                  f"原预约：{reservation.title}\n"
                                  f"时间：{reservation.start_time.strftime('%Y-%m-%d %H:%M')}",
                        "suggestions": ["查看其他预约", "创建新预约"]
                    }
                else:
                    return {
                        "response": "未找到可取消的预约，请检查预约编号。",
                        "suggestions": ["查看我的预约", "提供正确的预约编号"]
                    }
            else:
                # 显示可取消的预约列表
                active_reservations = db.query(Reservation).filter(
                    and_(
                        Reservation.user_id == user_id,
                        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED]),
                        Reservation.start_time > datetime.utcnow()
                    )
                ).order_by(Reservation.start_time).all()
                
                if not active_reservations:
                    return {
                        "response": "您没有可以取消的预约。",
                        "suggestions": ["查看所有预约", "创建新预约"]
                    }
                
                response_text = "请选择要取消的预约：\n\n"
                for res in active_reservations:
                    response_text += f"#{res.id} {res.title}\n"
                    response_text += f"时间：{res.start_time.strftime('%m-%d %H:%M')} - {res.end_time.strftime('%H:%M')}\n\n"
                
                return {
                    "response": response_text,
                    "suggestions": [f"取消预约 #{res.id}" for res in active_reservations[:3]]
                }
                
        except Exception as e:
            return {
                "response": f"处理取消请求时发生错误：{str(e)}",
                "suggestions": ["重新尝试", "联系管理员"]
            }
    
    def _determine_reservation_type(self, message: str, entities: Dict[str, Any]) -> ReservationType:
        """
        确定预约类型
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["会议室", "会议", "meeting"]):
            return ReservationType.MEETING
        elif any(word in message_lower for word in ["访客", "来访", "visitor"]):
            return ReservationType.VISITOR
        elif any(word in message_lower for word in ["车位", "停车", "parking", "车辆", "入园", "进园", "开车"]):
            return ReservationType.VEHICLE
        else:
            return ReservationType.MEETING  # 默认为会议室预约
    
    def _extract_time_info(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取时间信息
        """
        time_info = {}
        
        # 从实体中提取时间
        if "time" in entities:
            time_data = entities["time"]
            if isinstance(time_data, dict):
                time_info.update(time_data)
        
        # 从持续时间中提取
        if "duration" in entities:
            duration_data = entities["duration"]
            if isinstance(duration_data, dict):
                time_info.update(duration_data)
        
        # 从上下文中获取部分信息
        if "partial_info" in context and "time_info" in context["partial_info"]:
            time_info.update(context["partial_info"]["time_info"])
        
        return time_info
    
    def _has_sufficient_info(self, reservation_type: ReservationType, time_info: Dict[str, Any], entities: Dict[str, Any]) -> bool:
        """
        检查是否有足够信息创建预约
        """
        # 基本时间信息检查
        has_time = "hour" in time_info or "relative_day" in time_info
        has_duration = "hours" in time_info or "minutes" in time_info
        
        # 如果没有时间信息，返回False
        if not has_time:
            return False
        
        # 如果没有持续时间，使用默认值
        if not has_duration:
            time_info["hours"] = 1  # 默认1小时
        
        # 根据预约类型检查特定信息
        if reservation_type == ReservationType.VEHICLE:
            # 车辆预约需要车牌号
            if "license_plate" not in entities or not entities["license_plate"]:
                return False
        elif reservation_type == ReservationType.VISITOR:
            # 访客预约需要访客信息
            if "visitor_info" not in entities or not entities["visitor_info"]:
                return False
        
        return True
    
    async def _create_reservation(
        self,
        reservation_type: ReservationType,
        time_info: Dict[str, Any],
        entities: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Optional[Reservation]:
        """
        创建预约
        """
        try:
            # 计算开始和结束时间
            start_time, end_time = self._calculate_times(time_info)
            
            # 查找合适的资源
            resource = await self._find_available_resource(reservation_type, start_time, end_time, db)
            
            # 生成标题
            title = self._generate_title(reservation_type, entities)
            
            # 创建预约记录
            reservation = Reservation(
                type=reservation_type,
                user_id=user_id,
                resource_id=resource.id if resource else None,
                start_time=start_time,
                end_time=end_time,
                title=title,
                description=self._generate_description(entities),
                details=entities,
                status=ReservationStatus.PENDING
            )
            
            db.add(reservation)
            db.commit()
            db.refresh(reservation)
            
            return reservation
            
        except Exception as e:
            print(f"创建预约错误: {e}")
            return None
    
    def _calculate_times(self, time_info: Dict[str, Any]) -> tuple:
        """
        计算开始和结束时间
        """
        now = datetime.now()
        
        # 确定日期
        if "relative_day" in time_info:
            target_date = now.date() + timedelta(days=time_info["relative_day"])
        else:
            target_date = now.date()
        
        # 确定时间
        hour = time_info.get("hour", 9)  # 默认9点
        minute = time_info.get("minute", 0)
        
        start_time = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # 计算结束时间
        duration_hours = time_info.get("hours", 1)
        duration_minutes = time_info.get("minutes", 0)
        
        end_time = start_time + timedelta(hours=duration_hours, minutes=duration_minutes)
        
        return start_time, end_time
    
    async def _find_available_resource(
        self,
        reservation_type: ReservationType,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Optional[Resource]:
        """
        查找可用资源
        """
        # 确定资源类型
        if reservation_type == ReservationType.MEETING:
            resource_type = ResourceType.MEETING_ROOM
        elif reservation_type == ReservationType.VEHICLE:
            resource_type = ResourceType.PARKING_SPACE
        else:
            return None  # 访客预约不需要资源
        
        # 查找可用资源
        available_resources = db.query(Resource).filter(
            and_(
                Resource.type == resource_type,
                Resource.is_available == True
            )
        ).all()
        
        # 检查时间冲突
        for resource in available_resources:
            conflicting = db.query(Reservation).filter(
                and_(
                    Reservation.resource_id == resource.id,
                    Reservation.status.in_([ReservationStatus.APPROVED, ReservationStatus.PENDING]),
                    Reservation.start_time < end_time,
                    Reservation.end_time > start_time
                )
            ).first()
            
            if not conflicting:
                return resource
        
        return None
    
    def _generate_title(self, reservation_type: ReservationType, entities: Dict[str, Any]) -> str:
        """
        生成预约标题
        """
        type_names = {
            ReservationType.MEETING: "会议室预约",
            ReservationType.VISITOR: "访客预约",
            ReservationType.VEHICLE: "车位预约"
        }
        
        base_title = type_names.get(reservation_type, "预约")
        
        # 添加具体信息
        if "visitor_info" in entities and entities["visitor_info"]:
            base_title += f" - {entities['visitor_info'][0]}"
        elif "number" in entities and entities["number"]:
            base_title += f" - {entities['number'][0]}人"
        
        return base_title
    
    def _generate_description(self, entities: Dict[str, Any]) -> str:
        """
        生成预约描述
        """
        description_parts = []
        
        if "visitor_info" in entities:
            description_parts.append(f"访客信息：{', '.join(entities['visitor_info'])}")
        
        if "company_info" in entities:
            description_parts.append(f"目标公司：{', '.join(entities['company_info'])}")
        
        if "vehicle_info" in entities:
            description_parts.append(f"车辆信息：{', '.join(entities['vehicle_info'])}")
        
        if "license_plate" in entities:
            description_parts.append(f"车牌号：{', '.join(entities['license_plate'])}")
        
        if "number" in entities:
            description_parts.append(f"人数：{entities['number'][0]}人")
        
        return "; ".join(description_parts) if description_parts else "无特殊说明"
    
    def _get_missing_info(self, reservation_type: ReservationType, time_info: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """
        获取缺失信息提示
        """
        missing = []
        
        if "hour" not in time_info and "relative_day" not in time_info:
            missing.append("• 预约时间（如：明天下午2点）")
        
        if "hours" not in time_info and "minutes" not in time_info:
            missing.append("• 预约时长（如：2小时）")
        
        if reservation_type == ReservationType.VISITOR:
            if "visitor_info" not in entities:
                missing.append("• 访客姓名")
            if "company_info" not in entities:
                missing.append("• 目标公司")
        
        if reservation_type == ReservationType.VEHICLE:
            if "vehicle_info" not in entities:
                missing.append("• 车辆信息")
            if "license_plate" not in entities:
                 missing.append("• 车牌号")
        
        return "\n".join(missing)
    
    def _get_info_suggestions(self, reservation_type: ReservationType) -> List[str]:
        """
        获取信息收集建议
        """
        base_suggestions = ["明天上午9点", "2小时", "下午2点到4点"]
        
        if reservation_type == ReservationType.VISITOR:
            base_suggestions.extend(["张先生来访", "李女士", "ABC公司", "拜访技术部"])
        elif reservation_type == ReservationType.VEHICLE:
            base_suggestions.extend(["京A12345", "沪B67890", "车辆入园", "临时停车"])
        elif reservation_type == ReservationType.MEETING:
            base_suggestions.extend(["5人会议", "大会议室"])
        
        return base_suggestions
    
    def _extract_reservation_id(self, message: str, entities: Dict[str, Any]) -> Optional[int]:
        """
        从消息中提取预约ID
        """
        import re
        
        # 查找 #数字 格式
        id_match = re.search(r"#(\d+)", message)
        if id_match:
            return int(id_match.group(1))
        
        # 查找纯数字
        if "number" in entities and entities["number"]:
            return entities["number"][0]
        
        return None
    
    def _get_type_display(self, reservation_type: ReservationType) -> str:
        """
        获取预约类型显示名称
        """
        type_names = {
            ReservationType.MEETING: "会议室",
            ReservationType.VISITOR: "访客",
            ReservationType.VEHICLE: "车位"
        }
        return type_names.get(reservation_type, "未知")
    
    def _get_status_display(self, status: ReservationStatus) -> str:
        """
        获取状态显示名称
        """
        status_names = {
            ReservationStatus.PENDING: "待审批",
            ReservationStatus.APPROVED: "已批准",
            ReservationStatus.REJECTED: "已拒绝",
            ReservationStatus.COMPLETED: "已完成",
            ReservationStatus.CANCELLED: "已取消"
        }
        return status_names.get(status, "未知")


import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.database import Reservation, Resource, User, ReservationStatus, ReservationType, ResourceType
from app.services.intent_service import EnhancedIntentService
from app.services.notification_service import NotificationService
from app.core.logger import get_logger

logger = get_logger(__name__)

class EnhancedReservationService:
    """增强的预约服务，具备智能冲突检测和自动审批能力"""
    
    def __init__(self):
        self.intent_service = EnhancedIntentService()
        self.notification_service = NotificationService()
    
    async def process_conversational_request(self, message: str, intent: str, entities: Dict, 
                                           confidence: float, user_id: int, 
                                           session_context: Dict, db: Session) -> Dict[str, Any]:
        """处理对话式请求的统一入口"""
        try:
            # 根据意图分发到不同的处理方法
            if intent == 'reservation':
                return await self._handle_reservation_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}, 
                    user_id, session_context
                )
            elif intent == 'query':
                return await self._handle_query_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}, 
                    user_id
                )
            elif intent == 'cancel':
                return await self._handle_cancel_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}, 
                    user_id
                )
            elif intent == 'modify':
                return await self._handle_modify_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}, 
                    user_id
                )
            elif intent == 'help':
                return self._handle_help_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}
                )
            else:  # chat
                return self._handle_chat_intent(
                    {'intent': intent, 'entities': entities, 'confidence': confidence, 'message': message}
                )
        except Exception as e:
            logger.error(f"处理对话请求失败: {str(e)}")
            return {
                'response': '处理请求时发生错误，请稍后重试',
                'success': False,
                'error': str(e)
            }
    
    async def process_chat_reservation(self, message: str, user_id: int, 
                                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """处理对话式预约请求"""
        try:
            # 分析意图
            intent_result = self.intent_service.analyze_intent(message, context)
            logger.info(f"意图分析结果: {json.dumps(intent_result, ensure_ascii=False)}")
            
            # 根据意图处理不同类型的请求
            if intent_result['intent'] == 'reservation':
                return await self._handle_reservation_intent(intent_result, user_id, context)
            elif intent_result['intent'] == 'query':
                return await self._handle_query_intent(intent_result, user_id)
            elif intent_result['intent'] == 'cancel':
                return await self._handle_cancel_intent(intent_result, user_id)
            elif intent_result['intent'] == 'modify':
                return await self._handle_modify_intent(intent_result, user_id)
            elif intent_result['intent'] == 'help':
                return self._handle_help_intent(intent_result)
            else:  # chat
                return self._handle_chat_intent(intent_result)
                
        except Exception as e:
            logger.error(f"处理对话预约失败: {str(e)}")
            return {
                'success': False,
                'message': '处理请求时发生错误，请稍后重试',
                'error': str(e)
            }
    
    async def _handle_reservation_intent(self, intent_result: Dict, user_id: int, 
                                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """处理预约意图"""
        entities = intent_result.get('entities', {})
        
        # 提取预约信息
        reservation_info = self._extract_reservation_info(entities, context)
        
        # 检查信息完整性
        completeness = self._check_reservation_completeness(reservation_info)
        
        if not completeness['is_complete']:
            # 信息不完整，返回需要补充的信息
            return {
                'response': self._generate_completion_prompt(completeness['missing_fields']),
                'success': False,
                'intent': 'reservation',
                'missing_fields': completeness['missing_fields'],
                'current_info': reservation_info,
                'suggestions': self._generate_completion_suggestions(completeness['missing_fields'])
            }
        
        # 信息完整，尝试创建预约
        return await self._create_smart_reservation(reservation_info, user_id)
    
    def _extract_reservation_info(self, entities: Dict, context: Optional[Dict] = None) -> Dict[str, Any]:
        """从实体中提取预约信息"""
        info = {
            'type': ReservationType.MEETING,  # 默认会议室预约
            'title': '会议室预约',
            'description': '',
            'start_time': None,
            'end_time': None,
            'duration_hours': 1,  # 默认1小时
            'attendee_count': 1,  # 默认1人
            'requirements': []
        }
        
        # 从上下文获取信息
        if context:
            info.update({k: v for k, v in context.items() if v is not None})
        
        # 处理时间信息
        if 'time' in entities:
            time_result = self._parse_time_range_entities(entities['time'])
            if time_result:
                info['start_time'] = time_result['start_time']
                if time_result.get('end_time'):
                    info['end_time'] = time_result['end_time']
                    # 计算持续时间
                    duration = (time_result['end_time'] - time_result['start_time']).total_seconds() / 3600
                    info['duration_hours'] = duration
                else:
                    # 如果没有结束时间，根据持续时间计算
                    info['end_time'] = info['start_time'] + timedelta(hours=info['duration_hours'])
        
        # 处理持续时间
        if 'duration' in entities:
            info['duration_hours'] = self._parse_duration_entities(entities['duration'])
        
        # 处理会议室类型
        if 'room_type' in entities:
            info['requirements'].extend(entities['room_type'])
        
        # 处理参会人数
        if 'visitor_info' in entities:
            for visitor in entities['visitor_info']:
                if visitor.endswith('人'):
                    try:
                        count = int(visitor[:-1])
                        info['attendee_count'] = count
                    except ValueError:
                        pass
        
        return info
    
    def _parse_time_entities(self, time_entities: List[str]) -> Optional[datetime]:
        """解析时间实体"""
        now = datetime.now()
        
        # 将所有时间实体组合成一个字符串进行解析
        combined_time = ' '.join(time_entities)
        
        try:
            # 确定基准日期
            base_date = now
            if '明天' in combined_time:
                base_date = now + timedelta(days=1)
            elif '后天' in combined_time:
                base_date = now + timedelta(days=2)
            elif '今天' in combined_time:
                base_date = now
            elif '下周' in combined_time:
                base_date = now + timedelta(days=7)
            
            # 查找小时数
            hour = None
            for entity in time_entities:
                if entity.isdigit():
                    potential_hour = int(entity)
                    if 0 <= potential_hour <= 23:
                        hour = potential_hour
                        break
            
            if hour is not None:
                # 处理上午下午
                if '下午' in combined_time and hour < 12:
                    hour += 12
                elif '晚上' in combined_time and hour < 12:
                    hour += 12
                elif '上午' in combined_time and hour == 12:
                    hour = 0
                
                return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # 如果没有找到具体小时，但有时间相关词汇，返回基准日期
            if any(word in combined_time for word in ['明天', '后天', '今天', '下周']):
                return base_date.replace(hour=9, minute=0, second=0, microsecond=0)  # 默认上午9点
                        
        except Exception as e:
            logger.warning(f"解析时间失败: {combined_time}, 错误: {str(e)}")
        
        return None
    
    def _parse_time_range_entities(self, time_entities: List[str]) -> Optional[Dict[str, datetime]]:
        """解析时间范围实体，支持开始时间和结束时间"""
        now = datetime.now()
        combined_time = ' '.join(time_entities)
        
        try:
            # 确定基准日期
            base_date = now
            if '明天' in combined_time:
                base_date = now + timedelta(days=1)
            elif '后天' in combined_time:
                base_date = now + timedelta(days=2)
            elif '今天' in combined_time:
                base_date = now
            elif '下周' in combined_time:
                base_date = now + timedelta(days=7)
            
            # 查找所有数字（可能的时间点）
            hours = []
            for entity in time_entities:
                if entity.isdigit():
                    potential_hour = int(entity)
                    if 0 <= potential_hour <= 23:
                        hours.append(potential_hour)
            
            if len(hours) >= 2:
                # 有两个时间点，处理为开始和结束时间
                # 对小时进行排序，确保开始时间小于结束时间
                hours.sort()
                start_hour, end_hour = hours[0], hours[1]
                
                # 处理上午下午
                if '下午' in combined_time:
                    if start_hour < 12:
                        start_hour += 12
                    if end_hour < 12:
                        end_hour += 12
                elif '上午' in combined_time:
                    if start_hour == 12:
                        start_hour = 0
                    if end_hour == 12:
                        end_hour = 0
                
                start_time = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                end_time = base_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
                
                return {
                    'start_time': start_time,
                    'end_time': end_time
                }
            elif len(hours) == 1:
                # 只有一个时间点，作为开始时间
                hour = hours[0]
                if '下午' in combined_time and hour < 12:
                    hour += 12
                elif '上午' in combined_time and hour == 12:
                    hour = 0
                
                start_time = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                return {'start_time': start_time}
            
            # 如果没有找到具体小时，但有时间相关词汇，返回基准日期
            if any(word in combined_time for word in ['明天', '后天', '今天', '下周']):
                start_time = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
                return {'start_time': start_time}
                        
        except Exception as e:
            logger.warning(f"解析时间范围失败: {combined_time}, 错误: {str(e)}")
        
        return None
    
    def _parse_duration_entities(self, duration_entities: List[str]) -> float:
        """解析持续时间实体"""
        for duration_str in duration_entities:
            try:
                if '小时' in duration_str:
                    import re
                    hour_match = re.search(r'(\d+)', duration_str)
                    if hour_match:
                        return float(hour_match.group(1))
                    elif '半小时' in duration_str:
                        return 0.5
                    elif '一小时' in duration_str:
                        return 1.0
                    elif '两小时' in duration_str:
                        return 2.0
                    elif '三小时' in duration_str:
                        return 3.0
                
                elif '分钟' in duration_str:
                    import re
                    minute_match = re.search(r'(\d+)', duration_str)
                    if minute_match:
                        return float(minute_match.group(1)) / 60
                        
            except Exception as e:
                logger.warning(f"解析持续时间失败: {duration_str}, 错误: {str(e)}")
                continue
        
        return 1.0  # 默认1小时
    
    def _check_reservation_completeness(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """检查预约信息完整性"""
        missing_fields = []
        
        if not info.get('start_time'):
            missing_fields.append('start_time')
        
        # 其他字段都有默认值，所以不是必需的
        
        return {
            'is_complete': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'completion_score': 1.0 - (len(missing_fields) / 1)  # 只有start_time是必需的
        }
    
    def _generate_completion_prompt(self, missing_fields: List[str]) -> str:
        """生成信息补全提示"""
        prompts = {
            'start_time': '请告诉我预约时间，例如：明天下午2点、今天上午9点等'
        }
        
        if len(missing_fields) == 1:
            return prompts.get(missing_fields[0], '请提供更多信息')
        else:
            return '请提供以下信息：' + '、'.join([prompts.get(field, field) for field in missing_fields])
    
    def _generate_completion_suggestions(self, missing_fields: List[str]) -> List[str]:
        """生成信息补全建议"""
        suggestions = []
        
        if 'start_time' in missing_fields:
            suggestions.extend([
                '明天下午2点',
                '今天上午9点',
                '后天上午10点',
                '下周一下午3点'
            ])
        
        return suggestions[:4]
    
    async def _create_smart_reservation(self, info: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """创建智能预约（包含冲突检测和自动审批）"""
        try:
            db = next(get_db())
            
            # 计算结束时间
            start_time = info['start_time']
            duration_hours = info.get('duration_hours', 1)
            end_time = start_time + timedelta(hours=duration_hours)
            
            # 智能选择会议室
            suitable_room = await self._find_suitable_room(db, start_time, end_time, info)
            
            if not suitable_room:
                # 没有可用会议室，提供替代方案
                alternatives = await self._find_alternative_times(db, start_time, end_time, info)
                return {
                    'success': False,
                    'response': f'抱歉，{start_time.strftime("%Y-%m-%d %H:%M")}到{end_time.strftime("%H:%M")}没有合适的会议室可用',
                    'alternatives': alternatives,
                    'suggestion': '请选择其他时间段或查看推荐的可用时间'
                }
            
            # 创建预约
            reservation = Reservation(
                user_id=user_id,
                resource_id=suitable_room.id,
                type=info.get('type', ReservationType.MEETING),
                title=info.get('title', '会议室预约'),
                description=info.get('description', ''),
                start_time=start_time,
                end_time=end_time,
                status=ReservationStatus.APPROVED,  # 自动审批
                details={
                    'attendee_count': info.get('attendee_count', 1),
                    'requirements': info.get('requirements', [])
                }
            )
            
            db.add(reservation)
            db.commit()
            db.refresh(reservation)
            
            # TODO: 发送通知 (暂时注释掉，等待NotificationService实现)
            # await self.notification_service.send_reservation_confirmation(
            #     user_id, reservation.id, suitable_room.name
            # )
            
            logger.info(f"预约创建成功: 用户{user_id}, 预约ID{reservation.id}")
            
            return {
                'success': True,
                'response': f'预约创建成功！预约编号：{reservation.id}',
                'reservation_id': reservation.id,
                'room_name': suitable_room.name,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'status': '已自动审批通过'
            }
            
        except Exception as e:
            logger.error(f"创建预约失败: {str(e)}")
            return {
                'success': False,
                'response': '创建预约时发生错误，请稍后重试',
                'error': str(e)
            }
        finally:
            db.close()
    
    async def _find_suitable_room(self, db: Session, start_time: datetime, 
                                end_time: datetime, info: Dict[str, Any]) -> Optional[Any]:
        """智能查找合适的会议室"""
        try:
            # 获取所有会议室
            rooms = db.query(Resource).filter(
                Resource.type == ResourceType.MEETING_ROOM,
                Resource.is_available == True
            ).all()
            
            # 按优先级排序会议室
            suitable_rooms = []
            
            for room in rooms:
                # 检查容量
                attendee_count = info.get('attendee_count', 1)
                if room.capacity and room.capacity < attendee_count:
                    continue
                
                # 检查时间冲突
                if await self._check_room_availability(db, room.id, start_time, end_time):
                    # 计算匹配度
                    match_score = self._calculate_room_match_score(room, info)
                    suitable_rooms.append((room, match_score))
            
            # 按匹配度排序，返回最佳选择
            if suitable_rooms:
                suitable_rooms.sort(key=lambda x: x[1], reverse=True)
                return suitable_rooms[0][0]
            
            return None
            
        except Exception as e:
            logger.error(f"查找合适会议室失败: {str(e)}")
            return None
    
    async def _check_room_availability(self, db: Session, room_id: int, 
                                     start_time: datetime, end_time: datetime) -> bool:
        """检查会议室可用性（零冲突检测）"""
        try:
            # 查询时间段内的所有预约
            conflicting_reservations = db.query(Reservation).filter(
                Reservation.resource_id == room_id,
                Reservation.status.in_([ReservationStatus.APPROVED, ReservationStatus.PENDING]),
                # 检查时间重叠：新预约开始时间 < 现有预约结束时间 AND 新预约结束时间 > 现有预约开始时间
                Reservation.start_time < end_time,
                Reservation.end_time > start_time
            ).all()
            
            return len(conflicting_reservations) == 0
            
        except Exception as e:
            logger.error(f"检查会议室可用性失败: {str(e)}")
            return False
    
    def _calculate_room_match_score(self, room: Any, info: Dict[str, Any]) -> float:
        """计算会议室匹配度"""
        score = 0.0
        
        # 容量匹配度（避免浪费）
        attendee_count = info.get('attendee_count', 1)
        if room.capacity:
            if attendee_count <= room.capacity <= attendee_count * 2:
                score += 0.5  # 容量合适
            elif room.capacity > attendee_count * 2:
                score += 0.2  # 容量过大但可用
        
        # 设备需求匹配
        requirements = info.get('requirements', [])
        room_features = room.features or []
        
        for req in requirements:
            if any(req in feature for feature in room_features):
                score += 0.3
        
        # 位置偏好（可以根据用户部门等信息优化）
        score += 0.2  # 基础分
        
        return min(score, 1.0)
    
    async def _find_alternative_times(self, db: Session, preferred_start: datetime, 
                                    preferred_end: datetime, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找替代时间段"""
        alternatives = []
        
        try:
            # 在同一天查找其他时间段
            base_date = preferred_start.date()
            duration = preferred_end - preferred_start
            
            # 检查当天的其他时间段
            for hour in range(9, 18):  # 工作时间9-18点
                alt_start = datetime.combine(base_date, datetime.min.time().replace(hour=hour))
                alt_end = alt_start + duration
                
                if alt_start == preferred_start:  # 跳过原时间
                    continue
                
                suitable_room = await self._find_suitable_room(db, alt_start, alt_end, info)
                if suitable_room:
                    alternatives.append({
                        'start_time': alt_start.strftime('%H:%M'),
                        'end_time': alt_end.strftime('%H:%M'),
                        'room_name': suitable_room.name,
                        'date': base_date.strftime('%Y-%m-%d')
                    })
                
                if len(alternatives) >= 3:  # 最多返回3个替代方案
                    break
            
            # 如果当天没有合适时间，检查第二天
            if len(alternatives) < 3:
                next_date = base_date + timedelta(days=1)
                for hour in range(9, 18):
                    alt_start = datetime.combine(next_date, datetime.min.time().replace(hour=hour))
                    alt_end = alt_start + duration
                    
                    suitable_room = await self._find_suitable_room(db, alt_start, alt_end, info)
                    if suitable_room:
                        alternatives.append({
                            'start_time': alt_start.strftime('%H:%M'),
                            'end_time': alt_end.strftime('%H:%M'),
                            'room_name': suitable_room.name,
                            'date': next_date.strftime('%Y-%m-%d')
                        })
                    
                    if len(alternatives) >= 3:
                        break
            
        except Exception as e:
            logger.error(f"查找替代时间失败: {str(e)}")
        
        return alternatives
    
    async def _handle_query_intent(self, intent_result: Dict, user_id: int) -> Dict[str, Any]:
        """处理查询意图"""
        try:
            db = next(get_db())
            
            # 查询用户的预约
            reservations = db.query(Reservation).filter(
                Reservation.user_id == user_id
            ).order_by(Reservation.start_time.desc()).limit(10).all()
            
            if not reservations:
                return {
                    'success': True,
                    'response': '您暂时没有预约记录',
                    'reservations': []
                }
            
            reservation_list = []
            for res in reservations:
                resource = db.query(Resource).filter(Resource.id == res.resource_id).first()
                reservation_list.append({
                    'id': res.id,
                    'title': res.title,
                    'resource_name': resource.name if resource else '未知资源',
                    'start_time': res.start_time.strftime('%Y-%m-%d %H:%M'),
                    'end_time': res.end_time.strftime('%H:%M'),
                    'status': res.status.value,
                    'attendee_count': res.details.get('attendee_count', 1) if res.details else 1
                })
            
            response_text = f'找到{len(reservations)}条预约记录：\n'
            for i, res in enumerate(reservation_list, 1):
                response_text += f'{i}. {res["title"]} - {res["resource_name"]}\n'
                response_text += f'   时间：{res["start_time"]} - {res["end_time"]}\n'
                response_text += f'   状态：{res["status"]}\n\n'
            
            return {
                'success': True,
                'response': response_text.strip(),
                'reservations': reservation_list
            }
            
        except Exception as e:
            logger.error(f"查询预约失败: {str(e)}")
            return {
                'success': False,
                'response': '查询预约时发生错误，请稍后重试',
                'error': str(e)
            }
        finally:
            db.close()
    
    async def _handle_cancel_intent(self, intent_result: Dict, user_id: int) -> Dict[str, Any]:
        """处理取消意图"""
        return {
            'success': True,
            'response': '请提供要取消的预约编号，或者说"取消最近的预约"',
            'suggestions': ['取消最近的预约', '查看我的预约']
        }
    
    async def _handle_modify_intent(self, intent_result: Dict, user_id: int) -> Dict[str, Any]:
        """处理修改意图"""
        return {
            'success': True,
            'response': '请提供要修改的预约编号和新的时间，例如："修改预约123到明天下午3点"',
            'suggestions': ['查看我的预约', '修改最近的预约时间']
        }
    
    def _handle_help_intent(self, intent_result: Dict) -> Dict[str, Any]:
        """处理帮助意图"""
        return {
            'success': True,
            'response': '我可以帮助您：\n1. 预约会议室 - 说"我要预约明天下午2点的会议室"\n2. 查询预约 - 说"查看我的预约"\n3. 取消预约 - 说"取消预约"\n4. 修改预约 - 说"修改预约时间"',
            'suggestions': ['预约会议室', '查看我的预约', '取消预约', '修改预约']
        }
    
    def _handle_chat_intent(self, intent_result: Dict) -> Dict[str, Any]:
        """处理闲聊意图"""
        message = intent_result.get('message', '')
        
        # 简单的闲聊回复
        if any(word in message for word in ['你好', '您好', 'hi', 'hello']):
            response = '您好！我是智能预约助手，可以帮您预约会议室。有什么需要帮助的吗？'
        elif any(word in message for word in ['天气', '温度']):
            response = '我是预约助手，无法查询天气信息。不过我可以帮您预约会议室哦！'
        elif any(word in message for word in ['谢谢', '感谢']):
            response = '不客气！如果需要预约会议室，随时告诉我。'
        elif any(word in message for word in ['再见', '拜拜']):
            response = '再见！有预约需求时欢迎随时联系我。'
        else:
            response = '我是智能预约助手，主要帮助您预约会议室。您可以说"我要预约明天下午2点的会议室"来开始预约。'
        
        return {
            'success': True,
            'response': response,
            'suggestions': ['预约会议室', '查看我的预约', '帮助']
        }

# 保持向后兼容
class ReservationService(EnhancedReservationService):
    """向后兼容的预约服务"""
    pass