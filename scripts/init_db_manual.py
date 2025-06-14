import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import asyncio
from app.db.init_db import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    print("数据库表已初始化/同步完成！") 