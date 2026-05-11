from app.crud.database import db
from fastapi import HTTPException
from app.models.property import Property, PropertyCreate
from typing import List
from uuid import uuid4


class PropertyCRUD:
    @staticmethod
    async def create(prop: PropertyCreate, creator_id: str) -> Property:
        """
        Create a new property and link it to the creator user.
        """
        with db.get_session() as session:
            property_id = str(uuid4())

            create_result = session.run(
                """
                CREATE (p:Property {
                    id: $id,
                    title: $title,
                    description: $description,
                    contactEmail: $contactEmail,
                    contactPhone: $contactPhone,
                    address: $address,
                    rent: $rent,
                    size: $size,
                    rooms: $rooms,
                    utilities: $utilities,
                    parking: $parking,
                    petPolicy: $petPolicy,
                    creator_id: $creator_id,
                    status: 'available',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN p
                """,
                id=property_id,
                title=prop.title,
                description=prop.description,
                contactEmail=prop.contactEmail,
                contactPhone=prop.contactPhone,
                address=prop.address,
                rent=prop.rent,
                size=prop.size,
                rooms=prop.rooms,
                utilities=prop.utilities,
                parking=prop.parking,
                petPolicy=prop.petPolicy,
                creator_id=creator_id,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create property.")

            session.run(
                """
                MATCH (u:User {id: $user_id}), (p:Property {id: $property_id})
                CREATE (u)-[:CREATED]->(p)
                """,
                user_id=creator_id,
                property_id=property_id,
            )

            property_data = record["p"]
            return Property(
                id=property_data["id"],
                title=property_data["title"],
                description=property_data["description"],
                contactEmail=property_data["contactEmail"],
                contactPhone=property_data.get("contactPhone"),
                address=property_data["address"],
                rent=property_data["rent"],
                size=property_data["size"],
                rooms=property_data["rooms"],
                utilities=property_data.get("utilities"),
                parking=property_data.get("parking"),
                petPolicy=property_data.get("petPolicy"),
                creator_id=property_data["creator_id"],
                status=property_data["status"],
                created_at=property_data["created_at"].isoformat(),
                updated_at=property_data["updated_at"].isoformat() if property_data.get("updated_at") else None,
            )

    @staticmethod
    async def get_all() -> List[Property]:
        """
        Retrieve all properties from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (p:Property) RETURN p ORDER BY p.created_at DESC")
            properties = []
            for record in result:
                property_data = record["p"]
                properties.append(
                    Property(
                        id=property_data["id"],
                        title=property_data["title"],
                        description=property_data["description"],
                        contactEmail=property_data["contactEmail"],
                        contactPhone=property_data.get("contactPhone"),
                        address=property_data["address"],
                        rent=property_data["rent"],
                        size=property_data["size"],
                        rooms=property_data["rooms"],
                        utilities=property_data.get("utilities"),
                        parking=property_data.get("parking"),
                        petPolicy=property_data.get("petPolicy"),
                        creator_id=property_data["creator_id"],
                        status=property_data["status"],
                        created_at=property_data["created_at"].isoformat(),
                        updated_at=property_data["updated_at"].isoformat() if property_data.get("updated_at") else None,
                    )
                )
            return properties
