#!/bin/bash
# scripts/start.sh

# 设置错误时退出
set -e

echo "=== 启动 Anki 复习助手服务 ==="

# 启动 MySQL
echo "正在启动 MySQL..."
sudo mysql.server start

# 等待 MySQL 完全启动
sleep 5

# 创建数据库
echo "正在创建数据库..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS anki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 执行数据库迁移
echo "正在执行数据库迁移..."
alembic upgrade head

# 启动后端服务
echo "正在启动后端服务..."
uvicorn app.main:app --reload --port 8001
