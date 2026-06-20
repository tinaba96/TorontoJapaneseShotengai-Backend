from app.crud.database import db
from fastapi import HTTPException, status
from app.models.board import (
    BoardPostSummary,
    BoardPostDetail,
    CommentOut,
    ReactionCount,
    ReactionState,
    ALLOWED_EMOJIS,
)
from typing import List, Optional
from uuid import uuid4

# リアクション対象として許可するラベル（内部値のみ・ユーザー入力ではない）
_POST_LABEL = "BoardPost"
_COMMENT_LABEL = "Comment"


def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.to_native().replace(microsecond=0).isoformat()
    except Exception:
        return str(dt)


def _reactions_for(session, label: str, target_id: str) -> List[ReactionCount]:
    res = session.run(
        f"MATCH (t:{label} {{id: $id}})<-[r:REACTED]-() "
        f"RETURN r.emoji AS emoji, count(*) AS c ORDER BY c DESC",
        id=target_id,
    )
    return [ReactionCount(emoji=row["emoji"], count=row["c"]) for row in res]


def _my_reactions(session, label: str, target_id: str, email: Optional[str]) -> List[str]:
    if not email:
        return []
    res = session.run(
        f"MATCH (:User {{email: $e}})-[r:REACTED]->(t:{label} {{id: $id}}) "
        f"RETURN collect(r.emoji) AS es",
        e=email, id=target_id,
    ).single()
    return res["es"] if res and res["es"] else []


