from fastapi import FastAPI
from app.routers import users, auth
from app.crud.database import db

app = FastAPI(title="Toronto Japanese Shotengai API")

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(users.router, tags=["users"])


@app.on_event("startup")
async def startup_event():
    db.connect()


@app.on_event("shutdown")
async def shutdown_event():
    db.close()


@app.get("/")
async def root():
    return {"message": "Welcome to Toronto Japanese Shotengai API"}


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
