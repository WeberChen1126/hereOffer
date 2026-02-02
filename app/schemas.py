"""通用响应模型"""
from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, EmailStr, field_validator
import uuid

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """API 统一响应格式"""

    code: int = 0  # 0 表示成功
    message: str = "success"
    data: Optional[T] = None
    request_id: str = ""

    def __init__(self, **data):
        if "request_id" not in data:
            data["request_id"] = str(uuid.uuid4())
        super().__init__(**data)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class TokenResponse(BaseModel):
    """登录响应"""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_type: str


class UserCreate(BaseModel):
    """用户注册请求"""

    email: EmailStr
    password: str
    user_type: str

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v):
        if v not in ["candidate", "admin"]:
            raise ValueError("user_type must be 'candidate' or 'admin'")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """用户登录请求"""

    email: EmailStr
    password: str


# 错误响应对应的状态码
ERROR_CODE_MAP = {
    "AUTH_401": (401, "Unauthorized"),
    "PERM_403": (403, "Forbidden"),
    "SCHEMA_422": (422, "Validation Error"),
    "STATE_409": (409, "Conflict"),
    "LLM_502": (502, "LLM Service Error"),
    "TASK_500": (500, "Task Error"),
    "NOT_FOUND_404": (404, "Not Found"),
    "BAD_REQUEST_400": (400, "Bad Request"),
}
