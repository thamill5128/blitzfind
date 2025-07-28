from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, JSON, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import geojson
from datetime import datetime
import os
import tempfile
import shutil
import re
import sqlite3

# Create FastAPI app
app = FastAPI(title="BlitzFind API", description="Simple key-value query system with GeoJSON support")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blitzfind.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class KeyValueStore(Base):
    __tablename__ = "key_value_store"
    
    id = Column(String, primary_key=True, index=True)
    value = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class KeyValueCreate(BaseModel):
    id: str
    value: Dict[str, Any]

class KeyValueResponse(BaseModel):
    id: str
    value: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class QueryResponse(BaseModel):
    found: bool
    id: Optional[str] = None
    value: Optional[Dict[str, Any]] = None

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API endpoints
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"message": "BlitzFind API is running", "version": "1.0.0"}

@app.post("/import/geojson", tags=["Import"])
async def import_geojson(file: UploadFile = File(...)):
    """
    Import data from a GeoJSON file. 
    Each feature's ID will be used as the key, and the feature itself as the value.
    """
    if not file.filename.endswith('.geojson') and not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a GeoJSON file")
    
    try:
        # Read and parse the GeoJSON file
        content = await file.read()
        data = geojson.loads(content.decode('utf-8'))
        
        if not isinstance(data, geojson.FeatureCollection):
            raise HTTPException(status_code=400, detail="Invalid GeoJSON: must be a FeatureCollection")
        
        db = next(get_db())
        imported_count = 0
        updated_count = 0
        
        # Import each feature
        for feature in data.features:
            # Use feature id or generate one from properties
            feature_id = None
            if hasattr(feature, 'id') and feature.id:
                feature_id = str(feature.id)
            elif feature.properties and 'id' in feature.properties:
                feature_id = str(feature.properties['id'])
            else:
                # Skip features without ID
                continue
            
            # Check if record exists
            existing = db.query(KeyValueStore).filter(KeyValueStore.id == feature_id).first()
            
            if existing:
                # Update existing record
                existing.value = feature
                existing.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new record
                new_record = KeyValueStore(
                    id=feature_id,
                    value=feature
                )
                db.add(new_record)
                imported_count += 1
        
        db.commit()
        
        return {
            "message": "GeoJSON imported successfully",
            "imported": imported_count,
            "updated": updated_count,
            "total_features": len(data.features)
        }
        
    except geojson.GeoJSONError as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing file: {str(e)}")

