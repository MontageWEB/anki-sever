#!/usr/bin/env python3
# 更新标题为"退还"的卡片，将复习次数改为18

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.card import Card

async def update_card_review_count():
    async with SessionLocal() as db:
        try:
            # 查找标题包含"退还"关键词的卡片
            from sqlalchemy import or_
            result = await db.execute(
                select(Card).where(
                    or_(
                        Card.question.like("%退还%"),
                        Card.answer.like("%退还%")
                    )
                )
            )
            cards = result.scalars().all()
            
            if not cards:
                print("未找到包含'退还'关键词的卡片")
                return
            
            print(f"找到 {len(cards)} 张包含'退还'关键词的卡片：")
            for card in cards:
                print(f"卡片ID={card.id}, 标题='{card.question}', 答案='{card.answer[:50]}...', 当前复习次数={card.review_count}")
            
            # 询问用户要更新哪张卡片
            card_id = input("\n请输入要更新的卡片ID: ")
            try:
                card_id = int(card_id)
            except ValueError:
                print("无效的卡片ID")
                return
            
            # 查找指定ID的卡片
            target_card = None
            for card in cards:
                if card.id == card_id:
                    target_card = card
                    break
            
            if not target_card:
                print(f"未找到ID为 {card_id} 的卡片")
                return
            
            # 更新复习次数
            target_card.review_count = 18
            print(f"已将卡片ID={target_card.id}的复习次数从 {target_card.review_count} 更新为 18")
            
            # 提交更改
            await db.commit()
            print("\n更新成功完成！")
            
        except Exception as e:
            print(f"更新过程中发生错误: {str(e)}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_card_review_count())