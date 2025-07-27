# SpatiaLite Import Feature

## Overview
The BlitzFind API now supports importing data from SpatiaLite databases. This feature allows you to import spatial data stored in SQLite/SpatiaLite format, automatically converting geometry data to GeoJSON format.

## Features
- Import data from SQLite/SpatiaLite database files (.sqlite, .db, .spatialite)
- Automatic detection of SpatiaLite vs regular SQLite databases
- Geometry conversion from SpatiaLite format or GeoJSON strings to GeoJSON objects
- Configurable table name, ID column, and geometry column
- Support for the building table schema as specified

## Table Schema Support
The implementation supports the following building table schema:
```sql
CREATE TABLE IF NOT EXISTS 'building' (
    marking_pg_id TEXT,    -- Used as the primary ID
    struct_id TEXT,
    aoi_id TEXT,
    poi_id TEXT,
    mesh_id TEXT,
    centre_point TEXT,
    address TEXT,
    describe REAL,
    name_ch TEXT,
    dsm_max REAL,
    dem_min REAL,
    "geom" POLYGON        -- Geometry column (stored as GeoJSON string)
);
```

## API Endpoint

### POST /import/spatialite
Import data from a SpatiaLite database file.

**Parameters:**
- `file`: The database file to upload (multipart/form-data)
- `table_name`: Name of the table to import (default: "building")
- `id_column`: Column to use as ID (default: "marking_pg_id")
- `geom_column`: Geometry column name (default: "geom")

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/import/spatialite?table_name=building&id_column=marking_pg_id&geom_column=geom" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@building_data.sqlite"
```

**Response:**
```json
{
  "message": "SpatiaLite data imported successfully",
  "imported": 3,
  "updated": 0,
  "total_records": 3,
  "table": "building",
  "spatialite_detected": false
}
```

## CLI Usage

The CLI tool also supports SpatiaLite import:

```bash
python cli.py import-spatialite building_data.sqlite --table building --id-column marking_pg_id --geom-column geom
```

## Implementation Details

1. **Database Detection**: The system automatically detects whether the uploaded file is a true SpatiaLite database (with spatial_ref_sys table) or a regular SQLite database with geometry stored as GeoJSON strings.

2. **Geometry Handling**: 
   - For SpatiaLite databases: Attempts to use the AsGeoJSON() function
   - For regular SQLite: Assumes geometry is already stored as GeoJSON string
   - Parses and validates geometry data before storage

3. **Data Conversion**: Each row from the database is converted to a GeoJSON Feature with:
   - `id`: From the specified ID column
   - `geometry`: Parsed from the geometry column
   - `properties`: All other columns (excluding ID and geometry columns)

4. **Error Handling**: 
   - Validates file extensions
   - Handles missing or invalid geometry data
   - Provides detailed error messages

## Testing

A test script (`test_spatialite.py`) is provided to demonstrate the functionality:

```bash
python3 test_spatialite.py
```

This script:
1. Creates a sample SQLite database with the building table schema
2. Inserts test data with GeoJSON geometry strings
3. Imports the data using the API
4. Queries the imported data to verify correctness

## Requirements

The following Python packages are required:
- fastapi
- sqlalchemy
- geojson
- shapely (for geometry validation)
- geoalchemy2 (for spatial database support)