"""
Pydantic Schemas for Prompt Management API

This module defines comprehensive Pydantic schemas for a prompt management system,
providing data validation, serialization, and API documentation support. The schemas
are designed to be aligned with database models and OpenAPI specifications.

The module includes schemas for:
    - Prompt CRUD operations (create, read, update, delete)
    - Version management for prompt content
    - Tag system for categorization
    - User favorites functionality
    - Full-text search with advanced filtering
    - Saved search queries for reusability

All schemas follow RESTful API conventions and include proper validation,
type hints, and configuration for SQLAlchemy ORM integration.

Example:
    Basic usage for creating a new prompt:

    >>> from schemas import PromptCreate
    >>> prompt_data = PromptCreate(
    ...     name="Welcome Message",
    ...     content="Hello, welcome to our application!",
    ...     tenant_id=1,
    ...     description="Standard welcome message for new users"
    ... )

Author: Your Name
Version: 1.0.0
License: MIT
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# -------------------------
# Base Prompt Schemas
# -------------------------

class PromptBase(BaseModel):
    """
    Base schema for prompt-related operations.
    
    Contains common fields shared across prompt creation and response schemas.
    This base class ensures consistency and reduces code duplication.
    
    Attributes:
        name (str): The unique name/identifier for the prompt. Must be non-empty.
        content (str): The actual prompt content/text. Can include templates and variables.
        tenant_id (int): The ID of the tenant/organization this prompt belongs to.
        description (Optional[str]): Optional human-readable description of the prompt's purpose.
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Unique name for the prompt within the tenant scope"
    )
    content: str = Field(
        ..., 
        min_length=1,
        description="The prompt content, may include template variables"
    )
    tenant_id: int = Field(
        ..., 
        gt=0,
        description="ID of the tenant/organization owning this prompt"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Optional description explaining the prompt's purpose and usage"
    )


class PromptCreate(PromptBase):
    """
    Schema for creating a new prompt.
    
    When a prompt is created, it automatically gets assigned version 1.
    The system will generate timestamps and assign a unique ID upon creation.
    
    Example:
        >>> prompt = PromptCreate(
        ...     name="customer_greeting",
        ...     content="Hello {customer_name}, welcome to {company}!",
        ...     tenant_id=123,
        ...     description="Personalized customer greeting template"
        ... )
    """
    pass


class PromptUpdate(BaseModel):
    """
    Schema for updating an existing prompt's metadata.
    
    If the content field is modified, the system will automatically create
    a new version while preserving the prompt's history. All fields are
    optional to support partial updates.
    
    Note:
        Updating content creates a new version internally, while other
        field updates only modify metadata without version changes.
    
    Attributes:
        title (Optional[str]): New display title for the prompt.
        description (Optional[str]): Updated description.
        content (Optional[str]): New content (triggers version increment).
    """
    title: Optional[str] = Field(
        None, 
        max_length=255,
        description="Updated display title for the prompt"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Updated description of the prompt's purpose"
    )
    content: Optional[str] = Field(
        None, 
        min_length=1,
        description="New prompt content (creates new version if changed)"
    )


class PromptResponse(PromptBase):
    """
    Complete response schema for prompt data.
    
    Returns the latest version of a prompt by default, including all
    metadata, timestamps, and relationship information. This schema
    is used for API responses and data serialization.
    
    Attributes:
        id (str): Unique identifier (UUID) for the prompt.
        version (int): Current version number of the prompt.
        created_at (datetime): Timestamp when the prompt was first created.
        updated_at (datetime): Timestamp of the last modification.
        is_deleted (Optional[bool]): Soft deletion flag.
        tags (List[str]): List of associated tag names for categorization.
        is_favorite (Optional[bool]): Whether current user has favorited this prompt.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(
        ...,
        description="Unique identifier (UUID) for the prompt"
    )
    version: int = Field(
        ..., 
        ge=1,
        description="Current version number of the prompt content"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the prompt was first created"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of the most recent update"
    )
    is_deleted: Optional[bool] = Field(
        False,
        description="Soft deletion flag - true if prompt is marked as deleted"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tag names associated with this prompt"
    )
    is_favorite: Optional[bool] = Field(
        False,
        description="Whether the current user has marked this prompt as favorite"
    )


# -------------------------
# Version Management Schemas
# -------------------------

class PromptVersionCreate(BaseModel):
    """
    Schema for creating a new version of an existing prompt.
    
    Used when you want to create a new version without modifying
    the original prompt's metadata. Each version maintains its
    own content and optional description.
    
    Attributes:
        content (str): The new content for this version.
        description (Optional[str]): Version-specific description or changelog.
    """
    content: str = Field(
        ..., 
        min_length=1,
        description="Content for the new prompt version"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Optional description or changelog for this version"
    )


class PromptVersionResponse(BaseModel):
    """
    Response schema for a specific version of a prompt.
    
    Contains version-specific information without the full prompt metadata.
    Useful for version history and comparison operations.
    
    Attributes:
        id (str): Unique identifier for the prompt this version belongs to.
        version (int): The version number.
        content (str): The content for this specific version.
        description (Optional[str]): Version-specific description.
        created_at (datetime): When this version was created.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(
        ...,
        description="Unique identifier of the parent prompt"
    )
    version: int = Field(
        ..., 
        ge=1,
        description="Version number for this specific version"
    )
    content: str = Field(
        ...,
        description="Content of this specific version"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description or changelog for this version"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when this version was created"
    )


