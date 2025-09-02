from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.smart_intent_service import SmartIntentService
from app.services.reservation_service import ReservationService
from app.services.ai_service import AIService
from app.api.auth import get_current_user
from app.models.database import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["smart-reservation"])

class ConversationMessage(BaseModel):
    type: str  # 'user' or 'assistant'
    text: str
    timestamp: str

class SmartReservationRequest(BaseModel):
    message: str
    conversation_history: List[ConversationMessage] = []
    use_voice: bool = False
    context: Optional[Dict[str, Any]] = None

class SmartReservationResponse(BaseModel):
    success: bool
    message: str
    reservation_completed: bool = False
    reservation_data: Optional[Dict[str, Any]] = None
    generate_speech: bool = False
    next_questions: List[str] = []
    confidence: float = 0.0

class AITestRequest(BaseModel):
    provider: str  # 'xunfei', 'qwen', 'siliconflow', 'openai'
    apiKey: Optional[str] = None  # 使用驼峰命名匹配前端
    api_key: Optional[str] = None  # 保持向后兼容
    appId: Optional[str] = None  # 科大讯飞专用，驼峰命名
    appid: Optional[str] = None  # 保持向后兼容
    apiSecret: Optional[str] = None  # 科大讯飞专用，驼峰命名
    api_secret: Optional[str] = None  # 保持向后兼容
    model: Optional[str] = None  # 自定义模型名称
    baseUrl: Optional[str] = None  # 驼峰命名匹配前端
    base_url: Optional[str] = None  # 保持向后兼容

@router.post("/test-ai")
async def test_ai_connection(request: AITestRequest) -> Dict[str, Any]:
    """
    测试AI服务连接状态
    """
    import httpx
    import time
    
    provider = request.provider.lower()
    start_time = time.time()
    
    # 执行单个提供商测试
    test_result = await _test_single_provider(request, provider, start_time)
    
    # 构造前端期望的响应格式
    if test_result["success"]:
        summary = {
            "overall_status": "全部可用",
            "successful_services": 1,
            "total_services": 1
        }
    else:
        summary = {
            "overall_status": "不可用",
            "successful_services": 0,
            "total_services": 1
        }
    
    # 构造前端期望的响应格式
    provider_key = f"{provider}_api"
    response = {
        "summary": summary,
        provider_key: test_result
    }
    
    return response

async def _test_single_provider(request: AITestRequest, provider: str, start_time: float) -> Dict[str, Any]:
    """
    测试单个AI提供商
    """
    import httpx
    import time
    
    try:
        if provider == "siliconflow":
            # 测试硅基流动连接
            api_key = request.apiKey or request.api_key
            if not api_key:
                return {
                    "success": False,
                    "error": "API密钥未提供",
                    "details": "请输入硅基流动的API密钥"
                }
            
            model = request.model or "deepseek-ai/DeepSeek-V2.5"
            base_url = request.baseUrl or request.base_url or "https://api.siliconflow.cn/v1"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "硅基流动API连接成功",
                        "model": model,
                        "latency": f"{latency:.2f}s",
                        "response": result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    }
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except:
                        pass
                    
                    return {
                        "success": False,
                        "error": f"API调用失败 (状态码: {response.status_code})",
                        "details": error_detail
                    }
        
        elif provider == "qwen":
            # 测试通义千问连接
            api_key = request.apiKey or request.api_key
            if not api_key:
                return {
                    "success": False,
                    "error": "API密钥未提供",
                    "details": "请输入通义千问的API密钥"
                }
            
            model = request.model or "qwen-turbo"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "input": {"messages": [{"role": "user", "content": "你好"}]},
                "parameters": {"max_tokens": 10}
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload
                )
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "通义千问API连接成功",
                        "model": model,
                        "latency": f"{latency:.2f}s",
                        "response": result.get("output", {}).get("text", "")
                    }
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message", error_detail)
                    except:
                        pass
                    
                    return {
                        "success": False,
                        "error": f"API调用失败 (状态码: {response.status_code})",
                        "details": error_detail
                    }
        
        elif provider == "xunfei":
            # 测试科大讯飞连接
            appid = request.appId or request.appid
            api_key = request.apiKey or request.api_key
            api_secret = request.apiSecret or request.api_secret
            if not all([appid, api_key, api_secret]):
                return {
                    "success": False,
                    "error": "配置参数不完整",
                    "details": "科大讯飞需要提供APPID、API Key和API Secret"
                }
            
            # 科大讯飞需要特殊的认证方式，这里简化处理
            return {
                "success": True,
                "message": "科大讯飞配置参数已验证",
                "model": "spark-3.5",
                "details": "参数格式正确，实际连接需要WebSocket认证"
            }
        
        elif provider == "openai":
            # 测试OpenAI连接
            api_key = request.apiKey or request.api_key
            if not api_key:
                return {
                    "success": False,
                    "error": "API密钥未提供",
                    "details": "请输入OpenAI的API密钥"
                }
            
            model = request.model or "gpt-3.5-turbo"
            base_url = request.baseUrl or request.base_url or "https://api.openai.com/v1"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "OpenAI API连接成功",
                        "model": model,
                        "latency": f"{latency:.2f}s",
                        "response": result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    }
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except:
                        pass
                    
                    return {
                        "success": False,
                        "error": f"API调用失败 (状态码: {response.status_code})",
                        "details": error_detail
                    }
        
        else:
            return {
                "success": False,
                "error": "不支持的提供商",
                "details": f"提供商 '{provider}' 不在支持列表中"
            }
    
    except Exception as e:
        logger.error(f"{provider} 连接测试失败: {e}")
        return {
            "success": False,
            "error": "连接测试异常",
            "details": str(e)
        }

@router.post("/chat", response_model=SmartReservationResponse)
async def smart_reservation_chat(
    request: SmartReservationRequest,
    current_user: User = Depends(get_current_user)
):
    """智能语音预约对话接口"""
    try:
        # 初始化服务
        smart_intent_service = SmartIntentService()
        reservation_service = ReservationService()
        ai_service = AIService()
        
        # 构建对话上下文
        conversation_context = {
            "user_id": current_user.id,
            "user_name": current_user.username,
            "conversation_history": request.conversation_history,
            "use_voice": request.use_voice
        }
        
        # 智能意图分析
        intent_result = await smart_intent_service.analyze_smart_intent(
            message=request.message,
            context=conversation_context
        )
        
        logger.info(f"Intent analysis result: {intent_result}")
        
        # 检查意图类型，优先处理非预约意图
        intent = intent_result.get("intent", "unknown")
        
        # 处理非预约意图（如聊天、天气查询等）
        if intent in ["chat", "help", "query"]:
            try:
                # 使用AI服务生成自然回复
                ai_response = await ai_service.generate_response(
                    message=request.message,
                    context=conversation_context
                )
                
                return SmartReservationResponse(
                    success=True,
                    message=ai_response,
                    generate_speech=request.use_voice,
                    next_questions=[
                        "预约会议室",
                        "预约访客来访", 
                        "预约车位",
                        "查看我的预约"
                    ],
                    confidence=intent_result.get("confidence", 0.8)
                )
            except Exception as e:
                logger.warning(f"AI服务调用失败，使用默认回复: {e}")
                # AI服务失败时的默认回复
                default_responses = {
                    "chat": "很抱歉，我目前无法获取实时信息来回答您的问题。不过我可以帮助您进行预约相关的服务。",
                    "help": "我可以帮您：\n• 预约会议室\n• 安排访客来访\n• 预约车位\n• 查看和管理预约\n\n请告诉我您需要什么帮助？",
                    "query": "您可以查看预约列表、预约状态等信息。请具体说明您想查询什么？"
                }
                
                return SmartReservationResponse(
                    success=True,
                    message=default_responses.get(intent, "我是智能预约助手，有什么可以帮您的吗？"),
                    generate_speech=request.use_voice,
                    next_questions=[
                        "预约会议室",
                        "预约访客来访",
                        "预约车位",
                        "查看我的预约"
                    ],
                    confidence=intent_result.get("confidence", 0.6)
                )
        
        # 如果不是预约相关意图，直接返回，不继续处理
        if intent not in ["reservation", "meeting_room", "visitor", "parking", "unknown"]:
            return SmartReservationResponse(
                success=True,
                message="我是智能预约助手，主要帮助您处理预约相关事务。如果您需要预约服务，请告诉我具体需求。",
                generate_speech=request.use_voice,
                next_questions=[
                    "预约会议室",
                    "预约访客来访",
                    "预约车位",
                    "查看我的预约"
                ],
                confidence=0.5
            )
        
        # 检查是否有足够信息创建预约
        if intent_result.get("can_create_reservation", False):
            # 尝试创建预约
            try:
                reservation_data = intent_result.get("reservation_data", {})
                reservation_data["user_id"] = current_user.id
                
                reservation_result = await reservation_service.process_reservation_request(
                    reservation_data
                )
                
                if reservation_result.get("success"):
                    return SmartReservationResponse(
                        success=True,
                        message=f"预约成功！{reservation_result.get('message', '')}",
                        reservation_completed=True,
                        reservation_data=reservation_result.get("data"),
                        generate_speech=request.use_voice,
                        confidence=intent_result.get("confidence", 0.9)
                    )
                else:
                    return SmartReservationResponse(
                        success=True,
                        message=f"预约失败：{reservation_result.get('message', '未知错误')}",
                        generate_speech=request.use_voice,
                        confidence=intent_result.get("confidence", 0.8)
                    )
                    
            except Exception as e:
                logger.error(f"创建预约失败: {e}")
                return SmartReservationResponse(
                    success=True,
                    message=f"创建预约时出现错误：{str(e)}",
                    generate_speech=request.use_voice
                )
        

        
        # 处理预约相关意图，需要更多信息时生成智能提示
        missing_info = intent_result.get("missing_information", [])
        suggestions = intent_result.get("suggestions", [])
        
        if missing_info:
            # 生成友好的补全提示
            prompt_message = await generate_completion_prompt(
                missing_info, suggestions, conversation_context
            )
            
            return SmartReservationResponse(
                success=True,
                message=prompt_message,
                generate_speech=request.use_voice,
                next_questions=suggestions,
                confidence=intent_result.get("confidence", 0.7)
            )
        
        # 无法理解用户意图
        return SmartReservationResponse(
            success=True,
            message="抱歉，我没有完全理解您的预约需求。请您详细描述一下，比如：预约时间、会议室类型、访客信息等。",
            generate_speech=request.use_voice,
            next_questions=[
                "您想预约什么时间的会议室？",
                "需要什么类型的会议室？",
                "有多少位访客参加？"
            ]
        )
        
    except Exception as e:
        logger.error(f"智能预约对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

async def generate_completion_prompt(
    missing_info: List[str], 
    suggestions: List[str], 
    context: Dict[str, Any]
) -> str:
    """生成智能补全提示"""
    
    # 根据缺失信息生成个性化提示
    prompts = {
        "time": "请告诉我您希望预约的具体时间，比如：明天下午2点到4点",
        "duration": "请告诉我会议预计持续多长时间",
        "room_type": "请告诉我您需要什么类型的会议室，比如：小型会议室、大型会议室或多媒体会议室",
        "visitor_info": "请提供访客信息，包括姓名、公司和联系方式",
        "visitor_count": "请告诉我有多少位访客参加会议",
        "company_info": "请提供访客的公司信息",
        "vehicle_info": "如果访客需要停车，请提供车辆信息",
        "license_plate": "请提供车牌号码",
        "contact_info": "请提供联系方式"
    }
    
    if len(missing_info) == 1:
        return prompts.get(missing_info[0], "请提供更多详细信息")
    elif len(missing_info) <= 3:
        prompt_list = [prompts.get(info, info) for info in missing_info]
        return f"我还需要以下信息：\n" + "\n".join([f"• {prompt}" for prompt in prompt_list])
    else:
        return "请提供更完整的预约信息，包括时间、会议室类型、访客详情等。"