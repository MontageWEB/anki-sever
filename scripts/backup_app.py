#!/usr/bin/env python3
"""
应用层数据库备份脚本
支持按用户备份和完整备份
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import gzip
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.models.user import User
from app.models.card import Card
from app.models.review_rule import ReviewRule
from app.models.review_settings import ReviewSetting


async def backup_user_data(user_id: int, backup_dir: str = "./backups") -> str:
    """备份指定用户的所有数据"""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_backup_{timestamp}.json.gz"
    filepath = backup_dir / filename
    
    async for session in get_async_session():
        # 查询用户数据
        user_result = await session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"用户 {user_id} 不存在")
        
        # 查询用户的所有卡片
        cards_result = await session.execute(select(Card).where(Card.user_id == user_id))
        cards = cards_result.scalars().all()
        
        # 查询用户的复习规则
        rules_result = await session.execute(select(ReviewRule).where(ReviewRule.user_id == user_id))
        rules = rules_result.scalars().all()
        
        # 查询用户的复习设置
        settings_result = await session.execute(select(ReviewSetting).where(ReviewSetting.user_id == user_id))
        settings = settings_result.scalars().all()
        
        # 构建备份数据
        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "user": {
                "id": user.id,
                "openid": user.openid,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            },
            "cards": [
                {
                    "question": card.question,
                    "answer": card.answer,
                    "review_count": card.review_count,
                    "first_review_at": card.first_review_at.isoformat() if card.first_review_at else None,
                    "next_review_at": card.next_review_at.isoformat(),
                    "created_at": card.created_at.isoformat(),
                    "updated_at": card.updated_at.isoformat()
                }
                for card in cards
            ],
            "review_rules": [
                {
                    "review_count": rule.review_count,
                    "interval_days": rule.interval_days,
                    "created_at": rule.created_at.isoformat(),
                    "updated_at": rule.updated_at.isoformat()
                }
                for rule in rules
            ],
            "review_settings": [
                {
                    "setting_key": setting.setting_key,
                    "setting_value": setting.setting_value,
                    "created_at": setting.created_at.isoformat(),
                    "updated_at": setting.updated_at.isoformat()
                }
                for setting in settings
            ]
        }
        
        # 写入压缩文件
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"用户 {user_id} 数据备份完成: {filepath}")
        print(f"卡片数量: {len(cards)}")
        print(f"复习规则数量: {len(rules)}")
        print(f"设置数量: {len(settings)}")
        
        return str(filepath)


async def backup_all_data(backup_dir: str = "./backups") -> str:
    """备份所有用户数据"""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_users_backup_{timestamp}.json.gz"
    filepath = backup_dir / filename
    
    async for session in get_async_session():
        # 查询所有用户
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        all_data = {
            "backup_time": datetime.now().isoformat(),
            "users": []
        }
        
        for user in users:
            # 查询用户的所有数据
            cards_result = await session.execute(select(Card).where(Card.user_id == user.id))
            cards = cards_result.scalars().all()
            
            rules_result = await session.execute(select(ReviewRule).where(ReviewRule.user_id == user.id))
            rules = rules_result.scalars().all()
            
            settings_result = await session.execute(select(ReviewSetting).where(ReviewSetting.user_id == user.id))
            settings = settings_result.scalars().all()
            
            user_data = {
                "user": {
                    "id": user.id,
                    "openid": user.openid,
                    "nickname": user.nickname,
                    "avatar": user.avatar,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                },
                "cards": [
                    {
                        "question": card.question,
                        "answer": card.answer,
                        "review_count": card.review_count,
                        "first_review_at": card.first_review_at.isoformat() if card.first_review_at else None,
                        "next_review_at": card.next_review_at.isoformat(),
                        "created_at": card.created_at.isoformat(),
                        "updated_at": card.updated_at.isoformat()
                    }
                    for card in cards
                ],
                "review_rules": [
                    {
                        "review_count": rule.review_count,
                        "interval_days": rule.interval_days,
                        "created_at": rule.created_at.isoformat(),
                        "updated_at": rule.updated_at.isoformat()
                    }
                    for rule in rules
                ],
                "review_settings": [
                    {
                        "setting_key": setting.setting_key,
                        "setting_value": setting.setting_value,
                        "created_at": setting.created_at.isoformat(),
                        "updated_at": setting.updated_at.isoformat()
                    }
                    for setting in settings
                ]
            }
            all_data["users"].append(user_data)
        
        # 写入压缩文件
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        total_cards = sum(len(user_data["cards"]) for user_data in all_data["users"])
        print(f"所有用户数据备份完成: {filepath}")
        print(f"用户数量: {len(users)}")
        print(f"总卡片数量: {total_cards}")
        
        return str(filepath)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库备份工具")
    parser.add_argument("--user-id", type=int, help="备份指定用户的数据")
    parser.add_argument("--all", action="store_true", help="备份所有用户数据")
    parser.add_argument("--backup-dir", default="./backups", help="备份目录")
    
    args = parser.parse_args()
    
    if args.user_id:
        await backup_user_data(args.user_id, args.backup_dir)
    elif args.all:
        await backup_all_data(args.backup_dir)
    else:
        print("请指定 --user-id 或 --all 参数")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 