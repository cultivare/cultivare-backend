from fastapi import APIRouter, HTTPException, Form, File, Query
from typing import List, Optional, Dict
from app.database import db


router = APIRouter(
    prefix="/tags",
    tags=["tags"],
)

notes_collection = db.notes_collection
cultures_collection = db.cultures_collection

# ---- API Endpoints ----


@router.get("/", response_model=List[str])
async def get_all_tags():
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$project": {"_id": 0, "name": "$_id"}},
    ]

    culture_tags = [doc async for doc in cultures_collection.aggregate(pipeline)]
    note_tags = [doc async for doc in notes_collection.aggregate(pipeline)]

    all_tags = list({tag["name"] for tag in culture_tags + note_tags})
    return all_tags


@router.get("/frequency", response_model=Dict[str, int])
async def get_tag_frequency():
    """
    Endpoint to count the frequency of each tag.
    """
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
    ]

    culture_tag_counts = {
        doc["_id"]: doc["count"]
        async for doc in cultures_collection.aggregate(pipeline)
    }
    note_tag_counts = {
        doc["_id"]: doc["count"] async for doc in notes_collection.aggregate(pipeline)
    }

    all_tag_counts = {}
    for tag_counts in [culture_tag_counts, note_tag_counts]:
        for tag, count in tag_counts.items():
            all_tag_counts[tag] = all_tag_counts.get(tag, 0) + count

    return all_tag_counts


@router.get("/autocomplete/")
async def autocomplete_tags(
    q: Optional[str] = Query(None, description="Partial tag for autocompletion")
):
    if not q:
        raise HTTPException(status_code=400, detail="Missing autocompletion query")

    pipeline = [
        {"$unwind": "$tags"},
        {
            "$match": {
                "tags": {"$regex": f"{q}", "$options": "i"}  # Match anywhere in the tag
            }
        },
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},  # Sort by frequency, then alphabetically
        {"$limit": 10},  # Limit to top 10 suggestions
    ]

    culture_tags = [doc async for doc in cultures_collection.aggregate(pipeline)]
    note_tags = [doc async for doc in notes_collection.aggregate(pipeline)]

    all_tags = list({tag["_id"] for tag in culture_tags + note_tags})
    return all_tags
