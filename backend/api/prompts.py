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
- Add filters, sorting to list prompts. Also add info on number of versions
- update not working, also tags update, is archived, is favorite
- while creating content is not being saved


Created By
-------------
Sourav Das

Date
--------
2025-08-19
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.services import prompt_service
from backend.schemas.prompt_schemas import (
    PromptCreateRequest,
    PromptCreateResponse,
    PromptListRequest,
    PromptListResponse,
)

from typing import Optional
from datetime import datetime

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
    "/v1/prompts",
    response_model=PromptCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prompt(
    prompt: PromptCreateRequest,
    db: Session = Depends(get_db),
) -> PromptCreateResponse:
    """
    Create a new Prompt (initial version = 1).

    Roles:
        - editor
        - admin

    Args:
        prompt (PromptCreateRequest): Schema containing prompt data from client.
        db (Session): SQLAlchemy database session.

    Returns:
        PromptCreateResponse: API response with created prompt details.

    Raises:
        HTTPException: On failure to create prompt or unexpected server errors.
    """
    logger.info(
        "API Request: Creating new prompt for tenant_id=%s, title=%s",
        prompt.tenant_id,
        prompt.title,
    )

    try:
        # Call service layer to handle DB creation
        new_prompt = prompt_service.create_prompt(db, prompt)

        # Log success with identifiers
        logger.info(
            "Prompt created successfully: id=%s, tenant_id=%s, title=%s",
            new_prompt.id,
            new_prompt.tenant_id,
            new_prompt.title,
        )

        # Return structured API response
        return PromptCreateResponse(
            id=new_prompt.id,
            tenant_id=new_prompt.tenant_id,
            title=new_prompt.title,
            description=new_prompt.description,
            prompt_text=new_prompt.prompt_text,
            is_archived=new_prompt.is_archived,
            created_by=new_prompt.created_by,
            current_version_id=new_prompt.current_version_id,
            created_at=new_prompt.created_at,
            updated_at=new_prompt.updated_at,
            tags=new_prompt.tags,
        )

    except HTTPException as e:
        # Service layer already handled/logged error → just re-raise
        raise e

    except Exception as e:
        # Catch any unexpected server-side errors
        logger.exception(
            "Unexpected error in API while creating prompt (tenant_id=%s, title=%s): %s",
            prompt.tenant_id,
            prompt.title,
            str(e),
        )
        raise HTTPException(
            status_code=500, detail="Unexpected server error while creating prompt"
        )


@router.get(
    "/v1/prompts",
    response_model=PromptListResponse,
    status_code=status.HTTP_200_OK,
)
def list_prompts(
    tenant_id: int = Query(..., description="ID of the tenant"),
    offset: int = Query(0, description="Number of prompts to skip"),
    limit: int = Query(100, description="Maximum number of prompts to return"),
    title: Optional[str] = Query(None, description="Filter by title (substring match)"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    tags: Optional[str] = Query(None, description="Filter by comma-separated tags"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    date_from: Optional[datetime] = Query(None, description="Created at >= date"),
    date_to: Optional[datetime] = Query(None, description="Created at <= date"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> PromptListResponse:
    """
    Retrieve a list of prompts with advanced filtering, sorting, and pagination.

    Supported filters:
        - tenant_id (required)
        - title (substring match)
        - is_archived (bool)
        - tags (comma-separated)
        - created_by (user ID)
        - date_from/date_to (created_at range)

    Sorting:
        - sort_by: id, title, created_at, updated_at
        - sort_order: asc | desc

    Pagination:
        - offset, limit

    Args:
        tenant_id (int): Tenant ID (mandatory).
        offset (int): Records to skip (default=0).
        limit (int): Max records to return (default=100).
        title (str): Optional substring match filter for title.
        is_archived (bool): Optional archived filter.
        tags (str): Comma-separated tags for filtering.
        created_by (int): Filter prompts by creator.
        date_from (datetime): Lower bound for created_at.
        date_to (datetime): Upper bound for created_at.
        sort_by (str): Field to sort by.
        sort_order (str): asc or desc.
        db (Session): Database session.

    Returns:
        PromptListResponse: Paginated list of prompts with metadata.
    """
    logger.info(
        "API Request → Listing prompts [tenant_id=%s, offset=%s, limit=%s, filters=%s]",
        tenant_id,
        offset,
        limit,
        {
            "title": title,
            "is_archived": is_archived,
            "tags": tags,
            "created_by": created_by,
            "date_from": date_from,
            "date_to": date_to,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )

    try:
        request = PromptListRequest(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
        )

        prompts = prompt_service.list_prompts(
            db=db,
            request=request,
            title=title,
            is_archived=is_archived,
            tags=tags,
            created_by=created_by,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total_prompts = len(prompts)

        return PromptListResponse(total=total_prompts, prompts=prompts)

    except HTTPException as e:
        logger.error("Handled HTTPException in list_prompts: %s", str(e))
        raise e

    except Exception as e:
        logger.exception("Unexpected error in API list_prompts: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error while listing prompts",
        )


@router.get(
    "/v1/prompts/{prompt_id}",
    response_model=PromptCreateResponse,
    status_code=status.HTTP_200_OK,
)
def get_prompt(
    prompt_id: int = Path(..., description="ID of the prompt to retrieve"),
    db: Session = Depends(get_db),
) -> PromptCreateResponse:
    """
    Retrieve a single prompt by its unique ID.

    Args:
        prompt_id (int): Unique ID of the prompt (path parameter).
        db (Session): SQLAlchemy database session dependency.

    Returns:
        PromptCreateResponse: The prompt details if found.

    Raises:
        HTTPException (404): If the prompt does not exist.
        HTTPException (500): If any unexpected server/database error occurs.
    """
    logger.info("API Request → Fetching prompt [id=%s]", prompt_id)

    try:
        prompt = prompt_service.get_prompt_by_id(db, prompt_id)

        if not prompt:
            logger.warning("Prompt not found [id=%s]", prompt_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt with id={prompt_id} not found",
            )

        logger.info("Prompt retrieved successfully [id=%s]", prompt_id)
        return prompt

    except HTTPException:
        raise  # Re-raise known HTTP exceptions

    except Exception as e:
        logger.exception(
            "Unexpected error in API get_prompt [id=%s]: %s", prompt_id, str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error while retrieving prompt",
        )
