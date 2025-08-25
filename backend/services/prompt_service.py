"""
SQLAlchemy models and services for prompts and versions.
--------------------------------------------------------

Functionality
----------------
Provides CRUD operations, versioning, duplication, and rollback 
features for `Prompt` entities. Uses SQLAlchemy ORM with synchronous 
sessions to ensure blocking DB interactions. Also integrates 
logging, exception handling, and audit-friendly design.

Usage
---------
- Import functions in FastAPI routes to manage prompts.
- Each function is synchronous and expects a `Session`.
- Used for prompt creation, update, duplication, rollback, and deletion.

Requirements
-----------------
- SQLAlchemy (sync engine)
- FastAPI
- Database models: `Prompt`, `PromptVersion`
- Logging configuration

TODO
--------
- Add caching layer for frequently accessed prompts.
- Implement soft-delete instead of permanent deletion.
- Add audit logging integration with `AuditLog`.

FIXME
--------
- Ensure tenant-based filtering (multi-tenancy).
- Revisit transaction rollback handling for distributed setups.

Created By
-------------
Sourav Das

Date
--------
2025-08-19
"""

# Import Dependencies
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from backend.models.prompt import Prompt, PromptVersion
from backend.schemas.prompt_schemas import PromptCreate, PromptUpdate

# Configure module-level logger
logger = logging.getLogger(__name__)

DETAIL = "Prompt not found"


# -------------------------------
# CRUD Service Functions
# -------------------------------

def create_prompt(
    db: Session, prompt: PromptCreate, user_id: Optional[str] = None
) -> Prompt:
    """
    Create a new Prompt with its first version.

    Args:
        db (Session): SQLAlchemy session.
        prompt (PromptCreate): Prompt creation schema.
        user_id (Optional[str]): ID of the user creating the prompt.

    Returns:
        Prompt: The newly created prompt with its first version.

    Raises:
        HTTPException: If database operation fails.
    """
    try:
        # Generate UUID for the prompt
        prompt_id = str(uuid.uuid4())
        
        new_prompt = Prompt(
            id=prompt_id,
            tenant_id=prompt.tenant_id,
            title=prompt.title,
            description=prompt.description,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_prompt)
        db.flush()  # Ensure new_prompt.id is available

        version_id = str(uuid.uuid4())
        first_version = PromptVersion(
            id=version_id,
            prompt_id=new_prompt.id,
            version_number=1,
            body=prompt.body,
            style=prompt.style,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        db.add(first_version)
        db.flush()

        # Link prompt to its first version
        new_prompt.current_version_id = first_version.id
        db.commit()
        db.refresh(new_prompt)

        logger.info("Prompt created: id=%s, title=%s", new_prompt.id, new_prompt.title)
        return new_prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to create prompt: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create prompt")


def get_prompts(db: Session, skip: int = 0, limit: int = 20) -> List[Prompt]:
    """
    Retrieve a paginated list of Prompts with eager loading.

    Args:
        db (Session): SQLAlchemy session.
        skip (int): Offset for pagination.
        limit (int): Maximum number of prompts to return.

    Returns:
        List[Prompt]: List of prompts.
    """
    result = db.execute(
        select(Prompt)
        .options(selectinload(Prompt.versions))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


def get_prompt(db: Session, prompt_id: str) -> Optional[Prompt]:
    """
    Retrieve a single Prompt by ID.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): The prompt's ID.

    Returns:
        Optional[Prompt]: The Prompt if found, else None.
    """
    result = db.execute(
        select(Prompt)
        .options(selectinload(Prompt.current_version_id))
        .filter(Prompt.id == prompt_id)
    )
    return result.scalars().first()


def update_prompt(
    db: Session,
    prompt_id: str,
    prompt_update: PromptUpdate,
    user_id: Optional[str] = None,
) -> Prompt:
    """
    Update a Prompt by creating a new version.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): ID of the prompt to update.
        prompt_update (PromptUpdate): Update schema.
        user_id (Optional[str]): ID of the user updating the prompt.

    Returns:
        Prompt: The updated prompt with a new current version.

    Raises:
        HTTPException: If the prompt is not found or DB operation fails.
    """
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        logger.warning("Update failed: prompt_id=%s not found", prompt_id)
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        result = db.execute(
            select(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version_number.desc())
        )
        latest_version = result.scalars().first()
        new_version_number = (latest_version.version_number + 1) if latest_version else 1

        version_id = str(uuid.uuid4())
        new_version = PromptVersion(
            id=version_id,
            prompt_id=prompt_id,
            version_number=new_version_number,
            body=prompt_update.body,
            style=prompt_update.style,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_version)
        db.flush()

        prompt.current_version_id = new_version.id
        prompt.updated_at = datetime.now(tz=timezone.utc)

        db.commit()
        db.refresh(prompt)

        logger.info(
            "Prompt updated: id=%s, new_version=%s", prompt_id, new_version_number
        )
        return prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to update prompt %s: %s", prompt_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to update prompt")


def delete_prompt(db: Session, prompt_id: str) -> None:
    """
    Delete a Prompt and its associated versions.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): ID of the prompt to delete.

    Raises:
        HTTPException: If the prompt does not exist or DB operation fails.
    """
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        logger.warning("Delete failed: prompt_id=%s not found", prompt_id)
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        db.delete(prompt)
        db.commit()
        logger.info("Prompt deleted: id=%s", prompt_id)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to delete prompt %s: %s", prompt_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to delete prompt")


