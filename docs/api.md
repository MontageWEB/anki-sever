# Anki 复习助手 API 文档

## 基础信息
- 基础路径: `/api/v1`
- 响应格式: JSON
- 时间格式: ISO 8601 (例如: "2024-05-12T10:30:00")
- 服务地址: http://localhost:8001

## 错误响应
所有接口的错误响应格式统一为：
```json
{
    "detail": "错误信息"
}
```

## 认证与多用户说明
- 除认证接口外，所有卡片和复习规则相关接口均需在请求头携带 `Authorization: Bearer <token>`
- 所有数据均归属于当前登录用户，接口操作仅影响自己的数据，互不干扰
- 用户信息相关接口（`/auth/me`、`/auth/update-profile`）已设置禁用缓存，确保始终返回最新数据

## 接口列表

### 1. 用户认证

#### 1.1 微信一键登录
- 路径: POST `/auth/wx-login`
- 请求体:
```json
{
  "code": "微信登录临时凭证",
  "nickname": "用户昵称（可选）",
  "avatar": "用户头像url（可选）"
}
```
- 响应体:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```
- 说明: 
  - 前端传 code，后端换取 openid 并返回 token
  - 如果前端同时传递 nickname 和 avatar，会保存到用户信息中
  - 如果未传递用户信息，会使用默认的"微信用户"昵称和空头像
  - 建议前端在用户授权后传递真实的昵称和头像信息

#### 1.2 H5环境登录
- 路径: POST `/auth/h5-login`
- 描述: H5环境专用登录接口，不需要微信授权
- 请求体:
```json
{
  "nickname": "用户昵称",
  "avatar": "用户头像url"
}
```
- 响应体:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```
- 说明: 
  - 适用于 uni-app 等跨平台框架的 H5 环境
  - 不需要微信 code，直接创建或获取 H5 测试用户
  - 使用固定的 H5 用户标识，确保数据隔离

#### 1.3 获取当前用户信息
- 路径: GET `/auth/me`
- 描述: 获取当前登录用户的信息（需认证）
- 请求头:
  - `Authorization: Bearer <token>`
- 响应体:
```json
{
  "id": 1,
  "openid": "用户openid",
  "nickname": "微信昵称",
  "avatar": "微信头像url",
  "is_active": true,
  "created_at": "2024-05-12T10:30:00",
  "updated_at": "2024-05-12T10:30:00"
}
```
- 说明:
  - 需在请求头携带有效token
  - 返回当前登录用户的基本信息

#### 1.4 更新用户信息
- 路径: POST `/auth/update-profile`
- 描述: 登录后用户可更新自己的昵称和头像
- 请求头:
  - `Authorization: Bearer <token>`
- 请求体:
```json
{
  "nickname": "用户昵称",
  "avatar": "用户头像url"
}
```
- 响应体:
```json
{
  "id": 1,
  "openid": "用户openid",
  "nickname": "用户昵称",
  "avatar": "用户头像url",
  "is_active": true,
  "created_at": "2024-05-12T10:30:00",
  "updated_at": "2024-05-12T10:30:00"
}
```
- 说明:
  - 需在请求头携带有效token
  - 只允许更新当前登录用户自己的信息
  - 可用于微信登录后补充真实头像和昵称

### 2. 知识卡片管理

#### 2.1 创建卡片
- 路径: POST `/cards`
- 描述: 创建新的知识卡片
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时创建临时演示数据)
- 请求体:
```json
{
    "question": "知识点/问题，最多100字",
    "answer": "答案/解释，最多500字，支持富文本"
}
```
- 注意事项:
  - 已登录用户创建的卡片将保存到数据库
  - 未登录用户（访客模式）创建的卡片为临时演示数据，会自动添加【演示数据】标识
  - 临时演示数据在下次访问时将重置为系统默认演示数据
- 响应:
```json
{
    "id": 1,
    "question": "知识点",
    "answer": "答案",
    "review_count": 0,
    "next_review_at": "2024-05-12T10:30:00",
    "created_at": "2024-05-12T10:30:00",
    "updated_at": "2024-05-12T10:30:00"
}
```

