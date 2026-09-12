from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=10)
    price: float = Field(gt=0)
    category: str = Field(min_length=2, max_length=80)
    stock: int = Field(ge=0)
    image_url: str = Field(min_length=5)

class ProductCreate(ProductBase): pass
class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=160)
    description: str | None = Field(None, min_length=10)
    price: float | None = Field(None, gt=0)
    category: str | None = Field(None, min_length=2, max_length=80)
    stock: int | None = Field(None, ge=0)
    image_url: str | None = Field(None, min_length=5)

class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=50)

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_address: str = Field(min_length=5, max_length=300)
    items: list[OrderItemCreate] = Field(min_length=1)

class OrderItemRead(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class OrderRead(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_address: str
    total_amount: float
    status: str
    created_at: datetime
    items: list[OrderItemRead]

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    answer: str
    products: list[ProductRead] = []
    suggestions: list[str] = []

