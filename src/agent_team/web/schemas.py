"""
Pydantic Schema — 请求/响应数据验证。

三层职责分离:
- UserCreate:   注册表单 → 校验用户输入
- UserLogin:    登录表单 → 校验凭据
- UserResponse: 返回给前端的用户数据（不含密码！）
"""

from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """注册请求体"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="用户名（3-50 字符，仅字母数字下划线）",
    )
    email: str = Field(
        ...,
        max_length=100,
        description="邮箱地址",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码（最少 6 位）",
    )


class UserLogin(BaseModel):
    """登录请求体"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """返回给前端的用户信息（注意：没有密码！）"""
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}  # 支持从 ORM 对象直接转换


class TokenResponse(BaseModel):
    """JWT token 响应"""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    detail: str | None = None
