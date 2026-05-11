from app.crud.database import db
from fastapi import HTTPException
from app.models.store import Store, StoreCreate
from typing import List, Tuple
from uuid import uuid4


STORE_TYPE_TO_GENRE = {
    "restaurant": ("food", "restaurant"),
    "cafe": ("food", "cafe"),
    "bakery": ("food", "bakery"),
    "grocery": ("food", "grocery"),
    "convenience": ("food", "convenience"),
    "clothing": ("shopping", "clothing"),
    "electronics": ("shopping", "electronics"),
    "pharmacy": ("public", "pharmacy"),
    "beauty": ("service", "beauty"),
    "bank": ("service", "bank"),
    "other": ("service", "other"),
}


# Auto-positioning grid. 4x4 slots within safe range [15, 85] avoiding map frame
# edges. Stores beyond 16 wrap with a deterministic jitter so they remain inside
# the bounds but do not stack exactly on existing pins.
_GRID_COLS = 4
_GRID_ROWS = 4
_MIN_BOUND = 15.0
_MAX_BOUND = 85.0
_SAFE_MIN = 10.0
_SAFE_MAX = 90.0


def _compute_position(slot_index: int) -> Tuple[float, float]:
    cell = (_MAX_BOUND - _MIN_BOUND) / (_GRID_COLS - 1)
    base = slot_index % (_GRID_COLS * _GRID_ROWS)
    overflow_round = slot_index // (_GRID_COLS * _GRID_ROWS)
    col = base % _GRID_COLS
    row = base // _GRID_COLS
    # First 16 stores fill the clean grid; from the 17th onward, deterministic
    # jitter spreads pins so they don't stack exactly on earlier ones.
    if overflow_round == 0:
        jitter_x = 0.0
        jitter_y = 0.0
    else:
        jitter_x = ((overflow_round * 7) % 11) - 5
        jitter_y = ((overflow_round * 13) % 11) - 5
    x = _MIN_BOUND + col * cell + jitter_x
    y = _MIN_BOUND + row * cell + jitter_y
    # Hard clamp so a pin never exits the map frame
    x = max(_SAFE_MIN, min(_SAFE_MAX, x))
    y = max(_SAFE_MIN, min(_SAFE_MAX, y))
    return x, y


class StoreCRUD:
    @staticmethod
    async def create(store: StoreCreate, creator_id: str) -> Store:
        """
        Create a new store, auto-assign a (mainGenre, subGenre) from storeType,
        and compute a non-overlapping in-bounds position on the shotengai map.
        """
        main_genre, sub_genre = STORE_TYPE_TO_GENRE.get(
            store.storeType, ("service", "other")
        )

        with db.get_session() as session:
            store_id = str(uuid4())

            # Count existing stores in this subGenre to pick the next grid slot
            count_result = session.run(
                "MATCH (s:Store {subGenre: $sg}) RETURN count(s) AS n",
                sg=sub_genre,
            )
            existing = count_result.single()["n"] or 0
            position_x, position_y = _compute_position(existing)

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
                    mainGenre: $mainGenre,
                    subGenre: $subGenre,
                    position_x: $position_x,
                    position_y: $position_y,
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
                mainGenre=main_genre,
                subGenre=sub_genre,
                position_x=position_x,
                position_y=position_y,
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

            return _row_to_store(record["s"])

    @staticmethod
    async def get_all() -> List[Store]:
        """
        Retrieve all stores from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (s:Store) RETURN s ORDER BY s.created_at DESC")
            return [_row_to_store(r["s"]) for r in result]


def _row_to_store(store_data) -> Store:
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
        mainGenre=store_data.get("mainGenre", "service"),
        subGenre=store_data.get("subGenre", "other"),
        position_x=float(store_data.get("position_x", 50.0)),
        position_y=float(store_data.get("position_y", 50.0)),
        creator_id=store_data["creator_id"],
        status=store_data["status"],
        created_at=store_data["created_at"].isoformat(),
        updated_at=(
            store_data["updated_at"].isoformat()
            if store_data.get("updated_at")
            else None
        ),
    )
