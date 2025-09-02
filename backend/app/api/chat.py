from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from app.models.database import get_db, ChatSession, ChatMessage, User
from app.services.ai_service import AIService
from app.services.intent_service import EnhancedIntentService
from app.services.reservation_service import EnhancedReservationService
from app.services.qwen_service import qwen_service
from app.services.siliconflow_service import siliconflow_service

router = APIRouter()

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: int = 1  # 临时固定用户ID，后续集成认证
    voice_enabled: Optional[bool] = False
    voice_provider: Optional[str] = "qwen"  # qwen, siliconflow, xunfei
    voice_model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    reservation_created: Optional[bool] = False
    audio_url: Optional[str] = None

class ChatHistory(BaseModel):
    id: int
    message: str
    response: str
    intent: Optional[str]
    created_at: datetime

# Initialize enhanced services
ai_service = AIService()
intent_service = EnhancedIntentService()
reservation_service = EnhancedReservationService()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    处理用户聊天消息，识别意图并执行相应操作
    """
    try:
        # 获取或创建会话
        session_id = request.session_id or str(uuid.uuid4())
        
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            chat_session = ChatSession(
                user_id=request.user_id,
                session_id=session_id,
                context={}
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        # 使用增强意图识别服务
        intent_result = intent_service.analyze_intent(request.message, chat_session.context)
        intent = intent_result.get("intent")
        entities = intent_result.get("entities", {})
        confidence = intent_result.get("confidence", 0.0)
        suggestions = intent_result.get("suggestions", [])
        
        # 使用增强预约服务处理所有类型的请求
        result = await reservation_service.process_conversational_request(
            message=request.message,
            intent=intent,
            entities=entities,
            confidence=confidence,
            user_id=request.user_id,
            session_context=chat_session.context,
            db=db
        )
        
        response_text = result["response"]
        suggestions = result.get("suggestions", suggestions)
        reservation_created = result.get("reservation_created", False)
        
        # 更新会话上下文
        if "context_updates" in result:
            chat_session.context.update(result["context_updates"])
        
        # 保存聊天记录
        chat_message = ChatMessage(
            session_id=chat_session.id,
            message=request.message,
            response=response_text,
            intent=intent,
            entities=entities
        )
        db.add(chat_message)
        
        # 更新会话
        chat_session.updated_at = datetime.utcnow()
        db.commit()
        
        # 生成语音（如果启用）
        audio_url = None
        if request.voice_enabled and response_text:
            try:
                if request.voice_provider == "qwen":
                    audio_result = await qwen_service.text_to_speech(response_text)
                    if audio_result and "audio_url" in audio_result:
                        audio_url = audio_result["audio_url"]
                elif request.voice_provider == "siliconflow":
                    audio_result = await siliconflow_service.text_to_speech(response_text)
                    if audio_result and "audio_url" in audio_result:
                        audio_url = audio_result["audio_url"]
                # 科大讯飞语音可以在后续添加
            except Exception as voice_error:
                # 语音生成失败不影响文本响应
                print(f"语音生成失败: {voice_error}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            intent=intent,
            entities=entities,
            suggestions=suggestions,
            reservation_created=reservation_created,
            audio_url=audio_url
        )
        
    except Exception as e:
        print(f"聊天处理错误: {e}")
        # 返回友好的错误响应
        return ChatResponse(
            response="抱歉，系统暂时遇到问题，请稍后再试。如需帮助，请联系管理员。",
            session_id=session_id if 'session_id' in locals() else str(uuid.uuid4()),
            intent="error",
            entities={},
            suggestions=[
                "我想预约会议室",
                "查看我的预约",
                "预约访客来访",
                "预约车位"
            ],
            reservation_created=False
        )

@router.get("/history/{session_id}", response_model=List[ChatHistory])
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    获取指定会话的聊天历史
    """
    try:
        # 查找会话
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 获取聊天记录
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [
            ChatHistory(
                id=msg.id,
                message=msg.message,
                response=msg.response,
                intent=msg.intent,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天历史失败: {str(e)}"
        )

@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """
    删除指定会话及其所有聊天记录
    """
    try:
        # 查找会话
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 删除相关的聊天记录
        db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).delete()
        
        # 删除会话
        db.delete(chat_session)
        db.commit()
        
        return {"message": "会话删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )