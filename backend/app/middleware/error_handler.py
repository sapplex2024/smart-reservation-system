from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
import traceback
import time
from typing import Callable
from ..services.logger_service import logger_service
from ..api.auth import get_current_user_optional

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        start_time = time.time()
        
        try:
            # 获取当前用户（如果有的话）
            user_id = None
            try:
                user = await get_current_user_optional(request)
                if user:
                    user_id = user.id
            except:
                pass
            
            # 执行请求
            response = await call_next(request)
            
            # 记录访问日志
            duration_ms = (time.time() - start_time) * 1000
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent")
            
            logger_service.log_access(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            # 记录API调用日志
            if request.url.path.startswith("/api/"):
                logger_service.log_api(
                    endpoint=str(request.url.path),
                    method=request.method,
                    user_id=user_id,
                    duration_ms=duration_ms
                )
            
            return response
            
        except Exception as exc:
            return await self._handle_exception(request, exc, user_id, start_time)
    
    async def _handle_exception(self, request: Request, exc: Exception, user_id: int = None, start_time: float = None) -> JSONResponse:
        """统一异常处理"""
        client_ip = self._get_client_ip(request)
        duration_ms = (time.time() - start_time) * 1000 if start_time else 0
        
        # HTTP异常
        if isinstance(exc, HTTPException):
            logger_service.log_warning(
                f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}",
                category="http_error",
                user_id=user_id,
                extra_data={
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "method": request.method,
                    "path": str(request.url.path),
                    "ip_address": client_ip,
                    "duration_ms": duration_ms
                }
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": time.time()
                }
            )
        
        # Starlette HTTP异常
        elif isinstance(exc, StarletteHTTPException):
            logger_service.log_warning(
                f"Starlette HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}",
                category="http_error",
                user_id=user_id,
                extra_data={
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "method": request.method,
                    "path": str(request.url.path),
                    "ip_address": client_ip,
                    "duration_ms": duration_ms
                }
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": time.time()
                }
            )
        
        # 请求验证异常
        elif isinstance(exc, RequestValidationError):
            error_details = []
            for error in exc.errors():
                error_details.append({
                    "field": " -> ".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            logger_service.log_warning(
                f"Validation Error: {request.method} {request.url.path}",
                category="validation_error",
                user_id=user_id,
                extra_data={
                    "errors": error_details,
                    "method": request.method,
                    "path": str(request.url.path),
                    "ip_address": client_ip,
                    "duration_ms": duration_ms
                }
            )
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": True,
                    "message": "请求参数验证失败",
                    "details": error_details,
                    "status_code": 422,
                    "timestamp": time.time()
                }
            )
        
        # 数据库异常
        elif isinstance(exc, SQLAlchemyError):
            logger_service.log_error(
                f"Database Error: {str(exc)} - {request.method} {request.url.path}",
                category="database_error",
                user_id=user_id,
                extra_data={
                    "error_type": type(exc).__name__,
                    "method": request.method,
                    "path": str(request.url.path),
                    "ip_address": client_ip,
                    "duration_ms": duration_ms,
                    "traceback": traceback.format_exc()
                },
                exception=exc
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "数据库操作失败",
                    "status_code": 500,
                    "timestamp": time.time()
                }
            )
        
        # 其他未知异常
        else:
            logger_service.log_error(
                f"Unhandled Exception: {str(exc)} - {request.method} {request.url.path}",
                category="system_error",
                user_id=user_id,
                extra_data={
                    "error_type": type(exc).__name__,
                    "method": request.method,
                    "path": str(request.url.path),
                    "ip_address": client_ip,
                    "duration_ms": duration_ms,
                    "traceback": traceback.format_exc()
                },
                exception=exc
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "服务器内部错误",
                    "status_code": 500,
                    "timestamp": time.time()
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"

# 全局异常处理器
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "请求参数验证失败",
            "details": error_details,
            "status_code": 422,
            "timestamp": time.time()
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger_service.log_error(
        f"Unhandled Exception: {str(exc)}",
        category="system_error",
        extra_data={
            "error_type": type(exc).__name__,
            "method": request.method,
            "path": str(request.url.path),
            "traceback": traceback.format_exc()
        },
        exception=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误",
            "status_code": 500,
            "timestamp": time.time()
        }
    )