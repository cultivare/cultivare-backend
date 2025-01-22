from fastapi import APIRouter, UploadFile, status, HTTPException, Form, File
from typing import List, Optional

import os
import datetime
import random
import string
import json

from app.database import db
from app.config import settings
from app.models.note import NoteCreate, NoteUpdate, NoteOut

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)

notes_collection = db.notes_collection

# ---- Helper Functions ----


# Helper functions for ID generation
def generate_hex_id(length=12):
    """Generates a random hexadecimal string of specified length."""
    return "".join(random.choice(string.hexdigits) for _ in range(length)).lower()


async def save_attachment(image: UploadFile, filename: str) -> str:
    """Saves the uploaded file to the 'uploads' directory and returns the filename."""

    # Check if the file has an allowed extension
    if not image.filename.lower().endswith(tuple(settings.ALLOWED_EXTENSIONS)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format, allowed extensions: {list(settings.ALLOWED_EXTENSIONS)}",
        )

    os.makedirs(settings.MEDIA_DIR, exist_ok=True)

    unique_filename = filename + os.path.splitext(image.filename.lower())[1]

    file_path = os.path.join(settings.MEDIA_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())

    return unique_filename


# ---- API Endpoints ----


@router.post("/", response_model=NoteOut)
async def create_note(
    text: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    favorite: Optional[bool] = Form(None),
    culture_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    """Creates a new note with optional text, attachment, and tags."""
    current_utc_time = datetime.datetime.now(datetime.timezone.utc)
    note_id = generate_hex_id()

    # Parse tags from JSON string to list
    tags_list = []
    if tags:
        try:
            tags_list = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid format for tags")

    # Create the note document
    note_data = NoteCreate(
        id=note_id,
        favorite=favorite,
        culture_id=culture_id,
        text=text,
        color=color,
        image_filename=None,  # We'll set this later
        tags=tags_list,  # Add tags to the note
        updated_at=current_utc_time,
        created_at=current_utc_time,
    )
    note_dict = note_data.model_dump(by_alias=True)

    # Insert the note into the database
    result = await notes_collection.insert_one(note_dict)
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note",
        )

    # Save the attachment (if any)
    image_filename = None
    if file:
        image_filename = await save_attachment(image=file, filename=note_id)

        # Update the note document with the image filename
        await notes_collection.update_one(
            {"id": note_id}, {"$set": {"image_filename": image_filename}}
        )
        note_dict["image_filename"] = image_filename

    return note_dict


@router.get("/", response_model=List[NoteOut])
async def list_notes(favorite: Optional[bool] = None):
    """Retrieves all notes.
    Args:
        favorite (Optional[bool], optional): Filter by favorite status. Defaults to None."""
    notes = []
    if favorite is not None:
        # Filter by favorite status
        async for note in notes_collection.find({"favorite": favorite}):
            notes.append(note)
    else:
        # Retrieve all cultures
        async for note in notes_collection.find():
            notes.append(note)
    return notes


@router.get("/culture/{culture_id}", response_model=List[NoteOut])
async def list_notes(culture_id: str):
    """Retrieves all notes for the culture with _id"""
    notes = []
    async for note in notes_collection.find({"culture_id": culture_id}):
        notes.append(note)
    return notes


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: str):
    """Retrieve a note by its ID."""

    note = await notes_collection.find_one({"id": note_id})
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
    return note


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: str,
    text: Optional[str] = Form(None),
    favorite: Optional[bool] = Form(None),
    color: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    # Fetch the existing note
    existing_note = await notes_collection.find_one({"id": note_id})
    if not existing_note:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found")

    # Handle file upload if a new file is provided
    image_filename = existing_note.get("image_filename")
    if file:
        # Delete the old attachment if it exists
        if image_filename:
            file_path = os.path.join(settings.MEDIA_DIR, image_filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        # save new file
        image_filename = await save_attachment(image=file, filename=str(note_id))

    # Create update data
    update_data = NoteUpdate(
        culture_id=None, updated_at=datetime.datetime.now(datetime.timezone.utc)
    )
    if text is not None:
        update_data.text = text
    if favorite is not None:
        update_data.favorite = favorite
    if color is not None:
        update_data.color = color
    if image_filename is not None:
        update_data.image_filename = image_filename
    if tags is not None:
        try:
            tags_list = json.loads(tags)
            update_data.tags = tags_list
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid format for tags")

    update_data = update_data.model_dump(exclude_unset=True, exclude={"id"})
    update_data["culture_id"] = existing_note.get("culture_id")

    # Update the note in the database
    result = await notes_collection.update_one({"id": note_id}, {"$set": update_data})

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )

    # Fetch and return the updated note
    updated_note = await notes_collection.find_one({"id": note_id})
    return updated_note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str):
    """Delete a note by its ID."""
    existing_note = await get_note(note_id)

    # delete image file
    image_filename = existing_note.get("image_filename")
    if image_filename:
        file_path = os.path.join(settings.MEDIA_DIR, image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    delete_result = await notes_collection.delete_one({"id": note_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
