"""
API routes for managing prompts.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.prompt_schemas import PromptCreate, PromptUpdate, PromptResponse
from backend.core.database import get_db
from backend.services import prompt_service

router = APIRouter()


@router.post("/", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    """
    Create a new prompt (initial version = v1).
    """
    return prompt_service.create_prompt(db, prompt)


@router.get("/", response_model=List[PromptResponse])
def list_prompts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    List all prompts with pagination.
    """
    return prompt_service.get_prompts(db, skip=skip, limit=limit)


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single prompt by ID.
    """
    prompt = prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: int, prompt_update: PromptUpdate, db: Session = Depends(get_db)):
    """
    Update a prompt (creates a new version).
    """
    return prompt_service.update_prompt(db, prompt_id, prompt_update)


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """
    Delete a prompt (soft delete recommended).
    """
    prompt_service.delete_prompt(db, prompt_id)
    return {"message": f"Prompt {prompt_id} deleted successfully"}


@router.post("/{prompt_id}/duplicate", response_model=PromptResponse)
def duplicate_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """
    Duplicate a prompt (creates a copy with v1).
    """
    return prompt_service.duplicate_prompt(db, prompt_id)


@router.post("/{prompt_id}/versions/{version}/rollback", response_model=PromptResponse)
def rollback_prompt(prompt_id: int, version: int, db: Session = Depends(get_db)):
    """
    Rollback a prompt to a previous version.
    """
    return prompt_service.rollback_prompt(db, prompt_id, version)


@router.get("/{prompt_id}/versions", response_model=List[PromptResponse])
def list_versions(prompt_id: int, db: Session = Depends(get_db)):
    """
    List all versions of a prompt.
    """
    return prompt_service.get_versions(db, prompt_id)
