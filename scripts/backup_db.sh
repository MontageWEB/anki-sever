#!/bin/bash

# 数据库备份脚本
# 使用方法: ./backup_db.sh [数据库名] [备份目录]

# 默认配置
DB_NAME=${1:-"anki"}
BACKUP_DIR=${2:-"./backups"}
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/anki_backup_${DATE}.sql"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 从环境变量或配置文件读取数据库配置
source .env 2>/dev/null || true

# 数据库连接参数
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"3306"}
DB_USER=${DB_USER:-"root"}
DB_PASSWORD=${DB_PASSWORD:-""}

echo "开始备份数据库: $DB_NAME"
echo "备份文件: $BACKUP_FILE"

# 执行备份
mysqldump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --user="$DB_USER" \
    --password="$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --add-drop-database \
    --create-options \
    "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "备份成功: $BACKUP_FILE"
    echo "文件大小: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    echo "压缩完成: ${BACKUP_FILE}.gz"
    echo "压缩后大小: $(du -h "${BACKUP_FILE}.gz" | cut -f1)"
else
    echo "备份失败!"
    exit 1
fi 