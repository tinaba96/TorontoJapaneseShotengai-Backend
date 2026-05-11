from app.crud.database import db
from fastapi import HTTPException
from app.models.product import Product, ProductCreate
from typing import List
from uuid import uuid4


class ProductCRUD:
    @staticmethod
    async def create(product: ProductCreate, creator_id: str) -> Product:
        """
        Create a new product and link it to the creator user.
        """
        with db.get_session() as session:
            product_id = str(uuid4())

            create_result = session.run(
                """
                CREATE (p:Product {
                    id: $id,
                    title: $title,
                    description: $description,
                    contactEmail: $contactEmail,
                    contactPhone: $contactPhone,
                    price: $price,
                    condition: $condition,
                    category: $category,
                    images: $images,
                    creator_id: $creator_id,
                    status: 'available',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN p
                """,
                id=product_id,
                title=product.title,
                description=product.description,
                contactEmail=product.contactEmail,
                contactPhone=product.contactPhone,
                price=product.price,
                condition=product.condition,
                category=product.category,
                images=product.images,
                creator_id=creator_id,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create product.")

            session.run(
                """
                MATCH (u:User {id: $user_id}), (p:Product {id: $product_id})
                CREATE (u)-[:CREATED]->(p)
                """,
                user_id=creator_id,
                product_id=product_id,
            )

            product_data = record["p"]
            return Product(
                id=product_data["id"],
                title=product_data["title"],
                description=product_data["description"],
                contactEmail=product_data["contactEmail"],
                contactPhone=product_data.get("contactPhone"),
                price=product_data["price"],
                condition=product_data["condition"],
                category=product_data["category"],
                images=product_data.get("images"),
                creator_id=product_data["creator_id"],
                status=product_data["status"],
                created_at=product_data["created_at"].isoformat(),
                updated_at=product_data["updated_at"].isoformat() if product_data.get("updated_at") else None,
            )

    @staticmethod
    async def get_all() -> List[Product]:
        """
        Retrieve all products from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (p:Product) RETURN p ORDER BY p.created_at DESC")
            products = []
            for record in result:
                product_data = record["p"]
                products.append(
                    Product(
                        id=product_data["id"],
                        title=product_data["title"],
                        description=product_data["description"],
                        contactEmail=product_data["contactEmail"],
                        contactPhone=product_data.get("contactPhone"),
                        price=product_data["price"],
                        condition=product_data["condition"],
                        category=product_data["category"],
                        images=product_data.get("images"),
                        creator_id=product_data["creator_id"],
                        status=product_data["status"],
                        created_at=product_data["created_at"].isoformat(),
                        updated_at=product_data["updated_at"].isoformat() if product_data.get("updated_at") else None,
                    )
                )
            return products
