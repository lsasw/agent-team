"""
认证模块 — 密码哈希 + JWT token 签发/验证。

完整流程:
  [注册] 用户密码 → bcrypt.hash → 存入 DB
  [登录] 用户密码 → bcrypt.verify → 匹配则签发 JWT
  [请求] JWT (cookie) → 解码验证 → 提取 user_id
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .database import get_db
from .models import User
from .schemas import TokenResponse

# ── 密码哈希 ──────────────────────────────────────
# bcrypt 是 Blowfish 密码哈希算法，自动加盐，不可逆


def hash_password(password: str) -> str:
    """明文密码 → bcrypt 哈希（数据库只存这个）"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配数据库中的哈希"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT ───────────────────────────────────────────

def create_access_token(user_id: int, username: str) -> str:
    """
    签发 JWT token。

    payload:
      sub: user_id（主题，一般为用户 ID）
      username: 用户名
      exp: 过期时间
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """解码 JWT token，验证签名和过期时间。无效返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── 依赖注入：获取当前用户 ────────────────────────
from fastapi import Request as FastAPIRequest


async def get_current_user(
    request: FastAPIRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """
    从 Cookie 的 JWT token 获取当前登录用户。

    用于路由函数中:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/auth/login")

    返回 None 表示未登录（而非直接报错），让视图灵活处理。
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


def require_user(user: User | None) -> User:
    """要求用户必须登录，否则抛出 401。用于依赖注入链"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
