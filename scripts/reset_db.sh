#!/bin/bash
# scripts/reset_db.sh

# 设置错误时退出
set -e

echo "=== 重置数据库 ==="

# 启动 MySQL
echo "正在启动 MySQL..."
sudo mysql.server start

# 等待 MySQL 完全启动
sleep 5

# 删除并重新创建数据库
echo "正在重置数据库..."
mysql -u root -e "DROP DATABASE IF EXISTS anki;"
mysql -u root -e "CREATE DATABASE anki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 执行数据库迁移
echo "正在执行数据库迁移..."
alembic upgrade head

# 验证表是否创建成功
echo "正在验证数据库表..."
mysql -u root anki -e "SHOW TABLES;"

echo "数据库重置完成！" 