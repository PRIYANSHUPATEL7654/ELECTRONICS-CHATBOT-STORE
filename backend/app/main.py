from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from .ai import answer_chat
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Order, OrderItem, Product
from .schemas import (
    ChatRequest,
    ChatResponse,
    OrderCreate,
    OrderItemRead,
    OrderRead,
    OrderStatusUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from .seed import seed_products


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_products(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Electronics Chatbot Store API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )


def product_query(
    db: Session,
    search: str | None = None,
    category: str | None = None,
) -> list[Product]:
    stmt = select(Product).order_by(Product.id)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Product.category.ilike(term),
            )
        )
    if category:
        stmt = stmt.where(Product.category.ilike(category.strip()))
    return list(db.scalars(stmt).all())


def normalized_order_status(order: Order) -> str:
    # Existing databases may contain the original "placed" status.
    # Treat it as pending after the status-management upgrade.
    return "completed" if order.status == "completed" else "pending"


def order_to_read(order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_address=order.customer_address,
        total_amount=order.total_amount,
        status=normalized_order_status(order),
        created_at=order.created_at,
        items=[
            OrderItemRead(
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=round(item.unit_price * item.quantity, 2),
            )
            for item in order.items
        ],
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "electronics-chatbot-store"}


@app.get("/products", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    search: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=80),
):
    return product_query(db, search, category)


@app.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@app.post(
    "/products",
    response_model=ProductRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.put(
    "/products/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_admin)],
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted", "id": product_id}


@app.post("/orders", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    ids = [item.product_id for item in payload.items]
    products = {
        product.id: product
        for product in db.scalars(select(Product).where(Product.id.in_(ids))).all()
    }
    if len(products) != len(set(ids)):
        raise HTTPException(400, "One or more products do not exist")

    order = Order(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_address=payload.customer_address,
        total_amount=0,
        status="pending",
    )
    total = 0.0
    for item in payload.items:
        product = products[item.product_id]
        if product.stock < item.quantity:
            raise HTTPException(
                400,
                f"Not enough stock for {product.name}; available: {product.stock}",
            )
        product.stock -= item.quantity
        total += product.price * item.quantity
        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
            )
        )

    order.total_amount = round(total, 2)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order_to_read(order)


@app.get(
    "/orders",
    response_model=list[OrderRead],
    dependencies=[Depends(require_admin)],
)
def list_orders(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(
        None,
        alias="status",
        pattern="^(pending|completed)$",
    ),
):
    # Pending orders appear first. Within each status, newest orders appear first.
    priority = case((Order.status == "completed", 1), else_=0)
    stmt = select(Order)
    if status_filter == "pending":
        stmt = stmt.where(Order.status != "completed")
    elif status_filter == "completed":
        stmt = stmt.where(Order.status == "completed")
    orders = db.scalars(stmt.order_by(priority, Order.created_at.desc())).all()
    return [order_to_read(order) for order in orders]


# NEW: mark an order as pending or completed.
@app.patch(
    "/orders/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_admin)],
)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order_to_read(order)


# NEW: delete an order. Pending order quantities return to stock.
@app.delete(
    "/orders/{order_id}",
    dependencies=[Depends(require_admin)],
)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if normalized_order_status(order) == "pending":
        for item in order.items:
            item.product.stock += item.quantity
    db.delete(order)
    db.commit()
    return {"message": "Order deleted", "id": order_id}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    answer, product_ids = answer_chat(db, payload.message)
    products = [db.get(Product, product_id) for product_id in product_ids]
    return ChatResponse(
        answer=answer,
        products=[product for product in products if product],
        suggestions=[
            "Show budget options",
            "What laptops are in stock?",
            "Compare two laptops",
        ],
    )
