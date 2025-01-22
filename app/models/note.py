import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Model for a note with text, timestamp, and attachments."""
    id: Optional[str] = Field(None, description="Unique id for the note") 
    culture_id: str = Field(..., description="Culture id of the culture this note is attached to")
    favorite: Optional[bool] = Field(default=False, description="Add note to favorites")
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tags for the note")
    text: Optional[str] = Field(None, description="Text content of the note")
    color: Optional[str] = Field(None, description="Filename of the attachment")
    image_filename: Optional[str] = Field(None, description="Filename of the attachment")
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class NoteUpdate(NoteBase):
    """Model for updating a culture (all fields optional)."""
    text: Optional[str] = Field(None, description="Text content of the note")
    favorite: Optional[bool] = Field(None, description="Add note to favorites")
    tags: Optional[List[str]] = Field(None, description="List of tags for the note")
    culture_id: Optional[str] = Field(None, description="Culture id of the culture this note is attached to")
    color: Optional[str] = Field(None, description="Filename of the attachment")
    image_filename: Optional[str] = Field(None, description="Filename of the attachment")
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class NoteCreate(NoteBase):
    """Model for creating a new culture."""
    pass 


class NoteOut(NoteBase):
    """Model for returning a culture (response model)."""
    pass
