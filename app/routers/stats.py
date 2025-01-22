from fastapi import APIRouter
from typing import List, Optional, Dict
from app.database import db
from app.routers.tags import get_tag_frequency
import datetime

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

notes_collection = db.notes_collection
cultures_collection = db.cultures_collection
stats_collection = db.db["stats"]


async def update_stats():
    """Updates the statistics record in MongoDB."""
    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

    # get tag stats
    tag_data = await get_tag_frequency()
    tag_count = len(tag_data)  # uniq tags number
    tag_uses = sum(tag_data.values())  # total uses for all tags

    stats = {
        "notes_count": await notes_collection.count_documents({}),
        "notes_created_last_month": await notes_collection.count_documents(
            {"created_at": {"$gte": one_month_ago}}
        ),
        "notes_updated_last_month": await notes_collection.count_documents(
            {"updated_at": {"$gte": one_month_ago}}
        ),
        "favorite_notes_count": await notes_collection.count_documents(
            {"favorite": True}
        ),
        "cultures_count": await cultures_collection.count_documents({}),
        "cultures_created_last_month": await cultures_collection.count_documents(
            {"created_at": {"$gte": one_month_ago}}
        ),
        "cultures_updated_last_month": await cultures_collection.count_documents(
            {"updated_at": {"$gte": one_month_ago}}
        ),
        "favorite_cultures_count": await cultures_collection.count_documents(
            {"favorite": True}
        ),
        "images_count": await notes_collection.count_documents(
            {"image_filename": {"$nin": [None, ""]}}
        ),
        "tag_count": tag_count,
        "tag_uses": tag_uses,
    }

    # get note.color stats
    note_color_pipeline = [
        {"$group": {"_id": "$color"}},  # Group by color
        {"$count": "count"},  # Count the distinct colors
    ]
    note_color_result = await notes_collection.aggregate(note_color_pipeline).to_list(
        length=None
    )
    stats["note_colors_count"] = (
        note_color_result[0]["count"] if note_color_result else 0
    )

    # get parent_ids stats

    culture_parents_pipeline = [
        {"$unwind": "$parent_ids"},  # Deconstruct the parent_ids arrays
        {
            "$group": {"_id": None, "total_parent_ids": {"$sum": 1}}
        },  # Count all parent_ids
    ]
    culture_parents_result = await cultures_collection.aggregate(
        culture_parents_pipeline
    ).to_list(length=None)
    stats["culture_parent_ids_count"] = (
        culture_parents_result[0]["total_parent_ids"] if culture_parents_result else 0
    )

    await stats_collection.update_one({}, {"$set": stats}, upsert=True)


# ---- API Endpoints ----


@router.get("/")
async def search():
    await update_stats()

    results = await stats_collection.find_one()
    if results:
        # Convert ObjectId to string
        results["_id"] = str(results["_id"])
        return results
    return {}
