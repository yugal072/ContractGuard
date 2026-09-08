from fastapi import FastAPI, HTTPException
from resource.api.models import User, CreateUserRequest, Product, CreateProductRequest

app = FastAPI(title="ContractGuard Test API", version="1.0.0")

users_db: dict[int, User] = {
    1: User(id=1, name="Alice", email="alice@example.com", role="admin"),
    2: User(id=2, name="Bob", email="bob@example.com", role="user"),
}

products_db: dict[int, Product] = {
    1: Product(id=1, name="Laptop", price=999.99, category="electronics"),
    2: Product(id=2, name="Mouse", price=29.99, category="accessories"),
}

next_user_id = 3
next_product_id = 3


@app.get("/users", response_model=list[User])
def list_users():
    return list(users_db.values())


@app.post("/users", response_model=User, status_code=201)
def create_user(body: CreateUserRequest, master: int):
    global next_user_id
    user = User(id=next_user_id, name=body.name, email=body.email)
    users_db[next_user_id] = user
    next_user_id += 1
    return user, master


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@app.delete("/users", status_code=204)
def delete_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(404, "User not found")
    del users_db[user_id]


@app.get("/products", response_model=list[Product])
def list_products():
    return list(products_db.values())


@app.post("/products", response_model=Product, status_code=201)
def create_product(body: CreateProductRequest):
    global next_product_id
    product = Product(id=next_product_id, name=body.name, price=body.price, category=body.category)
    products_db[next_product_id] = product
    next_product_id += 1
    return product


@app.get("/products/{user_id}", response_model=Product)
def get_product(product_id: int):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product