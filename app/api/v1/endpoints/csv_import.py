"""
CSV导入相关的API端点
"""

import csv
import io
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.api import deps
from app.crud import card as crud_card
from app.schemas.csv_import import (
    CSVImportRequest,
    CSVImportResponse,
    ImportPreview,
    ImportResult,
    ImportError,
    CSVRowData
)

router = APIRouter()

# 定义东八区时区
CST = timezone(timedelta(hours=8))


def parse_datetime(date_str: str) -> datetime:
    """
    解析日期时间字符串，支持仅日期自动补全为00:00:00
    
    Args:
        date_str: 日期时间字符串，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss
        
    Returns:
        datetime: 解析后的日期时间对象
        
    Raises:
        ValueError: 格式错误时抛出异常
    """
    try:
        # 优先尝试完整时间
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=CST)
    except ValueError:
        try:
            # 尝试仅日期，自动补全为00:00:00
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return dt.replace(hour=0, minute=0, second=0, tzinfo=CST)
        except ValueError:
            raise ValueError(f"时间格式错误，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss，实际为: {date_str}")


def parse_csv_content(content: str) -> tuple[List[Dict[str, Any]], Dict[str, int], bool]:
    """
    解析CSV内容，支持表头自动检测和字段映射
    
    Args:
        content: CSV文件内容
        
    Returns:
        tuple: (解析后的数据列表, 字段映射信息, 是否检测到表头)
    """
    rows = []
    csv_reader = csv.reader(io.StringIO(content))
    csv_rows = list(csv_reader)
    
    if not csv_rows:
        return rows
    
    # 检测是否有表头
    first_row = csv_rows[0]
    has_header = False
    column_mapping = {}
    
    # 检查第一行是否包含表头关键词
    header_keywords = {
        'question': ['知识点', '问题', 'question', 'title', 'topic'],
        'answer': ['答案', '解释', 'answer', 'content', 'description'],
        'review_count': ['复习次数', '次数', 'review_count', 'count'],
        'next_review_at': ['下次复习时间', '下次时间', 'next_review_at', 'next_review'],
        'created_at': ['创建时间', '时间', 'created_at', 'created', 'date']
    }
    
    for i, cell in enumerate(first_row):
        cell_lower = cell.strip().lower()
        for field, keywords in header_keywords.items():
            if any(keyword in cell_lower for keyword in keywords):
                column_mapping[field] = i
                has_header = True
                break
    
    # 如果没有检测到表头，使用默认位置映射
    if not has_header:
        column_mapping = {
            'question': 0,
            'answer': 1,
            'created_at': 2 if len(first_row) > 2 else None,
            'review_count': 3 if len(first_row) > 3 else None,
            'next_review_at': 4 if len(first_row) > 4 else None
        }
        start_row = 0
    else:
        start_row = 1  # 跳过表头行
    
    # 解析数据行
    for row_number, row in enumerate(csv_rows[start_row:], start_row + 1):
        if not row or all(not cell.strip() for cell in row):
            continue  # 跳过空行
            
        # 确保至少有知识点和答案字段
        if 'question' not in column_mapping or 'answer' not in column_mapping:
            continue
            
        if (column_mapping['question'] >= len(row) or 
            column_mapping['answer'] >= len(row)):
            continue
            
        row_data = {
            "row_number": row_number,
            "question": row[column_mapping['question']].strip(),
            "answer": row[column_mapping['answer']].strip(),
            "created_at": None,
            "review_count": 0,
            "next_review_at": None
        }
        
        # 解析可选字段
        if 'created_at' in column_mapping and column_mapping['created_at'] is not None:
            idx = column_mapping['created_at']
            if idx < len(row) and row[idx].strip():
                try:
                    row_data["created_at"] = parse_datetime(row[idx])
                except ValueError:
                    pass
                    
        if 'review_count' in column_mapping and column_mapping['review_count'] is not None:
            idx = column_mapping['review_count']
            if idx < len(row) and row[idx].strip():
                try:
                    row_data["review_count"] = int(row[idx])
                except ValueError:
                    pass
                    
        if 'next_review_at' in column_mapping and column_mapping['next_review_at'] is not None:
            idx = column_mapping['next_review_at']
            if idx < len(row) and row[idx].strip():
                try:
                    row_data["next_review_at"] = parse_datetime(row[idx])
                except ValueError:
                    pass
                
        rows.append(row_data)
    
    return rows, column_mapping, has_header


