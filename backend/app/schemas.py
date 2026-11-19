from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["数码配件", "办公文具", "生活用品", "服饰箱包"]
ProductStatus = Literal["active", "inactive"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    display_name: str


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class ProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    category: Category
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0, le=1_000_000, strict=True)
    status: ProductStatus = "active"
    description: str = Field(default="", max_length=2000)

    @field_validator("sku", mode="before")
    @classmethod
    def normalize_sku(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class ProductRead(ProductInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int


class ProductStats(BaseModel):
    total: int
    active: int
    low_stock: int
    inventory_value: Decimal
