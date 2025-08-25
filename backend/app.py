"""
Application entry point and FastAPI initialization for the Prompt Manager backend.
"""

import sys
import os

# Add project root to sys.path to ensure backend imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import uvicorn

# Custom libraries
from backend.api import prompts  # APIs related to Prompts
from backend.core.database import init_db  # Database initialization
from backend.utils.logger import setup_logging  # Logging


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with detailed OpenAPI metadata.
    Returns:
        FastAPI: Configured FastAPI app instance.
    """

    app = FastAPI(
        title="Prompt Manager",
        description=(
            "🚀 A multi-tenant Prompt Manager API with support for versioning, "
            "analytics, and advanced prompt lifecycle management.\n\n"
            "### Features\n"
            "- Multi-tenant prompt storage\n"
            "- Version control for prompts\n"
            "- Analytics & usage insights\n"
            "- Secure and scalable"
        ),
        version="1.0.0",
        summary="Centralized Prompt Management API",
        contact={
            "name": "Sourav Das",
            "email": "sourav.bt.kt@gmail.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "Prompts",
                "description": "Operations related to managing prompts, including creation, versioning, and retrieval.",
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Register routers
    app.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        # Add branding/logo
        openapi_schema["info"]["x-logo"] = {
            "url": "https://cdn-icons-png.flaticon.com/512/4727/4727496.png"
        }
        # Ensure components (models) exist
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Startup event
    @app.on_event("startup")
    def startup_event():
        """Initialize database and logging on application startup."""
        setup_logging()
        init_db()

    return app


# Expose FastAPI app for ASGI servers
app = create_app()


if __name__ == "__main__":
    # Run the application directly with: python app.py
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)