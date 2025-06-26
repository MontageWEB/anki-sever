#!/bin/bash

# 数据库恢复脚本
# 使用方法: ./restore_db.sh [备份文件路径] [数据库名]

# 检查参数
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <备份文件路径> [数据库名]"
    echo "示例: $0 ./backups/anki_backup_20250625_143022.sql.gz anki"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME=${2:-"anki"}

# 从环境变量或配置文件读取数据库配置
source .env 2>/dev/null || true

# 数据库连接参数
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"3306"}
DB_USER=${DB_USER:-"root"}
DB_PASSWORD=${DB_PASSWORD:-""}

echo "开始恢复数据库: $DB_NAME"
echo "备份文件: $BACKUP_FILE"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 确认操作
echo "警告: 这将覆盖数据库 $DB_NAME 的所有数据!"
read -p "确认继续? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 1
fi

# 执行恢复
if [[ "$BACKUP_FILE" == *.gz ]]; then
    # 压缩文件，先解压
    gunzip -c "$BACKUP_FILE" | mysql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="$DB_PASSWORD" \
        "$DB_NAME"
else
    # 普通 SQL 文件
    mysql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="$DB_PASSWORD" \
        "$DB_NAME" < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "恢复成功!"
else
    echo "恢复失败!"
    exit 1
fi 