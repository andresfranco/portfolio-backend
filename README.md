# Portfolio Backend API

This is the backend API for the Portfolio project, built with FastAPI and SQLAlchemy.

## Features

- User Management with Role-based Access Control
- SQLite Database with Alembic Migrations
- FastAPI REST API
- Password Hashing with bcrypt
- Exception Handling and Logging

## Getting Started

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation is available at http://localhost:8000/docs
