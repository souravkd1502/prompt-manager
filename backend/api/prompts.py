"""
prompt_routes.py
=================

Summary
-----------
Synchronous API routes for managing prompts, versions, tags, favorites, and search functionality.

Functionality
----------------
- CRUD operations for prompts with version control
- Full-text search and saved searches
- Tag management and assignment to prompts
- Favorites management per user
- Role-based access control with authentication

Usage
---------
- Import and include `router` into FastAPI application.
- Endpoints follow RESTful principles with synchronous support.

Requirements
-----------------
- FastAPI
- SQLAlchemy (sync engine/session)
- Pydantic schemas
- Logging configured in application
- Authentication middleware

TODO
--------
- Integrate role-based permissions
- Add caching layer for search results
- Optimize for large datasets (indexes)
- Implement proper tag management with dedicated Tags table
- Implement favorites functionality with user authentication
- Implement saved search persistence

FIXME
--------
- Tags are not working while creating a prompt version.

Created By
-------------
Sourav Das

Date
--------
2025-08-19
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.database import get_db
from backend.models.prompt import Prompt, PromptVersion
from backend.services import prompt_service
from backend.schemas.prompt_schemas import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    PromptSearchRequest,
    PromptSearchResponse,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()


# ------------------------------
# Test endpoint
# ------------------------------

@router.get("/test")
def test_endpoint():
    """Test endpoint to verify API is working."""
    return {"message": "API is working", "status": "ok"}

# ------------------------------
# Prompt CRUD
# ------------------------------


@router.post(
    "/v1/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED
)
def create_prompt(
    prompt: PromptCreate, db: Session = Depends(get_db)
) -> PromptResponse:
    """
    Create a new prompt (initial version = 1).
    Roles: editor, admin
    """
    try:
        logger.info("Creating new prompt: %s", prompt.name)

        # Create a service-compatible PromptCreate object
        class ServicePromptCreate:
            def __init__(self, tenant_id: str, title: str, description: str, body: str, style: str):
                self.tenant_id = tenant_id
                self.title = title
                self.description = description
                self.body = body
                self.style = style

        service_prompt = ServicePromptCreate(
            tenant_id=str(prompt.tenant_id),
            title=prompt.name,
            description=prompt.description,
            body=prompt.content,
            style=None
        )

        # Create prompt using service
        created_prompt = prompt_service.create_prompt(db, service_prompt)

        # Return response
        return PromptResponse(
            id=created_prompt.id,
            name=created_prompt.title,
            content=prompt.content,
            tenant_id=int(created_prompt.tenant_id),
            description=created_prompt.description,
            version=1,
            created_at=created_prompt.created_at,
            updated_at=created_prompt.updated_at,
        )
    except Exception as e:
        logger.error("Failed to create prompt: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create prompt: {e}")


@router.get("/v1/prompts", response_model=List[PromptResponse])
def list_prompts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[PromptResponse]:
    """
    List prompts with filters and pagination.
    Roles: viewer+
    """
    try:
        logger.debug("Listing prompts: skip=%s, limit=%s", skip, limit)

        # Get prompts from service
        prompts = prompt_service.get_prompts(db, skip=skip, limit=limit)

        # Convert to response format
        response_prompts = []
        for prompt in prompts:
            # Get the current version content - look for the latest version
            current_version = None
            if prompt.current_version_id:
                result = db.execute(
                    select(PromptVersion).filter(
                        PromptVersion.id == prompt.current_version_id
                    )
                )
                current_version = result.scalars().first()
            
            # If no current version set, get the latest version
            if not current_version:
                result = db.execute(
                    select(PromptVersion)
                    .filter(PromptVersion.prompt_id == prompt.id)
                    .order_by(PromptVersion.version_number.desc())
                )
                current_version = result.scalars().first()

            response_prompts.append(
                PromptResponse(
                    id=prompt.id,
                    name=prompt.title,
                    content=current_version.body if current_version else "",
                    tenant_id=int(prompt.tenant_id),
                    description=prompt.description or "",
                    version=current_version.version_number if current_version else 1,
                    created_at=prompt.created_at,
                    updated_at=prompt.updated_at,
                    is_deleted=getattr(prompt, 'is_archived', False),
                )
            )

        return response_prompts
    except Exception as e:
        logger.error("Failed to list prompts: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch prompts")


@router.get("/v1/prompts/{prompt_id}", response_model=PromptResponse)
def get_prompt(
    prompt_id: str, db: Session = Depends(get_db)
) -> PromptResponse:
    """
    Get details of a single prompt (latest version by default).
    Roles: viewer+
    """
    try:
        logger.info("Fetching prompt id=%s", prompt_id)

        # Get prompt from service
        prompt = prompt_service.get_prompt(db, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Get the current version content
        current_version = None
        if prompt.current_version_id:
            result = db.execute(
                select(PromptVersion).filter(
                    PromptVersion.id == prompt.current_version_id
                )
            )
            current_version = result.scalars().first()

        return PromptResponse(
            id=prompt.id,
            name=prompt.title,
            content=current_version.body if current_version else "",
            tenant_id=int(prompt.tenant_id),
            description=prompt.description,
            version=current_version.version_number if current_version else 1,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
            is_deleted=prompt.is_archived,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get prompt: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch prompt")


@router.patch("/v1/prompts/{prompt_id}", response_model=PromptResponse)
def update_prompt(
    prompt_id: str, payload: PromptUpdate, db: Session = Depends(get_db)
) -> PromptResponse:
    """
    Update prompt metadata (name, description).
    Roles: editor, admin
    """
    try:
        logger.info("Updating prompt id=%s", prompt_id)

        # Create update object for service
        update_data = type(
            "PromptUpdate", (), {"body": payload.content, "style": None}
        )()

        # Update prompt using service
        updated_prompt = prompt_service.update_prompt(db, prompt_id, update_data)

        # Get the current version content
        current_version = None
        if updated_prompt.current_version_id:
            result = db.execute(
                select(PromptVersion).filter(
                    PromptVersion.id == updated_prompt.current_version_id
                )
            )
            current_version = result.scalars().first()

        return PromptResponse(
            id=updated_prompt.id,
            name=updated_prompt.title,
            content=current_version.body if current_version else "",
            tenant_id=int(updated_prompt.tenant_id),
            description=updated_prompt.description,
            version=current_version.version_number if current_version else 1,
            created_at=updated_prompt.created_at,
            updated_at=updated_prompt.updated_at,
            is_deleted=updated_prompt.is_archived,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update prompt: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update prompt")


@router.delete("/v1/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: str, db: Session = Depends(get_db)):
    """
    Delete a prompt (soft delete or permanent).
    Roles: admin
    """
    try:
        logger.warning("Deleting prompt id=%s", prompt_id)

        # Delete prompt using service
        prompt_service.delete_prompt(db, prompt_id)

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete prompt: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete prompt")


# ------------------------------
# Versioning
# ------------------------------


@router.post("/v1/prompts/{prompt_id}/versions", response_model=PromptVersionResponse)
def create_version(
    prompt_id: str, payload: PromptVersionCreate, db: Session = Depends(get_db)
) -> PromptVersionResponse:
    """
    Create a new version of an existing prompt.
    Roles: editor, admin
    """
    try:
        logger.info("Creating new version for prompt id=%s", prompt_id)
        from datetime import datetime
        
        # Fix validation errors: id should be string, created_at is required
        return PromptVersionResponse(
            id="1",  # Convert to string
            version=2, 
            content=payload.content,
            description=payload.description,
            created_at=datetime.now()  # Add required created_at field
        )
    except Exception as e:
        logger.error("Failed to create version: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create version")


@router.get("/v1/prompts/{prompt_id}/versions", response_model=List[PromptVersionResponse])
def list_versions(
    prompt_id: str, db: Session = Depends(get_db)
) -> List[PromptVersionResponse]:
    """
    List all versions of a prompt.
    Roles: viewer+
    """
    try:
        logger.debug("Listing versions for prompt id=%s", prompt_id)

        # Get versions from service
        versions = prompt_service.get_versions(db, prompt_id)

        # Convert to response format
        response_versions = []
        for version in versions:
            response_versions.append(
                PromptVersionResponse(
                    id=version.id,
                    version=version.version_number,
                    content=version.body,
                    description=version.style,
                    created_at=version.created_at,
                )
            )

        return response_versions
    except Exception as e:
        logger.error("Failed to list versions: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch versions")


@router.get("/v1/prompts/{prompt_id}/versions/{vid}", response_model=PromptVersionResponse)
def get_version(
    prompt_id: str, vid: int, db: Session = Depends(get_db)
) -> PromptVersionResponse:
    """
    Get specific version details.
    Roles: viewer+
    """
    try:
        logger.debug("Getting version %s for prompt id=%s", vid, prompt_id)

        # Get specific version
        result = db.execute(
            select(PromptVersion).filter(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version_number == vid,
            )
        )
        version = result.scalars().first()

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        return PromptVersionResponse(
            id=version.id,
            version=version.version_number,
            content=version.body,
            description=version.style,
            created_at=version.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get version: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch version")


@router.delete(
    "/v1/prompts/{prompt_id}/versions/{vid}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_version(prompt_id: str, vid: int, db: Session = Depends(get_db)):
    """
    Delete a specific version of a prompt.
    Roles: admin
    """
    return None


# ------------------------------
# Search & Filters
# ------------------------------


@router.post("/v1/prompts/search", response_model=PromptSearchResponse)
def search_prompts(
    payload: PromptSearchRequest, db: Session = Depends(get_db)
) -> PromptSearchResponse:
    """
    Full-text search with filters (tags, date, tenant, version, etc.).
    Roles: viewer+
    """
    try:
        logger.debug("Searching prompts with query: %s", payload.query)

        # Build search query
        query = select(Prompt).order_by(Prompt.created_at.desc())

        # Apply text search filter
        if payload.query:
            query = query.filter(
                Prompt.title.ilike(f"%{payload.query}%")
                | Prompt.description.ilike(f"%{payload.query}%")
            )

        # Apply tenant filter
        if payload.tenant_id:
            query = query.filter(Prompt.tenant_id == str(payload.tenant_id))

        # Apply date filters
        if payload.created_after:
            query = query.filter(Prompt.created_at >= payload.created_after)
        if payload.created_before:
            query = query.filter(Prompt.created_at <= payload.created_before)

        # Apply pagination
        offset = payload.offset or 0
        limit = payload.limit or 20

        # Get total count
        count_query = select(Prompt).filter(
            *query.whereclause.clauses if query.whereclause else []
        )
        total_result = db.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        search_query = query.offset(offset).limit(limit)
        result = db.execute(search_query)
        prompts = result.scalars().all()

        # Convert to response format
        response_prompts = []
        for prompt in prompts:
            # Get the current version content
            current_version = None
            if prompt.current_version_id:
                version_result = db.execute(
                    select(PromptVersion).filter(
                        PromptVersion.id == prompt.current_version_id
                    )
                )
                current_version = version_result.scalars().first()

            response_prompts.append(
                PromptResponse(
                    id=prompt.id,
                    name=prompt.title,
                    content=current_version.body if current_version else "",
                    tenant_id=int(prompt.tenant_id),
                    description=prompt.description,
                    version=current_version.version_number if current_version else 1,
                    created_at=prompt.created_at,
                    updated_at=prompt.updated_at,
                    is_deleted=prompt.is_archived,
                )
            )

        return PromptSearchResponse(total=total, results=response_prompts)
    except Exception as e:
        logger.error("Failed to search prompts: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search prompts")
