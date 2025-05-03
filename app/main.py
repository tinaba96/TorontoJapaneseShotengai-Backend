from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # 一旦ローカルのみ対応
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)