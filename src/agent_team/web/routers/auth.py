"""
认证路由 — 注册 + 登录 + 登出。

路由设计（RESTful + Server-Side Rendering）:
  GET  /auth/register  → 注册页面
  POST /auth/register  → 处理注册表单
  GET  /auth/login     → 登录页面
  POST /auth/login     → 处理登录表单
  GET  /auth/logout    → 清除 cookie 并跳转
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, UserResponse
from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_user,
)

router = APIRouter(prefix="/auth", tags=["认证"])

# 模板引擎 — 使用绝对路径
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


# ═══════════════════════════════════════════════════════
# 注册
# ═══════════════════════════════════════════════════════

@router.get("/register")
async def register_page(request: Request):
    """渲染注册页面"""
    return templates.TemplateResponse(request, "register.html")


@router.post("/register")
async def register(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """处理注册表单提交"""
    # ① 校验输入
    errors = []
    if len(username) < 3 or len(username) > 50:
        errors.append("用户名需 3-50 个字符")
    if len(password) < 6:
        errors.append("密码至少 6 位")

    # ② 检查用户名/邮箱是否已存在
    existing_user = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if existing_user.scalar_one_or_none():
        errors.append("用户名或邮箱已被注册")

    if errors:
        return templates.TemplateResponse(
            request, "register.html",
            {"request": request, "errors": errors, "username": username, "email": email},
            status_code=400,
        )

    # ③ 创建用户
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),  # 只存哈希，不存明文
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # ④ 签发 JWT 并设置 Cookie → 跳转仪表盘
    token = create_access_token(user.id, user.username)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,      # JS 无法读取，防 XSS
        max_age=3600,        # 1 小时
        samesite="lax",     # 防 CSRF
    )
    return response


# ═══════════════════════════════════════════════════════
# 登录
# ═══════════════════════════════════════════════════════

@router.get("/login")
async def login_page(request: Request):
    """渲染登录页面"""
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = Form(...),
    password: str = Form(...),
):
    """处理登录表单提交"""
    # ① 查用户
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    # ② 验证密码
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request, "login.html",
            {"request": request, "error": "用户名或密码错误"},
            status_code=401,
        )

    # ③ 签发 JWT → 设置 Cookie
    token = create_access_token(user.id, user.username)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
    )
    return response


# ═══════════════════════════════════════════════════════
# 登出
# ═══════════════════════════════════════════════════════

@router.get("/logout")
async def logout():
    """清除 Cookie → 跳转登录页"""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
