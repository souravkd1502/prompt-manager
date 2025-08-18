"""
Pydantic schemas for Prompt API.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromptBase(BaseModel):
    name: str
    content: str
    tenant_id: int


class PromptCreate(PromptBase):
    """
    Schema for creating a new prompt (initial version = v1).
    """
    pass


class PromptUpdate(BaseModel):
    """
    Schema for updating an existing prompt.
    Creates a new version internally.
    """
    content: str


class PromptResponse(PromptBase):
    """
    Response schema for a prompt.
    """
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
