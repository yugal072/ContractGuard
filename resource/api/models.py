from pydantic import BaseModel, EmailStr
from typing import Optional


class User(BaseModel):
    id: int
    name: str
    email: str
    role: str = "user"


class CreateUserRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


class Product(BaseModel):
    id: int
    name: str
    price: float
    category: Optional[str] = None
    in_stock: bool = True


class CreateProductRequest(BaseModel):
    name: str
    price: float
    category: Optional[str] = None