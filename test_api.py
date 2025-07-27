import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print("Health Check:", response.json())
    print()

def test_import_geojson():
    """Test importing GeoJSON data"""
    with open("sample_data.geojson", "rb") as f:
        files = {"file": ("sample_data.geojson", f, "application/geo+json")}
        response = requests.post(f"{BASE_URL}/import/geojson", files=files)
    
    print("Import GeoJSON:", response.json())
    print()

def test_query_by_id(id):
    """Test querying by ID"""
    response = requests.get(f"{BASE_URL}/query/{id}")
    print(f"Query for ID '{id}':", response.json())
    print()

def test_create_key_value():
    """Test creating a key-value pair"""
    data = {
        "id": "custom_001",
        "value": {
            "name": "Custom Location",
            "type": "office",
            "address": "123 Main St"
        }
    }
    response = requests.post(f"{BASE_URL}/data", json=data)
    print("Create Key-Value:", response.json())
    print()

def test_list_keys():
    """Test listing all keys"""
    response = requests.get(f"{BASE_URL}/data")
    print("List Keys:", response.json())
    print()

def main():
    print("=== Testing BlitzFind API ===\n")
    
    # Test health check
    test_health_check()
    
    # Test importing GeoJSON
    print("1. Testing GeoJSON import...")
    test_import_geojson()
    
    # Test querying by ID
    print("2. Testing query by ID...")
    test_query_by_id("location_001")
    test_query_by_id("location_999")  # Non-existent ID
    
    # Test creating custom key-value
    print("3. Testing create key-value...")
    test_create_key_value()
    
    # Test listing keys
    print("4. Testing list keys...")
    test_list_keys()

if __name__ == "__main__":
    main()