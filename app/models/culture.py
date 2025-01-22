from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import datetime



class CultureBase(BaseModel):
    """Shared properties for all culture models."""
    id: Optional[str] = Field(None, description="Unique id for the culture")
    name: str = Field(None, description="Unique name for the culture")
    favorite: Optional[bool] = Field(default=False, description="Add culture to favorites")
    slug: Optional[str] = Field(None, description="Unique slug for the culture")
    parent_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of the parent cultures")
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tags for the culture")
    source_id: Optional[str] = Field(None, description="ID of the source culture (for clones)")
    origin_date: Optional[datetime.datetime] = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), description="Date the culture was started") 
    completion_date: Optional[datetime.datetime] = Field(None, description="Date of completion of culture's cultivation (e.g. discarded, used, transferred, harvested and no longer in use)")
    species: Optional[str] = Field(None, description="Species of the fungi")
    strain: Optional[str] = Field(None, description="Strain of the fungi")
    media_type: Optional[str] = Field(None, description="Type of growth medium used")
    media_composition: Optional[str] = Field(None, description="Detailed composition of the medium")
    temperature: Optional[float] = Field(None, description="Incubation temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Incubation humidity (percentage)")
    light_conditions: Optional[str] = Field(None, description="Light conditions during incubation")
    growth_rate: Optional[str] = Field(None, description="Qualitative or quantitative growth rate")
    morphology_notes: Optional[str] = Field(None, description="Notes on the colony's appearance")
    experiment_id: Optional[str] = Field(None, description="ID of the experiment this culture is part of")
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class CultureUpdate(BaseModel):
    """Model for updating a culture (all fields optional)."""
    name: Optional[str] = None
    favorite: Optional[bool] = None
    parent_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    source_id: Optional[str] = None
    origin_date: Optional[datetime.datetime] = None
    completion_date: Optional[datetime.datetime] = None
    species: Optional[str] = None
    strain: Optional[str] = None
    media_type: Optional[str] = None
    media_composition: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light_conditions: Optional[str] = None
    growth_rate: Optional[str] = None
    morphology_notes: Optional[str] = None
    experiment_id: Optional[str] = None
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class CultureCreate(CultureBase):
    """Model for creating a new culture."""
    id: str = Field(None, description="Unique id for the culture", exclude=True)  # Use custom string ID
    slug: Optional[str] = Field(default=None, exclude=True) 


class CultureOut(CultureBase):
    """Model for returning a culture (response model)."""
    pass


class CultureSearch(BaseModel):
    """Model for returning a culture for search (response model)."""
    id: Optional[str] = Field(None, description="Unique id for the culture")
    name: str = Field(None, description="Unique name for the culture")
    slug: Optional[str] = Field(default=None)