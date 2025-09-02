from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

from app.models.database import get_db, Reservation, Resource, User, ReservationType, ReservationStatus

router = APIRouter()

# Pydantic models
class ReservationCreate(BaseModel):
    type: ReservationType
    resource_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    title: str
    description: Optional[str] = None
    participants: Optional[List[str]] = []
    details: Optional[dict] = {}

class ReservationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[ReservationStatus] = None
    participants: Optional[List[str]] = None
    details: Optional[dict] = None

class ReservationResponse(BaseModel):
    id: int
    type: ReservationType
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    resource_name: Optional[str] = None
    user_name: str
    participants: List[str]
    details: dict
    created_at: datetime
    
    class Config:
        from_attributes = True

class ResourceResponse(BaseModel):
    id: int
    name: str

class PaginatedReservationResponse(BaseModel):
    items: List[ReservationResponse]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True

class ResourceResponse(BaseModel):
    id: int
    name: str
    type: str
    capacity: int
    location: Optional[str]
    description: Optional[str]
    features: dict
    is_available: bool
    
    class Config:
        from_attributes = True

@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationCreate,
    user_id: int = 1,  # 临时固定用户ID
    db: Session = Depends(get_db)
):
    """
    创建新的预约
    """
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证资源存在（如果指定了资源）
    if reservation.resource_id:
        resource = db.query(Resource).filter(Resource.id == reservation.resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        # 检查时间冲突
        conflicting_reservation = db.query(Reservation).filter(
            Reservation.resource_id == reservation.resource_id,
            Reservation.status.in_([ReservationStatus.APPROVED, ReservationStatus.PENDING]),
            Reservation.start_time < reservation.end_time,
            Reservation.end_time > reservation.start_time
        ).first()
        
        if conflicting_reservation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该时间段资源已被预约"
            )
    
    # 创建预约
    db_reservation = Reservation(
        type=reservation.type,
        user_id=user_id,
        resource_id=reservation.resource_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        title=reservation.title,
        description=reservation.description,
        participants=reservation.participants,
        details=reservation.details,
        status=ReservationStatus.PENDING
    )
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    
    # 构造响应
    resource_name = None
    if db_reservation.resource:
        resource_name = db_reservation.resource.name
    
    return ReservationResponse(
        id=db_reservation.id,
        type=db_reservation.type,
        title=db_reservation.title,
        description=db_reservation.description,
        start_time=db_reservation.start_time,
        end_time=db_reservation.end_time,
        status=db_reservation.status,
        resource_name=resource_name,
        user_name=db_reservation.user.full_name,
        participants=db_reservation.participants or [],
        details=db_reservation.details or {},
        created_at=db_reservation.created_at
    )

@router.get("/", response_model=PaginatedReservationResponse)
async def get_reservations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int = 1,  # 临时固定用户ID
    status: Optional[ReservationStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    reservation_type: Optional[ReservationType] = None,
    db: Session = Depends(get_db)
):
    """
    获取预约列表
    """
    query = db.query(Reservation).filter(Reservation.user_id == user_id)
    
    if status:
        query = query.filter(Reservation.status == status)
    
    if start_date:
        query = query.filter(Reservation.start_time >= start_date)
    
    if end_date:
        query = query.filter(Reservation.end_time <= end_date)
    
    if reservation_type:
        query = query.filter(Reservation.type == reservation_type)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * size
    reservations = query.order_by(Reservation.start_time.desc()).offset(offset).limit(size).all()
    
    # 计算总页数
    pages = (total + size - 1) // size

    items = [
        ReservationResponse(
            id=res.id,
            type=res.type,
            title=res.title,
            description=res.description,
            start_time=res.start_time,
            end_time=res.end_time,
            status=res.status,
            resource_name=res.resource.name if res.resource else None,
            user_name=res.user.full_name,
            participants=res.participants or [],
            details=res.details or {},
            created_at=res.created_at
        )
        for res in reservations
    ]
    
    return PaginatedReservationResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    user_id: int = 1,  # 临时固定用户ID
    db: Session = Depends(get_db)
):
    """
    获取单个预约详情
    """
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )
    
    return ReservationResponse(
        id=reservation.id,
        type=reservation.type,
        title=reservation.title,
        description=reservation.description,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        resource_name=reservation.resource.name if reservation.resource else None,
        user_name=reservation.user.full_name,
        participants=reservation.participants or [],
        details=reservation.details or {},
        created_at=reservation.created_at
    )

@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    user_id: int = 1,  # 临时固定用户ID
    db: Session = Depends(get_db)
):
    """
    更新预约
    """
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )
    
    # 更新字段
    update_data = reservation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)
    
    reservation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reservation)
    
    return ReservationResponse(
        id=reservation.id,
        type=reservation.type,
        title=reservation.title,
        description=reservation.description,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        resource_name=reservation.resource.name if reservation.resource else None,
        user_name=reservation.user.full_name,
        participants=reservation.participants or [],
        details=reservation.details or {},
        created_at=reservation.created_at
    )

@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    user_id: int = 1,  # 临时固定用户ID
    db: Session = Depends(get_db)
):
    """
    取消预约
    """
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )
    
    reservation.status = ReservationStatus.CANCELLED
    reservation.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "预约已取消"}

@router.get("/resources/", response_model=List[ResourceResponse])
async def get_resources(
    resource_type: Optional[str] = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    获取可用资源列表
    """
    query = db.query(Resource)
    
    if resource_type:
        query = query.filter(Resource.type == resource_type)
    
    if available_only:
        query = query.filter(Resource.is_available == True)
    
    resources = query.all()
    
    return [
        ResourceResponse(
            id=res.id,
            name=res.name,
            type=res.type.value,
            capacity=res.capacity,
            location=res.location,
            description=res.description,
            features=res.features or {},
            is_available=res.is_available
        )
        for res in resources
    ]