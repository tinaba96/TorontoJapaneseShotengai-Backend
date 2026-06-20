from app.crud.database import db
from fastapi import HTTPException
from app.models.guide_reaction import GuideReactionState, ALLOWED_TYPES


class GuideReactionCRUD:
    """ガイド記事(slug)ごとの good/bad カウント。匿名・累計のみ。"""

    @staticmethod
    async def get_counts(slug: str) -> GuideReactionState:
        slug = (slug or "").strip()
        if not slug:
            raise HTTPException(status_code=400, detail="slug is required.")
        with db.get_session() as session:
            rec = session.run(
                """
                MATCH (g:GuideReaction {slug: $slug})
                RETURN coalesce(g.good, 0) AS good, coalesce(g.bad, 0) AS bad
                """,
                slug=slug,
            ).single()
            if not rec:
                return GuideReactionState(slug=slug, good=0, bad=0)
            return GuideReactionState(slug=slug, good=rec["good"], bad=rec["bad"])

    @staticmethod
    async def react(slug: str, rtype: str) -> GuideReactionState:
        slug = (slug or "").strip()
        if not slug:
            raise HTTPException(status_code=400, detail="slug is required.")
        if rtype not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="type must be 'good' or 'bad'.")
        field = "good" if rtype == "good" else "bad"
        with db.get_session() as session:
            rec = session.run(
                f"""
                MERGE (g:GuideReaction {{slug: $slug}})
                ON CREATE SET g.good = 0, g.bad = 0
                SET g.{field} = coalesce(g.{field}, 0) + 1
                RETURN coalesce(g.good, 0) AS good, coalesce(g.bad, 0) AS bad
                """,
                slug=slug,
            ).single()
            if not rec:
                raise HTTPException(status_code=500, detail="Failed to record reaction.")
            return GuideReactionState(slug=slug, good=rec["good"], bad=rec["bad"])