def _get_mapping_description(column_mapping: Dict[str, int], has_header: bool) -> str:
    """
    生成字段映射描述
    
    Args:
        column_mapping: 字段映射
        has_header: 是否检测到表头
        
    Returns:
        str: 映射描述
    """
    field_names = {
        'question': '知识点',
        'answer': '答案', 
        'created_at': '创建时间',
        'review_count': '复习次数',
        'next_review_at': '下次复习时间'
    }
    
    if has_header:
        desc = "检测到表头，字段映射如下：\n"
    else:
        desc = "未检测到表头，使用默认位置映射：\n"
    
    for field, col_idx in column_mapping.items():
        if col_idx is not None:
            desc += f"  - 第{col_idx + 1}列 → {field_names.get(field, field)}\n"
    
    return desc


def validate_csv_data(rows: List[Dict[str, Any]]) -> tuple[List[CSVRowData], List[ImportError]]:
    """
    验证CSV数据
    
    Args:
        rows: 原始CSV数据
        
    Returns:
        tuple: (有效数据列表, 错误列表)
    """
    valid_data = []
    errors = []
    now = datetime.now(CST)
    
    for row in rows:
        try:
            # 验证必填字段
            if not row["question"]:
                errors.append(ImportError(
                    row_number=row["row_number"],
                    field_name="question",
                    error_message="知识点不能为空",
                    raw_data=str(row)
                ))
                continue
                
            if not row["answer"]:
                errors.append(ImportError(
                    row_number=row["row_number"],
                    field_name="answer",
                    error_message="答案不能为空",
                    raw_data=str(row)
                ))
                continue
            
            # 验证字段长度
            if len(row["question"]) > 100:
                errors.append(ImportError(
                    row_number=row["row_number"],
                    field_name="question",
                    error_message="知识点长度不能超过100字符",
                    raw_data=str(row)
                ))
                continue
                
            if len(row["answer"]) > 500:
                errors.append(ImportError(
                    row_number=row["row_number"],
                    field_name="answer",
                    error_message="答案长度不能超过500字符",
                    raw_data=str(row)
                ))
                continue
            
            # 验证复习次数
            review_count = row.get("review_count", 0)
            if review_count < 0:
                errors.append(ImportError(
                    row_number=row["row_number"],
                    field_name="review_count",
                    error_message="复习次数不能为负数",
                    raw_data=str(row)
                ))
                continue
            
            # 创建有效数据对象
            valid_data.append(CSVRowData(
                question=row["question"],
                answer=row["answer"],
                created_at=row.get("created_at") or now,
                review_count=review_count,
                next_review_at=row.get("next_review_at") or now
            ))
            
        except Exception as e:
            errors.append(ImportError(
                row_number=row["row_number"],
                field_name="unknown",
                error_message=f"数据验证失败: {str(e)}",
                raw_data=str(row)
            ))
    
    return valid_data, errors


async def check_duplicates(
    db: AsyncSession,
    user_id: int,
    data: List[CSVRowData]
) -> tuple[List[CSVRowData], List[CSVRowData]]:
    """
    检查重复数据
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        data: 要检查的数据
        
    Returns:
        tuple: (非重复数据, 重复数据)
    """
    non_duplicates = []
    duplicates = []
    
    for row_data in data:
        # 检查数据库中是否存在相同的卡片
        existing_card = await crud_card.get_card_by_question_answer(
            db, user_id, row_data.question, row_data.answer
        )
        
        if existing_card:
            duplicates.append(row_data)
        else:
            non_duplicates.append(row_data)
    
    return non_duplicates, duplicates