@app.post("/import/spatialite", tags=["Import"])
async def import_spatialite(
    file: UploadFile = File(...),
    table_name: str = "building",
    id_column: str = "marking_pg_id",
    geom_column: str = "geom"
):
    """
    Import data from a SpatiaLite database file.
    
    Parameters:
    - file: The SpatiaLite database file
    - table_name: Name of the table to import (default: "building")
    - id_column: Column to use as ID (default: "marking_pg_id")
    - geom_column: Geometry column name (default: "geom")
    """
    if not file.filename.endswith('.sqlite') and not file.filename.endswith('.db') and not file.filename.endswith('.spatialite'):
        raise HTTPException(status_code=400, detail="File must be a SpatiaLite database file (.sqlite, .db, or .spatialite)")
    
    # Create a temporary file to store the uploaded database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as tmp_file:
        try:
            # Write uploaded file to temporary location
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Connect to the SpatiaLite database using sqlite3
            conn = sqlite3.connect(tmp_file.name)
            conn.row_factory = sqlite3.Row  # This allows column access by name
            cursor = conn.cursor()
            
            db = next(get_db())
            imported_count = 0
            updated_count = 0
            
            # Check if it's a SpatiaLite database
            is_spatialite = False
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_ref_sys'")
                if cursor.fetchone():
                    is_spatialite = True
            except:
                pass
            
            # Build the query based on whether it's SpatiaLite or regular SQLite
            if is_spatialite:
                # Try to load SpatiaLite extension from various paths
                spatialite_loaded = False
                extension_paths = [
                    'mod_spatialite',  # Default
                    '/opt/homebrew/lib/mod_spatialite',  # Homebrew on macOS ARM
                    '/usr/local/lib/mod_spatialite',  # Homebrew on macOS Intel
                    '/usr/lib/x86_64-linux-gnu/mod_spatialite',  # Ubuntu/Debian
                    '/usr/lib64/mod_spatialite',  # RHEL/CentOS
                ]
                
                # Enable extension loading
                conn.enable_load_extension(True)
                
                for ext_path in extension_paths:
                    try:
                        cursor.execute(f"SELECT load_extension('{ext_path}')")
                        spatialite_loaded = True
                        print(f"Successfully loaded SpatiaLite from: {ext_path}")
                        break
                    except Exception as e:
                        continue
                
                if spatialite_loaded:
                    # Use AsGeoJSON for SpatiaLite
                    query = f"""
                        SELECT 
                            {id_column} as id,
                            AsGeoJSON({geom_column}) as geometry_json,
                            *
                        FROM {table_name}
                        WHERE {id_column} IS NOT NULL
                    """
                else:
                    # If extension loading fails, treat as regular SQLite
                    is_spatialite = False
                    print("Failed to load SpatiaLite extension from any known path")
            
            if not is_spatialite:
                # For regular SQLite, assume geometry is already stored as GeoJSON string
                query = f"""
                    SELECT 
                        {id_column} as id,
                        {geom_column} as geometry_json,
                        *
                    FROM {table_name}
                    WHERE {id_column} IS NOT NULL
                """
            
            # Execute query
            cursor.execute(query)
            
            # Process each row
            for row in cursor:
                # Convert sqlite3.Row to dict
                row_dict = dict(row)
                feature_id = str(row_dict['id'])
                
                # Parse geometry
                geometry = None
                geometry_data = row_dict.get('geometry_json')
                
                if geometry_data:
                    if isinstance(geometry_data, str):
                        try:
                            # Try to parse as JSON
                            geometry = json.loads(geometry_data)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, skip this geometry
                            geometry = None
                    elif isinstance(geometry_data, dict):
                        geometry = geometry_data
                
                # If geometry is still null, try to use centre_point as fallback
                if geometry is None and 'centre_point' in row_dict:
                    centre_point = row_dict.get('centre_point')
                    if centre_point and isinstance(centre_point, str):
                        # Parse WKT format (e.g., "POINT Z (116.42115915 39.98681646 13.26017761)")
                        match = re.search(r'POINT\s*(?:Z\s*)?\(([\d.\s-]+)\)', centre_point)
                        if match:
                            coords = match.group(1).split()
                            if len(coords) >= 2:
                                geometry = {
                                    "type": "Point",
                                    "coordinates": [float(coords[0]), float(coords[1])]
                                }
                                # Add Z coordinate if present
                                if len(coords) >= 3:
                                    geometry["coordinates"].append(float(coords[2]))
                
                # Remove special columns from properties
                properties = {k: v for k, v in row_dict.items() 
                            if k not in ['id', 'geometry_json', geom_column] and v is not None}
                
                # Create GeoJSON feature
                feature = {
                    "type": "Feature",
                    "id": feature_id,
                    "geometry": geometry,
                    "properties": properties
                }
                
                # Check if record exists
                existing = db.query(KeyValueStore).filter(KeyValueStore.id == feature_id).first()
                
                if existing:
                    # Update existing record
                    existing.value = feature
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new record
                    new_record = KeyValueStore(
                        id=feature_id,
                        value=feature
                    )
                    db.add(new_record)
                    imported_count += 1
            
            db.commit()
            
            # Close the sqlite3 connection
            conn.close()
            
            return {
                "message": "SpatiaLite data imported successfully",
                "imported": imported_count,
                "updated": updated_count,
                "total_records": imported_count + updated_count,
                "table": table_name,
                "spatialite_detected": is_spatialite
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error importing SpatiaLite file: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)

@app.post("/data", tags=["Data"])
async def create_key_value(data: KeyValueCreate):
    """Create or update a key-value pair"""
    db = next(get_db())
    
    # Check if key exists
    existing = db.query(KeyValueStore).filter(KeyValueStore.id == data.id).first()
    
    if existing:
        # Update existing
        existing.value = data.value
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return KeyValueResponse(
            id=existing.id,
            value=existing.value,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )
    else:
        # Create new
        new_record = KeyValueStore(id=data.id, value=data.value)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return KeyValueResponse(
            id=new_record.id,
            value=new_record.value,
            created_at=new_record.created_at,
            updated_at=new_record.updated_at
        )

@app.get("/query/{id}", tags=["Query"])
async def query_by_id(id: str):
    """Query value by ID"""
    db = next(get_db())
    record = db.query(KeyValueStore).filter(KeyValueStore.id == id).first()
    
    if record:
        return QueryResponse(
            found=True,
            id=record.id,
            value=record.value
        )
    else:
        return QueryResponse(
            found=False,
            id=id,
            value=None
        )

@app.get("/data/{id}", tags=["Data"])
async def get_key_value(id: str):
    """Get a specific key-value pair by ID"""
    db = next(get_db())
    record = db.query(KeyValueStore).filter(KeyValueStore.id == id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail=f"ID '{id}' not found")
    
    return KeyValueResponse(
        id=record.id,
        value=record.value,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

@app.delete("/data/{id}", tags=["Data"])
async def delete_key_value(id: str):
    """Delete a key-value pair by ID"""
    db = next(get_db())
    record = db.query(KeyValueStore).filter(KeyValueStore.id == id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail=f"ID '{id}' not found")
    
    db.delete(record)
    db.commit()
    
    return {"message": f"ID '{id}' deleted successfully"}

@app.get("/data", tags=["Data"])
async def list_keys(skip: int = 0, limit: int = 100):
    """List all keys with pagination"""
    db = next(get_db())
    total = db.query(KeyValueStore).count()
    records = db.query(KeyValueStore).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": record.id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            }
            for record in records
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)