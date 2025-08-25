# Prompt Manager v2

A powerful, multi-tenant prompt management API built with FastAPI that provides comprehensive prompt lifecycle management, version control, and analytics capabilities.

## Features

- **Multi-Tenant Architecture**: Secure prompt storage with tenant isolation
- **Version Control**: Complete versioning system with rollback capabilities
- **Prompt Management**: Create, update, duplicate, and organize prompts
- **Metadata & Tagging**: Flexible metadata and tagging system for categorization
- **Analytics Ready**: Built-in support for usage analytics and insights
- **RESTful API**: Comprehensive REST endpoints with OpenAPI documentation
- **Database Agnostic**: Support for SQLite and PostgreSQL
- **Scalable Design**: Built for enterprise-scale prompt management

## Architecture

```
prompt-manager-v2/
├── backend/
│   ├── api/           # API route handlers
│   ├── app/           # FastAPI application setup
│   ├── core/          # Core configuration and database
│   ├── models/        # SQLAlchemy database models
│   ├── schemas/       # Pydantic schemas for request/response
│   ├── services/      # Business logic layer
│   └── utils/         # Utilities and helpers
├── frontend/          # Frontend application (future)
├── docs/              # Documentation
└── sql/               # Database scripts
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prompt-manager-v2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   # The database will be automatically initialized on first run
   python backend/app/app.py
   ```

4. **Run the application**
   ```bash
   # Development mode
   python backend/app/app.py
   
   # Or using uvicorn directly
   uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc
   - API Endpoints: http://localhost:8000

## API Endpoints

### Prompts Management

| Method   | Endpoint        | Description                           |
| -------- | --------------- | ------------------------------------- |
| `POST`   | `/prompts/`     | Create a new prompt                   |
| `GET`    | `/prompts/`     | List all prompts (paginated)          |
| `GET`    | `/prompts/{id}` | Get a specific prompt                 |
| `PUT`    | `/prompts/{id}` | Update a prompt (creates new version) |
| `DELETE` | `/prompts/{id}` | Delete a prompt                       |

### Version Control

| Method | Endpoint                                    | Description                    |
| ------ | ------------------------------------------- | ------------------------------ |
| `GET`  | `/prompts/{id}/versions`                    | List all versions of a prompt  |
| `POST` | `/prompts/{id}/versions/{version}/rollback` | Rollback to a specific version |
| `POST` | `/prompts/{id}/duplicate`                   | Duplicate a prompt             |

### Example Usage

```bash
# Create a new prompt
curl -X POST "http://localhost:8000/prompts/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Support Template",
    "description": "Template for customer support responses",
    "body": "Hello {customer_name}, thank you for contacting us...",
    "tenant_id": "tenant-123"
  }'

# List prompts with pagination
curl "http://localhost:8000/prompts/?skip=0&limit=20"

# Get a specific prompt
curl "http://localhost:8000/prompts/1"

# Update a prompt (creates new version)
curl -X PUT "http://localhost:8000/prompts/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Customer Support Template",
    "body": "Hi {customer_name}, thanks for reaching out..."
  }'
```

## Database Schema

### Core Models

- **Prompt**: Main prompt entity with metadata and relationships
- **PromptVersion**: Version history for each prompt
- **PromptMetadata**: Key-value metadata for prompts
- **PromptTag**: Tags for categorization and search

### Key Features

- **UUID-based IDs**: Secure, non-sequential identifiers
- **Soft Deletes**: Archive prompts instead of hard deletion
- **Tenant Isolation**: Multi-tenant data separation
- **Version Tracking**: Complete audit trail of changes
- **Flexible Metadata**: Extensible key-value storage

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./prompt_manager.db
# DATABASE_URL=postgresql://user:password@localhost/prompt_manager

# Application Settings
APP_NAME=Prompt Manager
APP_VERSION=1.0.0
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here
```

### Database Migration

```bash
# Using SQLite (default)
# Database file: prompt_manager.db

# Using PostgreSQL
# Update DATABASE_URL in environment variables
```

## Security Features

- **Tenant Isolation**: Secure multi-tenant architecture
- **CORS Configuration**: Configurable cross-origin settings
- **Input Validation**: Pydantic schema validation
- **Error Handling**: Comprehensive error handling and logging

## Monitoring & Analytics

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Performance Metrics**: Built-in request/response timing
- **Health Checks**: Application health monitoring endpoints
- **Analytics Ready**: Prepared for usage analytics integration

## Testing

```bash
# Run tests (when test suite is available)
pytest

# API testing with curl or tools like Postman/Insomnia
# Use the interactive docs at http://localhost:8000/docs
```

## Documentation

- **API Documentation**: Available at `/docs` (Swagger UI)
- **Alternative Docs**: Available at `/redoc` (ReDoc)
- **OpenAPI Spec**: Available at `/openapi.json`

## Development

### Project Structure

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: Lightning-fast ASGI server

### Code Quality

- **Type Hints**: Full type annotation support
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging throughout the application
- **Documentation**: Detailed docstrings and comments

## Deployment

### Docker (Recommended)

```dockerfile
# Example Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Deployment

```bash
# Using Gunicorn for production
gunicorn backend.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 👨‍💻 Author

**Sourav Das**
- Email: sourav.bt.kt@gmail.com

## 🙏 Acknowledgments

- FastAPI framework for the excellent foundation
- SQLAlchemy for robust ORM capabilities
- The Python community for amazing tools and libraries

---

For more information, visit the [API documentation](http://localhost:8000/docs) or check out the [project repository](https://github.com/your-repo/prompt-manager-v2).
