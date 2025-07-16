#!/usr/bin/env python3
"""
测试复习逻辑的一致性
比较 get_cards(filter_tag="today") 和 get_cards_to_review() 的返回结果
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

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

async def test_review_logic_consistency():
    """测试复习逻辑的一致性"""
    db = SessionLocal()
    try:
        user_id = 2  # 使用你提到的用户ID
        
        print("=== 测试复习逻辑一致性 ===")
        print(f"用户ID: {user_id}")
        print(f"当前UTC时间: {datetime.now(timezone.utc)}")
        print()
        
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
        print(f"总数: {total1}")
        print("卡片列表:")
        for i, card in enumerate(cards1, 1):
            print(f"  {i}. ID: {card.id}, 问题: {card.question[:20]}..., 下次复习: {card.next_review_at}")
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
        print(f"总数: {total2}")
        print("卡片列表:")
        for i, card in enumerate(cards2, 1):
            print(f"  {i}. ID: {card.id}, 问题: {card.question[:20]}..., 下次复习: {card.next_review_at}")
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
        
        # 检查所有卡片的 next_review_at
        print("\n=== 检查所有卡片的 next_review_at ===")
        all_cards_query = select(Card).filter(Card.user_id == user_id)
        result = await db.execute(all_cards_query)
        all_cards = result.scalars().all()
        
        now = datetime.now(timezone.utc)
        print(f"当前UTC时间: {now}")
        print("所有卡片的 next_review_at:")
        for card in all_cards:
            # 修正时区信息
            fix_timezone_fields(card)
            status = "已过期" if card.next_review_at <= now else "未过期"
            print(f"  ID: {card.id}, next_review_at: {card.next_review_at}, 状态: {status}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_review_logic_consistency()) 