# -------------------------
# Tag Management Schemas
# -------------------------

class TagCreate(BaseModel):
    """
    Schema for creating a new tag.
    
    Tags are used for categorizing and organizing prompts. They enable
    better search and filtering capabilities across the prompt library.
    
    Attributes:
        name (str): The tag name, must be unique within the tenant.
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Unique name for the tag, used for categorization"
    )


class TagResponse(BaseModel):
    """
    Response schema for tag information.
    
    Simple response containing tag details for API responses
    and data serialization.
    
    Attributes:
        id (int): Unique identifier for the tag.
        name (str): The tag name.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(
        ...,
        description="Unique identifier for the tag"
    )
    name: str = Field(
        ...,
        description="The tag name used for categorization"
    )


# -------------------------
# User Favorites Schemas
# -------------------------

class FavoriteResponse(BaseModel):
    """
    Response schema for user's favorite prompt relationships.
    
    Represents the many-to-many relationship between users and their
    favorited prompts, including when the favorite was created.
    
    Attributes:
        prompt_id (str): UUID of the favorited prompt.
        user_id (str): UUID of the user who favorited the prompt.
        created_at (datetime): When the prompt was added to favorites.
    """
    model_config = ConfigDict(from_attributes=True)
    
    prompt_id: str = Field(
        ...,
        description="UUID of the prompt that was favorited"
    )
    user_id: str = Field(
        ...,
        description="UUID of the user who favorited the prompt"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the prompt was added to user's favorites"
    )


# -------------------------
# Search and Query Schemas
# -------------------------

class PromptSearchRequest(BaseModel):
    """
    Schema for advanced prompt search with multiple filter options.
    
    Supports full-text search combined with various filters for precise
    prompt discovery. All filters are optional and can be combined.
    
    Attributes:
        query (Optional[str]): Full-text search query for name/content/description.
        tags (Optional[List[str]]): Filter by specific tag names (AND operation).
        tenant_id (Optional[int]): Limit search to specific tenant.
        version (Optional[int]): Filter by specific version number.
        created_after (Optional[datetime]): Show prompts created after this date.
        created_before (Optional[datetime]): Show prompts created before this date.
        limit (Optional[int]): Maximum number of results (default: 20, max: 100).
        offset (Optional[int]): Number of results to skip for pagination.
    """
    query: Optional[str] = Field(
        None,
        max_length=500,
        description="Full-text search query for prompt name, content, and description"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="List of tag names to filter by (AND operation)"
    )
    tenant_id: Optional[int] = Field(
        None,
        gt=0,
        description="Limit search results to a specific tenant"
    )
    version: Optional[int] = Field(
        None,
        ge=1,
        description="Filter prompts by specific version number"
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Show only prompts created after this timestamp"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Show only prompts created before this timestamp"
    )
    limit: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Maximum number of results to return (1-100)"
    )
    offset: Optional[int] = Field(
        0,
        ge=0,
        description="Number of results to skip for pagination"
    )


class PromptSearchResponse(BaseModel):
    """
    Response schema for search results.
    
    Contains paginated search results with total count information
    for proper pagination handling on the client side.
    
    Attributes:
        total (int): Total number of prompts matching the search criteria.
        results (List[PromptResponse]): List of matching prompts (limited by pagination).
    """
    total: int = Field(
        ...,
        ge=0,
        description="Total number of prompts matching the search criteria"
    )
    results: List[PromptResponse] = Field(
        ...,
        description="List of prompts matching the search (paginated)"
    )


# -------------------------
# Saved Search Schemas
# -------------------------

class SavedSearchCreate(BaseModel):
    """
    Schema for creating a saved search query.
    
    Allows users to save complex search criteria for reuse. The filters
    should contain the same structure as PromptSearchRequest for consistency.
    
    Attributes:
        name (str): User-defined name for the saved search.
        filters (Dict[str, Any]): Serialized search filters and criteria.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User-defined name for the saved search query"
    )
    filters: Dict[str, Any] = Field(
        ...,
        description="Search filters and criteria in JSON format"
    )


class SavedSearchResponse(BaseModel):
    """
    Response schema for saved search queries.
    
    Returns saved search information including the stored filters
    that can be used to recreate the search.
    
    Attributes:
        id (int): Unique identifier for the saved search.
        name (str): User-defined name for the saved search.
        filters (Dict[str, Any]): The stored search filters and criteria.
        created_at (datetime): When the search was saved.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(
        ...,
        description="Unique identifier for the saved search"
    )
    name: str = Field(
        ...,
        description="User-defined name for the saved search"
    )
    filters: Dict[str, Any] = Field(
        ...,
        description="Stored search filters and criteria"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the search query was saved"
    )


# -------------------------
# Utility Types and Constants
# -------------------------

# Common field constraints that can be reused
MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_NAME_LENGTH = 50
MAX_SEARCH_QUERY_LENGTH = 500
MAX_SAVED_SEARCH_NAME_LENGTH = 100
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 100


# Export all schemas for easy importing
__all__ = [
    "PromptBase",
    "PromptCreate", 
    "PromptUpdate",
    "PromptResponse",
    "PromptVersionCreate",
    "PromptVersionResponse", 
    "TagCreate",
    "TagResponse",
    "FavoriteResponse",
    "PromptSearchRequest",
    "PromptSearchResponse", 
    "SavedSearchCreate",
    "SavedSearchResponse"
]