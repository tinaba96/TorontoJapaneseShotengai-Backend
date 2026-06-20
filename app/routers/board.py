from fastapi import APIRouter, Depends, status
from typing import List, Optional

from ..models.board import (
    BoardPostCreate,
    BoardPostSummary,
    BoardPostDetail,
    CommentCreate,
    CommentOut,
    ReactionRequest,
    ReactionState,
)
from ..crud.board import BoardCRUD
from ..core.security import get_current_user, get_optional_user
from ..core.email import admin_emails

router = APIRouter(prefix="/board", tags=["board"])


def _is_admin(user) -> bool:
    return bool(user and user.email.lower() in admin_emails())


# ----- Posts -------------------------------------------------------------
@router.get("/posts", response_model=List[BoardPostSummary])
async def list_posts():
    """公開: 投稿一覧（新着順・コメント数/リアクション数つき）。"""
    return await BoardCRUD.list_posts()


@router.post("/posts", response_model=BoardPostDetail, status_code=status.HTTP_201_CREATED)
async def create_post(post: BoardPostCreate, current_user=Depends(get_current_user)):
    """投稿作成（ログイン必須）。表示名はニックネーム or「匿名」。実名は出さない。"""
    display = (post.display_name or "").strip() or "匿名"
    pid = await BoardCRUD.create_post(
        post.title, post.body, display, current_user.email
    )
    return await BoardCRUD.get_post(pid, current_user.email, _is_admin(current_user))


@router.get("/posts/{post_id}", response_model=BoardPostDetail)
async def get_post(post_id: str, current_user=Depends(get_optional_user)):
    """公開: 投稿詳細（本文＋コメント＋リアクション）。ログイン時は自分の反応/削除可否も返す。"""
    email = current_user.email if current_user else None
    return await BoardCRUD.get_post(post_id, email, _is_admin(current_user))


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, current_user=Depends(get_current_user)):
    """投稿削除（投稿者本人 or admin）。"""
    await BoardCRUD.delete_post(post_id, current_user.email, _is_admin(current_user))
    return None


# ----- Comments ----------------------------------------------------------
@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(post_id: str, comment: CommentCreate, current_user=Depends(get_current_user)):
    """コメント作成（ログイン必須）。表示名はニックネーム or「匿名」。実名は出さない。"""
    display = (comment.display_name or "").strip() or "匿名"
    return await BoardCRUD.add_comment(
        post_id, comment.body, display, current_user.email
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str, current_user=Depends(get_current_user)):
    """コメント削除（投稿者本人 or admin）。"""
    await BoardCRUD.delete_comment(comment_id, current_user.email, _is_admin(current_user))
    return None


# ----- Reactions ---------------------------------------------------------
@router.post("/posts/{post_id}/react", response_model=ReactionState)
async def react_post(post_id: str, req: ReactionRequest, current_user=Depends(get_current_user)):
    """投稿への絵文字リアクションをトグル（ログイン必須）。"""
    return await BoardCRUD.toggle_reaction("BoardPost", post_id, req.emoji, current_user.email)


@router.post("/comments/{comment_id}/react", response_model=ReactionState)
async def react_comment(comment_id: str, req: ReactionRequest, current_user=Depends(get_current_user)):
    """コメントへの絵文字リアクションをトグル（ログイン必須）。"""
    return await BoardCRUD.toggle_reaction("Comment", comment_id, req.emoji, current_user.email)
