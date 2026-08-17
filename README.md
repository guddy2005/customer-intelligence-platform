# Customer Intelligence Platform

A full-stack customer intelligence application for ingesting, validating, normalizing, classifying, and analyzing customer-related datasets. The project combines a FastAPI backend with a React + Vite frontend to process SMS and structured transaction data into a common data model.

## Overview

This platform supports:

- CSV file ingestion and validation
- Input-type detection for SMS and structured datasets
- Data cleaning and normalization
- Duplicate and rejection tracking
- Batch-based processing with progress reporting
- Classification and analytics workflows
- Web-based dashboard for operational monitoring

## Architecture

- Backend: Python + FastAPI
- Frontend: React + Vite
- Data layer: database-backed batch ingestion and processing
- Sample datasets: included under the backend sample_data folder

## Project Structure

```text
Customer_Intelligence_platform/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── database/
│   │   ├── modules/
│   │   ├── main.py
│   │   └── __init__.py
│   ├── sample_data/
│   └── tests/
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── .gitignore
└── README.md
```

## Tech Stack

### Backend

- Python 3.x
- FastAPI
- MySQL-compatible database setup
- CSV ingestion and validation pipeline

### Frontend

- React
- Vite
- Lucide React icons

## Prerequisites

Before running the app, ensure you have:

- Python installed
- Node.js and npm installed
- A database configured for the backend
- A virtual environment for Python dependencies

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Customer_Intelligence_platform
```

### 2. Create and activate a Python virtual environment

On Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

## Running the Application

### Start the backend

From the project root:

```bash
.\venv\Scripts\activate
uvicorn backend.app.main:app --reload
```

The API will run at:

- http://127.0.0.1:8000

### Start the frontend

```bash
cd frontend
npm run dev
```

The frontend will run at:

- http://localhost:5173

## API Notes

The backend exposes ingestion and classification endpoints under the API route prefix. The system also supports legacy ingestion routes for compatibility.

Useful endpoints include:

- Health check: /
- Ingestion routes: /api/v1/...
- Classification routes: /api/v1/...

## Sample Data

Sample CSVs are stored in:

- backend/sample_data/

These can be used to test the ingestion pipeline and validation behavior.

## Testing

Run backend tests from the project root:

```bash
pytest
```

If the repo uses a specific test runner or environment, check the backend test modules under:

- backend/tests/

## Development Notes

- Backend initialization runs database setup during application startup.
- The ingestion pipeline processes files in batches for scalability.
- The frontend dashboard loads recent ingestion runs from the backend whenever possible.

## License

This project is currently managed as an internal workspace project. Add your project license here if needed.

## Contributing

1. Create a feature branch.
2. Make changes with clear commit messages.
3. Validate the backend and frontend build/test flow.
4. Open a pull request for review.
