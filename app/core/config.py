"""
应用配置管理模块
使用 pydantic_settings 进行配置管理，支持：
1. 从环境变量加载配置
2. 从 .env 文件加载配置
3. 提供类型检查和验证
4. 提供默认值
"""

from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, MySQLDsn, validator


class Settings(BaseSettings):
    """
    应用配置类
    所有的配置项都可以通过环境变量覆盖
    例如：API_V1_STR 可以通过环境变量 API_V1_STR 覆盖
    """
    
    # API 版本路径前缀
    API_V1_STR: str = "/api/v1"
    
    # 项目名称，用于 API 文档显示
    PROJECT_NAME: str = "Anki API"
    
    # CORS 配置：允许跨域请求的源列表
    # 例如：["http://localhost:3000", "https://example.com"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # 数据库连接配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "anki"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None  # 改为 str 类型

    # 复习策略配置
    # 可以通过环境变量 REVIEW_STRATEGY_RULES 覆盖
    REVIEW_STRATEGY_RULES: List[Dict[str, int]] = [
        {"min_count": 1, "max_count": 3, "days": 1},    # 1-3次：1天
        {"min_count": 4, "max_count": 4, "days": 2},    # 第4次：2天
        {"min_count": 5, "max_count": 5, "days": 3},    # 第5次：3天
        {"min_count": 6, "max_count": 6, "days": 5},    # 第6次：5天
        {"min_count": 7, "max_count": 8, "days": 7},    # 7-8次：7天
        {"min_count": 9, "max_count": 10, "days": 14},  # 9-10次：14天
        {"min_count": 11, "max_count": 12, "days": 30}, # 11-12次：30天
        {"min_count": 13, "max_count": 999, "days": 60} # 13次以上：60天
    ]

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        # 直接构建连接字符串
        return f"mysql+aiomysql://{values.get('MYSQL_USER')}:{values.get('MYSQL_PASSWORD')}@{values.get('MYSQL_HOST')}:{values.get('MYSQL_PORT')}/{values.get('MYSQL_DB')}"

    # JWT 配置（预留，目前未使用）
    SECRET_KEY: str = "your-secret-key-here"  # JWT 密钥
    ALGORITHM: str = "HS256"                   # JWT 算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60      # Token 过期时间（分钟）

    class Config:
        """
        配置类的配置
        - case_sensitive: 配置键是否大小写敏感
        - env_file: 环境变量文件路径
        """
        case_sensitive = True
        env_file = ".env"


# 创建配置实例
# 这个实例会在应用启动时加载所有配置
settings = Settings() 