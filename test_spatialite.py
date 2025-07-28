#!/usr/bin/env python3
"""
Test script for SpatiaLite import functionality using Python's default sqlite3 library
"""

import requests
import json
import sqlite3
import tempfile
import os

def create_sample_spatialite_db():
    """Create a sample SpatiaLite database for testing"""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sqlite', delete=False) as f:
        db_path = f.name
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the building table as specified
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS building (
            marking_pg_id TEXT,
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
            geom TEXT
        )
    ''')
    
    # Insert sample data with GeoJSON geometry
    sample_data = [
        (
            'BLD001',
            'STRUCT001',
            'AOI001',
            'POI001',
            'MESH001',
            'POINT(121.5 31.2)',
            '123 Main Street',
            100.5,
            '主楼',
            50.0,
            10.0,
            json.dumps({
                "type": "Polygon",
                "coordinates": [[[121.5, 31.2], [121.51, 31.2], [121.51, 31.21], [121.5, 31.21], [121.5, 31.2]]]
            })
        ),
        (
            'BLD002',
            'STRUCT002',
            'AOI001',
            'POI002',
            'MESH001',
            'POINT(121.52 31.22)',
            '456 Second Avenue',
            80.3,
            '副楼',
            45.0,
            12.0,
            json.dumps({
                "type": "Polygon",
                "coordinates": [[[121.52, 31.22], [121.53, 31.22], [121.53, 31.23], [121.52, 31.23], [121.52, 31.22]]]
            })
        ),
        (
            'BLD003',
            'STRUCT003',
            'AOI002',
            'POI003',
            'MESH002',
            'POINT(121.54 31.24)',
            '789 Third Road',
            120.7,
            '办公楼',
            60.0,
            15.0,
            json.dumps({
                "type": "Polygon",
                "coordinates": [[[121.54, 31.24], [121.55, 31.24], [121.55, 31.25], [121.54, 31.25], [121.54, 31.24]]]
            })
        )
    ]
    
    cursor.executemany('''
        INSERT INTO building (
            marking_pg_id, struct_id, aoi_id, poi_id, mesh_id,
            centre_point, address, describe, name_ch, dsm_max, dem_min, geom
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    
    return db_path

def test_spatialite_import():
    """Test the SpatiaLite import functionality"""
    print("Creating sample SpatiaLite database...")
    db_path = create_sample_spatialite_db()
    
    try:
        # Test import via API
        print(f"\nImporting SpatiaLite database: {db_path}")
        
        with open(db_path, 'rb') as f:
            files = {'file': ('test_building.sqlite', f, 'application/octet-stream')}
            response = requests.post(
                'http://localhost:8000/import/spatialite',
                files=files,
                params={
                    'table_name': 'building',
                    'id_column': 'marking_pg_id',
                    'geom_column': 'geom'
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            print("\nImport successful!")
            print(json.dumps(result, indent=2))
            
            # Test querying the imported data
            print("\nQuerying imported data...")
            for building_id in ['BLD001', 'BLD002', 'BLD003']:
                query_response = requests.get(f'http://localhost:8000/query/{building_id}')
                if query_response.status_code == 200:
                    data = query_response.json()
                    if data['found']:
                        print(f"\nFound {building_id}:")
                        print(f"  Properties: {data['value']['properties']}")
                        print(f"  Geometry type: {data['value']['geometry']['type']}")
        else:
            print(f"\nImport failed with status code: {response.status_code}")
            print(response.text)
            
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\nCleaned up temporary database: {db_path}")

if __name__ == "__main__":
    print("SpatiaLite Import Test Script")
    print("=============================")
    print("\nMake sure the BlitzFind API is running on http://localhost:8000")
    print("Run with: python test_spatialite.py")
    
    try:
        # Check if API is running
        response = requests.get('http://localhost:8000/')
        if response.status_code == 200:
            test_spatialite_import()
        else:
            print("\nError: BlitzFind API is not responding")
    except requests.ConnectionError:
        print("\nError: Cannot connect to BlitzFind API at http://localhost:8000")
        print("Please start the API first with: python app.py")