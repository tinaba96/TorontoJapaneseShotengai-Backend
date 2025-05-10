from app.crud.database import db
from typing import Optional, List
from fastapi import HTTPException, status
from app.models import User, UserCreate, UserUpdate
from app.core.utils import get_password_hash, verify_password
from uuid import uuid4


class UserCRUD:
    @staticmethod
    async def create(user: UserCreate) -> User:
        """
        Create a new user. If the id is provided, use it; otherwise, generate a random UUID.
        """
        with db.get_session() as session:
            # Check for existing user by email
            result = session.run(
                "MATCH (u:User {email: $email}) RETURN u",
                email=user.email
            )
            if result.single():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already registered."
                )

            # Hash the user's password
            hashed_password = get_password_hash(user.password)

            # Set ID: Use provided id or generate a new random UUID
            provided_id = user.id if user.id else None

            # Create user in database
            create_result = session.run(
                """
                CREATE (u:User {
                    id: COALESCE($id, randomUUID()),  # Use provided id if exists; otherwise generate random UUID
                    name: $name,
                    email: $email,
                    hashed_password: $hashed_password,
                    created_at: datetime()
                })
                RETURN u.id AS id, u.name AS name, u.email AS email, u.created_at AS created_at
                """,
                id=provided_id,
                name=user.name,
                email=user.email,
                hashed_password=hashed_password,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create user.")

            # Construct user object from query result
            return User(
                id=record["id"],  # Return id (generated or provided)
                name=record["name"],
                email=record["email"],
                created_at=record["created_at"].isoformat(),
            )

    @staticmethod
    async def get_all() -> List[User]:
        """
        Retrieve all users from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (u:User) RETURN u")  # ユーザー全件取得
            users = [
                User(
                    id=record["u"].get("id") or str(uuid4()),  # idがない場合、UUIDを生成
                    name=record["u"]["name"],
                    email=record["u"]["email"],
                    created_at=record["u"]["created_at"].isoformat(),
                )
                for record in result
            ]
            return users


    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.
        """
        with db.get_session() as session:
            result = session.run(
                "MATCH (u:User {id: $id}) RETURN u", id=user_id
            )
            record = result.single()
            if record:
                user_data = record["u"]
                return User(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    created_at=user_data["created_at"].isoformat(),
                )
            return None

    @staticmethod
    async def update(user_id: int, user: UserUpdate) -> Optional[User]:
        """
        Update user details by ID.
        """
        with db.get_session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $id})
                SET u.name = $name, u.email = $email
                RETURN u
                """,
                id=user_id, name=user.name, email=user.email
            )
            record = result.single()
            if record:
                user_data = record["u"]
                return User(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    created_at=user_data["created_at"].isoformat(),
                )
            return None

    @staticmethod
    async def delete(user_id: int) -> bool:
        """
        Delete a user by ID.
        """
        with db.get_session() as session:
            result = session.run(
                "MATCH (u:User {id: $id}) DELETE u",
                id=user_id
            )
            return bool(result.summary().counters.nodes_deleted)

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        """
        Verify user's email and password for authentication.
        """
        with db.get_session() as session:
            result = session.run(
                "MATCH (u:User {email: $email}) RETURN u", email=email
            )
            record = result.single()
            if record:
                user = record["u"]
                # Verify the password with the hashed_password
                if verify_password(password, user["hashed_password"]):
                    return User(
                        id=user["id"],
                        name=user["name"],
                        email=user["email"],
                        created_at=user["created_at"].isoformat(),
                    )
        return None
