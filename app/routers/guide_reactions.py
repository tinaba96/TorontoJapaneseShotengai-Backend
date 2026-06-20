from fastapi import APIRouter

from ..models.guide_reaction import GuideReactionState, GuideReactionRequest
from ..crud.guide_reaction import GuideReactionCRUD

router = APIRouter(prefix="/guide-reactions", tags=["guide-reactions"])


@router.get("/{slug}", response_model=GuideReactionState)
async def get_reactions(slug: str):
    """公開: 記事(slug)の good/bad 累計を返す。"""
    return await GuideReactionCRUD.get_counts(slug)


@router.post("/{slug}", response_model=GuideReactionState)
async def react(slug: str, req: GuideReactionRequest):
    """公開・匿名: 記事(slug)に good/bad を1票加算。連投制御はクライアント側(localStorage)。"""
    return await GuideReactionCRUD.react(slug, req.type)
