"""选择环境文件，读取并检查数据库连接配置。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

PROJECT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    environment: str
    env_file: Path
    db_host: str
    db_port: int
    db_user: str
    db_password: str = field(repr=False)
    db_name: str


def load_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment not in {"development", "production"}:
        raise ValueError("APP_ENV 只能为 development 或 production")

    filename = ".env.production" if environment == "production" else ".env"
    env_file = PROJECT_DIR / filename
    # 不修改 os.environ，也不展开密码中的 ${...}；避免两份环境配置串用。
    file_values = dotenv_values(env_file, interpolate=False) if env_file.exists() else {}
    values = {}
    for key in ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"):
        value = os.environ.get(key, file_values.get(key))
        if value is None or (key != "DB_PASSWORD" and not value.strip()):
            raise ValueError(f"缺少 {key}，请配置 {env_file.name} 或同名进程环境变量")
        values[key] = value

    try:
        port = int(values["DB_PORT"])
    except ValueError:
        raise ValueError("DB_PORT 必须是 1 到 65535 的整数") from None
    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT 必须是 1 到 65535 的整数")
    if environment == "production" and (
        not values["DB_PASSWORD"] or values["DB_PASSWORD"].startswith("replace-with-")
    ):
        raise ValueError("请填写生产数据库密码，不能使用空值或模板占位值")

    return Settings(
        environment=environment,
        env_file=env_file,
        db_host=values["DB_HOST"],
        db_port=port,
        db_user=values["DB_USER"],
        db_password=values["DB_PASSWORD"],
        db_name=values["DB_NAME"],
    )
