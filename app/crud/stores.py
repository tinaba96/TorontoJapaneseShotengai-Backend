from app.crud.database import db
from fastapi import HTTPException
from app.models.store import Store, StoreCreate
from typing import List
from uuid import uuid4


class StoreCRUD:
    @staticmethod
    async def create(store: StoreCreate, creator_id: str) -> Store:
        """
        Create a new store and link it to the creator user.
        """
        with db.get_session() as session:
            store_id = str(uuid4())

            create_result = session.run(
                """
                CREATE (s:Store {
                    id: $id,
                    title: $title,
                    description: $description,
                    contactEmail: $contactEmail,
                    contactPhone: $contactPhone,
                    businessHours: $businessHours,
                    website: $website,
                    services: $services,
                    storeAddress: $storeAddress,
                    storeType: $storeType,
                    creator_id: $creator_id,
                    status: 'open',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN s
                """,
                id=store_id,
                title=store.title,
                description=store.description,
                contactEmail=store.contactEmail,
                contactPhone=store.contactPhone,
                businessHours=store.businessHours,
                website=store.website,
                services=store.services,
                storeAddress=store.storeAddress,
                storeType=store.storeType,
                creator_id=creator_id,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create store.")

            session.run(
                """
                MATCH (u:User {id: $user_id}), (s:Store {id: $store_id})
                CREATE (u)-[:CREATED]->(s)
                """,
                user_id=creator_id,
                store_id=store_id,
            )

            store_data = record["s"]
            return Store(
                id=store_data["id"],
                title=store_data["title"],
                description=store_data["description"],
                contactEmail=store_data["contactEmail"],
                contactPhone=store_data.get("contactPhone"),
                businessHours=store_data["businessHours"],
                website=store_data.get("website"),
                services=store_data.get("services"),
                storeAddress=store_data["storeAddress"],
                storeType=store_data["storeType"],
                creator_id=store_data["creator_id"],
                status=store_data["status"],
                created_at=store_data["created_at"].isoformat(),
                updated_at=store_data["updated_at"].isoformat() if store_data.get("updated_at") else None,
            )

    @staticmethod
    async def get_all() -> List[Store]:
        """
        Retrieve all stores from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (s:Store) RETURN s ORDER BY s.created_at DESC")
            stores = []
            for record in result:
                store_data = record["s"]
                stores.append(
                    Store(
                        id=store_data["id"],
                        title=store_data["title"],
                        description=store_data["description"],
                        contactEmail=store_data["contactEmail"],
                        contactPhone=store_data.get("contactPhone"),
                        businessHours=store_data["businessHours"],
                        website=store_data.get("website"),
                        services=store_data.get("services"),
                        storeAddress=store_data["storeAddress"],
                        storeType=store_data["storeType"],
                        creator_id=store_data["creator_id"],
                        status=store_data["status"],
                        created_at=store_data["created_at"].isoformat(),
                        updated_at=store_data["updated_at"].isoformat() if store_data.get("updated_at") else None,
                    )
                )
            return stores
