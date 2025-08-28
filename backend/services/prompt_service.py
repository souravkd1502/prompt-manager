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
import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from backend.models.prompt import Prompt
from backend.schemas.prompt_schemas import PromptCreateRequest

# Configure module-level logger
logger = logging.getLogger(__name__)

DETAIL = "Prompt not found"


# -------------------------------
# CRUD Service Functions
# -------------------------------


from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_, asc, desc
from fastapi import HTTPException
import logging

from backend.schemas.prompt_schemas import PromptListRequest, PromptCreateResponse

logger = logging.getLogger(__name__)


def create_prompt(db: Session, prompt: PromptCreateRequest) -> Prompt:
    """
    Create a new Prompt with its initial version and optional tags.

    This function handles:
    - Normalizing tags into JSON for DB storage.
    - Assigning current_version_id = 1 (first version).
    - Handling database transactions with rollback on error.

    Args:
        db (Session): Active SQLAlchemy session.
        prompt (PromptCreateRequest): Prompt data from request body.

    Returns:
        Prompt: Newly created prompt ORM object.

    Raises:
        HTTPException: If database operation fails.
    """
    try:
        # Normalize tags (ensure list, convert to JSON string for DB storage)
        normalized_tags = []
        if prompt.tags:
            if isinstance(prompt.tags, str):
                # Handle case where tags are passed as comma-separated string
                normalized_tags = [
                    tag.strip() for tag in prompt.tags.split(",") if tag.strip()
                ]
            elif isinstance(prompt.tags, list):
                normalized_tags = [
                    str(tag).strip() for tag in prompt.tags if str(tag).strip()
                ]
        tags_json = json.dumps(normalized_tags)

        # Create new prompt instance
        new_prompt = Prompt(
            tenant_id=prompt.tenant_id,
            created_by=prompt.created_by,
            title=prompt.title,
            description=prompt.description,
            prompt_text=prompt.prompt_text,
            is_archived=False,
            tags=tags_json,
            current_version_id=1,  # Always start at version 1
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        # Save to DB
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)

        logger.info(
            "Prompt created successfully with id=%s, tenant_id=%s",
            new_prompt.id,
            new_prompt.tenant_id,
        )
        return new_prompt

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error while creating prompt: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Database error while creating prompt: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "Unexpected error while creating prompt: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Unexpected error while creating prompt: {str(e)}"
        )


def list_prompts(
    db: Session,
    request: PromptListRequest,
    title: Optional[str] = None,
    is_archived: Optional[bool] = None,
    tags: Optional[str] = None,
    created_by: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> List[PromptCreateResponse]:
    """
    Retrieve prompts with filtering, sorting, and pagination.

    Args:
        db (Session): Database session.
        request (PromptListRequest): Contains tenant_id, offset, limit.
        title (str, optional): Substring filter on title.
        is_archived (bool, optional): Archived filter.
        tags (str, optional): Comma-separated tags filter.
        created_by (int, optional): Creator filter.
        date_from (datetime, optional): Lower bound for created_at.
        date_to (datetime, optional): Upper bound for created_at.
        sort_by (str): Field to sort by (id, title, created_at, updated_at).
        sort_order (str): Sorting direction ("asc" or "desc").

    Returns:
        List[PromptCreateResponse]: Filtered and sorted prompt list.

    Raises:
        RuntimeError: On DB error or unexpected failure.
    """
    try:
        logger.debug(
            "Service → Fetching prompts [tenant_id=%s, filters=%s]",
            request.tenant_id,
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

        query = db.query(Prompt).filter(Prompt.tenant_id == request.tenant_id)

        # Filtering
        if title:
            query = query.filter(Prompt.title.ilike(f"%{title}%"))
        if is_archived is not None:
            query = query.filter(Prompt.is_archived == is_archived)
        if created_by is not None:
            query = query.filter(Prompt.created_by == created_by)
        if date_from:
            query = query.filter(Prompt.created_at >= date_from)
        if date_to:
            query = query.filter(Prompt.created_at <= date_to)
        if tags:
            tag_list = [t.strip().lower() for t in tags.split(",")]
            query = query.filter(
                or_(*[Prompt.tags.ilike(f"%{tag}%") for tag in tag_list])
            )

        # Sorting (default: created_at desc)
        sort_field = getattr(Prompt, sort_by, Prompt.created_at)
        query = query.order_by(
            asc(sort_field) if sort_order.lower() == "asc" else desc(sort_field)
        )

        # Pagination
        query = query.offset(request.offset).limit(request.limit)

        results = query.all()

        prompts: List[PromptCreateResponse] = [
            PromptCreateResponse.model_validate(row, from_attributes=True)
            for row in results
        ]

        logger.info(
            "Service → Prompts retrieved [tenant_id=%s, count=%s]",
            request.tenant_id,
            len(prompts),
        )

        return prompts

    except SQLAlchemyError as db_err:
        logger.exception("DB error in list_prompts → %s", str(db_err))
        raise RuntimeError("Database error while fetching prompts") from db_err
    except Exception as e:
        logger.exception("Unexpected error in list_prompts → %s", str(e))
        raise RuntimeError("Unexpected error while fetching prompts") from e


def get_prompt_by_id(db: Session, prompt_id: int) -> Optional[PromptCreateResponse]:
    """
    Retrieve a single prompt by its ID.

    Optimized to fetch only one record and map it to the response schema.

    Args:
        db (Session): Active SQLAlchemy session.
        prompt_id (int): Unique ID of the prompt.

    Returns:
        Optional[PromptCreateResponse]: The prompt object if found, else None.

    Raises:
        RuntimeError: On database failure or unexpected errors.
    """
    if prompt_id <= 0:
        logger.error("Invalid prompt_id=%s provided to get_prompt_by_id", prompt_id)
        raise ValueError("prompt_id must be a positive integer")

    try:
        logger.debug("Querying prompt [id=%s]", prompt_id)

        # Use `get` for optimized primary key lookup
        prompt: Optional[Prompt] = db.get(Prompt, prompt_id)

        if not prompt:
            logger.info("Prompt not found in DB [id=%s]", prompt_id)
            return None

        logger.debug("Prompt found [id=%s, title=%s]", prompt.id, prompt.title)

        # Convert SQLAlchemy object to Pydantic schema
        return PromptCreateResponse.model_validate(prompt, from_attributes=True)

    except SQLAlchemyError as db_err:
        logger.exception("Database error while fetching prompt [id=%s]: %s", prompt_id, str(db_err))
        raise RuntimeError("Database error while fetching prompt") from db_err

    except Exception as e:
        logger.exception("Unexpected error in get_prompt_by_id [id=%s]: %s", prompt_id, str(e))
        raise RuntimeError("Unexpected error while fetching prompt") from e