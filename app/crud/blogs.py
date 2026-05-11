from app.crud.database import db
from fastapi import HTTPException
from app.models.blog import Blog, BlogCreate
from typing import List, Optional
from uuid import uuid4


def _row_to_blog(blog_data) -> Blog:
    return Blog(
        id=blog_data["id"],
        title=blog_data["title"],
        content=blog_data["content"],
        excerpt=blog_data.get("excerpt"),
        category=blog_data["category"],
        image=blog_data.get("image"),
        publishDate=blog_data.get("publishDate"),
        creator_id=blog_data["creator_id"],
        status=blog_data["status"],
        created_at=blog_data["created_at"].isoformat(),
        updated_at=(
            blog_data["updated_at"].isoformat()
            if blog_data.get("updated_at")
            else None
        ),
    )


class BlogCRUD:
    @staticmethod
    async def create(blog: BlogCreate, creator_id: str) -> Blog:
        with db.get_session() as session:
            blog_id = str(uuid4())
            result = session.run(
                """
                CREATE (b:Blog {
                    id: $id,
                    title: $title,
                    content: $content,
                    excerpt: $excerpt,
                    category: $category,
                    image: $image,
                    publishDate: $publishDate,
                    creator_id: $creator_id,
                    status: 'published',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN b
                """,
                id=blog_id,
                title=blog.title,
                content=blog.content,
                excerpt=blog.excerpt,
                category=blog.category,
                image=blog.image,
                publishDate=blog.publishDate,
                creator_id=creator_id,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create blog.")

            session.run(
                """
                MATCH (u:User {id: $user_id}), (b:Blog {id: $blog_id})
                CREATE (u)-[:CREATED]->(b)
                """,
                user_id=creator_id,
                blog_id=blog_id,
            )
            return _row_to_blog(record["b"])

    @staticmethod
    async def get_all() -> List[Blog]:
        with db.get_session() as session:
            result = session.run(
                "MATCH (b:Blog) RETURN b ORDER BY coalesce(b.publishDate, toString(b.created_at)) DESC"
            )
            return [_row_to_blog(r["b"]) for r in result]

    @staticmethod
    async def get_by_id(blog_id: str) -> Optional[Blog]:
        with db.get_session() as session:
            result = session.run(
                "MATCH (b:Blog {id: $id}) RETURN b", id=blog_id
            )
            record = result.single()
            return _row_to_blog(record["b"]) if record else None
