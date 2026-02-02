"""主应用入口"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

from app.config import settings
from app.database import engine
from app.models import Base
from app.schemas import ApiResponse
from app.routers import health, auth
from app.services.file_storage import init_buckets

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建所有表
Base.metadata.create_all(bind=engine)

# 初始化 MinIO 存储桶
try:
    init_buckets()
    logger.info("MinIO 存储桶初始化成功")
except Exception as e:
    logger.warning(f"MinIO 存储桶初始化失败: {e}")

# 创建 FastAPI 应用
app = FastAPI(
    title="hereOffer API",
    description="招聘流程自动化系统",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求ID中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加请求ID"""
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": -1,
            "message": "Internal Server Error",
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else "",
        },
    )


# 包含路由
app.include_router(health.router)
app.include_router(auth.router)

# 导入 debug 路由
from app.routers import debug
app.include_router(debug.router)

# 导入 applications 路由
from app.routers import applications
app.include_router(applications.router)

# 导入 jobs 路由
from app.routers import jobs
app.include_router(jobs.router)

# 导入 admin_applications 路由
from app.routers import admin_applications
app.include_router(admin_applications.router)

# 导入 chat 路由
from app.routers import chat
app.include_router(chat.router)

# 导入 websocket_chat 路由
from app.routers import websocket_chat
app.include_router(websocket_chat.router)

# 导入 admin_knowledge 路由
from app.routers import admin_knowledge
app.include_router(admin_knowledge.router)


@app.get("/")
async def root():
    """根路由"""
    return {"message": "hereOffer API V1.0"}
