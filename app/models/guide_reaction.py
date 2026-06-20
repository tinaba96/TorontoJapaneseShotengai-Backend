from pydantic import BaseModel

# ガイド記事の good / bad リアクション（匿名・カウントのみ）
ALLOWED_TYPES = ["good", "bad"]


class GuideReactionState(BaseModel):
    slug: str
    good: int = 0
    bad: int = 0


class GuideReactionRequest(BaseModel):
    type: str  # "good" | "bad"
