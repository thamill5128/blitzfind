#!/usr/bin/env python3
"""
BlitzFind CLI - Command line interface for BlitzFind API
"""

import argparse
import requests
import json
import sys
from typing import Optional

class BlitzFindCLI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def import_geojson(self, filepath: str) -> dict:
        """Import GeoJSON file to the database"""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath, f, 'application/geo+json')}
                response = requests.post(f"{self.base_url}/import/geojson", files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def import_spatialite(self, filepath: str, table_name: str = "building", 
                         id_column: str = "marking_pg_id", geom_column: str = "geom") -> dict:
        """Import SpatiaLite database file"""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath, f, 'application/octet-stream')}
                params = {
                    'table_name': table_name,
                    'id_column': id_column,
                    'geom_column': geom_column
                }
                response = requests.post(f"{self.base_url}/import/spatialite", 
                                       files=files, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def query(self, id: str) -> dict:
        """Query value by ID"""
        try:
            response = requests.get(f"{self.base_url}/query/{id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def set_value(self, id: str, value: dict) -> dict:
        """Set a key-value pair"""
        try:
            data = {"id": id, "value": value}
            response = requests.post(f"{self.base_url}/data", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def delete(self, id: str) -> dict:
        """Delete a key-value pair"""
        try:
            response = requests.delete(f"{self.base_url}/data/{id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_keys(self, skip: int = 0, limit: int = 100) -> dict:
        """List all keys"""
        try:
            response = requests.get(f"{self.base_url}/data", params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='BlitzFind CLI - Simple key-value query system')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import GeoJSON file')
    import_parser.add_argument('file', help='Path to GeoJSON file')
    
    # Import SpatiaLite command
    import_spatialite_parser = subparsers.add_parser('import-spatialite', help='Import SpatiaLite database')
    import_spatialite_parser.add_argument('file', help='Path to SpatiaLite database file')
    import_spatialite_parser.add_argument('--table', default='building', help='Table name (default: building)')
    import_spatialite_parser.add_argument('--id-column', default='marking_pg_id', help='ID column (default: marking_pg_id)')
    import_spatialite_parser.add_argument('--geom-column', default='geom', help='Geometry column (default: geom)')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query value by ID')
    query_parser.add_argument('id', help='ID to query')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set a key-value pair')
    set_parser.add_argument('id', help='ID for the key-value pair')
    set_parser.add_argument('value', help='JSON value (as string)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a key-value pair')
    delete_parser.add_argument('id', help='ID to delete')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all keys')
    list_parser.add_argument('--skip', type=int, default=0, help='Number of items to skip')
    list_parser.add_argument('--limit', type=int, default=100, help='Maximum number of items to return')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = BlitzFindCLI(args.url)
    
    # Execute command
    if args.command == 'import':
        result = cli.import_geojson(args.file)
    elif args.command == 'import-spatialite':
        result = cli.import_spatialite(args.file, args.table, args.id_column, args.geom_column)
    elif args.command == 'query':
        result = cli.query(args.id)
    elif args.command == 'set':
        try:
            value = json.loads(args.value)
            result = cli.set_value(args.id, value)
        except json.JSONDecodeError:
            print("Error: Invalid JSON value")
            sys.exit(1)
    elif args.command == 'delete':
        result = cli.delete(args.id)
    elif args.command == 'list':
        result = cli.list_keys(args.skip, args.limit)
    
    # Print result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()