from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Goodstock 商品管理 API"
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = Field(default="fastapi_shop", pattern=r"^[a-zA-Z0-9_]+$")
    jwt_secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    cors_origins: list[str] = ["http://localhost:5174", "http://127.0.0.1:5174"]
    seed_admin_username: str = "admin"
    seed_admin_password: str = Field(default="Admin@123456", min_length=8)

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_example_secret(cls, value: str) -> str:
        if value.startswith("replace-with-"):
            raise ValueError("请先运行 python scripts/setup_env.py 生成随机 JWT 密钥")
        return value

    @property
    def database_url(self) -> URL:
        # URL.create 会正确处理数据库密码中的 @、: 等特殊字符。
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
