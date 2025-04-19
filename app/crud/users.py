from typing import List, Optional
from ..models import User, UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password
from .database import db
from fastapi import HTTPException
from datetime import datetime


class UserCRUD:
    @staticmethod
    async def create(user: UserCreate) -> User:
        with db.get_session() as session:
            # メールアドレスの重複チェック
            result = session.run(
                "MATCH (u:User {email: $email}) RETURN u", email=user.email
            )
            if result.single():
                raise HTTPException(status_code=400, detail="Email already registered")

            # パスワードのハッシュ化
            hashed_password = get_password_hash(user.password)

            result = session.run(
                """
                CREATE (u:User {
                    name: $name,
                    email: $email,
                    hashed_password: $hashed_password,
                    created_at: datetime()
                })
                RETURN u
                """,
                name=user.name,
                email=user.email,
                hashed_password=hashed_password,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=400, detail="Failed to create user")
            user_data = record["u"]
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        with db.get_session() as session:
            result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
            record = result.single()
            if not record:
                return None
            user_data = record["u"]
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        with db.get_session() as session:
            result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
            record = result.single()
            if not record:
                return None
            user_data = record["u"]
            if not verify_password(password, user_data["hashed_password"]):
                return None
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    @staticmethod
    async def get_all() -> List[User]:
        with db.get_session() as session:
            result = session.run("MATCH (u:User) RETURN u")
            users = []
            for record in result:
                user_data = record["u"]
                users.append(
                    User(
                        id=user_data.id,
                        name=user_data["name"],
                        email=user_data["email"],
                        created_at=user_data["created_at"].isoformat(),
                    )
                )
            return users

    @staticmethod
    async def get_by_id(user_id: int) -> User:
        with db.get_session() as session:
            result = session.run(
                "MATCH (u:User) WHERE id(u) = $user_id RETURN u", user_id=user_id
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="User not found")
            user_data = record["u"]
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    @staticmethod
    async def update(user_id: int, user: UserUpdate) -> User:
        with db.get_session() as session:
            update_fields = {}
            if user.name is not None:
                update_fields["name"] = user.name
            if user.email is not None:
                update_fields["email"] = user.email
            if user.password is not None:
                update_fields["hashed_password"] = get_password_hash(user.password)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            query = """
            MATCH (u:User)
            WHERE id(u) = $user_id
            SET u += $update_fields
            RETURN u
            """
            result = session.run(query, user_id=user_id, update_fields=update_fields)
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="User not found")
            user_data = record["u"]
            return User(
                id=user_data.id,
                name=user_data["name"],
                email=user_data["email"],
                created_at=user_data["created_at"].isoformat(),
            )

    @staticmethod
    async def delete(user_id: int) -> dict:
        with db.get_session() as session:
            result = session.run(
                "MATCH (u:User) WHERE id(u) = $user_id DELETE u", user_id=user_id
            )
            if result.consume().counters.nodes_deleted == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"message": "User deleted successfully"}
