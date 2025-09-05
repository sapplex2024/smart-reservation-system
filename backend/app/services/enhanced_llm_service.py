from typing import Dict, List, Optional, Any, Callable
import json
import logging
from datetime import datetime, timedelta
from app.core.config import get_settings
# 移除已删除的siliconflow_service导入
from app.services.ai_service import AIService
from app.services.reservation_service import EnhancedReservationService
from app.models.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import ReservationType
from app.api.reservations import get_status_display

logger = logging.getLogger(__name__)

# Pydantic models for reservation creation
class ReservationCreate(BaseModel):
    type: ReservationType
    resource_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    title: str
    description: Optional[str] = None
    participants: Optional[List[str]] = []
    details: Optional[dict] = {}

class ConversationMemory:
    """对话记忆管理器"""
    
    def __init__(self, max_history: int = 10):
        self.conversations: Dict[str, List[Dict]] = {}
        self.max_history = max_history
    
    def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息到对话历史"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[user_id].append(message)
        
        # 保持历史记录在限制范围内
        if len(self.conversations[user_id]) > self.max_history:
            self.conversations[user_id] = self.conversations[user_id][-self.max_history:]
    
    def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取对话历史"""
        history = self.conversations.get(user_id, [])
        if limit:
            return history[-limit:]
        return history
    
    def clear_conversation(self, user_id: str):
        """清除用户对话历史"""
        if user_id in self.conversations:
            del self.conversations[user_id]

class EnhancedLLMService:
    """增强的LLM服务，支持Function Calling和智能对话管理"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_service = AIService()
        self.memory = ConversationMemory()
        self.reservation_service = None  # 延迟初始化
        
        # 定义可用的函数
        self.available_functions = {
            "create_reservation": self._create_reservation,
            "query_reservations": self._query_reservations,
            "cancel_reservation": self._cancel_reservation,
            "modify_reservation": self._modify_reservation,
            "get_available_times": self._get_available_times
        }
        
        # 函数定义（用于Function Calling）
        self.function_definitions = [
            {
                "name": "create_reservation",
                "description": "创建新的预约",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_type": {
                            "type": "string",
                            "description": "服务类型，如：会议室预约、设备预约、场地预约等"
                        },
                        "date": {
                            "type": "string",
                            "description": "预约日期，格式：YYYY-MM-DD"
                        },
                        "time": {
                            "type": "string",
                            "description": "预约时间，格式：HH:MM"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "预约时长（分钟）"
                        },
                        "description": {
                            "type": "string",
                            "description": "预约描述或备注"
                        }
                    },
                    "required": ["service_type", "date", "time", "duration"]
                }
            },
            {
                "name": "query_reservations",
                "description": "查询预约记录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date_from": {
                            "type": "string",
                            "description": "查询开始日期，格式：YYYY-MM-DD"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "查询结束日期，格式：YYYY-MM-DD"
                        },
                        "service_type": {
                            "type": "string",
                            "description": "服务类型筛选"
                        },
                        "status": {
                            "type": "string",
                            "description": "预约状态筛选：active, cancelled, completed"
                        }
                    }
                }
            },
            {
                "name": "cancel_reservation",
                "description": "取消预约",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {
                            "type": "string",
                            "description": "预约ID"
                        },
                        "reason": {
                            "type": "string",
                            "description": "取消原因"
                        }
                    },
                    "required": ["reservation_id"]
                }
            },
            {
                "name": "modify_reservation",
                "description": "修改预约",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {
                            "type": "string",
                            "description": "预约ID"
                        },
                        "new_date": {
                            "type": "string",
                            "description": "新的预约日期，格式：YYYY-MM-DD"
                        },
                        "new_time": {
                            "type": "string",
                            "description": "新的预约时间，格式：HH:MM"
                        },
                        "new_duration": {
                            "type": "integer",
                            "description": "新的预约时长（分钟）"
                        },
                        "new_description": {
                            "type": "string",
                            "description": "新的预约描述"
                        }
                    },
                    "required": ["reservation_id"]
                }
            },
            {
                "name": "get_available_times",
                "description": "获取可用时间段",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "查询日期，格式：YYYY-MM-DD"
                        },
                        "service_type": {
                            "type": "string",
                            "description": "服务类型"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "所需时长（分钟）"
                        }
                    },
                    "required": ["date"]
                }
            }
        ]
    
    def _get_reservation_service(self) -> EnhancedReservationService:
        """获取预约服务实例（延迟初始化）"""
        if self.reservation_service is None:
            db = next(get_db())
            self.reservation_service = EnhancedReservationService(db)
        return self.reservation_service
    
    async def _create_reservation(self, **kwargs) -> Dict[str, Any]:
        """创建预约的函数实现"""
        try:
            service = self._get_reservation_service()
            
            # 构建预约数据
            reservation_data = ReservationCreate(
                service_type=kwargs.get('service_type'),
                date=kwargs.get('date'),
                time=kwargs.get('time'),
                duration=kwargs.get('duration', 60),
                description=kwargs.get('description', '')
            )
            
            # 这里需要用户ID，实际应用中应该从认证上下文获取
            user_id = kwargs.get('user_id', 1)  # 临时使用默认用户ID
            
            result = service.create_reservation(user_id, reservation_data)
            
            return {
                "success": True,
                "message": "预约创建成功",
                "reservation_id": result.id,
                "data": {
                    "id": result.id,
                    "service_type": result.service_type,
                    "date": result.date.isoformat(),
                    "time": result.time.strftime('%H:%M'),
                    "duration": result.duration,
                    "status": get_status_display(result.status)
                }
            }
        except Exception as e:
            logger.error(f"创建预约失败: {e}")
            return {
                "success": False,
                "message": f"创建预约失败: {str(e)}"
            }
    
    async def _query_reservations(self, **kwargs) -> Dict[str, Any]:
        """查询预约的函数实现"""
        try:
            service = self._get_reservation_service()
            
            # 这里需要用户ID，实际应用中应该从认证上下文获取
            user_id = kwargs.get('user_id', 1)
            
            reservations = service.get_user_reservations(user_id)
            
            # 应用筛选条件
            if kwargs.get('date_from'):
                date_from = datetime.fromisoformat(kwargs['date_from']).date()
                reservations = [r for r in reservations if r.date >= date_from]
            
            if kwargs.get('date_to'):
                date_to = datetime.fromisoformat(kwargs['date_to']).date()
                reservations = [r for r in reservations if r.date <= date_to]
            
            if kwargs.get('service_type'):
                reservations = [r for r in reservations if r.service_type == kwargs['service_type']]
            
            if kwargs.get('status'):
                reservations = [r for r in reservations if r.status == kwargs['status']]
            
            return {
                "success": True,
                "message": f"找到 {len(reservations)} 条预约记录",
                "data": [
                    {
                        "id": r.id,
                        "service_type": r.service_type,
                        "date": r.date.isoformat(),
                        "time": r.time.strftime('%H:%M'),
                        "duration": r.duration,
                        "status": get_status_display(r.status),
                        "description": r.description
                    } for r in reservations
                ]
            }
        except Exception as e:
            logger.error(f"查询预约失败: {e}")
            return {
                "success": False,
                "message": f"查询预约失败: {str(e)}"
            }
    
    async def _cancel_reservation(self, **kwargs) -> Dict[str, Any]:
        """取消预约的函数实现"""
        try:
            service = self._get_reservation_service()
            reservation_id = kwargs.get('reservation_id')
            
            if not reservation_id:
                return {
                    "success": False,
                    "message": "缺少预约ID"
                }
            
            result = service.cancel_reservation(int(reservation_id))
            
            if result:
                return {
                    "success": True,
                    "message": "预约已成功取消",
                    "reservation_id": reservation_id
                }
            else:
                return {
                    "success": False,
                    "message": "取消预约失败，可能预约不存在或已被取消"
                }
        except Exception as e:
            logger.error(f"取消预约失败: {e}")
            return {
                "success": False,
                "message": f"取消预约失败: {str(e)}"
            }
    
    async def _modify_reservation(self, **kwargs) -> Dict[str, Any]:
        """修改预约的函数实现"""
        try:
            service = self._get_reservation_service()
            reservation_id = kwargs.get('reservation_id')
            
            if not reservation_id:
                return {
                    "success": False,
                    "message": "缺少预约ID"
                }
            
            # 构建修改数据
            update_data = {}
            if kwargs.get('new_date'):
                update_data['date'] = kwargs['new_date']
            if kwargs.get('new_time'):
                update_data['time'] = kwargs['new_time']
            if kwargs.get('new_duration'):
                update_data['duration'] = kwargs['new_duration']
            if kwargs.get('new_description'):
                update_data['description'] = kwargs['new_description']
            
            result = service.update_reservation(int(reservation_id), update_data)
            
            if result:
                return {
                    "success": True,
                    "message": "预约已成功修改",
                    "reservation_id": reservation_id,
                    "updated_fields": list(update_data.keys())
                }
            else:
                return {
                    "success": False,
                    "message": "修改预约失败，可能预约不存在"
                }
        except Exception as e:
            logger.error(f"修改预约失败: {e}")
            return {
                "success": False,
                "message": f"修改预约失败: {str(e)}"
            }
    
    async def _get_available_times(self, **kwargs) -> Dict[str, Any]:
        """获取可用时间段的函数实现"""
        try:
            # 这里应该实现实际的可用时间查询逻辑
            # 暂时返回模拟数据
            date = kwargs.get('date')
            duration = kwargs.get('duration', 60)
            
            # 模拟可用时间段（实际应该查询数据库）
            available_times = [
                "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"
            ]
            
            return {
                "success": True,
                "message": f"找到 {len(available_times)} 个可用时间段",
                "data": {
                    "date": date,
                    "duration": duration,
                    "available_times": available_times
                }
            }
        except Exception as e:
            logger.error(f"获取可用时间失败: {e}")
            return {
                "success": False,
                "message": f"获取可用时间失败: {str(e)}"
            }
    
    def _build_system_prompt(self, user_id: str) -> str:
        """构建系统提示词"""
        return f"""
你是一个智能预约助手，专门帮助用户管理预约服务。你具有以下能力：

1. **预约管理**：
   - 创建新预约
   - 查询现有预约
   - 取消预约
   - 修改预约时间或详情
   - 查询可用时间段

2. **智能对话**：
   - 理解用户的自然语言请求
   - 提供个性化的服务建议
   - 记住对话上下文，提供连贯的服务

3. **时间处理**：
   - 理解各种时间表达方式（如"明天下午"、"下周三"等）
   - 自动转换为标准格式
   - 处理时区和工作时间限制

**服务规则**：
- 工作时间：周一至周五 9:00-18:00，周六 9:00-12:00
- 预约最少提前1小时，最多提前30天
- 每次预约最短30分钟，最长4小时
- 支持的服务类型：会议室预约、设备预约、场地预约、咨询服务

**对话风格**：
- 友好、专业、高效
- 主动询问必要信息
- 提供清晰的确认和反馈
- 在出现问题时提供替代方案

当用户提出预约相关请求时，请使用提供的函数来执行操作。如果需要更多信息，请主动询问用户。

当前用户ID: {user_id}
当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    async def chat_with_context(self, user_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """带上下文的智能对话"""
        try:
            # 添加用户消息到记忆
            self.memory.add_message(user_id, "user", message)
            
            # 获取对话历史
            history = self.memory.get_conversation_history(user_id, limit=8)
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": self._build_system_prompt(user_id)}
            ]
            
            # 添加历史对话（排除当前消息，因为已经在最后添加）
            for msg in history[:-1]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": message})
            
            # 调用AI服务进行对话（暂时移除函数调用功能）
            # 由于移除了硅基流动服务，暂时降级到基础AI服务
            return await self._fallback_to_ai_service(user_id, message)
                
        except Exception as e:
            logger.error(f"智能对话失败: {e}")
            # 降级到原有AI服务
            return await self._fallback_to_ai_service(user_id, message)
    
    async def _fallback_to_ai_service(self, user_id: str, message: str) -> Dict[str, Any]:
        """降级到原有AI服务"""
        try:
            response = await self.ai_service.generate_response(message)
            
            # 添加到记忆
            self.memory.add_message(user_id, "assistant", response, {"fallback": True})
            
            return {
                "success": True,
                "response": response,
                "conversation_id": user_id,
                "fallback": True
            }
        except Exception as e:
            logger.error(f"降级AI服务也失败: {e}")
            error_response = "抱歉，服务暂时不可用，请稍后再试。"
            return {
                "success": False,
                "response": error_response,
                "conversation_id": user_id
            }
    
    def clear_conversation(self, user_id: str):
        """清除用户对话历史"""
        self.memory.clear_conversation(user_id)
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        history = self.memory.get_conversation_history(user_id)
        return {
            "user_id": user_id,
            "message_count": len(history),
            "last_interaction": history[-1]["timestamp"] if history else None,
            "function_calls": len([msg for msg in history if msg.get("metadata", {}).get("function_called")])
        }