#### 2.2 获取卡片列表
- 路径: GET `/cards`
- 描述: 获取卡片列表，支持分页、搜索和筛选
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时返回演示数据)
- 演示数据说明:
  - 未登录用户获取的是演示数据，包含【演示数据】标识
  - 演示数据支持实时修改（增删改查）
  - 演示数据为临时数据，下次访问时将重置为系统默认演示数据
- 演示数据说明：未登录状态下返回带有"【演示数据】"标识的示例卡片
- 查询参数:
  - `page`: 页码，默认 1
  - `per_page`: 每页数量，默认 20，最大 100
  - `search`: 搜索关键词（可选）
  - `filter_tag`: 筛选标签，可选值：
    - `all`（全部，默认，查询所有卡片）
    - `today`（今日复习，查询下次复习时间为今天的所有卡片，只比较日期部分，不区分具体时间点）
    - `tomorrow`（明日复习，查询下次复习时间为明天的卡片）
    - `week`（近7天，查询下次复习时间在近7天内的卡片，从今天开始计算）
- 响应:
```json
{
    "total": 100,
    "page": 1,
    "per_page": 20,
    "items": [
        {
            "id": 1,
            "question": "知识点",
            "answer": "答案",
            "review_count": 0,
            "next_review_at": "2024-05-12T10:30:00",
            "created_at": "2024-05-12T10:30:00",
            "updated_at": "2024-05-12T10:30:00"
        }
    ]
}
```

#### 2.3 获取卡片统计
- 路径: GET `/cards/stats`
- 描述: 获取卡片统计数据，返回不同筛选条件下的卡片数量
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时返回演示数据统计)
- 演示数据说明:
  - 未登录用户获取的是演示数据的统计
  - 已登录用户获取的是数据库中卡片的统计
- 响应:
```json
{
    "all": 100,
    "today": 15,
    "tomorrow": 8,
    "week": 42
}
```
- 字段说明:
  - `all`: 全部卡片数量
  - `today`: 今日复习卡片数量（包含已过期的卡片）
  - `tomorrow`: 明日复习卡片数量
  - `week`: 近7天复习卡片数量（从今天开始计算）

#### 2.4 获取卡片详情
- 路径: GET `/cards/{card_id}`
- 描述: 获取单个卡片的详细信息
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时返回演示数据)
- 演示数据说明：未登录状态下返回带有"【演示数据】"标识的示例卡片
- 响应: 同创建卡片的响应

#### 2.5 更新卡片
- 路径: PUT `/cards/{card_id}`
- 描述: 更新卡片内容
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时更新临时演示数据)
- 请求体:
```json
{
    "question": "知识点/问题，最多100字",
    "answer": "答案/解释，最多500字，支持富文本"
}
```
- 注意事项:
  - 已登录用户只能更新自己的卡片
  - 未登录用户（访客模式）只能更新临时演示数据
  - 更新后的临时演示数据在下次访问时将重置为系统默认演示数据
- 响应: 同创建卡片的响应

#### 2.6 删除卡片
- 路径: DELETE `/cards/{card_id}`
- 描述: 删除指定卡片
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时删除临时演示数据)
- 注意事项:
  - 已登录用户只能删除自己的卡片
  - 未登录用户（访客模式）只能删除临时演示数据
  - 删除的临时演示数据在下次访问时将重置为系统默认演示数据
- 响应: HTTP 204 No Content

#### 2.7 批量导入卡片（CSV导入）
- 路径: POST `/csv-import/import`
- 描述: 批量导入CSV文件中的卡片数据，支持重复处理策略
- 请求参数:
  - `file`: CSV文件（multipart/form-data）
  - `duplicate_strategy`: 重复处理策略（可选，默认"skip"）
    - `skip`: 跳过重复
    - `overwrite`: 覆盖重复
