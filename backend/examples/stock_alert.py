"""复用本地 MySQL，通过依赖注入查询低库存商品并计算补货建议。"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Annotated, Protocol

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import DbSession, get_current_user
from app.models import Product
from app.routers import auth


class ProductReader(Protocol):
    """业务服务需要的查询能力；实现此方法即可，无需继承。"""

    def find_low_stock(self, threshold: int, limit: int) -> Sequence[Product]: ...


class SqlAlchemyProductRepository:
    def __init__(self, db: Session):
        # 会话由外部提供，查询层不负责创建或关闭连接。
        self.db = db

    def find_low_stock(self, threshold: int, limit: int) -> Sequence[Product]:
        statement = (
            select(Product)
            .where(Product.status == "active", Product.stock <= threshold)
            .order_by(Product.stock, Product.id)
            .limit(limit)
        )
        return self.db.scalars(statement).all()


@dataclass(frozen=True)
class StockAlert:
    product_id: int
    sku: str
    name: str
    stock: int
    suggested_quantity: int


class StockAlertService:
    def __init__(self, repository: ProductReader):
        # 服务依赖查询能力，既可以注入 MySQL 实现，也可以注入测试替身。
        self.repository = repository

    def suggest(
        self, *, threshold: int = 10, target_stock: int = 30, limit: int = 20
    ) -> list[StockAlert]:
        if threshold < 0:
            raise ValueError("库存预警阈值不能为负数")
        if target_stock <= threshold:
            raise ValueError("补货目标库存必须大于预警阈值")
        if not 1 <= limit <= 100:
            raise ValueError("查询数量必须在 1 到 100 之间")

        return [
            StockAlert(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                stock=product.stock,
                suggested_quantity=target_stock - product.stock,
            )
            for product in self.repository.find_low_stock(threshold, limit)
        ]


def get_product_repository(db: DbSession) -> SqlAlchemyProductRepository:
    return SqlAlchemyProductRepository(db)


def get_stock_alert_service(
    repository: Annotated[SqlAlchemyProductRepository, Depends(get_product_repository)],
) -> StockAlertService:
    return StockAlertService(repository)


# 独立示例应用，启动时复用项目现有的登录接口和数据库依赖。
app = FastAPI(title="Goodstock 库存预警依赖注入案例")
app.include_router(auth.router)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "数据库暂时不可用"})


@app.get(
    "/api/examples/stock-alerts",
    response_model=list[StockAlert],
    dependencies=[Depends(get_current_user)],
    summary="查询低库存的在售商品，计算补货建议",
)
def stock_alerts(
    service: Annotated[StockAlertService, Depends(get_stock_alert_service)],
    threshold: Annotated[int, Query(ge=0)] = 10,
    target_stock: Annotated[int, Query(ge=1)] = 30,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    try:
        return service.suggest(threshold=threshold, target_stock=target_stock, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=10, help="库存预警阈值，默认 10")
    parser.add_argument("--target-stock", type=int, default=30, help="补货目标库存，默认 30")
    parser.add_argument("--limit", type=int, default=20, help="最多查询多少条，范围 1 到 100")
    args = parser.parse_args()

    try:
        # 普通 Python 程序由入口手动组装依赖，with 负责会话的关闭。
        with SessionLocal() as db:
            repository = SqlAlchemyProductRepository(db)
            service = StockAlertService(repository)
            alerts = service.suggest(
                threshold=args.threshold, target_stock=args.target_stock, limit=args.limit
            )
    except ValueError as exc:
        parser.error(str(exc))
    except SQLAlchemyError:
        parser.exit(1, "数据库查询失败，请检查本机 MySQL 和 backend/.env 配置。\n")

    print(json.dumps([asdict(alert) for alert in alerts], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
