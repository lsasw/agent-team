"""
数据库引擎 + 会话管理。

使用 SQLAlchemy 2.0 异步模式：
- create_async_engine: 创建异步引擎
- async_sessionmaker: 生成异步会话工厂
- get_db: FastAPI 依赖注入，自动管理会话生命周期
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from .config import DATABASE_URL

# ── 引擎 ────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 改成 True 可以看到 SQL 日志
)

# ── 会话工厂 ────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不使对象过期
)


# ── 声明式基类 ──────────────────────────────────
class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


# ── FastAPI 依赖注入 ────────────────────────────
async def get_db() -> AsyncSession:
    """
    每个请求自动创建并管理一个数据库会话。

    用法（在 FastAPI 路由中）:
        @router.get("/")
        async def index(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()    # 正常结束 → 提交
        except Exception:
            await session.rollback()  # 异常 → 回滚
            raise
        # with 退出时自动 close()


# ── 初始化 ──────────────────────────────────────
async def init_db():
    """在应用启动时创建所有表（开发用，生产用 Alembic 迁移）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
