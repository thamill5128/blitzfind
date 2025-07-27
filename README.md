# BlitzFind

A simple key-value query system using Python with GeoJSON import capabilities.

## Features

1. Import data from GeoJSON files to create a database
2. Import data from SpatiaLite databases with geometry support
3. Query by ID and return its value
4. Full CRUD operations for key-value pairs
5. RESTful API with FastAPI
6. SQLite database for lightweight storage
7. Automatic API documentation with Swagger UI

## Installation

### Option 1: Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd blitzfind
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

The server will start on `http://localhost:8000`

### Option 2: Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd blitzfind
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
python app.py
```

Or use uvicorn directly:
```bash
uvicorn app:app --reload
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Health Check
- `GET /` - Check if the API is running

### Import Data
- `POST /import/geojson` - Import data from a GeoJSON file
  - Upload a GeoJSON file with features that have an `id` field
  - Each feature will be stored as a key-value pair

- `POST /import/spatialite` - Import data from a SpatiaLite database
  - Upload a SpatiaLite database file (.sqlite, .db, or .spatialite)
  - Query parameters:
    - `table_name` (default: "building") - Table to import from
    - `id_column` (default: "marking_pg_id") - Column to use as ID
    - `geom_column` (default: "geom") - Geometry column name
  - Geometry data will be automatically converted to GeoJSON format

### Query Operations
- `GET /query/{id}` - Query value by ID (returns found status and value if exists)
- `GET /data/{id}` - Get a specific key-value pair by ID (returns 404 if not found)
- `GET /data` - List all keys with pagination (query params: skip, limit)

### Data Management
- `POST /data` - Create or update a key-value pair
  - Body: `{"id": "string", "value": {...}}`
- `DELETE /data/{id}` - Delete a key-value pair by ID

## Example Usage

### 1. Import GeoJSON Data
```bash
curl -X POST "http://localhost:8000/import/geojson" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_data.geojson"
```

### 2. Import SpatiaLite Data
```bash
curl -X POST "http://localhost:8000/import/spatialite?table_name=building&id_column=marking_pg_id&geom_column=geom" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@building_data.sqlite"
```

### 3. Query by ID
```bash
curl -X GET "http://localhost:8000/query/location_001"
```

### 4. Create/Update Key-Value
```bash
curl -X POST "http://localhost:8000/data" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "custom_001",
    "value": {
      "name": "Custom Location",
      "type": "office"
    }
  }'
```

### 5. List All Keys
```bash
curl -X GET "http://localhost:8000/data?skip=0&limit=10"
```

## CLI Usage

BlitzFind includes a command-line interface for easy interaction:

```bash
# Import GeoJSON file
python cli.py import sample_data.geojson

# Import SpatiaLite database
python cli.py import-spatialite building_data.sqlite --table building --id-column marking_pg_id --geom-column geom

# Query by ID
python cli.py query location_001

# Set a key-value pair
python cli.py set custom_001 '{"name": "Custom Location", "type": "office"}'

# Delete a key
python cli.py delete custom_001

# List all keys
python cli.py list --limit 10
```

## Testing

Run the test script to verify all endpoints:
```bash
python test_api.py
```

## Database

The application uses SQLite database stored in `blitzfind.db`. The database is created automatically when you first run the application.

## Sample Data

A sample GeoJSON file (`sample_data.geojson`) is included with example location data for testing the import functionality.
