#!/bin/bash

# 自动化备份脚本
# 建议添加到 crontab: 0 2 * * * /path/to/auto_backup.sh

# 配置
BACKUP_DIR="./backups"
RETENTION_DAYS=30  # 保留天数

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
./scripts/backup_db.sh

# 清理旧备份文件
echo "清理 $RETENTION_DAYS 天前的备份文件..."
find "$BACKUP_DIR" -name "anki_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "自动化备份完成" 