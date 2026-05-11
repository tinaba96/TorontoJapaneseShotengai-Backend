from app.crud.database import db
from fastapi import HTTPException
from app.models.news import News, NewsCreate
from typing import List, Optional
from uuid import uuid4


def _row_to_news(news_data) -> News:
    return News(
        id=news_data["id"],
        title=news_data["title"],
        content=news_data["content"],
        excerpt=news_data.get("excerpt"),
        category=news_data["category"],
        image=news_data.get("image"),
        author=news_data.get("author"),
        tags=news_data.get("tags"),
        publishDate=news_data.get("publishDate"),
        creator_id=news_data["creator_id"],
        status=news_data["status"],
        created_at=news_data["created_at"].isoformat(),
        updated_at=(
            news_data["updated_at"].isoformat()
            if news_data.get("updated_at")
            else None
        ),
    )


class NewsCRUD:
    @staticmethod
    async def create(news: NewsCreate, creator_id: str) -> News:
        with db.get_session() as session:
            news_id = str(uuid4())
            result = session.run(
                """
                CREATE (n:News {
                    id: $id,
                    title: $title,
                    content: $content,
                    excerpt: $excerpt,
                    category: $category,
                    image: $image,
                    author: $author,
                    tags: $tags,
                    publishDate: $publishDate,
                    creator_id: $creator_id,
                    status: 'published',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN n
                """,
                id=news_id,
                title=news.title,
                content=news.content,
                excerpt=news.excerpt,
                category=news.category,
                image=news.image,
                author=news.author,
                tags=news.tags,
                publishDate=news.publishDate,
                creator_id=creator_id,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create news.")

            session.run(
                """
                MATCH (u:User {id: $user_id}), (n:News {id: $news_id})
                CREATE (u)-[:CREATED]->(n)
                """,
                user_id=creator_id,
                news_id=news_id,
            )
            return _row_to_news(record["n"])

    @staticmethod
    async def get_all() -> List[News]:
        with db.get_session() as session:
            result = session.run(
                "MATCH (n:News) RETURN n ORDER BY coalesce(n.publishDate, toString(n.created_at)) DESC"
            )
            return [_row_to_news(r["n"]) for r in result]

    @staticmethod
    async def get_by_id(news_id: str) -> Optional[News]:
        with db.get_session() as session:
            result = session.run(
                "MATCH (n:News {id: $id}) RETURN n", id=news_id
            )
            record = result.single()
            return _row_to_news(record["n"]) if record else None
