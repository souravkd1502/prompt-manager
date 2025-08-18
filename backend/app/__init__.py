"""
app/__init__.py
-----------------

This module creates and configures the FastAPI application, initializes database connections, and registers routers.
"""

# Import dependencies
from fastapi import FastAPI

# Custom libraries
from backend.api import prompts  # APIs related to Prompts (Create, edit, etc)
from backend.core.database import init_db  # Database initialization
from backend.utils.logger import setup_logging  # Logging


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with detailed OpenAPI metadata.

    Returns:
        FastAPI: Configured FastAPI app instance.
    """
    # Setup logging before app creation
    setup_logging()

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
            "email": "ssourav.bt.kt@gmail.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        terms_of_service="https://your-company.com/terms",
        openapi_tags=[
            {
                "name": "Prompts",
                "description": "Operations related to managing prompts, including creation, versioning, and retrieval.",
            },
            {
                "name": "Analytics",
                "description": "Endpoints for analyzing prompt usage and performance.",
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Initialize database
    init_db()

    # Register routers
    app.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
    # (example) app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

    # Enable CORS (optional)
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
            routes=app.routes,   # <-- ensures all routers + models are included
        )
        # Add branding/logo without removing schemas
        openapi_schema["info"]["x-logo"] = {
            "url": "https://your-company.com/static/logo.png"
        }

        # Ensure components (models) are preserved
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    # Assign the custom OpenAPI function to the app
    app.openapi = custom_openapi

    return app


# Expose the app instance for ASGI servers (uvicorn/gunicorn)
app = create_app()