def duplicate_prompt(
    db: Session, prompt_id: str, user_id: Optional[str] = None
) -> Prompt:
    """
    Duplicate a Prompt by creating a new prompt with its first version.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): ID of the prompt to duplicate.
        user_id (Optional[str]): ID of the user performing duplication.

    Returns:
        Prompt: The duplicated prompt.

    Raises:
        HTTPException: If the original prompt is not found or DB operation fails.
    """
    existing = get_prompt(db, prompt_id)
    if not existing:
        logger.warning("Duplicate failed: prompt_id=%s not found", prompt_id)
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        # Get current version content for duplication
        result = db.execute(
            select(PromptVersion).filter(PromptVersion.id == existing.current_version_id)
        )
        latest_version = result.scalars().first()

        new_prompt_id = str(uuid.uuid4())
        new_prompt = Prompt(
            id=new_prompt_id,
            tenant_id=existing.tenant_id,
            title=f"{existing.title}_copy",
            description=existing.description,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_prompt)
        db.flush()

        first_version_id = str(uuid.uuid4())
        first_version = PromptVersion(
            id=first_version_id,
            prompt_id=new_prompt.id,
            version_number=1,
            body=latest_version.body if latest_version else "",
            style=latest_version.style if latest_version else None,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        db.add(first_version)
        db.flush()

        new_prompt.current_version_id = first_version.id
        db.commit()
        db.refresh(new_prompt)

        logger.info(
            "Prompt duplicated: original_id=%s, new_id=%s",
            prompt_id,
            new_prompt.id,
        )
        return new_prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to duplicate prompt %s: %s", prompt_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to duplicate prompt")


def rollback_prompt(
    db: Session, prompt_id: str, version_number: int, user_id: Optional[str] = None
) -> Prompt:
    """
    Rollback a Prompt to an older version by creating a new version from it.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): ID of the prompt to rollback.
        version_number (int): Version number to rollback to.
        user_id (Optional[str]): ID of the user performing the rollback.

    Returns:
        Prompt: The prompt rolled back to the specified version.

    Raises:
        HTTPException: If the target version is not found or DB operation fails.
    """
    result = db.execute(
        select(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version_number,
        )
    )
    target = result.scalars().first()
    if not target:
        logger.warning(
            "Rollback failed: prompt_id=%s, version=%s not found",
            prompt_id,
            version_number,
        )
        raise HTTPException(status_code=404, detail="Target version not found")

    try:
        result = db.execute(
            select(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version_number.desc())
        )
        latest_version = result.scalars().first()
        new_version_number = (
            (latest_version.version_number + 1) if latest_version else 1
        )

        rollback_version_id = str(uuid.uuid4())
        new_version = PromptVersion(
            id=rollback_version_id,
            prompt_id=prompt_id,
            version_number=new_version_number,
            body=target.body,
            style=target.style,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_version)
        db.flush()

        prompt = get_prompt(db, prompt_id)
        prompt.current_version_id = new_version.id
        prompt.updated_at = datetime.now(tz=timezone.utc)

        db.commit()
        db.refresh(prompt)

        logger.info(
            "Prompt rolled back: id=%s, rolled_to_version=%s, new_version=%s",
            prompt_id,
            version_number,
            new_version_number,
        )
        return prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Failed to rollback prompt %s to version %s: %s",
            prompt_id,
            version_number,
            str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to rollback prompt")


def get_versions(db: Session, prompt_id: str) -> List[PromptVersion]:
    """
    Retrieve all versions of a Prompt in ascending order.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): ID of the prompt.

    Returns:
        List[PromptVersion]: List of versions for the given prompt.
    """
    result = db.execute(
        select(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number.asc())
    )
    return result.scalars().all()
