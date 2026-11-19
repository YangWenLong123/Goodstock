"""运行 python -m app.init_db，创建专用数据库、表和初始数据。"""

from decimal import Decimal

from sqlalchemy import create_engine, func, select, text

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Product, User
from app.security import hash_password

SEED_PRODUCTS = [
    (
        "无线降噪耳机",
        "DG-001",
        "数码配件",
        "299.00",
        128,
        "active",
        "轻盈佩戴，专注每一段声音。支持蓝牙 5.3 与主动降噪。",
    ),
    (
        "极简机械键盘",
        "DG-002",
        "数码配件",
        "459.00",
        36,
        "active",
        "紧凑 75% 配列，热插拔轴体，支持三模连接。",
    ),
    (
        "便携随行保温杯",
        "LF-001",
        "生活用品",
        "89.00",
        205,
        "active",
        "500ml 食品级不锈钢内胆，日常通勤的好搭档。",
    ),
    (
        "棉麻帆布托特包",
        "BG-001",
        "服饰箱包",
        "69.00",
        8,
        "active",
        "加厚棉麻面料，内置分隔口袋，轻松装下日常所需。",
    ),
    (
        "点阵灵感笔记本",
        "ST-001",
        "办公文具",
        "35.00",
        160,
        "active",
        "A5 点阵内页，180° 平摊，让灵感自在发生。",
    ),
    (
        "桌面氛围台灯",
        "LF-002",
        "生活用品",
        "169.00",
        42,
        "active",
        "三档色温，无级调光，陪伴每一个专注时刻。",
    ),
    (
        "65W 氮化镓充电器",
        "DG-003",
        "数码配件",
        "129.00",
        6,
        "active",
        "双 USB-C 接口，兼容笔记本与手机快速充电。",
    ),
    (
        "复古黄铜签字笔",
        "ST-002",
        "办公文具",
        "58.00",
        0,
        "inactive",
        "黄铜笔身，细腻手感，适合书写与礼赠。",
    ),
    (
        "轻量城市双肩包",
        "BG-002",
        "服饰箱包",
        "239.00",
        24,
        "active",
        "防泼水面料，独立电脑隔层，城市出行更从容。",
    ),
    (
        "可折叠笔记本支架",
        "DG-004",
        "数码配件",
        "119.00",
        57,
        "active",
        "铝合金材质，六档角度调节，折叠便携。",
    ),
    (
        "陶瓷马克杯",
        "LF-003",
        "生活用品",
        "49.00",
        73,
        "active",
        "温润哑光釉面，350ml 容量，为生活留一点慢时光。",
    ),
    (
        "桌面收纳托盘",
        "ST-003",
        "办公文具",
        "45.00",
        18,
        "inactive",
        "简洁分区设计，让桌面回归有序。",
    ),
]


def main():
    settings = get_settings()
    # db_name 已经过白名单校验；这里只创建专用库，不修改其他数据库。
    # URL.set(database=None) 会保留原数据库；空字符串才表示连接服务器本身。
    server_engine = create_engine(settings.database_url.set(database=""))
    try:
        with server_engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        server_engine.dispose()

    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.username == settings.seed_admin_username))
        if user is None:
            db.add(
                User(
                    username=settings.seed_admin_username,
                    password_hash=hash_password(settings.seed_admin_password),
                    display_name="演示管理员",
                )
            )
            print(f"已创建管理员：{settings.seed_admin_username}（密码见 .env 配置）")
        if not db.scalar(select(func.count()).select_from(Product)):
            db.add_all(
                [
                    Product(
                        name=name,
                        sku=sku,
                        category=category,
                        price=Decimal(price),
                        stock=stock,
                        status=status,
                        description=description,
                    )
                    for name, sku, category, price, stock, status, description in SEED_PRODUCTS
                ]
            )
            print(f"已创建 {len(SEED_PRODUCTS)} 条演示商品。")
    print(f"数据库 {settings.db_name} 初始化完成，重复运行不会覆盖已有账号和商品。")


if __name__ == "__main__":
    main()
