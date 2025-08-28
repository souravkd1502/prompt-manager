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


class PromptCreateRequest(BaseModel):
    """
    Request schema for creating a new prompt.

    Args:
        BaseModel (BaseModel): Pydantic base model for data validation.
    """

    tenant_id: int = Field(..., description="ID of the tenant")
    title: str = Field(..., description="Title of the prompt")
    description: Optional[str] = Field(None, description="Description of the prompt")
    prompt_text: str = Field(..., description="Content of the prompt")
    is_archived: Optional[bool] = Field(
        False, description="Whether the prompt is archived"
    )
    created_by: int = Field(..., description="ID of the user who created the prompt")
    tags: Optional[List[str]] = Field(None, description="List of tags for the prompt")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "tenant_id": 1,
                "title": "Sample Prompt",
                "description": "This is a sample prompt.",
                "prompt_text": "What is the capital of France?",
                "is_archived": False,
                "created_by": 1,
                "tags": ["geography", "france"],
            }
        },
    }
    

class PromptCreateResponse(BaseModel):
    """
    Response schema for a created prompt.

    Args:
        BaseModel (BaseModel): Pydantic base model for data validation.
    """

    id: int = Field(..., description="Unique identifier of the prompt")
    tenant_id: int = Field(..., description="ID of the tenant")
    title: str = Field(..., description="Title of the prompt")
    description: Optional[str] = Field(None, description="Description of the prompt")
    prompt_text: str = Field(..., description="Content of the prompt")
    is_archived: bool = Field(..., description="Whether the prompt is archived")
    created_by: int = Field(..., description="ID of the user who created the prompt")
    current_version_id: int = Field(..., description="Current version ID of the prompt")
    created_at: datetime = Field(..., description="Timestamp when the prompt was created")
    updated_at: datetime = Field(..., description="Timestamp when the prompt was last updated")
    tags: Optional[str] = Field(None, description="Comma-separated list of tags for the prompt")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "tenant_id": 1,
                "title": "Sample Prompt",
                "description": "This is a sample prompt.",
                "prompt_text": "What is the capital of France?",
                "is_archived": False,
                "created_by": 1,
                "current_version_id": 1,
                "created_at": "2023-10-01T12:00:00Z",
                "updated_at": "2023-10-01T12:00:00Z",
                "tags": "geography,france",
            }
        },
    }
    

class PromptListRequest(BaseModel):
    """
    Request schema for listing prompts.

    Args:
        BaseModel (BaseModel): Pydantic base model for data validation.
    """

    tenant_id: int = Field(..., description="ID of the tenant")
    offset: int = Field(0, description="Number of prompts to skip")
    limit: int = Field(100, description="Maximum number of prompts to return")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "tenant_id": 1,
                "offset": 0,
                "limit": 100,
            }
        },
    }
    
    
class PromptListResponse(BaseModel):
    """
    Response schema for listing prompts.

    Args:
        BaseModel (BaseModel): Pydantic base model for data validation.
    """

    total: int = Field(..., description="Total number of prompts available")
    prompts: List[PromptCreateResponse] = Field(..., description="List of prompts")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "total": 2,
                "prompts": [
                    {
                        "id": 1,
                        "tenant_id": 1,
                        "title": "Sample Prompt 1",
                        "description": "This is a sample prompt.",
                        "prompt_text": "What is the capital of France?",
                        "is_archived": False,
                        "created_by": 1,
                        "current_version_id": 1,
                        "created_at": "2023-10-01T12:00:00Z",
                        "updated_at": "2023-10-01T12:00:00Z",
                        "tags": "geography,france",
                    },
                    {
                        "id": 2,
                        "tenant_id": 1,
                        "title": "Sample Prompt 2",
                        "description": "This is another sample prompt.",
                        "prompt_text": "What is the largest ocean on Earth?",
                        "is_archived": False,
                        "created_by": 1,
                        "current_version_id": 1,
                        "created_at": "2023-10-01T12:00:00Z",
                        "updated_at": "2023-10-01T12:00:00Z",
                        "tags": "geography,ocean",
                    },
                ],
            }
        },
    }
