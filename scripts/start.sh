#!/bin/bash
# scripts/start.sh

# 设置错误时退出
set -e

echo "=== 启动 Anki 复习助手服务 ==="

# 检查 MySQL 是否已经在运行
echo "检查 MySQL 状态..."
if mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
    echo "MySQL 已经在运行"
else
    echo "正在启动 MySQL..."
    sudo mysql.server start
    
    # 等待 MySQL 完全启动
    echo "等待 MySQL 启动完成..."
    for i in {1..30}; do
        if mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
            echo "MySQL 启动成功"
            break
        fi
        sleep 1
    done
    
    # 最终检查
    if ! mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
        echo "错误: MySQL 启动失败"
        exit 1
    fi
fi

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
