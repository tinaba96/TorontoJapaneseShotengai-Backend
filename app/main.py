from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users  # 必要に応じてモジュール名を変更
from dotenv import load_dotenv

load_dotenv()  # 環境変数（.envファイル）の読み込み

app = FastAPI()

# CORSのミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 必要に応じて変更
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# usersルーターを登録
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, tags=["users"])  # プレフィックスを削除

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}