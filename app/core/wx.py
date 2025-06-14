import httpx
from typing import Optional

WECHAT_API = "https://api.weixin.qq.com/sns/jscode2session"

async def get_wx_openid(appid: str, secret: str, code: str) -> Optional[dict]:
    params = {
        "appid": appid,
        "secret": secret,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(WECHAT_API, params=params)
        data = resp.json()
        if "openid" in data:
            return data
        return None 