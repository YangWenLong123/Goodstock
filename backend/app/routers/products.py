from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError

from app.dependencies import DbSession, get_current_user
from app.models import Product
from app.schemas import (
    Category,
    ProductInput,
    ProductPage,
    ProductRead,
    ProductStats,
    ProductStatus,
)

# 在整个路由组执行鉴权，覆盖查询、新增、修改、删除及统计接口。
router = APIRouter(
    prefix="/api/products", tags=["商品管理"], dependencies=[Depends(get_current_user)]
)


def find_product(product_id: int, db: DbSession) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="商品不存在或已被删除")
    return product


def save_product(product: Product, db: DbSession) -> Product:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="商品编码 SKU 已存在，请使用其他编码") from None
    db.refresh(product)
    return product


@router.get("", response_model=ProductPage, summary="分页查询商品，支持搜索和筛选")
def list_products(
    db: DbSession,
    q: str = Query(default="", max_length=100),
    category: Category | None = None,
    status: ProductStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=100),
):
    conditions = []
    if keyword := q.strip():
        conditions.append(
            or_(
                Product.name.contains(keyword, autoescape=True),
                Product.sku.contains(keyword, autoescape=True),
            )
        )
    if category:
        conditions.append(Product.category == category)
    if status:
        conditions.append(Product.status == status)
    total = db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    items = db.scalars(
        select(Product)
        .where(*conditions)
        .order_by(Product.updated_at.desc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ProductPage(items=items, total=total, page=page, page_size=page_size)


# 固定路径需定义在 /{product_id} 前面，避免 stats 被当成商品 ID。
@router.get("/stats", response_model=ProductStats, summary="查看全部商品的统计")
def product_stats(db: DbSession):
    row = db.execute(
        select(
            func.count(Product.id),
            func.sum(case((Product.status == "active", 1), else_=0)),
            func.sum(case(((Product.status == "active") & (Product.stock <= 10), 1), else_=0)),
            func.sum(Product.price * Product.stock),
        )
    ).one()
    return ProductStats(
        total=row[0],
        active=row[1] or 0,
        low_stock=row[2] or 0,
        inventory_value=row[3] or Decimal("0.00"),
    )


@router.get("/{product_id}", response_model=ProductRead, summary="查询单个商品")
def get_product(product_id: int, db: DbSession):
    return find_product(product_id, db)


@router.post("", response_model=ProductRead, status_code=201, summary="新增商品")
def create_product(body: ProductInput, db: DbSession):
    product = Product(**body.model_dump())
    db.add(product)
    return save_product(product, db)


@router.put("/{product_id}", response_model=ProductRead, summary="修改商品的全部可编辑字段")
def update_product(product_id: int, body: ProductInput, db: DbSession):
    product = find_product(product_id, db)
    for key, value in body.model_dump().items():
        setattr(product, key, value)
    return save_product(product, db)


@router.delete("/{product_id}", status_code=204, summary="删除商品")
def delete_product(product_id: int, db: DbSession):
    db.delete(find_product(product_id, db))
    db.commit()
    return Response(status_code=204)
