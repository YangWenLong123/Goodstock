"""首次运行生成本地配置；已有 .env 时不会覆盖。"""

import secrets
from pathlib import Path

backend = Path(__file__).resolve().parents[1]
target = backend / ".env"
if target.exists():
    print(".env 已存在，保留原有配置。")
else:
    template = (backend / ".env.example").read_text(encoding="utf-8")
    template = template.replace(
        "replace-with-a-random-secret-at-least-32-characters", secrets.token_hex(32)
    )
    with target.open("x", encoding="utf-8") as file:
        file.write(template)
    target.chmod(0o600)
    print("已生成 .env 和随机 JWT 密钥，默认数据库为本机 MySQL root/root。")
