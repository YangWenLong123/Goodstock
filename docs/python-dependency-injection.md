# 用本机商品数据库理解 Python 依赖注入

## 这个案例解决什么问题

Goodstock 已经使用 MySQL、SQLAlchemy 和 FastAPI，并有 `products` 商品表。本例复用
`backend/.env` 的连接配置和现有 `Product` 模型，查询需要补货的商品。

完整代码：[`backend/examples/stock_alert.py`](../backend/examples/stock_alert.py)。

业务规则：

- 只考虑 `status = 'active'` 的在售商品。
- `stock <= threshold` 时触发预警，默认阈值为 10，包含库存正好等于 10 的商品。
- 按库存从少到多、商品 ID 从小到大排序，默认最多返回 20 条，最多允许 100 条。
- 建议补货数量为 `target_stock - stock`，默认补到 30 件。
- 目标库存必须大于预警阈值；结果只是一份建议，不执行补货或更新库存。

例如某商品库存为 6，阈值为 10，目标库存为 30，建议补货数量就是 24。

## 先连接本机 MySQL 跑一遍

在项目根目录执行：

```bash
cd backend
.venv/bin/python -m examples.stock_alert
```

自定义阈值、目标库存和返回数量：

```bash
.venv/bin/python -m examples.stock_alert --threshold 5 --target-stock 20 --limit 5
```

输出是 JSON 数组，每条包含 `product_id`、`sku`、`name`、`stock` 和
`suggested_quantity`。没有符合条件的商品时返回 `[]`。

脚本使用现有数据库，只执行查询，不创建表、不插入演示商品、不提交库存修改。
数据库连接失败时，先确认本机 MySQL 已启动、`backend/.env` 的数据库配置正确。

## 第一步：把数据库会话注入查询层

```python
class SqlAlchemyProductRepository:
    def __init__(self, db: Session):
        self.db = db
```

`db` 是外部传进来的会话。查询层用它执行 SQL，但不在内部创建连接，也不负责关闭会话。

`find_low_stock()` 使用现有 `Product` 模型，把查询条件、排序和条数限制交给数据库。

## 第二步：把查询能力注入业务服务

```python
class StockAlertService:
    def __init__(self, repository: ProductReader):
        self.repository = repository
```

`ProductReader` 是 `Protocol`，约定依赖需要提供 `find_low_stock()` 方法。
`SqlAlchemyProductRepository` 实现了该方法，所以无需显式继承就可以作为这个依赖。
本例为便于理解，查询接口直接返回现有 `Product` 模型。

业务服务负责校验参数、计算补货数量，不负责选择数据库连接方式。

## 第三步：在程序入口组装依赖

```python
with SessionLocal() as db:
    repository = SqlAlchemyProductRepository(db)
    service = StockAlertService(repository)
    alerts = service.suggest(threshold=10, target_stock=30)
```

这里发生了两次构造函数注入：先把 `db` 传给查询层，再把查询层传给业务服务。
离开 `with` 时，会话关闭，使用的连接归还连接池。

依赖关系是：

```text
程序入口
  └─ StockAlertService（业务服务）
       └─ SqlAlchemyProductRepository（查询层）
            └─ Session（数据库会话）
                 └─ 本机 MySQL 的 products 表
```

## 第四步：让 FastAPI 自动组装同一组依赖

同一文件也提供了一个独立的 FastAPI 示例应用。在 `backend` 目录运行：

```bash
.venv/bin/python -m uvicorn examples.stock_alert:app --host 127.0.0.1 --port 8002
```

打开 <http://127.0.0.1:8002/docs>，点击 **Authorize**，填写已有登录账号的用户名和密码。
授权后调用 `GET /api/examples/stock-alerts`，可以修改 `threshold`、`target_stock` 和
`limit` 参数。示例应用复用现有认证逻辑，无有效 Token 时返回 401。

关键代码是：

```python
def get_product_repository(db: DbSession) -> SqlAlchemyProductRepository:
    return SqlAlchemyProductRepository(db)


def get_stock_alert_service(
    repository: Annotated[SqlAlchemyProductRepository, Depends(get_product_repository)],
) -> StockAlertService:
    return StockAlertService(repository)
```

接口声明 `Depends(get_stock_alert_service)` 后，FastAPI 会依次解析：

```text
stock_alerts()
  → get_stock_alert_service()
  → get_product_repository()
  → get_db()（通过 DbSession 引用）
  → SessionLocal()
```

`DbSession` 已在 `backend/app/dependencies.py` 定义：

```python
DbSession = Annotated[Session, Depends(get_db)]
```

`get_db()` 已在 `backend/app/database.py` 实现：

```python
def get_db():
    with SessionLocal() as session:
        yield session
```

FastAPI 获取 `yield` 产生的会话并注入后续依赖，在依赖清理时关闭会话。
认证和商品查询都引用同一个 `get_db`，默认会在同一次请求内复用它的结果。

`Depends` 的自动解析发生在 FastAPI 处理请求时。普通脚本直接调用服务时，需要像
`main()` 那样手动传入依赖。

## 第五步：不连接 MySQL，也能验证业务规则

在 `backend` 目录执行 `.venv/bin/python`，然后输入：

```python
from app.models import Product
from examples.stock_alert import StockAlertService


class FakeProductRepository:
    def find_low_stock(self, threshold, limit):
        products = [
            Product(id=1, sku="DEMO-001", name="演示耳机", stock=6, status="active")
        ]
        return [p for p in products if p.stock <= threshold][:limit]


service = StockAlertService(FakeProductRepository())
alerts = service.suggest(threshold=10, target_stock=30)
assert alerts[0].suggested_quantity == 24
```

这里的 `Product` 只是内存中的 Python 对象，没有加入会话或写入数据库。
替换查询依赖后，业务服务仍然执行同一份补货计算逻辑。

测试 HTTP 接口时，也可以通过
`app.dependency_overrides[get_product_repository]` 替换查询依赖；项目现有的
`backend/tests/conftest.py` 则演示了覆盖 `get_db`、改用内存 SQLite 的方式。
