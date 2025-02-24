# Portfolio Application Backend

This is the backend for the portfolio application built using FastAPI and fastapi-admin.

## Project Structure

```
portfolio-backend
├── app
│   ├── main.py                # Entry point of the FastAPI application
│   ├── api
│   │   └── endpoints.py       # API endpoints for the portfolio application
│   ├── admin
│   │   └── admin_config.py    # Configuration for the FastAPI Admin interface
│   ├── models
│   │   └── user.py            # User model definition
│   └── core
│       └── config.py          # Application configuration settings
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd portfolio-backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

- The FastAPI application will be available at `http://127.0.0.1:8000`.
- The admin interface can be accessed at `http://127.0.0.1:8000/admin`.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes. 

## License

This project is licensed under the MIT License.