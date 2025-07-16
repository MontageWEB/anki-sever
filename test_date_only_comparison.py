#!/usr/bin/env python3
"""
测试只比较日期的逻辑
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.crud import card as crud_card
from app.models.card import Card
from sqlalchemy import select

def fix_timezone_fields(card):
    """修正卡片时间字段的时区信息"""
    if card.created_at and card.created_at.tzinfo is None:
        card.created_at = card.created_at.replace(tzinfo=timezone.utc)
    if card.updated_at and card.updated_at.tzinfo is None:
        card.updated_at = card.updated_at.replace(tzinfo=timezone.utc)
    if card.first_review_at and card.first_review_at.tzinfo is None:
        card.first_review_at = card.first_review_at.replace(tzinfo=timezone.utc)
    if card.next_review_at and card.next_review_at.tzinfo is None:
        card.next_review_at = card.next_review_at.replace(tzinfo=timezone.utc)

async def test_date_only_comparison():
    """测试只比较日期的逻辑"""
    db = SessionLocal()
    try:
        user_id = 2
        
        print("=== 测试只比较日期的逻辑 ===")
        print(f"用户ID: {user_id}")
        
        # 获取当前时间
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        tomorrow_start = today_start + timedelta(days=1)
        
        print(f"当前UTC时间: {now}")
        print(f"今天开始时间: {today_start}")
        print(f"明天开始时间: {tomorrow_start}")
        print()
        
        # 模拟你提到的三条卡片数据
        test_cards = [
            {"id": 279, "next_review_at": "2025-07-16T00:00:00+00:00"},
            {"id": 226, "next_review_at": "2025-07-16T00:54:53+00:00"},
            {"id": 228, "next_review_at": "2025-07-16T11:32:36+00:00"}
        ]
        
        print("=== 模拟卡片数据测试 ===")
        for card_data in test_cards:
            next_review_at = datetime.fromisoformat(card_data["next_review_at"].replace("Z", "+00:00"))
            is_today = next_review_at < tomorrow_start
            print(f"卡片 ID {card_data['id']}:")
            print(f"  next_review_at: {next_review_at}")
            print(f"  明天开始时间: {tomorrow_start}")
            print(f"  是否今天: {is_today}")
            print()
        
        # 测试实际数据库中的卡片
        print("=== 测试实际数据库中的卡片 ===")
        all_cards_query = select(Card).filter(Card.user_id == user_id)
        result = await db.execute(all_cards_query)
        all_cards = result.scalars().all()
        
        today_cards = []
        for card in all_cards:
            fix_timezone_fields(card)
            if card.next_review_at < tomorrow_start:
                today_cards.append(card)
        
        print(f"今天应该复习的卡片数量: {len(today_cards)}")
        for card in today_cards:
            print(f"  ID: {card.id}, next_review_at: {card.next_review_at}")
        print()
        
        # 测试两种方法
        print("=== 测试两种方法 ===")
        
        # 方法1: get_cards with filter_tag="today"
        print("方法1: get_cards(filter_tag='today')")
        cards1, total1 = await crud_card.get_cards(
            db=db,
            skip=0,
            limit=100,
            user_id=user_id,
            filter_tag="today"
        )
        print(f"返回卡片数量: {len(cards1)}")
        print(f"卡片ID列表: {[card.id for card in cards1]}")
        print()
        
        # 方法2: get_cards_to_review
        print("方法2: get_cards_to_review()")
        cards2, total2 = await crud_card.get_cards_to_review(
            db=db,
            user_id=user_id,
            page=1,
            per_page=100
        )
        print(f"返回卡片数量: {len(cards2)}")
        print(f"卡片ID列表: {[card.id for card in cards2]}")
        print()
        
        # 比较结果
        print("=== 比较结果 ===")
        print(f"方法1总数: {total1}, 方法2总数: {total2}")
        print(f"总数是否一致: {'是' if total1 == total2 else '否'}")
        
        # 比较卡片ID列表
        ids1 = {card.id for card in cards1}
        ids2 = {card.id for card in cards2}
        print(f"方法1卡片ID: {sorted(ids1)}")
        print(f"方法2卡片ID: {sorted(ids2)}")
        print(f"ID列表是否一致: {'是' if ids1 == ids2 else '否'}")
        
        if ids1 != ids2:
            print(f"方法1独有: {ids1 - ids2}")
            print(f"方法2独有: {ids2 - ids1}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_date_only_comparison()) 