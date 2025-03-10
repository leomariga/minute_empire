# Backend FastAPI project

This directory contains the FastAPI backend for the Minute Empire application.

## Getting Started

These instructions will help you set up the Poetry project from scratch while maintaining the provided folder structure.

### Prerequisites

- Python 3.12 or later
- Poetry (package manager)
- MongoDB

### Initializing the Poetry Project

1. **Install Poetry** if you haven't already:
   ```bash
   # Windows
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

   # macOS/Linux
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Initialize a new Poetry project** in the backend directory:
   ```bash
   cd backend
   poetry init
   ```
   
   Follow the interactive prompts to set up your project:
   - Name: minute-empire-backend
   - Version: 0.1.0
   - Description: FastAPI backend for Minute Empire application
   - Author: Your Name
   - License: MIT (or your preferred license)
   - Python compatibility: ^3.12

3. **Add required dependencies**:
   ```bash
   poetry add fastapi uvicorn motor pydantic pydantic-settings python-dotenv
   ```

4. **Add development dependencies**:
   ```bash
   poetry add --group dev pytest black isort mypy
   ```

5. **Create a virtual environment and install dependencies**:
   ```bash
   poetry install
   ```

### Project Structure

The backend follows this structure:

```
backend/
├── app/                  # Application code
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API routes
│   │   └── endpoints/    # API endpoint modules
│   ├── core/             # Core application code
│   │   └── config.py     # Application configuration
│   ├── db/               # Database related code
│   │   └── mongodb.py    # MongoDB connection utilities
│   ├── models/           # Data models
│   └── schemas/          # Pydantic schemas
├── pyproject.toml        # Poetry configuration
└── Dockerfile            # Docker configuration
```

### Creating the Application Structure

After initializing the Poetry project, create the necessary directories and files:

```bash
# Create directory structure (if not already created)
mkdir -p app/api/endpoints app/core app/db app/models app/schemas
```

### Running the Application

To run the application in development mode:

```bash
poetry run uvicorn app.main:app --reload
```

This will start the FastAPI server at http://localhost:8000 with auto-reload enabled.

### Docker

The project includes a Dockerfile for containerization. To build and run the Docker container:

```bash
docker build -t minute-empire-backend .
docker run -p 8000:8000 minute-empire-backend
```

Or use Docker Compose from the project root:

```bash
cd ../docker
docker-compose up
```
