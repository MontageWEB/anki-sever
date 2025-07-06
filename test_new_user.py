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
import httpx
from app.main import app

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

async def test_wx_login_with_user_info():
    """测试微信登录时传递用户信息"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/wx-login", json={
            "code": "test-code",
            "nickname": "测试用户昵称",
            "avatar": "https://example.com/avatar.jpg"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # 验证用户信息是否正确保存
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await ac.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["nickname"] == "测试用户昵称"
        assert user_data["avatar"] == "https://example.com/avatar.jpg"

if __name__ == "__main__":
    asyncio.run(test_new_user_creation()) 