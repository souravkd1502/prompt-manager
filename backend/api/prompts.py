"""
summary
-----------
API routes for managing prompts, including creation, retrieval, updating,
deletion, duplication, rollback, and version management.

Functionality
----------------
- Create, list, retrieve, update, and delete prompts
- Duplicate prompts with versioning support
- Rollback prompts to previous versions
- Manage multiple versions of a single prompt

usage
---------
Import this router and include it in the main FastAPI application:
    from backend.api import prompts
    app.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])

requirements
-----------------
- FastAPI
- SQLAlchemy
- Pydantic schemas (PromptCreate, PromptUpdate, PromptResponse)
- Backend database session provider

TODO
--------
- Add caching for frequently accessed prompts
- Implement authentication & authorization
- Implement rate limiting for better API governance

FIXME
--------
- Ensure rollback handles edge cases (e.g., non-existent versions)
- Improve pagination for large datasets using cursor-based pagination

Created By
-------------
Your Name

Date
--------
2025-08-19
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.prompt_schemas import PromptCreate, PromptUpdate, PromptResponse
from backend.core.database import get_db
from backend.services import prompt_service

# Initialize logger
logger = logging.getLogger(__name__)

# Router instance
router = APIRouter()


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)) -> PromptResponse:
    """
    Create a new prompt with initial version (v1).

    Args:
        prompt (PromptCreate): The prompt data to be created.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptResponse: The newly created prompt with version info.
    """
    try:
        created_prompt = prompt_service.create_prompt(db, prompt)
        logger.info(f"Prompt created successfully: {created_prompt.id}")
        return created_prompt
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to create prompt")


@router.get("/", response_model=List[PromptResponse])
def list_prompts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[PromptResponse]:
    """
    Retrieve a paginated list of prompts.

    Args:
        skip (int): Number of records to skip (default: 0).
        limit (int): Max number of records to return (default: 20).
        db (Session): SQLAlchemy database session.

    Returns:
        List[PromptResponse]: A list of prompts.
    """
    try:
        prompts = prompt_service.get_prompts(db, skip=skip, limit=limit)
        logger.debug(f"Retrieved {len(prompts)} prompts (skip={skip}, limit={limit})")
        return prompts
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch prompts")


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)) -> PromptResponse:
    """
    Retrieve a single prompt by its unique ID.

    Args:
        prompt_id (int): The ID of the prompt.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptResponse: The requested prompt object.
    """
    try:
        prompt = prompt_service.get_prompt(db, prompt_id)
        if not prompt:
            logger.warning(f"Prompt not found: ID {prompt_id}")
            raise HTTPException(status_code=404, detail="Prompt not found")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prompt")


@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: int, prompt_update: PromptUpdate, db: Session = Depends(get_db)) -> PromptResponse:
    """
    Update a prompt, creating a new version.

    Args:
        prompt_id (int): The ID of the prompt to update.
        prompt_update (PromptUpdate): The updated data.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptResponse: The updated prompt with new version info.
    """
    try:
        updated_prompt = prompt_service.update_prompt(db, prompt_id, prompt_update)
        logger.info(f"Prompt {prompt_id} updated to new version {updated_prompt.version}")
        return updated_prompt
    except Exception as e:
        logger.error(f"Error updating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")


@router.delete("/{prompt_id}", status_code=status.HTTP_200_OK)
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Delete a prompt (soft delete recommended).

    Args:
        prompt_id (int): The ID of the prompt to delete.
        db (Session): SQLAlchemy database session.

    Returns:
        dict: Confirmation message.
    """
    try:
        prompt_service.delete_prompt(db, prompt_id)
        logger.info(f"Prompt {prompt_id} deleted successfully")
        return {"message": f"Prompt {prompt_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete prompt")


@router.post("/{prompt_id}/duplicate", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
def duplicate_prompt(prompt_id: int, db: Session = Depends(get_db)) -> PromptResponse:
    """
    Duplicate a prompt, creating a new copy with initial version (v1).

    Args:
        prompt_id (int): The ID of the prompt to duplicate.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptResponse: The duplicated prompt.
    """
    try:
        duplicated = prompt_service.duplicate_prompt(db, prompt_id)
        logger.info(f"Prompt {prompt_id} duplicated successfully as {duplicated.id}")
        return duplicated
    except Exception as e:
        logger.error(f"Error duplicating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate prompt")


@router.post("/{prompt_id}/versions/{version}/rollback", response_model=PromptResponse)
def rollback_prompt(prompt_id: int, version: int, db: Session = Depends(get_db)) -> PromptResponse:
    """
    Rollback a prompt to a specific previous version.

    Args:
        prompt_id (int): The ID of the prompt.
        version (int): The version number to rollback to.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptResponse: The rolled-back prompt object.
    """
    try:
        rolled_back = prompt_service.rollback_prompt(db, prompt_id, version)
        logger.info(f"Prompt {prompt_id} rolled back to version {version}")
        return rolled_back
    except Exception as e:
        logger.error(f"Error rolling back prompt {prompt_id} to version {version}: {e}")
        raise HTTPException(status_code=500, detail="Failed to rollback prompt")


@router.get("/{prompt_id}/versions", response_model=List[PromptResponse])
def list_versions(prompt_id: int, db: Session = Depends(get_db)) -> List[PromptResponse]:
    """
    List all versions of a specific prompt.

    Args:
        prompt_id (int): The ID of the prompt.
        db (Session): SQLAlchemy database session.

    Returns:
        List[PromptResponse]: List of all versions of the prompt.
    """
    try:
        versions = prompt_service.get_versions(db, prompt_id)
        logger.debug(f"Retrieved {len(versions)} versions for prompt {prompt_id}")
        return versions
    except Exception as e:
        logger.error(f"Error listing versions for prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list versions")
