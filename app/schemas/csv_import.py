"""
CSV导入相关的数据验证模型
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CSVImportRequest(BaseModel):
    """
    CSV导入请求模型
    """
    duplicate_strategy: Literal["skip", "overwrite", "create_copy"] = Field(
        default="skip",
        description="重复处理策略：skip(跳过), overwrite(覆盖), create_copy(创建副本)"
    )


class CSVRowData(BaseModel):
    """
    CSV行数据模型
    """
    question: str = Field(..., description="知识点", max_length=100)
    answer: str = Field(..., description="答案", max_length=500)
    created_at: Optional[datetime] = Field(None, description="创建时间")
    review_count: Optional[int] = Field(0, description="复习次数")
    next_review_at: Optional[datetime] = Field(None, description="下次复习时间")

    @validator('review_count')
    def validate_review_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('复习次数不能为负数')
        return v or 0


class ImportError(BaseModel):
    """
    导入错误信息
    """
    row_number: int = Field(..., description="行号")
    field_name: str = Field(..., description="字段名")
    error_message: str = Field(..., description="错误信息")
    raw_data: str = Field(..., description="原始数据")


class ImportPreview(BaseModel):
    """
    导入预览信息
    """
    total_records: int = Field(..., description="总记录数")
    valid_records: int = Field(..., description="有效记录数")
    duplicate_records: int = Field(..., description="重复记录数")
    error_records: int = Field(..., description="错误记录数")
    errors: List[ImportError] = Field(default=[], description="错误详情")


class ImportResult(BaseModel):
    """
    导入结果
    """
    success_count: int = Field(..., description="成功导入数量")
    skip_count: int = Field(..., description="跳过数量")
    error_count: int = Field(..., description="错误数量")
    duplicate_count: int = Field(..., description="重复数量")
    errors: List[ImportError] = Field(default=[], description="错误详情")
    message: str = Field(..., description="结果消息")


class CSVImportResponse(BaseModel):
    """
    CSV导入响应模型
    """
    preview: Optional[ImportPreview] = Field(None, description="预览信息")
    result: Optional[ImportResult] = Field(None, description="导入结果")
    status: Literal["preview", "success", "error"] = Field(..., description="状态")
    column_mapping: Optional[dict] = Field(None, description="字段映射信息，key为字段名，value为列索引（从0开始）")
    has_header: Optional[bool] = Field(None, description="是否检测到表头")
    mapping_description: Optional[str] = Field(None, description="字段映射说明") 