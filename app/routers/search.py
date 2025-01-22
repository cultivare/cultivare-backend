from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from app.database import db
from app.models.culture import CultureOut

router = APIRouter(
    prefix="/search",
    tags=["search"],
)

notes_collection = db.notes_collection
cultures_collection = db.cultures_collection

# ---- API Endpoints ----


@router.get("/", response_model=List[CultureOut])
async def search(q: Optional[str] = Query(None, description="Search query")):
    if not q:
            raise HTTPException(status_code=400, detail="Missing search query")

    cultures = []
    # TODO Global search
    
    return cultures


