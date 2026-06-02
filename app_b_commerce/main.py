from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Commerce Product API", version="1.0.0")


class SortBy(str, Enum):
    price = "price"
    name = "name"
    rating = "rating"


class Variant(BaseModel):
    id: int
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    stock: int
    price_delta: float = 0.0


class Product(BaseModel):
    id: int
    name: str
    brand: str
    category_id: int
    price: float
    currency: str = "USD"
    stock: int
    attributes: dict = {}
    variants: list[Variant] = []
    tags: list[str] = []
    rating: float = 0.0


_products: dict[int, Product] = {}
_reviews: dict[int, list[dict]] = {}


@app.get("/health")
def health():
    return {"status": "ok", "products": len(_products)}


@app.get("/products")
def list_products(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    in_stock: Optional[bool] = None,
    tag: Optional[str] = None,
    sort_by: SortBy = SortBy.name,
    order: str = "asc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items = list(_products.values())
    if q:
        items = [p for p in items if q.lower() in p.name.lower()]
    if category_id is not None:
        items = [p for p in items if p.category_id == category_id]
    if brand:
        items = [p for p in items if p.brand == brand]
    if min_price is not None:
        items = [p for p in items if p.price >= min_price]
    if max_price is not None:
        items = [p for p in items if p.price <= max_price]
    if in_stock is not None:
        items = [p for p in items if (p.stock > 0) == in_stock]
    if tag:
        items = [p for p in items if tag in p.tags]

    items.sort(key=lambda p: getattr(p, sort_by.value), reverse=(order == "desc"))

    start = (page - 1) * page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "results": items[start:start + page_size],
    }


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    return p


@app.get("/products/{product_id}/variants", response_model=list[Variant])
def list_variants(product_id: int):
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    return p.variants


@app.get("/products/{product_id}/variants/{variant_id}", response_model=Variant)
def get_variant(product_id: int, variant_id: int):
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    for v in p.variants:
        if v.id == variant_id:
            return v
    raise HTTPException(status_code=404, detail="variant not found")


@app.get("/items/{item_id}/v1/status")
def item_status(item_id: int, include_variants: bool = False):
    p = _products.get(item_id)
    if not p:
        raise HTTPException(status_code=404, detail="item not found")
    payload = {
        "item_id": item_id,
        "available": p.stock > 0,
        "stock": p.stock,
    }
    if include_variants:
        payload["variants"] = [
            {"id": v.id, "sku": v.sku, "available": v.stock > 0} for v in p.variants
        ]
    return payload


@app.get("/products/{product_id}/reviews")
def list_reviews(
    product_id: int,
    min_rating: int = Query(default=1, ge=1, le=5),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    reviews = _reviews.get(product_id, [])
    filtered = [r for r in reviews if r["rating"] >= min_rating]
    start = (page - 1) * page_size
    return {
        "product_id": product_id,
        "total": len(filtered),
        "results": filtered[start:start + page_size],
    }


@app.get("/categories/{category_id}/products", response_model=list[Product])
def products_by_category(
    category_id: int,
    in_stock: Optional[bool] = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    items = [p for p in _products.values() if p.category_id == category_id]
    if in_stock is not None:
        items = [p for p in items if (p.stock > 0) == in_stock]
    return items[:limit]


@app.get("/products/{product_id}/related", response_model=list[Product])
def related_products(product_id: int, limit: int = 5):
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    related = [
        x for x in _products.values()
        if x.category_id == p.category_id and x.id != product_id
    ]
    return related[:limit]


def _seed():
    _products[1] = Product(
        id=1, name="Wireless Mouse", brand="Logi", category_id=10,
        price=29.99, stock=120,
        attributes={"dpi": 1600, "wireless": True},
        variants=[
            Variant(id=1, sku="MOUSE-BLK", color="black", stock=80),
            Variant(id=2, sku="MOUSE-WHT", color="white", stock=40, price_delta=2.0),
        ],
        tags=["accessory", "office"], rating=4.3,
    )
    _products[2] = Product(
        id=2, name="Mechanical Keyboard", brand="Logi", category_id=10,
        price=89.0, stock=0,
        attributes={"switch": "brown", "layout": "tkl"},
        variants=[Variant(id=3, sku="KB-BRN", color="grey", stock=0)],
        tags=["accessory"], rating=4.7,
    )
    _products[3] = Product(
        id=3, name="USB-C Cable", brand="Anker", category_id=11,
        price=12.5, stock=300, tags=["cable"], rating=4.1,
    )
    _reviews[1] = [
        {"id": 1, "rating": 5, "body": "great"},
        {"id": 2, "rating": 3, "body": "ok"},
    ]
    _reviews[2] = [{"id": 3, "rating": 5, "body": "love the switches"}]


_seed()
