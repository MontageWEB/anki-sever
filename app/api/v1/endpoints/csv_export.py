"""
CSV导出相关的API端点
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import csv_export as crud_export
from app.schemas.csv_export import (
    CSVExportRequest,
    CSVExportResponse,
    ExportProgress
)

router = APIRouter()

# 存储导出任务状态（实际项目中应该使用Redis等缓存）
export_tasks = {}


@router.post("/export", response_model=CSVExportResponse)
async def export_csv_data(
    request: CSVExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CSVExportResponse:
    """
    导出用户的卡片数据为CSV文件
    
    功能：
    1. 获取用户的所有卡片数据
    2. 生成CSV文件
    3. 返回下载链接
    """
    try:
        # 检查用户是否有卡片数据
        total_count = await crud_export.get_user_cards_count(db, user_id)
        if total_count == 0:
            return CSVExportResponse(
                status="error",
                message="没有可导出的卡片数据",
                error_message="您的卡片库为空，请先添加一些卡片"
            )
        
        # 获取所有卡片数据
        cards_data = await crud_export.get_user_cards_for_export(db, user_id)
        
        # 生成CSV内容
        csv_content = crud_export.generate_csv_content(cards_data, request.include_headers)
        
        # 保存文件
        filepath = crud_export.save_csv_file(csv_content, user_id)
        
        # 生成下载链接（这里使用相对路径，实际部署时需要配置静态文件服务）
        filename = os.path.basename(filepath)
        download_url = f"/api/v1/csv-export/download/{filename}"
        
        return CSVExportResponse(
            status="success",
            message=f"导出成功，共导出 {total_count} 张卡片",
            download_url=download_url,
            file_name=filename,
            total_records=total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/download/{filename}")
async def download_csv_file(
    filename: str,
    user_id: int = Depends(deps.get_current_user_id)
):
    """
    下载CSV文件
    
    Args:
        filename: 文件名
        user_id: 用户ID（用于验证文件权限）
    """
    # 验证文件名格式（防止路径遍历攻击）
    if not filename.startswith(f"anki_cards_user_{user_id}_"):
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    filepath = os.path.join("./exports", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/progress/{task_id}", response_model=ExportProgress)
async def get_export_progress(
    task_id: str,
    user_id: int = Depends(deps.get_current_user_id)
) -> ExportProgress:
    """
    获取导出进度（用于大量数据导出时的进度跟踪）
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
    """
    # 这里应该从缓存中获取任务状态
    # 实际项目中建议使用Redis存储任务状态
    if task_id not in export_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = export_tasks[task_id]
    
    return ExportProgress(
        status=task_info.get("status", "processing"),
        progress=task_info.get("progress", 0),
        processed_records=task_info.get("processed_records", 0),
        total_records=task_info.get("total_records", 0),
        message=task_info.get("message", "处理中...")
    )


@router.delete("/cancel/{task_id}")
async def cancel_export_task(
    task_id: str,
    user_id: int = Depends(deps.get_current_user_id)
):
    """
    取消导出任务
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
    """
    if task_id not in export_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 标记任务为取消状态
    export_tasks[task_id]["status"] = "cancelled"
    export_tasks[task_id]["message"] = "任务已取消"
    
    return {"message": "任务已取消"} 