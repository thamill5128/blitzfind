#!/usr/bin/env python3
"""
Demo script showing how to use Python's default sqlite3 library
to process SpatiaLite files instead of SQLAlchemy
"""

import sqlite3
import json
import tempfile
import os

def process_spatialite_with_sqlite3(db_path, table_name="building", id_column="marking_pg_id", geom_column="geom"):
    """
    Process a SpatiaLite database using Python's sqlite3 library
    
    Args:
        db_path: Path to the SpatiaLite database file
        table_name: Name of the table to process
        id_column: Column to use as ID
        geom_column: Geometry column name
    
    Returns:
        List of GeoJSON features
    """
    features = []
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    cursor = conn.cursor()
    
    try:
        # Check if it's a SpatiaLite database
        is_spatialite = False
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_ref_sys'")
            if cursor.fetchone():
                is_spatialite = True
                print(f"Detected SpatiaLite database")
        except:
            pass
        
        # Build the query based on whether it's SpatiaLite or regular SQLite
        if is_spatialite:
            # Try to load SpatiaLite extension
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
                    print(f"Successfully loaded SpatiaLite extension from: {ext_path}")
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
                print("Failed to load SpatiaLite extension, treating as regular SQLite")
        
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
        print(f"Executing query: {query}")
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
                        print(f"Warning: Could not parse geometry for ID {feature_id}")
                        geometry = None
                elif isinstance(geometry_data, dict):
                    geometry = geometry_data
            
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
            
            features.append(feature)
            print(f"Processed feature: {feature_id}")
    
    finally:
        # Close the connection
        conn.close()
    
    return features

def create_sample_spatialite_db():
    """Create a sample SpatiaLite database for demonstration"""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sqlite', delete=False) as f:
        db_path = f.name
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the building table
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

if __name__ == "__main__":
    print("SpatiaLite Processing with sqlite3 Demo")
    print("=" * 40)
    
    # Create a sample database
    print("\nCreating sample database...")
    db_path = create_sample_spatialite_db()
    print(f"Created database at: {db_path}")
    
    try:
        # Process the database
        print("\nProcessing SpatiaLite database with sqlite3...")
        features = process_spatialite_with_sqlite3(db_path)
        
        # Display results
        print(f"\nProcessed {len(features)} features:")
        for feature in features:
            print(f"\nFeature ID: {feature['id']}")
            print(f"  Geometry Type: {feature['geometry']['type'] if feature['geometry'] else 'None'}")
            print(f"  Properties: {json.dumps(feature['properties'], indent=4)}")
    
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\nCleaned up temporary database: {db_path}")