- 响应:
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
- 字段说明：
  | 字段         | 类型     | 必需 | 最大长度 | 说明 |
  |--------------|----------|------|----------|------|
  | 知识点       | string   | ✅   | 100字符   | 卡片的问题/知识点 |
  | 答案         | string   | ✅   | 500字符   | 卡片的答案/解释 |
  | 创建时间     | datetime | ❌   | -        | 支持“YYYY-MM-DD”、“YYYY-MM-DD HH:mm:ss”、“YYYY/M/D H:mm”等多种常见格式，系统自动识别 |
  | 复习次数     | integer  | ❌   | -        | 非负整数，默认0 |
  | 下次复习时间 | datetime | ❌   | -        | 支持“YYYY-MM-DD”、“YYYY-MM-DD HH:mm:ss”、“YYYY/M/D H:mm”等多种常见格式，系统自动识别 |
- 示例CSV：
```csv
知识点,答案,创建时间,复习次数,下次复习时间
什么是Python装饰器？,Python装饰器是一种设计模式...,2024-01-01,0,2024-01-01 10:00:00
FastAPI的主要特点有哪些？,FastAPI是一个现代、快速的Web框架...,2024-01-01 10:00:00,0,2024-01-01
```
- 重复处理策略：
  - skip（跳过重复）：跳过所有重复的卡片，只导入新的卡片，适合增量导入
  - overwrite（覆盖重复）：用导入数据覆盖现有卡片，适合数据更新

#### 2.8 预览CSV导入
- 路径: POST `/csv-import/preview`
- 描述: 解析CSV文件，验证数据格式，检查重复数据，返回预览信息
- 请求参数:
  - `file`: CSV文件（multipart/form-data）
- 响应:
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

#### 错误处理
- 文件格式错误：`{"detail": "请上传CSV格式的文件"}`
- 编码错误：`{"detail": "文件编码错误，请使用UTF-8编码"}`
- 数据验证错误：见预览接口响应
- 重复处理策略错误：`{"detail": "无效的重复处理策略"}`

#### 数据验证规则
- 必填字段：知识点（1-100字符）、答案（1-500字符）
- 可选字段：创建时间、下次复习时间（支持“YYYY-MM-DD”或“YYYY-MM-DD HH:mm:ss”），复习次数（非负整数）
- 重复检测：知识点和答案都相同才算重复，忽略大小写和空格差异

#### 最佳实践
- 建议导入前用预览接口验证数据，确认无误后再导入
- 时间字段支持多种常见格式（如 2025-8-7 0:00、2025/8/7 0:00、2025-08-07 00:00:00 等），系统自动识别，无需手动调整格式
- 文件建议UTF-8编码，单次导入不超过1000条
- 导入前建议备份数据
- 导入后检查结果，处理错误

#### 2.8 导出卡片（CSV导出）
- 路径: POST `/csv-export/export`
- 描述: 导出当前用户所有卡片为CSV文件，支持自定义是否包含表头
- 请求头:
  - `Authorization: Bearer <token>`
- 请求体:
```json
{
  "include_headers": true  // 是否包含表头，默认true
}
```
- 响应体:
```json
{
  "status": "success",
  "message": "导出成功，共导出 106 张卡片",
  "download_url": "/api/v1/csv-export/download/anki_cards_user_2_20250707_195059.csv",
  "file_name": "anki_cards_user_2_20250707_195059.csv",
  "total_records": 106,
  "error_message": null
}
```
- 字段说明：
  | 字段           | 类型     | 说明                 |
  |----------------|----------|----------------------|
  | status         | string   | 状态（success/error）|
  | message        | string   | 状态消息             |
  | download_url   | string   | 下载链接             |
  | file_name      | string   | 文件名               |
  | total_records  | integer  | 导出记录数           |
  | error_message  | string   | 错误信息（如有）     |

