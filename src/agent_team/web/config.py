"""
Web 应用配置。

所有配置项通过环境变量读取，有默认值。
敏感信息（SECRET_KEY）在生产环境必须通过 .env 覆盖。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录的 .env
load_dotenv()

# ── 基础路径 ───────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # 项目根目录

# ── 安全 ───────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production!")
ALGORITHM = "HS256"                        # JWT 签名算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60            # Token 过期时间（分钟）

# ── 数据库 ─────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR / 'app.db'}"  # 默认 SQLite
)

# ── 服务 ───────────────────────────────────────
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
