from typing import List, Optional
from pydantic import BaseModel

# リアクションで使える絵文字（固定）
ALLOWED_EMOJIS = ["👍", "❤️", "😂", "😮", "🎉", "🙏"]


class BoardPostCreate(BaseModel):
    title: str
    body: str
    display_name: Optional[str] = None  # 表示名（空なら「匿名」）


class CommentCreate(BaseModel):
    body: str
    display_name: Optional[str] = None  # 表示名（空なら「匿名」）


class ReactionRequest(BaseModel):
    emoji: str


class ReactionCount(BaseModel):
    emoji: str
    count: int


class ReactionState(BaseModel):
    reactions: List[ReactionCount] = []
    my_reactions: List[str] = []


class CommentOut(BaseModel):
    id: str
    body: str
    author_name: str
    created_at: str
    reactions: List[ReactionCount] = []
    my_reactions: List[str] = []
    can_delete: bool = False


class BoardPostSummary(BaseModel):
    id: str
    title: str
    author_name: str
    created_at: str
    comment_count: int = 0
    reaction_total: int = 0


class BoardPostDetail(BaseModel):
    id: str
    title: str
    body: str
    author_name: str
    created_at: str
    reactions: List[ReactionCount] = []
    my_reactions: List[str] = []
    can_delete: bool = False
    comments: List[CommentOut] = []
