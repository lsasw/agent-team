"""
FastAPI 应用入口。

启动:
  uv run uvicorn agent_team.web.main:app --reload

或者:
  python -m agent_team.web.main
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from .config import HOST, PORT
from .database import get_db, init_db
from .auth import get_current_user
from .routers.auth import router as auth_router


# ── 生命周期 ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的操作"""
    await init_db()  # 启动时自动建表（开发用）
    print("✅ 数据库表已就绪")
    yield


# ── 创建应用 ──────────────────────────────────────
app = FastAPI(
    title="Agent Team Web",
    description="多智能体协作平台 — 用户登录注册 Demo",
    version="0.1.0",
    lifespan=lifespan,
)

# ── 静态文件（绝对路径）───────────────────────────
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# ── 注册路由 ──────────────────────────────────────
app.include_router(auth_router)

# ── 模板引擎 ──────────────────────────────────────
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


# ═══════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════

@app.get("/")
async def root():
    """根路径 → 重定向到仪表盘"""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
async def dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user=Depends(get_current_user),
):
    """
    仪表盘 — 需要登录。

    通过 get_current_user 依赖注入获取当前用户：
    - 登录 → 显示用户信息
    - 未登录 → 重定向到登录页
    """
    if not user:
        return RedirectResponse(url="/auth/login")

    return templates.TemplateResponse(
        request, "dashboard.html",
        {"request": request, "user": user},
    )


@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "ok", "service": "agent-team-web"}


# ═══════════════════════════════════════════════════
# 直接运行
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