@router.post("/preview", response_model=CSVImportResponse)
async def preview_csv_import(
    file: UploadFile = File(..., description="CSV文件"),
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CSVImportResponse:
    """
    预览CSV导入数据
    
    功能：
    1. 解析CSV文件内容
    2. 验证数据格式
    3. 检查重复数据
    4. 返回预览信息
    """
    # 检查文件格式
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV格式的文件")
    
    try:
        # 读取文件内容
        content = await file.read()
        try:
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码错误，请使用UTF-8编码")
        
        # 解析CSV数据
        raw_rows, column_mapping, has_header = parse_csv_content(csv_content)
        if not raw_rows:
            raise HTTPException(status_code=400, detail="CSV文件为空或格式错误")
        
        # 验证数据
        valid_data, errors = validate_csv_data(raw_rows)
        
        # 检查重复数据
        non_duplicates, duplicates = await check_duplicates(db, user_id, valid_data)
        
        # 构建预览信息
        preview = ImportPreview(
            total_records=len(raw_rows),
            valid_records=len(valid_data),
            duplicate_records=len(duplicates),
            error_records=len(errors),
            errors=errors
        )
        
        # 添加字段映射信息到响应中
        preview_info = {
            "column_mapping": column_mapping,
            "has_header": has_header,
            "mapping_description": _get_mapping_description(column_mapping, has_header)
        }
        
        return CSVImportResponse(
            preview=preview,
            result=None,
            status="preview",
            column_mapping=column_mapping,
            has_header=has_header,
            mapping_description=_get_mapping_description(column_mapping, has_header)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.post("/import", response_model=CSVImportResponse)
async def import_csv_data(
    file: UploadFile = File(..., description="CSV文件"),
    duplicate_strategy: str = Form("skip", description="重复处理策略"),
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CSVImportResponse:
    """
    导入CSV数据
    
    功能：
    1. 解析和验证CSV数据
    2. 根据策略处理重复数据
    3. 批量导入到数据库
    4. 返回导入结果
    """
    # 验证重复处理策略
    if duplicate_strategy not in ["skip", "overwrite", "create_copy"]:
        raise HTTPException(status_code=400, detail="无效的重复处理策略")
    
    # 检查文件格式
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV格式的文件")
    
    try:
        # 读取文件内容
        content = await file.read()
        try:
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码错误，请使用UTF-8编码")
        
        # 解析CSV数据
        raw_rows, column_mapping, has_header = parse_csv_content(csv_content)
        if not raw_rows:
            raise HTTPException(status_code=400, detail="CSV文件为空或格式错误")
        
        # 验证数据
        valid_data, errors = validate_csv_data(raw_rows)
        
        # 检查重复数据
        non_duplicates, duplicates = await check_duplicates(db, user_id, valid_data)
        
        # 根据策略处理重复数据
        to_import = non_duplicates.copy()
        skip_count = 0
        overwrite_count = 0
        
        if duplicate_strategy == "skip":
            skip_count = len(duplicates)
        elif duplicate_strategy == "overwrite":
            # 覆盖重复数据
            for duplicate in duplicates:
                await crud_card.update_card_by_question_answer(
                    db, user_id, duplicate.question, duplicate.answer, duplicate
                )
            overwrite_count = len(duplicates)
        elif duplicate_strategy == "create_copy":
            # 为重复数据创建副本
            for duplicate in duplicates:
                # 添加序号后缀
                counter = 1
                original_question = duplicate.question
                while True:
                    new_question = f"{original_question} ({counter})"
                    existing = await crud_card.get_card_by_question_answer(
                        db, user_id, new_question, duplicate.answer
                    )
                    if not existing:
                        duplicate.question = new_question
                        to_import.append(duplicate)
                        break
                    counter += 1
        
        # 批量导入数据
        import_result = await crud_card.batch_create_cards_from_csv(
            db, to_import, user_id
        )
        
        # 构建结果
        result = ImportResult(
            success_count=import_result["success"],
            skip_count=skip_count,
            error_count=len(errors),
            duplicate_count=len(duplicates),
            errors=errors,
            message=f"导入完成：成功 {import_result['success']} 张，跳过 {skip_count} 张，错误 {len(errors)} 张"
        )
        
        return CSVImportResponse(
            preview=None,
            result=result,
            status="success",
            column_mapping=column_mapping,
            has_header=has_header,
            mapping_description=_get_mapping_description(column_mapping, has_header)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}") 