class BoardCRUD:
    # ===== Posts =====
    @staticmethod
    async def create_post(title: str, body: str, author_name: str, author_email: str) -> str:
        title = (title or "").strip()
        body = (body or "").strip()
        if not title or not body:
            raise HTTPException(status_code=400, detail="Title and body are required.")
        with db.get_session() as session:
            pid = str(uuid4())
            rec = session.run(
                """
                CREATE (p:BoardPost {
                    id: $id, title: $title, body: $body,
                    author_name: $name, author_email: $email,
                    created_at: datetime()
                })
                RETURN p.id AS id
                """,
                id=pid, title=title, body=body, name=author_name, email=author_email,
            ).single()
            if not rec:
                raise HTTPException(status_code=500, detail="Failed to create post.")
            return pid

    @staticmethod
    async def list_posts() -> List[BoardPostSummary]:
        with db.get_session() as session:
            res = session.run(
                """
                MATCH (p:BoardPost)
                OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
                OPTIONAL MATCH (p)<-[r:REACTED]-()
                RETURN p, count(DISTINCT c) AS comment_count, count(DISTINCT r) AS reaction_total
                ORDER BY p.created_at DESC
                """
            )
            out = []
            for row in res:
                p = row["p"]
                out.append(
                    BoardPostSummary(
                        id=p["id"],
                        title=p["title"],
                        author_name=p.get("author_name") or "匿名",
                        created_at=_iso(p["created_at"]),
                        comment_count=row["comment_count"],
                        reaction_total=row["reaction_total"],
                    )
                )
            return out

    @staticmethod
    async def get_post(post_id: str, email: Optional[str], is_admin: bool) -> BoardPostDetail:
        with db.get_session() as session:
            rec = session.run(
                "MATCH (p:BoardPost {id: $id}) RETURN p", id=post_id
            ).single()
            if not rec:
                raise HTTPException(status_code=404, detail="Post not found.")
            p = rec["p"]

            comments_res = session.run(
                """
                MATCH (p:BoardPost {id: $id})-[:HAS_COMMENT]->(c:Comment)
                RETURN c ORDER BY c.created_at ASC
                """,
                id=post_id,
            )
            comments = []
            for crow in comments_res:
                c = crow["c"]
                c_email = c.get("author_email")
                comments.append(
                    CommentOut(
                        id=c["id"],
                        body=c["body"],
                        author_name=c.get("author_name") or "匿名",
                        created_at=_iso(c["created_at"]),
                        reactions=_reactions_for(session, _COMMENT_LABEL, c["id"]),
                        my_reactions=_my_reactions(session, _COMMENT_LABEL, c["id"], email),
                        can_delete=bool(is_admin or (email and c_email and email == c_email)),
                    )
                )

            p_email = p.get("author_email")
            return BoardPostDetail(
                id=p["id"],
                title=p["title"],
                body=p["body"],
                author_name=p.get("author_name") or "匿名",
                created_at=_iso(p["created_at"]),
                reactions=_reactions_for(session, _POST_LABEL, post_id),
                my_reactions=_my_reactions(session, _POST_LABEL, post_id, email),
                can_delete=bool(is_admin or (email and p_email and email == p_email)),
                comments=comments,
            )

    @staticmethod
    async def delete_post(post_id: str, email: str, is_admin: bool) -> None:
        with db.get_session() as session:
            rec = session.run(
                "MATCH (p:BoardPost {id: $id}) RETURN p.author_email AS owner", id=post_id
            ).single()
            if not rec:
                raise HTTPException(status_code=404, detail="Post not found.")
            if not (is_admin or rec["owner"] == email):
                raise HTTPException(status_code=403, detail="Not allowed.")
            session.run(
                """
                MATCH (p:BoardPost {id: $id})
                OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
                DETACH DELETE c, p
                """,
                id=post_id,
            )

    # ===== Comments =====
    @staticmethod
    async def add_comment(post_id: str, body: str, author_name: str, author_email: str) -> CommentOut:
        body = (body or "").strip()
        if not body:
            raise HTTPException(status_code=400, detail="Comment body is required.")
        with db.get_session() as session:
            if not session.run("MATCH (p:BoardPost {id: $id}) RETURN p", id=post_id).single():
                raise HTTPException(status_code=404, detail="Post not found.")
            cid = str(uuid4())
            rec = session.run(
                """
                MATCH (p:BoardPost {id: $pid})
                CREATE (c:Comment {
                    id: $id, post_id: $pid, body: $body,
                    author_name: $name, author_email: $email,
                    created_at: datetime()
                })
                CREATE (p)-[:HAS_COMMENT]->(c)
                RETURN c
                """,
                pid=post_id, id=cid, body=body, name=author_name, email=author_email,
            ).single()
            c = rec["c"]
            return CommentOut(
                id=c["id"],
                body=c["body"],
                author_name=c.get("author_name") or "匿名",
                created_at=_iso(c["created_at"]),
                reactions=[],
                my_reactions=[],
                can_delete=True,
            )

    @staticmethod
    async def delete_comment(comment_id: str, email: str, is_admin: bool) -> None:
        with db.get_session() as session:
            rec = session.run(
                "MATCH (c:Comment {id: $id}) RETURN c.author_email AS owner", id=comment_id
            ).single()
            if not rec:
                raise HTTPException(status_code=404, detail="Comment not found.")
            if not (is_admin or rec["owner"] == email):
                raise HTTPException(status_code=403, detail="Not allowed.")
            session.run("MATCH (c:Comment {id: $id}) DETACH DELETE c", id=comment_id)

    # ===== Reactions =====
    @staticmethod
    async def toggle_reaction(label: str, target_id: str, emoji: str, email: str) -> ReactionState:
        if emoji not in ALLOWED_EMOJIS:
            raise HTTPException(status_code=400, detail="Emoji not allowed.")
        if label not in (_POST_LABEL, _COMMENT_LABEL):
            raise HTTPException(status_code=400, detail="Invalid target.")
        with db.get_session() as session:
            if not session.run(
                f"MATCH (t:{label} {{id: $id}}) RETURN t", id=target_id
            ).single():
                raise HTTPException(status_code=404, detail="Target not found.")

            exists = session.run(
                f"MATCH (:User {{email: $e}})-[r:REACTED {{emoji: $em}}]->(t:{label} {{id: $id}}) "
                f"RETURN r LIMIT 1",
                e=email, em=emoji, id=target_id,
            ).single()

            if exists:
                session.run(
                    f"MATCH (:User {{email: $e}})-[r:REACTED {{emoji: $em}}]->(t:{label} {{id: $id}}) "
                    f"DELETE r",
                    e=email, em=emoji, id=target_id,
                )
            else:
                session.run(
                    f"""
                    MATCH (t:{label} {{id: $id}})
                    MERGE (u:User {{email: $e}})
                    MERGE (u)-[:REACTED {{emoji: $em}}]->(t)
                    """,
                    e=email, em=emoji, id=target_id,
                )

            return ReactionState(
                reactions=_reactions_for(session, label, target_id),
                my_reactions=_my_reactions(session, label, target_id, email),
            )
