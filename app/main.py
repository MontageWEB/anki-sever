"""
FastAPI 应用的主入口文件
主要职责：
1. 创建 FastAPI 应用实例
2. 配置中间件（如 CORS）
3. 注册路由
4. 提供健康检查接口
5. 提供静态文件服务（H5前端）
"""

import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
from fastapi.openapi.utils import get_openapi

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.init_db import init_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
# title: API 文档的标题
# description: API 文档的描述
# version: API 版本
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
**开发/测试环境说明：**

1. 微信小程序登录接口 `/auth/wx-login` 支持 `code: test-code`，可获取测试账号 token。
2. H5环境登录接口 `/auth/h5-login` 不需要微信 code，直接获取 H5 测试用户 token。
3. 在右上角 Authorize 按钮中填入 `Bearer <token>`，即可测试所有需要认证的接口。
4. 生产环境请使用真实微信授权流程。
""",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置 CORS (跨源资源共享)
# 这允许前端应用从不同的域名访问我们的 API
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:59371",  # 你本地开发工具的端口
    "https://montage.vip",     # 你的正式域名
    # 还可以加其它需要允许的来源
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],  # 仅开发环境用
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，记录详细错误信息"""
    logger.error(f"全局异常: {exc}")
    logger.error(f"请求路径: {request.url}")
    logger.error(f"请求方法: {request.method}")
    logger.error(f"异常详情: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "path": str(request.url)
        }
    )

# 注册路由
# prefix: API 路由前缀，所有卡片相关的接口都会加上这个前缀
# tags: 用于 API 文档的分类标签
app.include_router(api_router, prefix=settings.API_V1_STR)

# 配置静态文件服务（H5前端）
# 检查静态文件目录是否存在
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # 添加 /assets/ 路径映射到 static/assets/ 目录
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

# H5 首页路由
@app.get("/")
async def h5_index():
    """H5 应用首页"""
    index_file = "static/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "H5 前端文件未找到，请确保 static/index.html 文件存在"}

# 健康检查接口
# 用于监控系统确认 API 服务是否正常运行
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_db() 

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="""
**开发/测试环境说明：**

1. 微信小程序登录接口 `/auth/wx-login` 支持 `code: test-code`，可获取测试账号 token。
2. H5环境登录接口 `/auth/h5-login` 不需要微信 code，直接获取 H5 测试用户 token。
3. 在右上角 Authorize 按钮中填入 `Bearer <token>`，即可测试所有需要认证的接口。
4. 生产环境请使用真实微信授权流程。
""",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "在下方输入框粘贴你的JWT Token即可，格式无需加Bearer前缀"
        }
    }
    # 全局应用BearerAuth
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 