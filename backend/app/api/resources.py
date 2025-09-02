from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.database import (
    get_db, User, Resource, ResourceType
)
from app.api.auth import get_current_user

router = APIRouter()

# Pydantic模型
class ResourceCreate(BaseModel):
    name: str
    type: ResourceType
    description: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ResourceType] = None
    description: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None

class ResourceResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str]
    location: Optional[str]
    capacity: Optional[int]
    is_available: bool
    is_active: bool  # 添加is_active字段
    created_at: datetime
    features: Optional[dict] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            type=obj.type.value if hasattr(obj.type, 'value') else str(obj.type),
            description=obj.description,
            location=obj.location,
            capacity=obj.capacity,
            is_available=obj.is_available,
            is_active=obj.is_available,  # 使用is_available作为is_active的值
            created_at=obj.created_at,
            features=obj.features if hasattr(obj, 'features') else None
        )

# API端点
@router.post("/", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新资源（仅管理员）"""
    # 检查权限
    if current_user.role.value not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create resources"
        )
    
    # 检查资源名称是否已存在
    existing_resource = db.query(Resource).filter(Resource.name == resource_data.name).first()
    if existing_resource:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource with this name already exists"
        )
    
    # 创建资源
    db_resource = Resource(
        name=resource_data.name,
        type=resource_data.type,
        description=resource_data.description,
        location=resource_data.location,
        capacity=resource_data.capacity,
        is_available=True
    )
    
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    
    return db_resource

@router.get("/", response_model=List[ResourceResponse])
async def get_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource_type: Optional[ResourceType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取资源列表"""
    try:
        query = db.query(Resource)
        
        # 应用过滤条件
        if resource_type:
            query = query.filter(Resource.type == resource_type)
        
        if is_active is not None:
            query = query.filter(Resource.is_available == is_active)
        
        if search:
            query = query.filter(
                Resource.name.contains(search) | 
                Resource.description.contains(search) |
                Resource.location.contains(search)
            )
        
        resources = query.order_by(Resource.name).offset(skip).limit(limit).all()
        
        # 手动转换为响应模型
        result = []
        for resource in resources:
            result.append(ResourceResponse(
                id=resource.id,
                name=resource.name,
                type=resource.type.value if hasattr(resource.type, 'value') else str(resource.type),
                description=resource.description,
                location=resource.location,
                capacity=resource.capacity,
                is_available=resource.is_available,
                is_active=resource.is_available,  # 添加is_active字段
                created_at=resource.created_at,
                features=resource.features if hasattr(resource, 'features') else None
            ))
        
        return result
    except Exception as e:
        print(f"Error in get_resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resources: {str(e)}"
        )

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """获取特定资源详情"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    return resource

@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_update: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新资源（仅管理员）"""
    # 检查权限
    if current_user.role.value not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update resources"
        )
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # 检查名称冲突（如果更新名称）
    if resource_update.name and resource_update.name != resource.name:
        existing_resource = db.query(Resource).filter(
            Resource.name == resource_update.name,
            Resource.id != resource_id
        ).first()
        if existing_resource:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource with this name already exists"
            )
    
    # 应用更新
    update_data = resource_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    
    return resource

@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除资源（仅管理员）"""
    # 检查权限
    if current_user.role.value not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete resources"
        )
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # 软删除：设置为不活跃而不是物理删除
    resource.is_active = False
    db.commit()
    
    return {"message": "Resource deactivated successfully"}