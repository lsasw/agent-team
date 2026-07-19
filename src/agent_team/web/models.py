"""
用户 ORM 模型 — 映射到数据库 users 表。

SQLAlchemy 2.0 Mapped 风格（类型安全）:
- Mapped[int]   → 映射为 INT 列
- Mapped[str]   → 映射为 VARCHAR 列
- mapped_column  → 定义列的详细属性
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"  # 表名

    # id 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # username 唯一索引，不能为空
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # email 唯一索引
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # 哈希后的密码（存储格式: $2b$12$...）
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    # 创建时间（自动填充）
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
