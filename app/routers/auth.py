"""认证路由（注册、登录）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token
from app.constants import UserType
from app.schemas import ApiResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    """注册请求"""

    email: EmailStr
    password: str
    user_type: str  # 'candidate' or 'admin'


class LoginRequest(BaseModel):
    """登录请求"""

    email: EmailStr
    password: str


@router.post("/register")
async def register(
    request: RegisterRequest, db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """用户注册"""
    # 验证 user_type
    if request.user_type not in [UserType.CANDIDATE.value, UserType.ADMIN.value]:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 创建新用户
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        user_type=request.user_type,
        status="active",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return ApiResponse(
        code=0,
        message="success",
        data={
            "user_id": new_user.id,
            "email": new_user.email,
            "user_type": new_user.user_type,
        },
    )


@router.post("/login")
async def login(
    request: LoginRequest, db: Session = Depends(get_db)
) -> ApiResponse[TokenResponse]:
    """用户登录"""
    # 查询用户
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User account is inactive")

    # 创建 token
    access_token_expires = timedelta(
        minutes=1440  # 24小时
    )
    access_token = create_access_token(
        data={"user_id": user.id, "user_type": user.user_type},
        expires_delta=access_token_expires,
    )

    return ApiResponse(
        code=0,
        message="success",
        data=TokenResponse(
            access_token=access_token,
            user_id=user.id,
            user_type=user.user_type,
        ),
    )
