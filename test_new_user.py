#!/usr/bin/env python3
"""
测试新用户创建和复习规则初始化
"""
import asyncio
from app.db.session import SessionLocal
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.crud.review_rule import get_review_rules
import uuid

async def test_new_user_creation():
    """测试新用户创建和复习规则初始化"""
    async with SessionLocal() as db:
        # 创建新用户，openid 用 uuid 保证唯一
        user_in = UserCreate(
            openid="test-new-user-openid-" + str(uuid.uuid4()),
            nickname="新测试用户",
            avatar=""
        )
        
        user = await create_user(db, user_in)
        print(f"创建用户成功: ID={user.id}, OpenID={user.openid}")
        
        # 检查复习规则是否自动初始化
        rules = await get_review_rules(db, user_id=user.id)
        print(f"复习规则数量: {len(rules)}")
        
        if rules:
            print("前5条规则:")
            for rule in rules[:5]:
                print(f"  复习次数: {rule.review_count}, 间隔天数: {rule.interval_days}")
        else:
            print("❌ 复习规则未初始化")

if __name__ == "__main__":
    asyncio.run(test_new_user_creation()) 