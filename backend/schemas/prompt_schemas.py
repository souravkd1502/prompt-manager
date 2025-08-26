"""
Pydantic schemas for Prompt API.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# -------------------------
# Prompt Schemas
# -------------------------

class PromptBase(BaseModel):
    name: str
    content: str
    tenant_id: int
    description: Optional[str] = None


class PromptCreate(PromptBase):
    """
    Schema for creating a new prompt (initial version = v1).
    """
    pass


class PromptUpdate(BaseModel):
    """
    Schema for updating an existing prompt metadata.
    Creates a new version internally if content changes.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

class PromptResponse(PromptBase):
    """
    Response schema for a prompt (latest version by default).
    """
    id: str
    version: int
    created_at: datetime
    updated_at: datetime
    is_deleted: Optional[bool] = False
    tags: List[str] = []
    is_favorite: Optional[bool] = False

    class Config:
        from_attributes = True


# -------------------------
# Version Schemas
# -------------------------

class PromptVersionCreate(BaseModel):
    """
    Schema for creating a new version of a prompt.
    """
    content: str
    description: Optional[str] = None


class PromptVersionResponse(BaseModel):
    """
    Response schema for a specific version of a prompt.
    """
    id: str
    version: int
    content: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------
# Tag Schemas
# -------------------------

class TagCreate(BaseModel):
    """
    Schema for creating a new tag.
    """
    name: str


class TagResponse(BaseModel):
    """
    Response schema for a tag.
    """
    id: int
    name: str

    class Config:
        from_attributes = True


# -------------------------
# Favorite Schemas
# -------------------------

class FavoriteResponse(BaseModel):
    """
    Response schema for a user's favorite prompt.
    """
    prompt_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------
# Search Schemas
# -------------------------

class PromptSearchRequest(BaseModel):
    """
    Schema for full-text search with filters.
    """
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    tenant_id: Optional[int] = None
    version: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0


class PromptSearchResponse(BaseModel):
    """
    Schema for search result response.
    """
    total: int
    results: List[PromptResponse]


# -------------------------
# Saved Search Schemas
# -------------------------

class SavedSearchCreate(BaseModel):
    """
    Schema for saving a search query.
    """
    name: str
    filters: Dict[str, Any]


class SavedSearchResponse(BaseModel):
    """
    Response schema for saved searches.
    """
    id: int
    name: str
    filters: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
