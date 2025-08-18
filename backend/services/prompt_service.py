"""
SQLAlchemy models for logs and analytics.
-----------------------------------------

Functionality
----------------
Defines the `AuditLog` model to record audit trail events such as
create, update, rollback, and delete actions performed on prompts.
Captures details about the prompt, user, old version, new version,
and the timestamp of the action.

Usage
---------
- Import the model in database migration and session logic.
- Use it to persist audit records whenever a prompt-related action occurs.
- Query the table for analytics, accountability, and debugging.

Requirements
-----------------
- SQLAlchemy ORM
- A database engine supported by SQLAlchemy
- Models: `prompts`, `users`, `prompt_versions`

TODO
--------
- Add indexing on frequently queried fields (e.g., `user_id`, `action`, `timestamp`)
- Implement relationship properties for easier joins with `Prompt`, `User`, and `PromptVersion`

FIXME
--------
- None identified at present

Created By
-------------
Your Name

Date
--------
2025-08-19
"""

# Import Dependencies
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime, timezone
import logging
from typing import Optional, List

from backend.models.prompt import Prompt, PromptVersion
from backend.schemas.prompt_schemas import PromptCreate, PromptUpdate

# Configure module-level logger
logger = logging.getLogger(__name__)

DETAIL = "Prompt not found"


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
        new_prompt = Prompt(
            tenant_id=prompt.tenant_id,
            title=prompt.title,
            description=prompt.description,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_prompt)
        db.flush()  # Ensure new_prompt.id is available

        first_version = PromptVersion(
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

        logger.info(f"Prompt created: id={new_prompt.id}, title={new_prompt.title}")
        return new_prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to create prompt")


def get_prompts(db: Session, skip: int = 0, limit: int = 20) -> List[Prompt]:
    """
    Retrieve a paginated list of Prompts.

    Args:
        db (Session): SQLAlchemy session.
        skip (int): Offset for pagination.
        limit (int): Maximum number of prompts to return.

    Returns:
        List[Prompt]: List of prompts.
    """
    return db.query(Prompt).offset(skip).limit(limit).all()


def get_prompt(db: Session, prompt_id: str) -> Optional[Prompt]:
    """
    Retrieve a single Prompt by ID.

    Args:
        db (Session): SQLAlchemy session.
        prompt_id (str): The prompt's ID.

    Returns:
        Optional[Prompt]: The Prompt if found, else None.
    """
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


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
        logger.warning(f"Update failed: prompt_id={prompt_id} not found")
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        latest_version = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version_number.desc())
            .first()
        )
        new_version_number = (
            (latest_version.version_number + 1) if latest_version else 1
        )

        new_version = PromptVersion(
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

        logger.info(f"Prompt updated: id={prompt_id}, new_version={new_version_number}")
        return prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update prompt {prompt_id}: {e}")
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
        logger.warning(f"Delete failed: prompt_id={prompt_id} not found")
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        db.delete(prompt)
        db.commit()
        logger.info(f"Prompt deleted: id={prompt_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete prompt {prompt_id}: {e}")
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
        logger.warning(f"Duplicate failed: prompt_id={prompt_id} not found")
        raise HTTPException(status_code=404, detail=DETAIL)

    try:
        # Get current version content for duplication
        latest_version = (
            db.query(PromptVersion)
            .filter(PromptVersion.id == existing.current_version_id)
            .first()
        )

        new_prompt = Prompt(
            tenant_id=existing.tenant_id,
            title=f"{existing.title}_copy",
            description=existing.description,
            created_by=user_id,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        db.add(new_prompt)
        db.flush()

        first_version = PromptVersion(
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
            f"Prompt duplicated: original_id={prompt_id}, new_id={new_prompt.id}"
        )
        return new_prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to duplicate prompt {prompt_id}: {e}")
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
    target = (
        db.query(PromptVersion)
        .filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version_number,
        )
        .first()
    )
    if not target:
        logger.warning(
            f"Rollback failed: prompt_id={prompt_id}, version={version_number} not found"
        )
        raise HTTPException(status_code=404, detail="Target version not found")

    try:
        latest_version = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version_number.desc())
            .first()
        )
        new_version_number = (
            (latest_version.version_number + 1) if latest_version else 1
        )

        new_version = PromptVersion(
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
            f"Prompt rolled back: id={prompt_id}, rolled_to_version={version_number}, new_version={new_version_number}"
        )
        return prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Failed to rollback prompt {prompt_id} to version {version_number}: {e}"
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
    return (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number.asc())
        .all()
    )
