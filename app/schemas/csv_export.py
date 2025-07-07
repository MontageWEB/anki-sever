"""
CSV导出相关的数据验证模型
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class CSVExportRequest(BaseModel):
    """
    CSV导出请求模型
    """
    include_headers: bool = Field(
        default=True,
        description="是否包含表头"
    )


class CSVExportResponse(BaseModel):
    """
    CSV导出响应模型
    """
    status: Literal["processing", "success", "error"] = Field(..., description="导出状态")
    message: str = Field(..., description="状态消息")
    download_url: Optional[str] = Field(None, description="下载链接")
    file_name: Optional[str] = Field(None, description="文件名")
    total_records: Optional[int] = Field(None, description="导出记录数")
    error_message: Optional[str] = Field(None, description="错误信息")


class ExportProgress(BaseModel):
    """
    导出进度信息
    """
    status: Literal["processing", "success", "error"] = Field(..., description="导出状态")
    progress: int = Field(..., description="进度百分比 (0-100)")
    processed_records: int = Field(..., description="已处理记录数")
    total_records: int = Field(..., description="总记录数")
    message: str = Field(..., description="进度消息") 