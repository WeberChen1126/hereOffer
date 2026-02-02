"""健康检查路由"""
from fastapi import APIRouter
from app.schemas import ApiResponse

router = APIRouter(tags=["Health"])


@router.get("/healthz")
async def healthz() -> ApiResponse[dict]:
    """健康检查接口"""
    return ApiResponse(code=0, message="ok", data={"status": "ok"})
