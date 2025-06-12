"""
FastAPI 应用的主入口文件
主要职责：
1. 创建 FastAPI 应用实例
2. 配置中间件（如 CORS）
3. 注册路由
4. 提供健康检查接口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base

# 创建 FastAPI 应用实例
# title: API 文档的标题
# description: API 文档的描述
# version: API 版本
app = FastAPI(
    title="Anki API",
    description="Anki 复习助手 API",
    version="1.0.0",
)

# 配置 CORS (跨源资源共享)
# 这允许前端应用从不同的域名访问我们的 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
# prefix: API 路由前缀，所有卡片相关的接口都会加上这个前缀
# tags: 用于 API 文档的分类标签
app.include_router(api_router, prefix="/api/v1")

# 健康检查接口
# 用于监控系统确认 API 服务是否正常运行
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 