from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
)
from app.database import db
from app.config import settings
from typing import List, Optional, Set
import datetime
from app.models.culture import CultureCreate, CultureUpdate, CultureOut, CultureSearch
import random
import string
from slugify import slugify
from pymongo.errors import DuplicateKeyError

router = APIRouter(
    prefix="/cultures",
    tags=["cultures"],
)

# ---- Helper Functions ----


# Helper functions for ID generation
def generate_hex_id(length=12):
    """Generates a random hexadecimal string of specified length."""
    return "".join(random.choice(string.hexdigits) for _ in range(length)).lower()


def generate_slug_from_name(name):
    """Generates a slug from the given name."""
    return slugify(name)


# ---- API Endpoints ----


@router.post("/", response_model=CultureOut, status_code=status.HTTP_201_CREATED)
async def create_culture(culture: CultureCreate):
    """Create a new culture record."""

    culture_dict = culture.model_dump(
        by_alias=True, exclude=["id", "slug"]
    )  # user cannot set manually these fields
    culture_dict["id"] = generate_hex_id()  # set uniq id
    culture_dict["slug"] = generate_slug_from_name(culture_dict["name"])

    # TODO check if parent exists

    # Add updated_at timestamp to the update
    current_utc_time = datetime.datetime.now(datetime.timezone.utc)
    culture_dict["updated_at"] = current_utc_time
    culture_dict["created_at"] = current_utc_time

    try:
        result = await db.cultures_collection.insert_one(culture_dict)
    except DuplicateKeyError as e:
        # TODO check slug for duplicate
        detail = f"Duplicate key error: Enter different name. Details: {e}"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    return culture_dict


@router.get("/", response_model=List[CultureOut])
async def list_cultures(favorite: Optional[bool] = None):
    """Retrieve a list of all cultures.

    Args:
        favorite (Optional[bool], optional): Filter by favorite status. Defaults to None.
    """

    cultures = []
    if favorite is not None:
        # Filter by favorite status
        async for culture in db.cultures_collection.find({"favorite": favorite}):
            cultures.append(culture)
    else:
        # Retrieve all cultures
        async for culture in db.cultures_collection.find():
            cultures.append(culture)

    return cultures


@router.get("/search", response_model=List[CultureSearch])
async def get_culture_search(
    culture_name: str = Query(
        None, description="Partial string to search for in the name field"
    ),
    parent_ids: List[str] = Query(None, description="List of parent IDs to retrieve"),
    skip: int = Query(0, description="Number of items to skip", ge=0),
    limit: int = Query(20, description="Maximum number of items to return", le=100),
):
    """
    Search for cultures by partial matching of the name field or retrieve cultures by a list of IDs.
    """

    if parent_ids:
        # Retrieve cultures by IDs
        query = {
            "id": {"$in": parent_ids}
        } 
        results = []
        async for culture in db.cultures_collection.find(query):
            results.append(
                CultureSearch(
                    id=str(culture["id"]), name=culture["name"], slug=culture["slug"]
                )
            )
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cultures found for the given IDs",
            )
        return results

    elif culture_name:
        # Search by culture name
        query = {"name": {"$regex": culture_name, "$options": "i"}}
        results = []
        async for culture in db.cultures_collection.find(query).skip(skip).limit(limit):
            results.append(
                CultureSearch(
                    id=str(culture["id"]), name=culture["name"], slug=culture["slug"]
                )
            )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No results found"
            )
        return results

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'culture_name' or 'parent_ids' query parameter must be provided",
        )


@router.get("/{id}", response_model=CultureOut)
async def get_culture(id: str):
    """Retrieve a culture by its ID."""

    culture = await db.cultures_collection.find_one({"id": id})
    if culture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Culture with id {id} not found",
        )
    return culture


@router.put("/{id}", response_model=CultureOut)
async def update_culture(id: str, culture_update: CultureUpdate):
    """Update a culture by its ID."""

    culture_update_dict = culture_update.model_dump(
        exclude_unset=True
    )  # Exclude unset fields from the update

    # if user updated name - update slug as well
    if "name" in culture_update_dict and culture_update_dict["name"]:
        culture_update_dict["slug"] = generate_slug_from_name(
            culture_update_dict["name"]
        )

    # TODO check if parent exists

    # Add updated_at timestamp to the update
    culture_update_dict["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

    result = await db.cultures_collection.update_one({"id": id}, {"$set": culture_update_dict})
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Culture with id {id} not found",
        )

    updated_culture = await db.cultures_collection.find_one({"id": id})
    return updated_culture


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_culture(id: str):
    """Delete a culture by its ID."""

    delete_result = await db.cultures_collection.delete_one({"id": id})
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Culture with id {id} not found",
        )


## Genealogy ###########################
async def get_related_cultures(
    id: str,
    processed_ids: Set[str] = None,
    depth_limit: int = 1,
    current_depth: int = 0,
) -> List[dict]:
    """
    Recursively retrieves related cultures (ancestors and descendants) for a given culture_id.

    Args:
        id: The ID of the culture to start the search from.
        processed_ids: A set of culture IDs that have already been processed to avoid infinite loops.
        depth_limit: The maximum depth of recursion.
        depth: The current depth of recursion.

    Returns:
        A list of culture dictionaries.
    """
    if processed_ids is None:
        processed_ids = set()

    if current_depth > depth_limit:
        return []

    culture = await db.cultures_collection.find_one({"id": id})
    if not culture:
        return []

    if id in processed_ids:
        return []

    processed_ids.add(id)
    tree = [culture]

    next_depth = current_depth + 1

    if next_depth > depth_limit:
        return tree

    # Find parent cultures
    if "parent_ids" in culture and culture["parent_ids"]:
        for parent_id in culture["parent_ids"]:
            parent_culture = await db.cultures_collection.find_one({"id": parent_id})
            if parent_culture:
                related_cultures = await get_related_cultures(
                    parent_culture["id"],
                    processed_ids.copy(),
                    depth_limit,
                    next_depth,
                )
                if related_cultures:
                    tree.extend(related_cultures)  # Use extend to flatten the list

    # Find children cultures
    async for child_culture in db.cultures_collection.find(
        {"parent_ids": {"$in": [culture["id"]]}}
    ):
        related_cultures = await get_related_cultures(
            child_culture["id"],
            processed_ids.copy(),
            depth_limit,
            next_depth,
        )
        if related_cultures:
            tree.extend(related_cultures)  # Use extend to flatten the list

    return tree


@router.get("/{id}/genealogy", response_model=List[CultureOut])
async def read_related_cultures(
    id: str,
    depth_limit: Optional[int] = Query(
        1, ge=1, le=6, description="Maximum depth of the genealogy tree"
    ),
):
    """
    Retrieve all related cultures (ancestors and descendants) for a given culture_id.

    Args:
        culture_id: The ID of the culture to start the search from.
        depth_limit: The maximum depth of the genealogy tree to search.
                     Defaults to 1. Minimum value is 1, maximum is 5.
    """
    related_cultures = await get_related_cultures(id, depth_limit=depth_limit)
    return related_cultures
