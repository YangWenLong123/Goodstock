"""命令行入口：python main.py --help。"""

import argparse
import json

import pymysql

from config import PROJECT_DIR, load_settings
from crud import create_product, delete_product, get_product, list_products, update_product
from database import get_connection


def main():
    parser = argparse.ArgumentParser(description="Python + MySQL 商品 CRUD 独立示例")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("config", help="查看所选环境与连接位置，不输出密码")
    commands.add_parser("init", help="在已存在的数据库中创建 products 表")
    listing = commands.add_parser("list", help="查询商品列表")
    listing.add_argument("--limit", type=int, default=20)
    reading = commands.add_parser("get", help="查询指定商品")
    reading.add_argument("id", type=int)
    for command in ("create", "update"):
        editing = commands.add_parser(command, help="新增商品" if command == "create" else "修改商品")
        if command == "update":
            editing.add_argument("id", type=int)
        editing.add_argument("--name", required=True)
        editing.add_argument("--price", required=True, help="如 99.90")
        editing.add_argument("--stock", type=int, required=True)
    deleting = commands.add_parser("delete", help="删除指定商品")
    deleting.add_argument("id", type=int)
    args = parser.parse_args()

    try:
        if args.command == "config":
            settings = load_settings()
            result = {
                "environment": settings.environment,
                "env_file": str(settings.env_file),
                "host": settings.db_host,
                "port": settings.db_port,
                "user": settings.db_user,
                "database": settings.db_name,
            }
        elif args.command == "init":
            with get_connection() as connection, connection.cursor() as cursor:
                cursor.execute((PROJECT_DIR / "schema.sql").read_text(encoding="utf-8"))
            result = {"message": "products 表已准备好"}
        elif args.command == "create":
            result = {"id": create_product(args.name, args.price, args.stock)}
        elif args.command == "list":
            result = list_products(args.limit)
        elif args.command == "get":
            result = get_product(args.id)
            if result is None:
                parser.exit(1, "商品不存在。\n")
        elif args.command == "update":
            if not update_product(args.id, args.name, args.price, args.stock):
                parser.exit(1, "商品不存在。\n")
            result = {"updated": True, "id": args.id}
        else:
            if not delete_product(args.id):
                parser.exit(1, "商品不存在。\n")
            result = {"deleted": True, "id": args.id}
    except ValueError as exc:
        parser.exit(2, f"配置或参数错误：{exc}\n")
    except pymysql.MySQLError as exc:
        # 不把包含连接信息的完整数据库异常直接输出给使用者。
        parser.exit(1, f"数据库操作失败（错误码 {exc.args[0]}），请检查连接配置与表结构。\n")

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
