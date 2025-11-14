from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, events  # 必要に応じてモジュール名を変更
from dotenv import load_dotenv
import os

load_dotenv()  # 環境変数（.envファイル）の読み込み

app = FastAPI()

# CORSのミドルウェア設定
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, tags=["users"])
app.include_router(events.router, tags=["events"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}