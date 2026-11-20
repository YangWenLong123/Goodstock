"""products 表的简单增删改查，使用参数化 SQL。"""

from decimal import Decimal, InvalidOperation

from database import get_connection


def validate_product(name: str, price: str | Decimal, stock: int) -> tuple[str, Decimal, int]:
    name = name.strip()
    if not 1 <= len(name) <= 100:
        raise ValueError("商品名称应为 1 到 100 个字符")
    try:
        amount = Decimal(str(price))
    except InvalidOperation:
        raise ValueError("价格必须是有效数字") from None
    if (
        not amount.is_finite()
        or not Decimal("0") < amount <= Decimal("99999999.99")
        or amount != amount.quantize(Decimal("0.01"))
    ):
        raise ValueError("价格应大于 0、不超过 99999999.99，且最多两位小数")
    if isinstance(stock, bool) or not isinstance(stock, int) or not 0 <= stock <= 2_147_483_647:
        raise ValueError("库存应为 0 到 2147483647 的整数")
    return name, amount, stock


def validate_id(product_id: int) -> None:
    if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1:
        raise ValueError("商品 ID 必须是正整数")


def create_product(name: str, price: str | Decimal, stock: int) -> int:
    """增：返回新商品 ID。"""
    values = validate_product(name, price, stock)
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
            values,
        )
        return cursor.lastrowid


def list_products(limit: int = 20) -> list[dict]:
    """查：按 ID 排序，默认最多查询 20 条。"""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("查询数量必须是 1 到 100 的整数")
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT * FROM products ORDER BY id LIMIT %s", (limit,))
        return list(cursor.fetchall())


def get_product(product_id: int) -> dict | None:
    """查：按 ID 查一条，不存在时返回 None。"""
    validate_id(product_id)
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        return cursor.fetchone()


def update_product(product_id: int, name: str, price: str | Decimal, stock: int) -> bool:
    """改：按 ID 更新名称、价格和库存，返回是否匹配到商品。"""
    validate_id(product_id)
    values = validate_product(name, price, stock)
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE products SET name = %s, price = %s, stock = %s WHERE id = %s",
            (*values, product_id),
        )
        return cursor.rowcount > 0


def delete_product(product_id: int) -> bool:
    """删：只删除指定 ID，返回是否删除到商品。"""
    validate_id(product_id)
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        return cursor.rowcount > 0
