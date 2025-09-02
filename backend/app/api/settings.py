from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..models.database import get_db
from ..services.settings_service import SettingsService
from ..services.auth_service import AuthService
from ..api.auth import get_current_user

router = APIRouter()

# 创建服务实例
settings_service = SettingsService()
auth_service = AuthService()

# Pydantic 模型
class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class SettingsImport(BaseModel):
    settings_data: Dict[str, Any]

class SettingsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("/", response_model=Dict[str, Any])
async def get_all_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有系统设置"""
    try:
        # 检查用户权限（只有管理员可以查看系统设置）
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看系统设置"
            )
        
        settings = settings_service.get_all_settings(db)
        return {
            "success": True,
            "message": "获取设置成功",
            "data": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设置失败: {str(e)}"
        )

@router.get("/category/{category}", response_model=Dict[str, Any])
async def get_category_settings(
    category: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定类别的设置"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看系统设置"
            )
        
        settings = settings_service.get_category_settings(db, category)
        return {
            "success": True,
            "message": f"获取{category}设置成功",
            "data": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设置失败: {str(e)}"
        )

@router.get("/value/{category}/{key}")
async def get_setting_value(
    category: str,
    key: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个设置值"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看系统设置"
            )
        
        value = settings_service.get_setting(db, category, key)
        return {
            "success": True,
            "message": "获取设置值成功",
            "data": {
                "category": category,
                "key": key,
                "value": value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设置值失败: {str(e)}"
        )

@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新系统设置"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以修改系统设置"
            )
        
        # 验证设置数据
        validation_errors = settings_service.validate_settings(settings_update.settings)
        if validation_errors:
            return SettingsResponse(
                success=False,
                message="设置验证失败",
                data={"errors": validation_errors}
            )
        
        # 更新设置
        success = settings_service.update_settings(db, settings_update.settings)
        
        if success:
            return SettingsResponse(
                success=True,
                message="设置更新成功"
            )
        else:
            return SettingsResponse(
                success=False,
                message="设置更新失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新设置失败: {str(e)}"
        )

@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """重置设置到默认值"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以重置系统设置"
            )
        
        success = settings_service.reset_settings(db, category)
        
        if success:
            message = f"重置{category}设置成功" if category else "重置所有设置成功"
            return SettingsResponse(
                success=True,
                message=message
            )
        else:
            return SettingsResponse(
                success=False,
                message="重置设置失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置设置失败: {str(e)}"
        )

@router.get("/system-info", response_model=Dict[str, Any])
async def get_system_info(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取系统信息"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看系统信息"
            )
        
        system_info = settings_service.get_system_info(db)
        return {
            "success": True,
            "message": "获取系统信息成功",
            "data": system_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统信息失败: {str(e)}"
        )

@router.get("/export", response_model=Dict[str, Any])
async def export_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导出系统设置"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以导出系统设置"
            )
        
        exported_data = settings_service.export_settings(db)
        return {
            "success": True,
            "message": "导出设置成功",
            "data": exported_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出设置失败: {str(e)}"
        )

@router.post("/import", response_model=SettingsResponse)
async def import_settings(
    settings_import: SettingsImport,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导入系统设置"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以导入系统设置"
            )
        
        success = settings_service.import_settings(db, settings_import.settings_data)
        
        if success:
            return SettingsResponse(
                success=True,
                message="导入设置成功"
            )
        else:
            return SettingsResponse(
                success=False,
                message="导入设置失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入设置失败: {str(e)}"
        )

@router.post("/validate", response_model=Dict[str, Any])
async def validate_settings(
    settings_update: SettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """验证设置数据"""
    try:
        # 检查用户权限
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以验证系统设置"
            )
        
        validation_errors = settings_service.validate_settings(settings_update.settings)
        
        return {
            "success": len(validation_errors) == 0,
            "message": "验证完成" if len(validation_errors) == 0 else "验证失败",
            "data": {
                "valid": len(validation_errors) == 0,
                "errors": validation_errors
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证设置失败: {str(e)}"
        )

# 公共设置接口（不需要管理员权限）
@router.get("/public/general", response_model=Dict[str, Any])
async def get_public_settings(
    db: Session = Depends(get_db)
):
    """获取公共设置（不需要认证）"""
    try:
        general_settings = settings_service.get_category_settings(db, "general")
        
        # 只返回公共可见的设置
        public_settings = {
            "system_name": general_settings.get("system_name", "智能预约系统"),
            "system_description": general_settings.get("system_description", "基于AI的智能预约管理系统"),
            "default_language": general_settings.get("default_language", "zh-CN"),
            "theme_mode": general_settings.get("theme_mode", "light")
        }
        
        return {
            "success": True,
            "message": "获取公共设置成功",
            "data": public_settings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公共设置失败: {str(e)}"
        )