- 下载接口:
  - 路径: GET `/csv-export/download/{filename}`
  - 描述: 下载导出的CSV文件（需token，且只能下载自己的文件）
  - 请求头:
    - `Authorization: Bearer <token>`
  - 路径参数:
    - `filename`: 文件名（由导出接口返回）
  - 响应: 文件流（`Content-Type: text/csv`）

- 错误处理：
  - 未登录或token无效：`{"detail": "Not authenticated"}`
  - 文件不存在：`{"detail": "文件不存在"}`
  - 无权访问：`{"detail": "无权访问此文件"}`
  - 没有可导出的卡片：`{"status": "error", "message": "没有可导出的卡片数据", "error_message": "您的卡片库为空，请先添加一些卡片"}`

- 最佳实践：
  - 建议导出前先用卡片列表接口检查数据
  - 导出后可直接用Excel、Numbers等工具打开CSV文件
  - 文件编码为UTF-8，字段顺序：知识点、答案、创建时间、复习次数、下次复习时间
  - 导出文件仅保存在服务器本地，建议及时下载备份


### 3. 复习功能

#### 3.1 获取待复习卡片
- 路径: GET `/cards/review`
- 描述: 获取需要复习的卡片列表
- 查询参数:
  - `page`: 页码，默认 1
  - `per_page`: 每页数量，默认 20，最大 100
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时返回演示数据)
- 演示数据说明:
  - 未登录用户获取的是演示数据中需要复习的卡片
  - 演示数据支持实时修改（增删改查）
  - 演示数据为临时数据，下次访问时将重置为系统默认演示数据
- 演示数据说明：未登录状态下返回带有"【演示数据】"标识的示例复习卡片
- 规则说明：只要卡片的 `next_review_at` 日期等于今天（即在今天0点~明天0点之间），都算“今日复习”，不考虑具体时间点（T后面的时分秒）。
- 时间判断以用户本地时间（北京时间）为准。
- 响应: 同获取卡片列表的响应

#### 3.2 更新复习状态
- 路径: POST `/cards/{card_id}/review`
- 描述: 更新卡片的复习状态
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时更新临时演示数据的复习状态)
- 请求体:
```json
{
    "remembered": true  // true: 记住了，false: 忘记了
}
```
- 注意事项:
  - 已登录用户的复习进度将保存到数据库
  - 未登录用户（访客模式）的复习进度为临时演示数据
  - 临时复习进度在下次访问时将重置为系统默认演示数据
- 响应: 同创建卡片的响应

#### 3.3 修改下次复习日期
- 路径: PUT `/cards/{card_id}/next-review`
- 描述: 手动修改卡片的下次复习日期，不影响复习次数和复习规则
- 请求头:
  - `Authorization: Bearer <token>` (可选，未登录时修改临时演示数据的复习日期)
- 请求体:
```json
{
    "next_review_at": "2024-05-12T10:30:00"  // ISO 8601 格式的日期时间
}
```
- 注意事项:
  - 已登录用户修改的复习时间将保存到数据库
  - 未登录用户（访客模式）修改的复习时间为临时演示数据
  - 临时复习时间在下次访问时将重置为系统默认演示数据
- 响应: 同创建卡片的响应

### 4. 复习规则管理

#### 4.1 获取复习规则列表
- 路径: GET `/review-rules`
- 描述: 获取所有复习规则，按复习次数排序
- 响应:
```json
{
    "items": [
        {
            "id": 1,
            "review_count": 1,
            "interval_days": 1,
            "created_at": "2024-05-12T10:30:00",
            "updated_at": "2024-05-12T10:30:00"
        }
    ]
}
```

#### 4.2 批量更新复习规则
- 路径: PUT `/review-rules`
- 描述: 批量更新复习规则
- 请求体:
```json
{
    "rules": [
        {
            "review_count": 1,
            "interval_days": 1
        },
        {
            "review_count": 2,
            "interval_days": 2
        }
    ]
}
```
- 响应: 同获取规则列表的响应

#### 4.3 重置复习规则
- 路径: POST `/review-rules/reset`
- 描述: 重置复习规则为默认值
- 响应: 同获取规则列表的响应


