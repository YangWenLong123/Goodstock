"""生成开发或生产配置；已有配置不会覆盖。"""

import argparse
import secrets
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true", help="生成 .env.production")
    args = parser.parse_args()

    backend = Path(__file__).resolve().parents[1]
    filename = ".env.production" if args.production else ".env"
    target = backend / filename
    if target.exists():
        print(f"{filename} 已存在，保留原有配置。")
        return

    template = (backend / f"{filename}.example").read_text(encoding="utf-8")
    template = template.replace(
        "replace-with-a-random-secret-at-least-32-characters", secrets.token_hex(32)
    )
    if args.production:
        template = template.replace(
            "replace-with-a-strong-admin-password", secrets.token_urlsafe(20)
        )
    with target.open("x", encoding="utf-8") as file:
        file.write(template)
    target.chmod(0o600)
    if args.production:
        print("已生成 .env.production、随机 JWT 密钥和管理员初始密码。请填写数据库密码。")
    else:
        print("已生成 .env 和随机 JWT 密钥，默认数据库为本机 MySQL root/root。")


if __name__ == "__main__":
    main()
