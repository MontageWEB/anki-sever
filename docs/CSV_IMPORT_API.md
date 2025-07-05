# CSV导入功能API文档

## 📋 功能概述

CSV导入功能允许用户通过上传CSV文件批量导入卡片数据，支持数据验证、重复检测和多种重复处理策略。

## 🚀 API端点

### 1. 预览CSV数据

**端点**: `POST /api/v1/csv-import/preview`

**功能**: 解析CSV文件，验证数据格式，检查重复数据，返回预览信息

**请求参数**:
- `file`: CSV文件（multipart/form-data）

**响应示例**:
```json
{
  "preview": {
    "total_records": 5,
    "valid_records": 5,
    "duplicate_records": 0,
    "error_records": 0,
    "errors": []
  },
  "result": null,
  "status": "preview"
}
```

### 2. 导入CSV数据

**端点**: `POST /api/v1/csv-import/import`

**功能**: 执行实际的CSV数据导入

**请求参数**:
- `file`: CSV文件（multipart/form-data）
- `duplicate_strategy`: 重复处理策略（可选，默认"skip"）
  - `skip`: 跳过重复
  - `overwrite`: 覆盖重复
  - `create_copy`: 创建副本

**响应示例**:
```json
{
  "preview": null,
  "result": {
    "success_count": 5,
    "skip_count": 0,
    "error_count": 0,
    "duplicate_count": 0,
    "errors": [],
    "message": "导入完成：成功 5 张，跳过 0 张，错误 0 张"
  },
  "status": "success"
}
```

## 📊 CSV文件格式

### 字段说明

| 字段         | 类型     | 必需 | 最大长度 | 说明 |
|--------------|----------|------|----------|------|
| 知识点       | string   | ✅   | 100字符   | 卡片的问题/知识点 |
| 答案         | string   | ✅   | 500字符   | 卡片的答案/解释 |
| 创建时间     | datetime | ❌   | -        | 支持“YYYY-MM-DD”或“YYYY-MM-DD HH:mm:ss”，如只填日期会自动补全为00:00:00 |
| 复习次数     | integer  | ❌   | -        | 非负整数，默认0 |
| 下次复习时间 | datetime | ❌   | -        | 支持“YYYY-MM-DD”或“YYYY-MM-DD HH:mm:ss”，如只填日期会自动补全为00:00:00 |

### 示例CSV文件

```csv
知识点,答案,创建时间,复习次数,下次复习时间
什么是Python装饰器？,Python装饰器是一种设计模式...,2024-01-01,0,2024-01-01 10:00:00
FastAPI的主要特点有哪些？,FastAPI是一个现代、快速的Web框架...,2024-01-01 10:00:00,0,2024-01-01
```

## 🔧 使用示例

### 使用curl测试

```bash
# 1. 获取访问令牌
TOKEN=$(curl -s -X POST "http://localhost:8001/api/v1/auth/wx-login" \
  -H "Content-Type: application/json" \
  -d '{"code": "test-code"}' | jq -r '.access_token')

# 2. 预览CSV数据
curl -X POST "http://localhost:8001/api/v1/csv-import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_cards.csv"

# 3. 导入CSV数据（跳过重复）
curl -X POST "http://localhost:8001/api/v1/csv-import/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_cards.csv" \
  -F "duplicate_strategy=skip"

# 4. 导入CSV数据（覆盖重复）
curl -X POST "http://localhost:8001/api/v1/csv-import/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_cards.csv" \
  -F "duplicate_strategy=overwrite"
```

### 使用JavaScript测试

```javascript
// 1. 获取访问令牌
const tokenResponse = await fetch('/api/v1/auth/wx-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code: 'test-code' })
});
const { access_token } = await tokenResponse.json();

// 2. 预览CSV数据
const formData = new FormData();
formData.append('file', csvFile);

const previewResponse = await fetch('/api/v1/csv-import/preview', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
const preview = await previewResponse.json();

// 3. 导入CSV数据
const importFormData = new FormData();
importFormData.append('file', csvFile);
importFormData.append('duplicate_strategy', 'skip');

const importResponse = await fetch('/api/v1/csv-import/import', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: importFormData
});
const result = await importResponse.json();
```

## ⚠️ 错误处理

### 常见错误

1. **文件格式错误**
   ```json
   {
     "detail": "请上传CSV格式的文件"
   }
   ```

2. **编码错误**
   ```json
   {
     "detail": "文件编码错误，请使用UTF-8编码"
   }
   ```

3. **数据验证错误**
   ```json
   {
     "preview": {
       "errors": [
         {
           "row_number": 2,
           "field_name": "question",
           "error_message": "知识点不能为空",
           "raw_data": "..."
         }
       ]
     }
   }
   ```

4. **重复处理策略错误**
   ```json
   {
     "detail": "无效的重复处理策略"
   }
   ```

## 🔍 数据验证规则

### 必填字段验证
- 知识点：不能为空，长度1-100字符
- 答案：不能为空，长度1-500字符

### 可选字段验证
- 创建时间：支持"YYYY-MM-DD"或"YYYY-MM-DD HH:mm:ss"，如只填日期会自动补全为00:00:00
- 复习次数：非负整数
- 下次复习时间：支持"YYYY-MM-DD"或"YYYY-MM-DD HH:mm:ss"，如只填日期会自动补全为00:00:00

### 重复检测
- 根据知识点和答案内容同时判断重复
- 忽略大小写和空格差异
- 只有当知识点和答案都完全相同时，才认为是重复

## 📈 性能考虑

### 文件大小限制
- 建议单个CSV文件不超过10MB
- 单次导入建议不超过1000条记录

### 处理策略
- 大文件建议分批处理
- 导入过程中支持取消操作
- 使用事务确保数据一致性

## 🛡️ 安全考虑

### 文件验证
- 只接受CSV格式文件
- 验证文件编码为UTF-8
- 限制文件大小

### 数据清理
- 自动清理输入数据
- 防止SQL注入
- 验证用户权限

## 📝 最佳实践

### 文件准备
1. 使用UTF-8编码保存CSV文件
2. 确保字段顺序正确
3. 验证时间格式
4. 检查数据完整性

### 导入流程
1. 先使用预览接口验证数据
2. 根据预览结果调整数据
3. 选择合适的重复处理策略
4. 执行导入操作
5. 检查导入结果

### 错误处理
1. 仔细查看错误信息
2. 根据错误提示修正数据
3. 重新验证和导入
4. 保留导入日志

## 🔄 重复处理策略

### skip（跳过重复）
- 跳过所有重复的卡片
- 只导入新的卡片
- 适合增量导入

### overwrite（覆盖重复）
- 用导入数据覆盖现有卡片
- 更新所有字段
- 适合数据更新

### create_copy（创建副本）
- 为重复卡片添加序号后缀
- 保留原有卡片
- 适合数据备份

## 📊 监控和日志

### 导入统计
- 总记录数
- 有效记录数
- 重复记录数
- 错误记录数

### 错误详情
- 行号
- 字段名
- 错误信息
- 原始数据

### 操作日志
- 导入时间
- 用户ID
- 文件信息
- 处理结果 