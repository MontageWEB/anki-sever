# Anki复习助手

基于 Vue 3.0 的移动端知识点复习应用，采用间隔重复算法帮助用户高效记忆和管理知识点。
本项目是该产品的服务端工程。

## 技术栈
- 语言：Python 3.11+
- Web 框架：FastAPI 0.104.1
- ORM 框架：SQLAlchemy 2.0.23
- 数据库：MySQL 8.0+
- 异步驱动：aiomysql
- 中间件：跨域（CORS）配置

## 功能特性
- [x] 知识卡片管理：创建、编辑、删除和查询知识卡片
- [x] 复习计划：基于间隔重复算法的智能复习计划生成

## 项目结构
```
anki-server/
├── alembic/           # 数据库迁移
│   ├── versions/     # 迁移版本
│   ├── env.py       # 迁移环境配置
│   └── alembic.ini  # alembic配置文件
├── app/              # 应用主目录
│   ├── api/         # API路由
│   │   └── v1/     # API v1版本
│   ├── core/        # 核心配置
│   ├── crud/        # 数据库操作
│   ├── models/      # 数据模型
│   └── schemas/     # 数据验证
├── docs/            # 项目文档
└── tests/           # 测试用例
```

## 环境要求
- Python 3.11+
- MySQL 8.0+
- 操作系统：macOS/Linux/Windows

## 安装部署
1. 克隆项目
```bash
git clone [repository_url]
cd anki-server
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 创建数据库
```bash
mysql -u root -e "CREATE DATABASE anki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

5. 初始化数据库
```bash
alembic upgrade head
sudo mysql.server start  # 启动 MySQL
```

6. 启动服务
```bash
source venv/bin/activate  # 重新激活虚拟环境
uvicorn app.main:app --reload --port 8001  # 启动服务
```


## 快速启动
1. 一键启动（推荐）
```bash
# 给启动脚本添加执行权限
chmod +x scripts/start.sh

# 运行启动脚本
./scripts/start.sh
```

2. 或者手动启动：
```bash
# 启动 MySQL
sudo mysql.server start

# 创建数据库
mysql -u root -e "CREATE DATABASE anki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 激活虚拟环境
source venv/bin/activate

# 执行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8001
```

## API文档
启动服务后，访问以下地址：

- API 接口文档（Swagger UI）: http://localhost:8001/docs
- API 替代文档（ReDoc）: http://localhost:8001/redoc
- API 基础路径: http://localhost:8001/api/v1

详细的 API 接口说明请查看 `docs/api.md`

## 开发指南
1. 代码规范
   - 遵循PEP 8规范
   - 使用pylint进行代码检查
   - 提交前运行单元测试

2. 分支管理
   - main: 主分支，用于生产环境
   - develop: 开发分支
   - feature/*: 功能分支
   - hotfix/*: 紧急修复分支

3. 提交规范
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式化
   - refactor: 重构
   - test: 测试相关
   - chore: 构建过程或辅助工具的变动

## 贡献指南
1. Fork 本仓库
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 许可证
MIT License