"""
Business logic for Prompt management.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from backend.models.prompt import Prompt
from backend.schemas.prompt_schemas import PromptCreate, PromptUpdate

DETAIL = "Prompt not found"


def create_prompt(db: Session, prompt: PromptCreate) -> Prompt:
    """
    Create a new prompt with version=1.
    """
    new_prompt = Prompt(
        name=prompt.name,
        content=prompt.content,
        tenant_id=prompt.tenant_id,
        version=1,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc)
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt


def get_prompts(db: Session, skip: int = 0, limit: int = 20):
    return db.query(Prompt).offset(skip).limit(limit).all()


def get_prompt(db: Session, prompt_id: int) -> Prompt:
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


def update_prompt(db: Session, prompt_id: int, prompt_update: PromptUpdate) -> Prompt:
    """
    Update prompt → creates a new version.
    """
    existing = get_prompt(db, prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail=DETAIL)

    # Create a new version record
    new_version = Prompt(
        name=existing.name,
        content=prompt_update.content,
        tenant_id=existing.tenant_id,
        version=existing.version + 1,
        created_at=existing.created_at,
        updated_at=datetime.now(tz=timezone.utc)
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def delete_prompt(db: Session, prompt_id: int) -> None:
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=DETAIL)

    db.delete(prompt)
    db.commit()


def duplicate_prompt(db: Session, prompt_id: int) -> Prompt:
    """
    Duplicate prompt → creates a new prompt with version=1.
    """
    existing = get_prompt(db, prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail=DETAIL)

    new_prompt = Prompt(
        name=f"{existing.name}_copy",
        content=existing.content,
        tenant_id=existing.tenant_id,
        version=1,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc)
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt


def rollback_prompt(db: Session, prompt_id: int, version: int) -> Prompt:
    """
    Rollback to an older version.
    Creates a new prompt version based on the rollback target.
    """
    target = db.query(Prompt).filter(
        Prompt.id == prompt_id, Prompt.version == version
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Target version not found")

    # Create a new version based on the target
    new_version = Prompt(
        name=target.name,
        content=target.content,
        tenant_id=target.tenant_id,
        version=target.version + 1,
        created_at=target.created_at,
        updated_at=datetime.now(tz=timezone.utc)
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def get_versions(db: Session, prompt_id: int):
    """
    List all versions of a given prompt.
    """
    return db.query(Prompt).filter(Prompt.id == prompt_id).order_by(Prompt.version).all()
